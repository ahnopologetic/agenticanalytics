import { supabase } from './supabaseClient';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL! ?? 'http://localhost:8000';

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
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch GitHub repos');
    return res.json();
};

export type Session = {
    id: string;
    app_name: string;
    user_id: string;
    state: Record<string, unknown>;
    events: unknown[];
    last_update_time: number;
}

export const talkToAgent = async (agentId: string, text: string, userId: string) => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/agent/create-task`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
            message: text,
            context: {
                user_id: userId,
            },
        },
        )
    });
    console.log({ agentId, text, userId });
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

export type TrackingPlanEvent = {
    id?: string;
    repo_id: string;
    event_name: string;
    context: string;
    tags: string[];
    file_path: string;
    line_number: number;
    created_at?: string;
}

export type UserSession = {
    id: string;
    user_id: string;
    app_name: string;
    state: Record<string, unknown> | {
        status?: string;
        error?: string;
        dependency_found?: boolean;
        repo_id?: string;
        user_id?: string;
        session_id?: string;
        dependency_reconnaissance_output?: string;
    };
    events: unknown[];
    last_update_time: number;
}

export type UserSessionResponse = {
    sessions: UserSession[];
    error: string | null;
}

export const getUserSessionList = async (): Promise<UserSessionResponse> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/agent/sessions`, {
        headers: {
            'Content-Type': 'application/json',
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
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch user session');
    return (await res.json()) as UserSession;
};

type Repo = {
    id: number;
    name: string;
    description: string;
    url: string;
    session_id?: string;
    created_at: Date;
    updated_at: Date;
}

export const listRepos = async (): Promise<Repo[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/repo/`, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to list repos');
    return (await res.json()) as Repo[];
}

export const listTrackingPlanEvents = async (repoId: string): Promise<TrackingPlanEvent[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/repo/${repoId}/events`, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch tracking plan events');
    return await res.json();
};

export const createTrackingPlanEvent = async (event: Omit<TrackingPlanEvent, 'id' | 'created_at'>): Promise<TrackingPlanEvent> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/repo/events`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(event),
    });
    if (!res.ok) throw new Error('Failed to create tracking plan event');
    return await res.json();
};

export const updateTrackingPlanEvent = async (eventId: string, event: Partial<TrackingPlanEvent>): Promise<TrackingPlanEvent> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/repo/events/${eventId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(event),
    });
    if (!res.ok) throw new Error('Failed to update tracking plan event');
    return await res.json();
};

export const deleteTrackingPlanEvent = async (eventId: string): Promise<void> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/repo/events/${eventId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to delete tracking plan event');
};

export const exportTrackingPlanEvents = async (repoId?: string): Promise<Blob> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const url = repoId ? `${API_BASE_URL}/repo/events/export?repo_id=${repoId}` : `${API_BASE_URL}/repo/events/export`;
    const res = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to export tracking plan events');
    return await res.blob();
};

export const importTrackingPlanEvents = async (file: File): Promise<TrackingPlanEvent[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/repo/events/import`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
        body: formData,
    });
    if (!res.ok) throw new Error('Failed to import tracking plan events');
    return await res.json();
};

export type Plan = {
    id: string;
    repo_id: string;
    name: string;
    description: string;
    status: string;
    version: string;
    import_source: string;
    created_at: string;
    updated_at: string;
};

export type PlanEvent = {
    id?: string;
    plan_id: string;
    repo_id: string;
    event_name: string;
    context: string;
    tags: string[];
    file_path: string;
    line_number: number;
    created_at?: string;
    updated_at?: string;
};

// Plan CRUD
export const listPlans = async (repoId: string): Promise<Plan[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/repo/${repoId}/plans`, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch plans');
    return await res.json();
};

export const getPlan = async (planId: string): Promise<Plan> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/plans/${planId}`, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch plan');
    return await res.json();
};

export const createPlan = async (plan: Omit<Plan, 'id' | 'created_at' | 'updated_at'>): Promise<Plan> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/plans`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(plan),
    });
    if (!res.ok) throw new Error('Failed to create plan');
    return await res.json();
};

export const updatePlan = async (planId: string, plan: Partial<Plan>): Promise<Plan> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/plans/${planId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(plan),
    });
    if (!res.ok) throw new Error('Failed to update plan');
    return await res.json();
};

export const deletePlan = async (planId: string): Promise<void> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/plans/${planId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to delete plan');
};

// Plan Event CRUD
export const listPlanEvents = async (planId: string): Promise<PlanEvent[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/plans/${planId}/events`, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch plan events');
    return await res.json();
};

export const createPlanEvent = async (event: Omit<PlanEvent, 'id' | 'created_at' | 'updated_at'>): Promise<PlanEvent> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/events`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(event),
    });
    if (!res.ok) throw new Error('Failed to create plan event');
    return await res.json();
};

export const updatePlanEvent = async (eventId: string, event: Partial<PlanEvent>): Promise<PlanEvent> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/events/${eventId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(event),
    });
    if (!res.ok) throw new Error('Failed to update plan event');
    return await res.json();
};

export const deletePlanEvent = async (eventId: string): Promise<void> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/events/${eventId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to delete plan event');
};

export const exportPlanEvents = async (planId: string): Promise<Blob> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/plans/${planId}/events/export`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to export plan events');
    return await res.blob();
};

export const importPlanEvents = async (planId: string, file: File): Promise<PlanEvent[]> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/plans/${planId}/events/import`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
        body: formData,
    });
    if (!res.ok) throw new Error('Failed to import plan events');
    return await res.json();
};

export type GithubRepoInfo = {
    sha: string;
    message: string;
    author: string;
    date: string;
    status: string | null;
};

export const getGithubRepoInfo = async (repoFullName: string): Promise<GithubRepoInfo> => {
    const accessToken = await getAccessToken();
    if (!accessToken) throw new Error('Not authenticated');
    const res = await fetch(`${API_BASE_URL}/github/info?repo=${encodeURIComponent(repoFullName)}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });
    if (!res.ok) throw new Error('Failed to fetch GitHub repo info');
    return await res.json();
};