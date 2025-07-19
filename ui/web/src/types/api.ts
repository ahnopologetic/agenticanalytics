// Common API response types
export type ApiResponse<T> = {
    data: T;
    status: number;
    message?: string;
};

// Error response type
export type ApiError = {
    message: string;
    status: number;
    errors?: Record<string, string[]>;
};

// Pagination response wrapper
export type PaginatedResponse<T> = {
    data: T[];
    meta: {
        total: number;
        currentPage: number;
        lastPage: number;
        perPage: number;
    };
};

// Re-export existing types from api.ts
export type {
    Session,
    TrackingPlanEvent,
    UserSession,
    UserSessionResponse,
    Plan,
    PlanEvent,
    GithubRepoInfo
} from '../api';

// Define additional types for API endpoints
export type Repo = {
    id: number;
    name: string;
    description: string;
    url: string;
    session_id?: string;
    created_at: Date;
    updated_at: Date;
};

export type GithubRepo = {
    id: number;
    name: string;
    full_name: string;
    description: string;
    html_url: string;
    private: boolean;
    owner: {
        login: string;
        avatar_url: string;
    };
};

// Request payload types
export type SaveGithubTokenPayload = {
    github_token: string;
};

export type CloneRepoPayload = {
    repo_name: string;
};

export type TalkToAgentPayload = {
    message: string;
    context: {
        user_id: string;
    };
}; 