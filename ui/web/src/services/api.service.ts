import { type AxiosRequestConfig } from 'axios';
import axiosInstance, { createAPIRequest } from '../lib/axios';
import {
    type CloneRepoPayload,
    type GithubRepo,
    type GithubRepoInfo,
    type Plan,
    type PlanEvent,
    type Repo,
    type SaveGithubTokenPayload,
    type TalkToAgentPayload,
    type TrackingPlanEvent,
    type UserSession,
    type UserSessionResponse
} from '../types/api';

// API Service class for GitHub related endpoints
export class GithubService {
    static saveToken(payload: SaveGithubTokenPayload): Promise<unknown> {
        return createAPIRequest({
            method: 'POST',
            url: '/github/token',
            data: payload
        });
    }

    static getRepos(): Promise<GithubRepo[]> {
        return createAPIRequest<GithubRepo[]>({
            method: 'GET',
            url: '/github/repos'
        });
    }

    static getReposBySessionId(sessionId: string): Promise<{ owners: Array<{ login: string, type: string, avatar_url: string, repos: Array<{ id: number, full_name: string }> }> }> {
        return createAPIRequest({
            method: 'GET',
            url: `/auth/github/repos`,
            params: { session_id: sessionId }
        });
    }

    static cloneRepo(payload: CloneRepoPayload): Promise<unknown> {
        return createAPIRequest({
            method: 'POST',
            url: '/github/clone-repo',
            data: payload
        });
    }

    static getRepoInfo(repoFullName: string): Promise<GithubRepoInfo> {
        return createAPIRequest<GithubRepoInfo>({
            method: 'GET',
            url: `/github/info`,
            params: { repo: repoFullName }
        });
    }
}

// API Service class for Agent related endpoints
export class AgentService {
    static createTask(payload: TalkToAgentPayload): Promise<unknown> {
        return createAPIRequest({
            method: 'POST',
            url: '/agent/create-task',
            data: payload
        });
    }

    static getSessions(): Promise<UserSessionResponse> {
        return createAPIRequest<UserSessionResponse>({
            method: 'GET',
            url: '/agent/sessions'
        });
    }

    static getSession(sessionId: string): Promise<UserSession> {
        return createAPIRequest<UserSession>({
            method: 'GET',
            url: '/agent/sessions/session',
            params: { session_id: sessionId }
        });
    }
}

// API Service class for Repository related endpoints
export class RepoService {
    static listRepos(): Promise<Repo[]> {
        return createAPIRequest<Repo[]>({
            method: 'GET',
            url: '/repo/'
        });
    }

    static listTrackingPlanEvents(repoId: string): Promise<TrackingPlanEvent[]> {
        return createAPIRequest<TrackingPlanEvent[]>({
            method: 'GET',
            url: `/repo/${repoId}/events`
        });
    }

    static createTrackingPlanEvent(event: Omit<TrackingPlanEvent, 'id' | 'created_at'>): Promise<TrackingPlanEvent> {
        return createAPIRequest<TrackingPlanEvent>({
            method: 'POST',
            url: '/repo/events',
            data: event
        });
    }

    static updateTrackingPlanEvent(eventId: string, event: Partial<TrackingPlanEvent>): Promise<TrackingPlanEvent> {
        return createAPIRequest<TrackingPlanEvent>({
            method: 'PUT',
            url: `/repo/events/${eventId}`,
            data: event
        });
    }

    static deleteTrackingPlanEvent(eventId: string): Promise<void> {
        return createAPIRequest<void>({
            method: 'DELETE',
            url: `/repo/events/${eventId}`
        });
    }

    static exportTrackingPlanEvents(repoId?: string): Promise<Blob> {
        const config: AxiosRequestConfig = {
            method: 'GET',
            url: '/repo/events/export',
            responseType: 'blob'
        };

        if (repoId) {
            config.params = { repo_id: repoId };
        }

        return axiosInstance(config).then(response => response.data);
    }

    static importTrackingPlanEvents(file: File): Promise<TrackingPlanEvent[]> {
        const formData = new FormData();
        formData.append('file', file);

        return axiosInstance({
            method: 'POST',
            url: '/repo/events/import',
            data: formData,
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        }).then(response => response.data);
    }
}

// API Service class for Plan related endpoints
export class PlanService {
    static listPlans(repoId: string): Promise<Plan[]> {
        return createAPIRequest<Plan[]>({
            method: 'GET',
            url: `/repo/${repoId}/plans`
        });
    }

    static getPlan(planId: string): Promise<Plan> {
        return createAPIRequest<Plan>({
            method: 'GET',
            url: `/plans/${planId}`
        });
    }

    static createPlan(plan: Omit<Plan, 'id' | 'created_at' | 'updated_at'>): Promise<Plan> {
        return createAPIRequest<Plan>({
            method: 'POST',
            url: '/plans',
            data: plan
        });
    }

    static updatePlan(planId: string, plan: Partial<Plan>): Promise<Plan> {
        return createAPIRequest<Plan>({
            method: 'PUT',
            url: `/plans/${planId}`,
            data: plan
        });
    }

    static deletePlan(planId: string): Promise<void> {
        return createAPIRequest<void>({
            method: 'DELETE',
            url: `/plans/${planId}`
        });
    }

    static listPlanEvents(planId: string): Promise<PlanEvent[]> {
        return createAPIRequest<PlanEvent[]>({
            method: 'GET',
            url: `/plans/${planId}/events`
        });
    }

    static createPlanEvent(event: Omit<PlanEvent, 'id' | 'created_at' | 'updated_at'>): Promise<PlanEvent> {
        return createAPIRequest<PlanEvent>({
            method: 'POST',
            url: '/events',
            data: event
        });
    }

    static updatePlanEvent(eventId: string, event: Partial<PlanEvent>): Promise<PlanEvent> {
        return createAPIRequest<PlanEvent>({
            method: 'PUT',
            url: `/events/${eventId}`,
            data: event
        });
    }

    static deletePlanEvent(eventId: string): Promise<void> {
        return createAPIRequest<void>({
            method: 'DELETE',
            url: `/events/${eventId}`
        });
    }

    static exportPlanEvents(planId: string): Promise<Blob> {
        return axiosInstance({
            method: 'GET',
            url: `/plans/${planId}/events/export`,
            responseType: 'blob'
        }).then(response => response.data);
    }

    static importPlanEvents(planId: string, file: File): Promise<PlanEvent[]> {
        const formData = new FormData();
        formData.append('file', file);

        return axiosInstance({
            method: 'POST',
            url: `/plans/${planId}/events/import`,
            data: formData,
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        }).then(response => response.data);
    }
} 