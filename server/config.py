import base64
import secrets
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    github_app_id: str = Field(..., env="GITHUB_APP_ID")
    github_app_private_key_path: str
    github_oauth_client_id: str = Field(..., env="GITHUB_OAUTH_CLIENT_ID")
    github_oauth_client_secret: str = Field(..., env="GITHUB_OAUTH_CLIENT_SECRET")
    fernet_secret_str: str | None = Field(None, env="FERNET_SECRET")
    base_url: str = Field(..., env="BASE_URL")
    frontend_base_url: str = Field(..., env="FRONTEND_BASE_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # db
    db_url: str = Field(..., env="DB_URL")
    supabase_access_token: str = Field(..., env="SUPABASE_ACCESS_TOKEN")
    supabase_project_ref: str = Field(..., env="SUPABASE_PROJECT_REF")

    repo_reader_prompt_path: str = Field(..., env="REPO_READER_PROMPT_PATH")
    repomix_agent_prompt_path: str = Field(..., env="REPOMIX_AGENT_PROMPT_PATH")
    pattern_matching_analyze_tracking_agent_prompt_path: str = Field(
        ..., env="PATTERN_MATCHING_ANALYZE_TRACKING_AGENT_PROMPT_PATH"
    )
    dependency_reconnaissance_agent_prompt_path: str = Field(
        ..., env="DEPENDENCY_RECONNAISSANCE_AGENT_PROMPT_PATH"
    )

    @property
    def github_app_private_key(self) -> str:
        with open(self.github_app_private_key_path, "r") as f:
            return f.read()

    @property
    def fernet_secret(self) -> bytes:
        if self.fernet_secret_str is None:
            self.fernet_secret_str = base64.urlsafe_b64encode(secrets.token_bytes(32))
        return self.fernet_secret_str


config = ServerConfig()
