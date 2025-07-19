# React Query with Axios Implementation

This document outlines the implementation of React Query with Axios for handling API calls in the application.

## Architecture

The implementation follows a layered architecture:

1. **Axios Client Layer** (`lib/axios.ts`): Base configuration for Axios with interceptors for authentication and error handling.
2. **API Service Layer** (`services/api.service.ts`): Service classes that use the Axios client to make API calls.
3. **React Query Hooks Layer** (`hooks/api/*`): Custom hooks that use React Query to manage data fetching, caching, and mutations.
4. **Component Layer**: React components that use the hooks to display data and handle user interactions.

## Key Files

- `lib/axios.ts`: Axios instance with interceptors
- `types/api.ts`: TypeScript interfaces for API requests and responses
- `services/api.service.ts`: Service classes for different API endpoints
- `hooks/api/*.ts`: React Query hooks for data fetching and mutations
- `hooks/api/index.ts`: Entry point for all API hooks

## Usage

### Fetching Data

```tsx
import { useRepos } from '../hooks/api';

const MyComponent = () => {
  const { data, isLoading, error } = useRepos();
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      {data?.map(repo => (
        <div key={repo.id}>{repo.name}</div>
      ))}
    </div>
  );
};
```

### Mutations

```tsx
import { useCreateTrackingPlanEvent } from '../hooks/api';

const MyForm = () => {
  const { mutate, isPending } = useCreateTrackingPlanEvent();
  
  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    mutate({
      repo_id: formData.get('repo_id'),
      event_name: formData.get('event_name'),
      context: formData.get('context'),
      tags: formData.get('tags').split(','),
      file_path: formData.get('file_path'),
      line_number: parseInt(formData.get('line_number')),
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={isPending}>
        {isPending ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
};
```

## React Query Configuration

The React Query client is configured in `main.tsx` with the following options:

- **staleTime**: 5 minutes (data is considered fresh for 5 minutes)
- **gcTime**: 10 minutes (unused data is garbage collected after 10 minutes)
- **retry**: 1 (failed requests are retried once)
- **refetchOnWindowFocus**: Only in production (data is refetched when the window regains focus)
- **refetchOnMount**: true (data is refetched when a component mounts)

## API Services

The API services are organized into the following classes:

- **GithubService**: GitHub-related endpoints
- **AgentService**: Agent-related endpoints
- **RepoService**: Repository-related endpoints
- **PlanService**: Plan-related endpoints

Each service class provides static methods for interacting with the API.

## Error Handling

Errors are handled at multiple levels:

1. **Axios Interceptors**: Global error handling for all API calls
2. **Service Layer**: Specific error handling for each API call
3. **React Query Hooks**: Error state management for components

## Caching Strategy

React Query handles caching automatically based on query keys. The query keys are structured hierarchically:

- `['github', 'repos']`: GitHub repositories
- `['github', 'repo-info', repoFullName]`: GitHub repository info
- `['repo', 'list']`: List of repositories
- `['repo', repoId, 'events']`: Tracking plan events for a specific repository
- `['plan', 'list', repoId]`: Plans for a specific repository
- `['plan', planId]`: Specific plan
- `['plan', planId, 'events']`: Events for a specific plan

## Adding New API Endpoints

To add a new API endpoint:

1. Add the appropriate types to `types/api.ts`
2. Add the API call to the relevant service class in `services/api.service.ts`
3. Create a new hook in the appropriate file in `hooks/api/`
4. Export the hook from `hooks/api/index.ts` 