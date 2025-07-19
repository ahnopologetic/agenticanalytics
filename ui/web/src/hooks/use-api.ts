import { useQuery, useMutation, type UseQueryOptions, type UseMutationOptions } from '@tanstack/react-query';
import { type AxiosError } from 'axios';

/**
 * Type for API errors
 */
export type ApiErrorType = AxiosError | Error;

/**
 * Wrapper for useQuery to provide consistent error handling and typing
 */
export function useApiQuery<TData>(
  queryKey: unknown[],
  queryFn: () => Promise<TData>,
  options?: Omit<UseQueryOptions<TData, ApiErrorType, TData>, 'queryKey' | 'queryFn'>
) {
  return useQuery<TData, ApiErrorType>({
    queryKey,
    queryFn,
    ...options,
  });
}

/**
 * Wrapper for useMutation to provide consistent error handling and typing
 */
export function useApiMutation<TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: Omit<UseMutationOptions<TData, ApiErrorType, TVariables>, 'mutationFn'>
) {
  return useMutation<TData, ApiErrorType, TVariables>({
    mutationFn,
    ...options,
  });
} 