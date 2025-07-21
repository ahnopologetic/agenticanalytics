import { useQueryClient } from '@tanstack/react-query';
import { GithubService } from '../services/api.service';
import { type CloneRepoPayload, type GithubRepo, type GithubRepoInfo, type SaveGithubTokenPayload } from '../types/api';
import { useApiQuery, useApiMutation } from './use-api';

/**
 * Hook for fetching GitHub repositories
 */
export function useGithubRepos() {
  return useApiQuery<GithubRepo[]>(
    ['github', 'repos'],
    () => GithubService.getAllRepos()
  );
}

/**
 * Hook for fetching GitHub repositories by session ID
 */
export function useGithubSessionRepos(sessionId: string | null) {
  return useApiQuery<{ owners: Array<{ login: string, type: string, avatar_url: string, repos: Array<{ id: number, full_name: string }> }> }>(
    ['github', 'repos', sessionId],
    () => GithubService.getReposBySessionId(sessionId!),
    { enabled: !!sessionId }
  );
}

/**
 * Hook for fetching GitHub repository info
 */
export function useGithubRepoInfo(repoFullName: string, enabled = true) {
  return useApiQuery<GithubRepoInfo>(
    ['github', 'repo-info', repoFullName],
    () => GithubService.getRepoInfo(repoFullName),
    { enabled: enabled && !!repoFullName }
  );
}

/**
 * Hook for saving GitHub token
 */
export function useSaveGithubToken() {
  const queryClient = useQueryClient();
  
  return useApiMutation<unknown, SaveGithubTokenPayload>(
    (payload) => GithubService.saveToken(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['github'] });
      }
    }
  );
}

/**
 * Hook for cloning GitHub repository
 */
export function useCloneGithubRepo() {
  const queryClient = useQueryClient();
  
  return useApiMutation<unknown, CloneRepoPayload>(
    (payload) => GithubService.cloneRepo(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['github', 'repos'] });
        queryClient.invalidateQueries({ queryKey: ['repo'] });
      }
    }
  );
} 