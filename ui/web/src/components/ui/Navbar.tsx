import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../../supabaseClient'
import { useCallback } from 'react'
import { useUserContext } from '../../hooks/use-user-context'

import useUserSessions from '../../hooks/use-user-sessions'

const Navbar = () => {
  const navigate = useNavigate()
  const { user } = useUserContext()
  // Use the custom hook to fetch user sessions
  const userId = user?.id ?? ''
  const { data: sessionsData, isLoading: isSessionsLoading } = useUserSessions(userId)

  // Determine if the user is logged in and has sessions
  const hasLoggedIn = !!user && !!sessionsData && Array.isArray(sessionsData.sessions) && sessionsData.sessions.length > 0

  const handleLogout = useCallback(async () => {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }, [navigate])

  return (
    <div className="navbar bg-base-100 shadow-md px-4 sticky top-0 z-50 border">
      <div className="flex-1">
        <Link to="/" className="btn btn-ghost normal-case text-xl" tabIndex={0} aria-label="Agentic Analytics Home">Agentic Analytics</Link>
      </div>
      <div className="flex-none gap-2">
        {isSessionsLoading ? (
          <span className="loading loading-spinner loading-sm"></span>
        ) : hasLoggedIn ? (
          <>
            <Link to="/github-connect" className="btn btn-ghost" tabIndex={0} aria-label="Scan More Repos">Scan More Repos</Link>
            <Link to="/tracking-plan" className="btn btn-ghost" tabIndex={0} aria-label="Tracking Plan">Tracking Plan</Link>
            <button
              className="btn btn-error ml-2"
              onClick={handleLogout}
              tabIndex={0}
              aria-label="Logout"
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLogout() }}
            >
              Logout
            </button>
          </>
        ) : (
          <Link to="/login" className="btn btn-primary" tabIndex={0} aria-label="Login">Login</Link>
        )}
      </div>
    </div>
  )
}

export default Navbar 