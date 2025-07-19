import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { GithubService } from '../../services/api.service';
import { type CloneRepoPayload, type SaveGithubTokenPayload } from '../../types/api';

// Hook for fetching GitHub repositories
export const useGithubRepos = () => {
    return useQuery({
        queryKey: ['github', 'repos'],
        queryFn: () => GithubService.getRepos(),
    });
};

// Hook for fetching GitHub repositories using a session_id
export const useGithubSessionRepos = (sessionId: string | null) => {
    return useQuery({
        queryKey: ['github', 'repos', sessionId],
        queryFn: () => GithubService.getReposBySessionId(sessionId!),
        enabled: !!sessionId,
    });
};

// Hook for fetching GitHub repository info
export const useGithubRepoInfo = (repoFullName: string, enabled = true) => {
    return useQuery({
        queryKey: ['github', 'repo-info', repoFullName],
        queryFn: () => GithubService.getRepoInfo(repoFullName),
        enabled: enabled && !!repoFullName,
    });
};

// Hook for saving GitHub token
export const useSaveGithubToken = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: SaveGithubTokenPayload) => GithubService.saveToken(payload),
        onSuccess: () => {
            // Invalidate relevant queries after successful token save
            queryClient.invalidateQueries({ queryKey: ['github'] });
        },
    });
};

// Hook for cloning GitHub repository
export const useCloneGithubRepo = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: CloneRepoPayload) => GithubService.cloneRepo(payload),
        onSuccess: () => {
            // Invalidate relevant queries after successful repo clone
            queryClient.invalidateQueries({ queryKey: ['github', 'repos'] });
            queryClient.invalidateQueries({ queryKey: ['repo'] });
        },
    });
}; 