import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../../supabaseClient'
import { useCallback } from 'react'

const Navbar = () => {
  const navigate = useNavigate()
  const handleLogout = useCallback(async () => {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }, [navigate])

  return (
    <nav className="flex gap-4 p-4 items-center">
      <Link to="/login" className="hover:underline">Login</Link>
      <Link to="/github-connect" className="hover:underline">GitHub Connect</Link>
      <button
        className="ml-auto px-4 py-2 rounded bg-red-600 text-white font-semibold hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-400"
        onClick={handleLogout}
        tabIndex={0}
        aria-label="Logout"
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLogout() }}
      >
        Logout
      </button>
    </nav>
  )
}

export default Navbar 