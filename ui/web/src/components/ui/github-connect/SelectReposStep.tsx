import { useState } from "react";

type Repo = { id: number; name: string }

type SelectReposStepProps = {
  repos: Repo[]
  selectedRepos: number[]
  onToggle: (repo: Repo) => void
  onContinue: () => void
}

const SelectReposStep = ({ repos, selectedRepos, onToggle, onContinue }: SelectReposStepProps) => {
  const [displayCount, setDisplayCount] = useState(10)

  const displayedRepos = repos.slice(0, displayCount)

  const loadMore = () => {
    setDisplayCount(prev => Math.min(prev + 10, repos.length))
  }

  return (
    <div className="w-96 bg-white rounded shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Select repositories to scan</h2>
      <div className="max-h-80 overflow-y-auto mb-4">
        <ul>
          {displayedRepos.map(repo => (
            <li key={repo.id} className="mb-2 flex items-center">
              <input
                id={`repo-${repo.id}`}
                type="checkbox"
                checked={selectedRepos.includes(repo.id)}
                onChange={() => onToggle(repo)}
                className="mr-2"
                aria-label={`Select ${repo.name}`}
              />
              <label htmlFor={`repo-${repo.id}`} className="cursor-pointer select-none">
                {repo.name}
              </label>
            </li>
          ))}
        </ul>
        {displayCount < repos.length && (
          <button
            onClick={loadMore}
            className="w-full py-2 mt-2 text-sm text-blue-600 hover:text-blue-800"
          >
            Load more repositories...
          </button>
        )}
      </div>
      <button
        className="w-full py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        onClick={onContinue}
        tabIndex={0}
        aria-label="Continue to label repositories"
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onContinue() }}
        disabled={selectedRepos.length === 0}
      >
        Continue
      </button>
    </div>
  )
}

export default SelectReposStep