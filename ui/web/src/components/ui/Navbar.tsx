import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../../supabaseClient'
import { useCallback, useEffect, useState } from 'react'

const Navbar = () => {
  const navigate = useNavigate()
  const [hasLoggedIn, setHasLoggedIn] = useState(false)
  useEffect(() => {
    const checkLoggedIn = async () => {
      const { data, error } = await supabase.auth.getSession()
      if (error) {
        console.error(error)
        setHasLoggedIn(false)
        return
      }
      setHasLoggedIn(data.session !== null)
    }
    checkLoggedIn()
  }, [])
  const handleLogout = useCallback(async () => {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }, [navigate])

  return (
    <div className="navbar bg-base-100 shadow-md px-4">
      <div className="flex-1">
        <Link to="/" className="btn btn-ghost normal-case text-xl" tabIndex={0} aria-label="Agentic Analytics Home">Agentic Analytics</Link>
      </div>
      <div className="flex-none gap-2">
        {hasLoggedIn ? (
          <>
            <Link to="/github-connect" className="btn btn-ghost" tabIndex={0} aria-label="Connect GitHub">Connect GitHub</Link>
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