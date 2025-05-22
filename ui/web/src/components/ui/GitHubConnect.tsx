import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../../supabaseClient'
import ConnectGitHubStep from './github-connect/ConnectGitHubStep'
import SelectReposStep from './github-connect/SelectReposStep'
import LabelReposStep from './github-connect/LabelReposStep'
import StartIndexingStep from './github-connect/StartIndexingStep'

const mockRepos = [
  { id: 1, name: 'agenticanlaytics/app' },
  { id: 2, name: 'agenticanlaytics/ui' },
  { id: 3, name: 'agenticanlaytics/infra' },
]

type RepoLabelState = { [repoId: number]: string }

const stepLabels = [
  'Connect GitHub',
  'Select Repos',
  'Label/Explain',
  'Start Indexing',
]

const GitHubConnect = () => {
  const [step, setStep] = useState(1)
  const [selectedRepos, setSelectedRepos] = useState<number[]>([])
  const [repoLabels, setRepoLabels] = useState<RepoLabelState>({})
  const [connected, setConnected] = useState(false)
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexingStarted, setIndexingStarted] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const checkUser = async () => {
      const { data } = await supabase.auth.getUser()
      if (!data.user) {
        navigate('/login', { replace: true })
        return
      }
      // Check for GitHub identity
      const hasGitHub = data.user.identities?.some(
        (id: { provider: string }) => id.provider === 'github'
      )
      if (hasGitHub) {
        setConnected(true)
        setStep(2)
      } else {
        setConnected(false)
        setStep(1)
      }
    }
    checkUser()
  }, [navigate])

  const handleConnectGitHub = async () => {
    await supabase.auth.signInWithOAuth({ provider: 'github' })
    // After redirect, useEffect will re-check and update state
  }

  const handleRepoToggle = (repoId: number) => {
    setSelectedRepos(prev =>
      prev.includes(repoId)
        ? prev.filter(id => id !== repoId)
        : [...prev, repoId]
    )
  }

  const handleContinueToLabel = () => {
    // Initialize labels for selected repos if not already set
    const initialLabels: RepoLabelState = {}
    selectedRepos.forEach(id => {
      initialLabels[id] = repoLabels[id] || ''
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

  const handleStartIndexing = () => {
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
      {step === 1 && !connected && (
        <ConnectGitHubStep onConnect={handleConnectGitHub} />
      )}
      {step === 2 && connected && (
        <SelectReposStep
          repos={mockRepos}
          selectedRepos={selectedRepos}
          onToggle={handleRepoToggle}
          onContinue={handleContinueToLabel}
        />
      )}
      {step === 3 && (
        <LabelReposStep
          selectedRepos={selectedRepos}
          repos={mockRepos}
          repoLabels={repoLabels}
          onLabelChange={handleLabelChange}
          onContinue={handleContinueToIndex}
        />
      )}
      {step === 4 && (
        <StartIndexingStep
          selectedRepos={selectedRepos}
          repos={mockRepos}
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