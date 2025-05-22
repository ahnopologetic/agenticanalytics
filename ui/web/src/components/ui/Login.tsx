import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../../supabaseClient'

const handleLoginWithGoogle = async () => {
  await supabase.auth.signInWithOAuth({ provider: 'google' })
}

const handleLoginWithGitHub = async () => {
  await supabase.auth.signInWithOAuth({ provider: 'github' })
}

const Login = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const checkUser = async () => {
      const { data } = await supabase.auth.getUser()
      if (data.user) {
        navigate('/github-connect', { replace: true })
      }
    }
    checkUser()
  }, [navigate])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-2xl font-bold mb-8">Sign in to Agentic Analytics</h1>
      <button
        className="w-64 py-3 mb-4 rounded text-white font-semibold shadow hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        onClick={handleLoginWithGoogle}
        tabIndex={0}
        aria-label="Sign in with Google"
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLoginWithGoogle() }}
      >
        Sign in with Google
      </button>
      <button
        className="w-64 py-3 rounded text-white font-semibold shadow hover:bg-gray-500 hover:duration-300 hover:shadow-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-gray-400"
        onClick={handleLoginWithGitHub}
        tabIndex={0}
        aria-label="Sign in with GitHub"
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLoginWithGitHub() }}
      >
        Sign in with GitHub
      </button>
    </div>
  )
}

export default Login 