import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { saveGithubToken, talkToAgent } from '../../api'
import type { Repo } from '../../api'
import { useUserContext } from '../../hooks/use-user-context'
import { supabase } from '../../supabaseClient'
import ConnectGitHubStep from './github-connect/ConnectGitHubStep'
import LabelReposStep from './github-connect/LabelReposStep'
import SelectReposStep from './github-connect/SelectReposStep'
import StartIndexingStep from './github-connect/StartIndexingStep'

// type Repo = { id: number; name: string } // Now using unified Repo type from api.ts
// type GitHubRepo = { id: number; full_name: string }

type RepoLabelState = { [repoId: number]: string }

const stepLabels = [
  'Connect GitHub',
  'Select Repos',
  'Label/Explain',
  'Start Indexing',
]

const GitHubConnect = () => {
  const [step, setStep] = useState(1)
  // Remove repos state, handled by SelectReposStep
  const [selectedRepos, setSelectedRepos] = useState<Repo[]>([])
  const [repoLabels, setRepoLabels] = useState<RepoLabelState>({})
  const [connected, setConnected] = useState(false)
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexingStarted, setIndexingStarted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { user } = useUserContext()

  if (!user || user.id === null) {
    navigate('/login')
  }

  useEffect(() => {
    const checkSessions = async () => {
      if (!user) return
      const res = await getUserSessions(user.id)
      if (res.sessions && res.sessions.length > 0) {
        navigate('/home', { replace: true })
      }
    }
    checkSessions()
    const checkUser = async () => {
      // Check for GitHub identity
      const githubIdentity = user?.identities?.find(
        (id: { provider: string }) => id.provider === 'github'
      )
      if (githubIdentity) {
        setConnected(true)
        setStep(2)
        // Save GitHub token to backend if available
        if (githubIdentity.identity_data?.access_token) {
          try {
            await saveGithubToken(githubIdentity.identity_data.access_token)
          } catch {
            setError('Failed to save GitHub token to backend.')
          }
        }
        // No need to fetch repos here
      } else {
        setConnected(false)
        setStep(1)
      }
    }
    checkUser()
  }, [navigate, user, user?.id])

  const handleConnectGitHub = async () => {
    await supabase.auth.signInWithOAuth({ provider: 'github' })
  }
  const handleRepoToggle = (repo: Repo) => {
    setSelectedRepos(prev =>
      prev.map(r => r.id).includes(repo.id)
        ? prev.filter(r => r.id !== repo.id)
        : [...prev, repo]
    )
  }

  const handleContinueToLabel = () => {
    // Initialize labels for selected repos if not already set
    const initialLabels: RepoLabelState = {}
    selectedRepos.forEach(repo => {
      initialLabels[repo.id] = repoLabels[repo.id] || ''
    })
    setRepoLabels(initialLabels)
    setStep(3)
  }

  const handleLabelChange = (repoId: number, value: string) => {
    setRepoLabels(prev => ({ ...prev, [repoId]: value }))
  }

  const handleContinueToIndex = () => {
    setStep(4)
  }

  const handleStartIndexing = async () => {
    for (const repo of selectedRepos) {
      await talkToAgent('repo-reader', repo.name, user!.id, repo.name)
    }
    setIsIndexing(true)
    setTimeout(() => {
      setIsIndexing(false)
      setIndexingStarted(true)
      navigate('/home')
    }, 2000) // Mock indexing delay
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <ul className="steps w-full max-w-xl mb-8 steps-horizontal">
        {stepLabels.map((label, idx) => (
          <li
            key={label}
            className={`step${step > idx ? ' step-primary' : ''}`}
          >
            {label}
          </li>
        ))}
      </ul>
      <h1 className="text-2xl font-bold mb-8">Connect your GitHub</h1>
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {step === 1 && !connected && (
        <ConnectGitHubStep onConnect={handleConnectGitHub} />
      )}
      {step === 2 && connected && (
        <SelectReposStep
          selectedRepos={selectedRepos}
          onToggle={handleRepoToggle}
          onContinue={handleContinueToLabel}
        />
      )}
      {step === 3 && (
        <LabelReposStep
          selectedRepos={selectedRepos}
          repoLabels={repoLabels}
          onLabelChange={handleLabelChange}
          onContinue={handleContinueToIndex}
        />
      )}
      {step === 4 && (
        <StartIndexingStep
          selectedRepos={selectedRepos}
          repoLabels={repoLabels}
          isIndexing={isIndexing}
          indexingStarted={indexingStarted}
          onStartIndexing={handleStartIndexing}
        />
      )}
    </div>
  )
}

export default GitHubConnect 