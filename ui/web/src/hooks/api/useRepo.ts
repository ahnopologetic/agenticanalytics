import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { RepoService } from '../../services/api.service';
import { type TrackingPlanEvent } from '../../types/api';

// Hook for fetching repositories
export const useRepos = (enabled = true) => {
    return useQuery({
        queryKey: ['repo', 'list'],
        queryFn: () => RepoService.listRepos(),
        enabled,
    });
};

// Hook for fetching tracking plan events for a specific repository
export const useTrackingPlanEvents = (repoId: string, enabled = true) => {
    return useQuery({
        queryKey: ['repo', repoId, 'events'],
        queryFn: () => RepoService.listTrackingPlanEvents(repoId),
        enabled: enabled && !!repoId,
    });
};

// Hook for creating a tracking plan event
export const useCreateTrackingPlanEvent = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (event: Omit<TrackingPlanEvent, 'id' | 'created_at'>) =>
            RepoService.createTrackingPlanEvent(event),
        onSuccess: (data) => {
            // Invalidate relevant queries after successful event creation
            queryClient.invalidateQueries({
                queryKey: ['repo', data.repo_id, 'events']
            });
        },
    });
};

// Hook for updating a tracking plan event
export const useUpdateTrackingPlanEvent = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ eventId, event }: {
            eventId: string;
            event: Partial<TrackingPlanEvent>
        }) => RepoService.updateTrackingPlanEvent(eventId, event),
        onSuccess: (data) => {
            // Invalidate relevant queries after successful event update
            queryClient.invalidateQueries({
                queryKey: ['repo', data.repo_id, 'events']
            });
        },
    });
};

// Hook for deleting a tracking plan event
export const useDeleteTrackingPlanEvent = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (eventId: string) => RepoService.deleteTrackingPlanEvent(eventId),
        onSuccess: () => {
            // Since we don't know the repo_id from the response, we invalidate all events queries
            queryClient.invalidateQueries({
                queryKey: ['repo'],
                predicate: (query) => query.queryKey[2] === 'events'
            });
        },
    });
};

// Hook for exporting tracking plan events
export const useExportTrackingPlanEvents = () => {
    return useMutation({
        mutationFn: (repoId?: string) => RepoService.exportTrackingPlanEvents(repoId),
    });
};

// Hook for importing tracking plan events
export const useImportTrackingPlanEvents = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (file: File) => RepoService.importTrackingPlanEvents(file),
        onSuccess: () => {
            // Invalidate all repo events queries
            queryClient.invalidateQueries({
                queryKey: ['repo'],
                predicate: (query) => query.queryKey[2] === 'events'
            });
        },
    });
}; 