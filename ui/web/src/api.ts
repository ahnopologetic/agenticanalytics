import { supabase } from './supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

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