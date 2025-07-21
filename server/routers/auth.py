from fastapi import APIRouter, Request, Response, HTTPException, Depends
from config import config
import secrets
import uuid
import httpx
from cryptography.fernet import Fernet
from structlog import get_logger
from sqlalchemy.orm import Session
from routers.deps import get_current_user
from gotrue.types import User
from utils.db_session import get_db
from db_models import Profile

router = APIRouter()

GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_USER_URL = "https://api.github.com/user"
GITHUB_API_ORGS_URL = "https://api.github.com/user/orgs"
FERNET_SECRET = config.fernet_secret
fernet = Fernet(FERNET_SECRET)

OAUTH_STATE_COOKIE = "gh_oauth_state"
OAUTH_TOKEN_COOKIE = "gh_oauth_token"

# Temporary in-memory session store for OAuth (for dev)
github_oauth_sessions = {}

FRONTEND_URL = config.frontend_base_url
logger = get_logger()


@router.get("/github/login")
async def github_oauth_login(response: Response):
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": config.github_oauth_client_id,
        "scope": "repo read:org",
        "redirect_uri": f"{config.base_url}/auth/github/callback",
        "state": state,
        "allow_signup": "false",
    }
    from urllib.parse import urlencode

    url = f"{GITHUB_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    response.set_cookie(
        OAUTH_STATE_COOKIE, state, httponly=True, secure=True, max_age=600
    )
    return Response(status_code=307, headers={"Location": url})


@router.get("/github/callback")
async def github_oauth_callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_OAUTH_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": config.github_oauth_client_id,
                "client_secret": config.github_oauth_client_secret,
                "code": code,
                "redirect_uri": f"{config.base_url}/auth/github/callback",
                "state": state,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("GitHub OAuth callback", token_resp=token_resp.json())
            raise HTTPException(
                status_code=400, detail="Failed to obtain GitHub access token."
            )
        user_resp = await client.get(
            GITHUB_API_USER_URL,
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        user_data = user_resp.json()
        github_login = user_data.get("login")
        if not github_login:
            raise HTTPException(
                status_code=400, detail="Failed to get GitHub user info."
            )
        orgs_resp = await client.get(
            GITHUB_API_ORGS_URL,
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        orgs = orgs_resp.json() if orgs_resp.status_code == 200 else []
    user_id = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from supabase import Client, create_client

            supabase: Client = create_client(
                config.supabase_url, config.supabase_service_role_key
            )
            supa_token = auth_header.split(" ", 1)[1]
            resp = supabase.auth.get_user(supa_token)
            user = resp.user
            if user and user.id:
                user_id = user.id
    except Exception:
        pass
    encrypted_token = fernet.encrypt(access_token.encode()).decode()
    if user_id:
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if profile:
            profile.name = user_data.get("name")
            profile.avatar_url = user_data.get("avatar_url")
            profile.github_token = encrypted_token
            db.add(profile)
            db.commit()
    session_id = str(uuid.uuid4())
    github_oauth_sessions[session_id] = {
        "orgs": orgs,
        "github_login": github_login,
        "encrypted_token": encrypted_token,
    }
    logger.info("Oauth token saved", encrypted_token=encrypted_token)
    redirect_url = f"{FRONTEND_URL}/github-connect?session_id={session_id}"
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/github/orgs")
async def github_oauth_orgs(session_id: str):
    session = github_oauth_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return session


@router.get("/github/repos")
async def github_oauth_repos(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # session = github_oauth_sessions.get(session_id)
    # if not session:
    #     raise HTTPException(status_code=404, detail="Session not found or expired.")
    # encrypted_token = session.get("encrypted_token")
    # if not encrypted_token:
    #     raise HTTPException(status_code=400, detail="No access token in session.")
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile or not getattr(profile, "github_token", None):
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")
    encrypted_token = profile.github_token

    try:
        access_token = fernet.decrypt(encrypted_token.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid GitHub token.")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            GITHUB_API_USER_URL,
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        user = user_resp.json()
        orgs_resp = await client.get(
            GITHUB_API_ORGS_URL,
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        orgs = orgs_resp.json() if orgs_resp.status_code == 200 else []
        # Fetch all user repos with pagination
        user_repos = []
        page = 1
        while True:
            user_repos_resp = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github+json",
                },
                params={
                    "visibility": "all",
                    "affiliation": "owner,collaborator,organization_member",
                    "per_page": 100,
                    "page": page,
                },
            )
            if user_repos_resp.status_code != 200:
                break
            data = user_repos_resp.json()
            if not data:
                break
            user_repos.extend(data)
            if len(data) < 100:
                break
            page += 1
        owners = [
            {
                "type": "user",
                "login": user.get("login"),
                "avatar_url": user.get("avatar_url"),
                "repos": user_repos,
            }
        ]
        # Fetch all org repos with pagination
        for org in orgs:
            org_login = org.get("login")
            org_avatar = org.get("avatar_url")
            org_repos = []
            page = 1
            while True:
                org_repos_resp = await client.get(
                    f"https://api.github.com/orgs/{org_login}/repos",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                    params={
                        "type": "all",
                        "per_page": 100,
                        "page": page,
                    },
                )
                if org_repos_resp.status_code != 200:
                    break
                data = org_repos_resp.json()
                if not data:
                    break
                org_repos.extend(data)
                if len(data) < 100:
                    break
                page += 1
            owners.append(
                {
                    "type": "org",
                    "login": org_login,
                    "avatar_url": org_avatar,
                    "repos": org_repos,
                }
            )
    return {"owners": owners}
