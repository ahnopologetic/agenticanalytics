import type { PlanEvent } from "../api";
import { EventService } from "../services/api.service";
import { useApiMutation } from "./use-api";

export function useCreateEvent() {
    return useApiMutation<PlanEvent, Omit<PlanEvent, 'id' | 'created_at' | 'updated_at'>>(
        (event) => EventService.createEvent(event)
    );
}

export function useBulkCreateEvents() {
    return useApiMutation<PlanEvent[], { events: Omit<PlanEvent, 'id' | 'created_at' | 'updated_at'>[] }>(
        ({ events }) => Promise.all(events.map(event => EventService.createEvent(event))).then(events => events)
    );
}