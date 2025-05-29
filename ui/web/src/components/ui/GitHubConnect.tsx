import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../../supabaseClient'
import ConnectGitHubStep from './github-connect/ConnectGitHubStep'
import SelectReposStep from './github-connect/SelectReposStep'
import LabelReposStep from './github-connect/LabelReposStep'
import StartIndexingStep from './github-connect/StartIndexingStep'
import { saveGithubToken, getGithubRepos, cloneGithubRepo } from '../../api'

// type Repo = { id: number; name: string } // Now using GitHub's repo id (number) and name (string)
type Repo = { id: number; name: string }
type GitHubRepo = { id: number; full_name: string }

type RepoLabelState = { [repoId: number]: string }

const stepLabels = [
  'Connect GitHub',
  'Select Repos',
  'Label/Explain',
  'Start Indexing',
]

const GitHubConnect = () => {
  const [step, setStep] = useState(1)
  const [repos, setRepos] = useState<Repo[]>([])
  const [selectedRepos, setSelectedRepos] = useState<Repo[]>([])
  const [repoLabels, setRepoLabels] = useState<RepoLabelState>({})
  const [connected, setConnected] = useState(false)
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexingStarted, setIndexingStarted] = useState(false)
  const [loadingRepos, setLoadingRepos] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const checkUser = async () => {
      const { data } = await supabase.auth.getUser()
      if (!data.user) {
        navigate('/login', { replace: true })
        return
      }
      // Check for GitHub identity
      const githubIdentity = data.user.identities?.find(
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
        // Fetch repos from backend
        setLoadingRepos(true)
        setError(null)
        try {
          const ghRepos: GitHubRepo[] = await getGithubRepos()
          // Map GitHub API repos to { id, name }
          setRepos(ghRepos.map((r) => ({ id: r.id, name: r.full_name })))
        } catch {
          setError('Failed to fetch GitHub repositories.')
        } finally {
          setLoadingRepos(false)
        }
      } else {
        setConnected(false)
        setStep(1)
      }
    }
    checkUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate])

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
      await cloneGithubRepo(repo.name)
    }
    setIsIndexing(true)
    setTimeout(() => {
      setIsIndexing(false)
      setIndexingStarted(true)
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
        loadingRepos ? (
          <div className="skeleton h-32 w-96"></div>
        ) : (
          <SelectReposStep
            repos={repos}
            selectedRepos={selectedRepos}
            onToggle={handleRepoToggle}
            onContinue={handleContinueToLabel}
          />
        )
      )}
      {step === 3 && (
        <LabelReposStep
          repos={repos}
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