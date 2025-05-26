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
    <nav className="flex gap-4 p-4 items-center">
      {
        hasLoggedIn ? (
          <>
            <Link to="/github-connect" className="hover:underline">Connect GitHub</Link>
          </>
        ) : (
          <Link to="/login" className="hover:underline">Login</Link>
        )
      }
      {
        hasLoggedIn ? (
          <button
            className="ml-auto px-4 py-2 rounded bg-red-600 text-white font-semibold hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-400"
            onClick={handleLogout}
            tabIndex={0}
            aria-label="Logout"
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLogout() }}
          >
            Logout
          </button>
        ) : undefined
      }
    </nav>
  )
}

export default Navbar 