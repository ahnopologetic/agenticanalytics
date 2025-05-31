import { supabase } from './supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL! ?? 'http://localhost:8000';

const getAccessToken = async (): Promise<string | null> => {
    const session = (await supabase.auth.getSession()).data.session;
    return session?.access_token ?? null;
};

export const saveGithubToken = async (githubToken: string) => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/github/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ github_token: githubToken }),
    });
    if (!res.ok) throw new Error('Failed to save GitHub token');
    return res.json();
};

export const getGithubRepos = async () => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/github/repos`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch GitHub repos');
    return res.json();
};

export const talkToAgent = async (agentId: string, text: string, userId: string, sessionId: string) => {
    const res = await fetch(`${API_BASE_URL}/agent/create-task`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: text,
            context: {
                user_id: userId,
                session_id: sessionId,
            },
            session_id: sessionId,
        },
        )
    });
    console.log({ agentId, text, userId, sessionId });
    if (!res.ok) throw new Error('Failed to talk to agent');
    return res.json();
};

export const cloneGithubRepo = async (repoName: string) => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/github/clone-repo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ repo_name: repoName }),
    });
    if (!res.ok) throw new Error('Failed to clone GitHub repo');
    return res.json();
};

export type UserSession = {
    id: string;
    user_id: string;
    app_name: string;
    state: Record<string, unknown>;
    events: unknown[];
    last_update_time: number;
}

export type UserSessionResponse = {
    sessions: UserSession[];
    error: string | null;
}

export const getUserSessions = async (userId: string): Promise<UserSessionResponse> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/agent/users/${userId}/sessions`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch user sessions');
    return (await res.json()) as UserSessionResponse;
};

export const getUserSession = async (sessionId: string): Promise<UserSession> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/agent/sessions/session?session_id=${sessionId}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch user session');
    return (await res.json()) as UserSession;
};

export type Repo = {
    id: number;
    name: string;
    full_name: string;
    private: boolean;
    owner?: { login: string };
    [key: string]: unknown;
};

export type Org = {
    id: number;
    login: string;
    avatar_url: string;
};

export const getGithubOrgs = async (): Promise<Org[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/github/orgs`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch GitHub orgs');
    return res.json();
};

export const getGithubOrgRepos = async (org: string): Promise<Repo[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/github/orgs/${org}/repos`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch GitHub org repos');
    return res.json();
};