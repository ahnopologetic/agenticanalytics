import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getUserSessions } from '../../api'
import { useUserContext } from '../../hooks/use-user-context'
import { supabase } from '../../supabaseClient'

const handleLoginWithGoogle = async () => {
  await supabase.auth.signInWithOAuth({ provider: 'google' })
}

const handleLoginWithGitHub = async () => {
  await supabase.auth.signInWithOAuth({ provider: 'github', options: { redirectTo: `${window.location.origin}/github-callback` } })
}

const Login = () => {
  const navigate = useNavigate()
  const { user, loading, error } = useUserContext()

  useEffect(() => {
    const checkSessionsAndNavigate = async () => {
      if (!user) return
      try {
        const res = await getUserSessions(user.id)
        if (res.sessions && res.sessions.length > 0) {
          navigate('/home', { replace: true })
        } else {
          navigate('/github-connect', { replace: true })
        }
      } catch {
        // fallback: go to github-connect if error
        navigate('/github-connect', { replace: true })
      }
    }
    if (!loading && user) {
      checkSessionsAndNavigate()
    }
  }, [user, loading, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-base-200">
        <div className="card w-96 bg-base-100 shadow-xl flex items-center justify-center p-8">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-200">
      <div className="card w-96 bg-base-100 shadow-xl">
        <div className="card-body items-center text-center">
          <h1 className="card-title text-2xl mb-4">Sign in to Agentic Analytics</h1>
          {error && <div className="text-red-500 mb-2">{error}</div>}
          <button
            className="btn btn-outline btn-wide mb-2"
            onClick={handleLoginWithGoogle}
            tabIndex={0}
            aria-label="Sign in with Google"
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLoginWithGoogle() }}
          >
            <span className="mr-2"><svg width="20" height="20" viewBox="0 0 48 48"><g><path fill="#4285F4" d="M43.611 20.083H42V20H24v8h11.303C33.972 32.091 29.418 35 24 35c-6.065 0-11-4.935-11-11s4.935-11 11-11c2.507 0 4.805.857 6.646 2.278l6.364-6.364C33.084 6.527 28.768 5 24 5 12.954 5 4 13.954 4 25s8.954 20 20 20c11.046 0 20-8.954 20-20 0-1.341-.138-2.651-.389-3.917z" /><path fill="#34A853" d="M6.306 14.691l6.571 4.819C14.655 16.108 19.001 13 24 13c2.507 0 4.805.857 6.646 2.278l6.364-6.364C33.084 6.527 28.768 5 24 5c-6.627 0-12.24 3.438-15.694 8.691z" /><path fill="#FBBC05" d="M24 43c4.418 0 8.432-1.507 11.572-4.091l-6.857-5.627C27.03 34.091 25.564 34.5 24 34.5c-5.418 0-9.972-2.909-11.303-7.091l-6.571 4.819C7.76 39.562 13.373 43 24 43z" /><path fill="#EA4335" d="M43.611 20.083H42V20H24v8h11.303C34.64 32.091 29.418 35 24 35c-6.065 0-11-4.935-11-11s4.935-11 11-11c2.507 0 4.805.857 6.646 2.278l6.364-6.364C33.084 6.527 28.768 5 24 5c-6.627 0-12.24 3.438-15.694 8.691z" /></g></svg></span>
            Sign in with Google
          </button>
          <button
            className="btn btn-primary btn-wide"
            onClick={handleLoginWithGitHub}
            tabIndex={0}
            aria-label="Sign in with GitHub"
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLoginWithGitHub() }}
          >
            <span className="mr-2"><svg width="20" height="20" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.477 2 2 6.484 2 12.021c0 4.428 2.865 8.186 6.839 9.504.5.092.682-.217.682-.482 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.157-1.11-1.465-1.11-1.465-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.892 1.53 2.341 1.088 2.91.832.091-.647.35-1.088.636-1.339-2.221-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.025A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.295 2.748-1.025 2.748-1.025.546 1.378.202 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.847-2.337 4.695-4.566 4.944.359.309.678.919.678 1.852 0 1.336-.012 2.417-.012 2.747 0 .268.18.579.688.481C19.138 20.204 22 16.447 22 12.021 22 6.484 17.523 2 12 2Z" /></svg></span>
            Sign in with GitHub
          </button>
        </div>
      </div>
    </div>
  )
}

export default Login 