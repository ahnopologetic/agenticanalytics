# Technical Logs

### 2023-06-15
- Initial setup of the project with Vite, React, TypeScript, and TailwindCSS
- Added basic authentication with Supabase
- Created basic layout and navigation

### 2023-06-20
- Implemented GitHub OAuth integration
- Added GitHub repository listing and selection
- Created tracking plan view

### 2023-07-05
- Added React Query for data fetching
- Implemented API service layer for better organization
- Created custom hooks for API calls

### 2023-07-10
- Enhanced tracking plan UI with better visualization
- Added export/import functionality for tracking plans
- Improved error handling and loading states

### 2023-09-15
- Refactored GitHub connection flow
- Implemented React Query for GitHub repositories fetching
- Modified GitHubConnect component to skip to step 2 when repositories are available
- Added session-based repository fetching to maintain state after OAuth redirect
- Improved error handling for API requests

### 2023-09-20
- Refactored React Query implementation to use custom hooks
- Created domain-specific hooks for better organization and scalability
- Implemented consistent error handling and typing across all API calls
- Simplified component code by abstracting away React Query implementation details
- Added comprehensive documentation for the new hook-based approach
- Created centralized hooks index for easier imports
- Improved type safety with explicit type annotations
- Enhanced developer experience with simpler API for data fetching and mutations
