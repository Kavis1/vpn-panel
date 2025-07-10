/**
 * Utility functions for React Query v5 migration
 */
import { QueryClient } from '@tanstack/react-query';

/**
 * Helper to invalidate queries with the new v5 API
 */
export const invalidateQueries = (queryClient: QueryClient, queryKey: string[]) => {
  return queryClient.invalidateQueries({ queryKey });
};

/**
 * Helper to create useQuery options object for v5 API
 */
export const createQueryOptions = <TData = unknown, TError = Error>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<TData>,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    cacheTime?: number;
    refetchOnWindowFocus?: boolean;
    retry?: boolean | number;
  }
) => ({
  queryKey,
  queryFn,
  ...options,
});

/**
 * Helper to create useMutation options object for v5 API
 */
export const createMutationOptions = <TData = unknown, TError = Error, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: TError, variables: TVariables) => void;
    onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables) => void;
  }
) => ({
  mutationFn,
  ...options,
});

/**
 * Type-safe wrapper for mutation variables
 */
export type MutationVariables<T> = T extends (...args: infer P) => any 
  ? P extends [infer First, ...any[]] 
    ? First 
    : void
  : void;
