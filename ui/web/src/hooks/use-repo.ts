import { useQueryClient } from '@tanstack/react-query';
import { RepoService } from '../services/api.service';
import { type Repo, type TrackingPlanEvent } from '../types/api';
import { useApiQuery, useApiMutation } from './use-api';

/**
 * Hook for fetching repositories
 */
export function useRepos(enabled = true) {
  return useApiQuery<Repo[]>(
    ['repo', 'list'],
    () => RepoService.listRepos(),
    { enabled }
  );
}

/**
 * Hook for fetching tracking plan events for a specific repository
 */
export function useTrackingPlanEvents(repoId: string, enabled = true) {
  return useApiQuery<TrackingPlanEvent[]>(
    ['repo', repoId, 'events'],
    () => RepoService.listTrackingPlanEvents(repoId),
    { enabled: enabled && !!repoId }
  );
}

/**
 * Hook for creating a tracking plan event
 */
export function useCreateTrackingPlanEvent() {
  const queryClient = useQueryClient();
  
  return useApiMutation<TrackingPlanEvent, Omit<TrackingPlanEvent, 'id' | 'created_at'>>(
    (event) => RepoService.createTrackingPlanEvent(event),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries({ 
          queryKey: ['repo', data.repo_id, 'events'] 
        });
      }
    }
  );
}

/**
 * Hook for updating a tracking plan event
 */
export function useUpdateTrackingPlanEvent() {
  const queryClient = useQueryClient();
  
  return useApiMutation<
    TrackingPlanEvent, 
    { eventId: string; event: Partial<TrackingPlanEvent> }
  >(
    ({ eventId, event }) => RepoService.updateTrackingPlanEvent(eventId, event),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries({ 
          queryKey: ['repo', data.repo_id, 'events'] 
        });
      }
    }
  );
}

/**
 * Hook for deleting a tracking plan event
 */
export function useDeleteTrackingPlanEvent() {
  const queryClient = useQueryClient();
  
  return useApiMutation<void, string>(
    (eventId) => RepoService.deleteTrackingPlanEvent(eventId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ 
          queryKey: ['repo'],
          predicate: (query) => query.queryKey[2] === 'events'
        });
      }
    }
  );
}

/**
 * Hook for exporting tracking plan events
 */
export function useExportTrackingPlanEvents() {
  return useApiMutation<Blob, string | undefined>(
    (repoId) => RepoService.exportTrackingPlanEvents(repoId)
  );
}

/**
 * Hook for importing tracking plan events
 */
export function useImportTrackingPlanEvents() {
  const queryClient = useQueryClient();
  
  return useApiMutation<TrackingPlanEvent[], File>(
    (file) => RepoService.importTrackingPlanEvents(file),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ 
          queryKey: ['repo'],
          predicate: (query) => query.queryKey[2] === 'events'
        });
      }
    }
  );
} 