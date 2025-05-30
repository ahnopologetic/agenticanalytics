import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { SupabaseUserProvider } from './contexts/SupabaseUserContext.tsx'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <SupabaseUserProvider>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </SupabaseUserProvider>
  </StrictMode>,
)
