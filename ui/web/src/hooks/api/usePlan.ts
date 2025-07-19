import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PlanService } from '../../services/api.service';
import { type Plan, type PlanEvent } from '../../types/api';

// Hook for fetching plans for a specific repository
export const usePlans = (repoId: string, enabled = true) => {
  return useQuery({
    queryKey: ['plan', 'list', repoId],
    queryFn: () => PlanService.listPlans(repoId),
    enabled: enabled && !!repoId,
  });
};

// Hook for fetching a specific plan
export const usePlan = (planId: string, enabled = true) => {
  return useQuery({
    queryKey: ['plan', planId],
    queryFn: () => PlanService.getPlan(planId),
    enabled: enabled && !!planId,
  });
};

// Hook for creating a plan
export const useCreatePlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (plan: Omit<Plan, 'id' | 'created_at' | 'updated_at'>) => 
      PlanService.createPlan(plan),
    onSuccess: (data) => {
      // Invalidate relevant queries after successful plan creation
      queryClient.invalidateQueries({ 
        queryKey: ['plan', 'list', data.repo_id] 
      });
    },
  });
};

// Hook for updating a plan
export const useUpdatePlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ planId, plan }: { 
      planId: string; 
      plan: Partial<Plan> 
    }) => PlanService.updatePlan(planId, plan),
    onSuccess: (data) => {
      // Invalidate relevant queries after successful plan update
      queryClient.invalidateQueries({ queryKey: ['plan', data.id] });
      queryClient.invalidateQueries({ 
        queryKey: ['plan', 'list', data.repo_id] 
      });
    },
  });
};

// Hook for deleting a plan
export const useDeletePlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (planId: string) => PlanService.deletePlan(planId),
    onSuccess: (_, planId) => {
      // Invalidate the specific plan query and all plan lists
      queryClient.invalidateQueries({ queryKey: ['plan', planId] });
      queryClient.invalidateQueries({ 
        queryKey: ['plan', 'list'] 
      });
    },
  });
};

// Hook for fetching plan events
export const usePlanEvents = (planId: string, enabled = true) => {
  return useQuery({
    queryKey: ['plan', planId, 'events'],
    queryFn: () => PlanService.listPlanEvents(planId),
    enabled: enabled && !!planId,
  });
};

// Hook for creating a plan event
export const useCreatePlanEvent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (event: Omit<PlanEvent, 'id' | 'created_at' | 'updated_at'>) => 
      PlanService.createPlanEvent(event),
    onSuccess: (data) => {
      // Invalidate relevant queries after successful event creation
      queryClient.invalidateQueries({ 
        queryKey: ['plan', data.plan_id, 'events'] 
      });
    },
  });
};

// Hook for updating a plan event
export const useUpdatePlanEvent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ eventId, event }: { 
      eventId: string; 
      event: Partial<PlanEvent> 
    }) => PlanService.updatePlanEvent(eventId, event),
    onSuccess: (data) => {
      // Invalidate relevant queries after successful event update
      queryClient.invalidateQueries({ 
        queryKey: ['plan', data.plan_id, 'events'] 
      });
    },
  });
};

// Hook for deleting a plan event
export const useDeletePlanEvent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (eventId: string) => PlanService.deletePlanEvent(eventId),
    onSuccess: () => {
      // Since we don't know the plan_id from the response, we invalidate all plan events queries
      queryClient.invalidateQueries({ 
        queryKey: ['plan'],
        predicate: (query) => query.queryKey[2] === 'events'
      });
    },
  });
};

// Hook for exporting plan events
export const useExportPlanEvents = () => {
  return useMutation({
    mutationFn: (planId: string) => PlanService.exportPlanEvents(planId),
  });
};

// Hook for importing plan events
export const useImportPlanEvents = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ planId, file }: { planId: string; file: File }) => 
      PlanService.importPlanEvents(planId, file),
    onSuccess: (_, { planId }) => {
      // Invalidate plan events queries for the specific plan
      queryClient.invalidateQueries({ 
        queryKey: ['plan', planId, 'events'] 
      });
    },
  });
}; 