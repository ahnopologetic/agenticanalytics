import { useQueryClient } from '@tanstack/react-query';
import { PlanService } from '../services/api.service';
import { type Plan, type PlanEvent } from '../types/api';
import { useApiQuery, useApiMutation } from './use-api';

/**
 * Hook for fetching plans for a specific repository
 */
export function usePlans(enabled = true) {
  return useApiQuery<Plan[]>(
    ['plan', 'list'],
    () => PlanService.listPlans(),
    { enabled: enabled }
  );
}

/**
 * Hook for fetching a specific plan
 */
export function usePlan(planId: string, enabled = true) {
  return useApiQuery<Plan>(
    ['plan', planId],
    () => PlanService.getPlan(planId),
    { enabled: enabled && !!planId }
  );
}

/**
 * Hook for creating a plan
 */
export function useCreatePlan() {
  const queryClient = useQueryClient();

  return useApiMutation<Plan, Omit<Plan, 'id' | 'created_at' | 'updated_at'>>(
    (plan) => PlanService.createPlan(plan),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries({
          queryKey: ['plan', 'list', data.user_id]
        });
      }
    }
  );
}

/**
 * Hook for updating a plan
 */
export function useUpdatePlan() {
  const queryClient = useQueryClient();

  return useApiMutation<Plan, { planId: string; plan: Partial<Plan> }>(
    ({ planId, plan }) => PlanService.updatePlan(planId, plan),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries({ queryKey: ['plan', data.id] });
        queryClient.invalidateQueries({
          queryKey: ['plan', 'list', data.id]
        });
      }
    }
  );
}

/**
 * Hook for deleting a plan
 */
export function useDeletePlan() {
  const queryClient = useQueryClient();

  return useApiMutation<void, string>(
    (planId) => PlanService.deletePlan(planId),
    {
      onSuccess: (_, planId) => {
        queryClient.invalidateQueries({ queryKey: ['plan', planId] });
        queryClient.invalidateQueries({
          queryKey: ['plan', 'list']
        });
      }
    }
  );
}

/**
 * Hook for fetching plan events
 */
export function usePlanEvents(planId: string, enabled = true) {
  return useApiQuery<PlanEvent[]>(
    ['plan', planId, 'events'],
    () => PlanService.listPlanEvents(planId),
    { enabled: enabled && !!planId }
  );
}

/**
 * Hook for creating a plan event
 */
export function useCreatePlanEvent() {
  const queryClient = useQueryClient();

  return useApiMutation<PlanEvent, Omit<PlanEvent, 'id' | 'created_at' | 'updated_at'>>(
    (event) => PlanService.createPlanEvent(event),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries({
          queryKey: ['plan', data.id, 'events']
        });
      }
    }
  );
}

/**
 * Hook for updating a plan event
 */
export function useUpdatePlanEvent() {
  const queryClient = useQueryClient();

  return useApiMutation<PlanEvent, { eventId: string; event: Partial<PlanEvent> }>(
    ({ eventId, event }) => PlanService.updatePlanEvent(eventId, event),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries({
          queryKey: ['plan', data.id, 'events']
        });
      }
    }
  );
}

/**
 * Hook for deleting a plan event
 */
export function useDeletePlanEvent() {
  const queryClient = useQueryClient();

  return useApiMutation<void, string>(
    (eventId) => PlanService.deletePlanEvent(eventId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: ['plan'],
          predicate: (query) => query.queryKey[2] === 'events'
        });
      }
    }
  );
}

/**
 * Hook for exporting plan events
 */
export function useExportPlanEvents() {
  return useApiMutation<Blob, string>(
    (planId) => PlanService.exportPlanEvents(planId)
  );
}

/**
 * Hook for importing plan events
 */
export function useImportPlanEvents() {
  const queryClient = useQueryClient();

  return useApiMutation<PlanEvent[], { planId: string; file: File }>(
    ({ planId, file }) => PlanService.importPlanEvents(planId, file),
    {
      onSuccess: (_, { planId }) => {
        queryClient.invalidateQueries({
          queryKey: ['plan', planId, 'events']
        });
      }
    }
  );
}

export function useAddReposToPlan() {
  return useApiMutation<void, { planId: string; repoIds: string[] }>(
    ({ planId, repoIds }) => PlanService.addReposToPlan(planId, repoIds)
  );
}