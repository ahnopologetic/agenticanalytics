import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { SupabaseUserProvider } from './contexts/SupabaseUserContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <SupabaseUserProvider>
      <App />
    </SupabaseUserProvider>
  </StrictMode>,
)
