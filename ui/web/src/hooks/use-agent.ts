import { useQueryClient } from '@tanstack/react-query';
import { AgentService } from '../services/api.service';
import { type TalkToAgentPayload, type UserSession, type UserSessionResponse } from '../types/api';
import { useApiQuery, useApiMutation } from './use-api';

/**
 * Hook for fetching user sessions
 */
export function useUserSessions(enabled = true) {
  return useApiQuery<UserSessionResponse>(
    ['agent', 'sessions'],
    () => AgentService.getSessions(),
    { enabled }
  );
}

/**
 * Hook for fetching a specific user session
 */
export function useUserSession(sessionId: string, enabled = true) {
  return useApiQuery<UserSession>(
    ['agent', 'session', sessionId],
    () => AgentService.getSession(sessionId),
    { enabled: enabled && !!sessionId }
  );
}

/**
 * Hook for creating a task via agent
 */
export function useTalkToAgent() {
  const queryClient = useQueryClient();

  return useApiMutation<unknown, TalkToAgentPayload>(
    (payload) => AgentService.createTask(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['agent', 'sessions'] });
      }
    }
  );
}
