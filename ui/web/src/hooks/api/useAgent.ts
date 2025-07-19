import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AgentService } from '../../services/api.service';
import { type TalkToAgentPayload } from '../../types/api';

// Hook for fetching user sessions
export const useUserSessions = (enabled = true) => {
  return useQuery({
    queryKey: ['agent', 'sessions'],
    queryFn: () => AgentService.getSessions(),
    enabled,
  });
};

// Hook for fetching a specific user session
export const useUserSession = (sessionId: string, enabled = true) => {
  return useQuery({
    queryKey: ['agent', 'session', sessionId],
    queryFn: () => AgentService.getSession(sessionId),
    enabled: enabled && !!sessionId,
  });
};

// Hook for creating a task via agent
export const useTalkToAgent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (payload: TalkToAgentPayload) => AgentService.createTask(payload),
    onSuccess: () => {
      // Invalidate sessions queries to reflect the new task
      queryClient.invalidateQueries({ queryKey: ['agent', 'sessions'] });
    },
  });
}; 