import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { talkToAgent, API_BASE_URL } from '../../api'
import { useUserContext } from '../../hooks/use-user-context'
import ConnectGitHubStep from './github-connect/ConnectGitHubStep'
import LabelReposStep from './github-connect/LabelReposStep'
import StartIndexingStep from './github-connect/StartIndexingStep'

type Repo = { id: number; name: string }
type Owner = { type: 'user' | 'org'; login: string; avatar_url: string; repos: { id: number; full_name: string }[] }
type RepoLabelState = { [repoId: number]: string }

const stepLabels = [
  'Connect GitHub',
  'Select Repos',
  'Label/Explain',
  'Start Indexing',
]

const GitHubConnect = () => {
  const [step, setStep] = useState(1)
  const [owners, setOwners] = useState<Owner[]>([])
  const [selectedOwner, setSelectedOwner] = useState<string>('')
  const [selectedRepos, setSelectedRepos] = useState<Repo[]>([])
  const [repoLabels, setRepoLabels] = useState<RepoLabelState>({})
  const [connected, setConnected] = useState(false)
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexingStarted, setIndexingStarted] = useState(false)
  const [loadingRepos, setLoadingRepos] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { user } = useUserContext()

  // Check for session_id in URL (after OAuth)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const session_id = params.get('session_id')
    if (session_id) {
      setLoadingRepos(true)
      fetch(`${API_BASE_URL}/auth/github/repos?session_id=${encodeURIComponent(session_id)}`, { credentials: 'include' })
        .then(async (res) => {
          if (!res.ok) throw new Error('Failed to fetch repositories from GitHub.')
          return res.json()
        })
        .then((data) => {
          setOwners(data.owners || [])
          if (data.owners && data.owners.length > 0) {
            setSelectedOwner(data.owners[0].login)
            setStep(2)
            setConnected(true)
          }
        })
        .catch((err) => {
          setError(err.message)
        })
        .finally(() => setLoadingRepos(false))
    }
  }, [])

  if (!user || user.id === null) {
    navigate('/login')
  }

  const handleConnectGitHub = async () => {
    window.location.href = `${API_BASE_URL}/auth/github/login`;
  }

  const handleOwnerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedOwner(e.target.value)
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

  const currentOwner = owners.find(o => o.login === selectedOwner)
  const currentRepos = currentOwner ? currentOwner.repos.map(r => ({ id: r.id, name: r.full_name })) : []

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
          <div className="skeleton h-32 w-96">Loading repositories...</div>
        ) : (
          <div className="w-full max-w-lg bg-white rounded shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Select repositories to scan</h2>
            <div className="mb-4">
              <label htmlFor="owner-select" className="block font-medium mb-1">Select owner</label>
              <select
                id="owner-select"
                value={selectedOwner}
                onChange={handleOwnerChange}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                aria-label="Select owner"
              >
                {owners.map(owner => (
                  <option key={owner.login} value={owner.login}>
                    {owner.type === 'org' ? 'Org: ' : 'User: '}{owner.login}
                  </option>
                ))}
              </select>
            </div>
            <div className="max-h-80 overflow-y-auto mb-4">
              <ul>
                {currentRepos.map(repo => (
                  <li key={repo.id} className="mb-2 flex items-center">
                    <input
                      id={`repo-${repo.id}`}
                      type="checkbox"
                      checked={selectedRepos.some(r => r.id === repo.id)}
                      onChange={() => handleRepoToggle(repo)}
                      className="mr-2"
                      aria-label={`Select ${repo.name}`}
                    />
                    <label htmlFor={`repo-${repo.id}`} className="cursor-pointer select-none">
                      {repo.name}
                    </label>
                  </li>
                ))}
              </ul>
            </div>
            <button
              className="w-full py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
              onClick={handleContinueToLabel}
              tabIndex={0}
              aria-label="Continue to label repositories"
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleContinueToLabel() }}
              disabled={selectedRepos.length === 0}
            >
              Continue
            </button>
          </div>
        )
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