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
    const res = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            appName: agentId,
            userId,
            sessionId,
            newMessage: {
                parts: [
                    {
                        text
                    }
                ],
                role: 'user',
            }
        },
        )
    });
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

export const mixGithubRepos = async (repoNames: string[]) => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/github/mix-repos`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ repo_names: repoNames }),
    });
    if (!res.ok) throw new Error('Failed to mix GitHub repos');
    return res.json();
};