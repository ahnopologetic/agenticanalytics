type Repo = { id: number; name: string }

type SelectReposStepProps = {
  repos: Repo[]
  selectedRepos: number[]
  onToggle: (repoId: number) => void
  onContinue: () => void
}

const SelectReposStep = ({ repos, selectedRepos, onToggle, onContinue }: SelectReposStepProps) => (
  <div className="w-96 bg-white rounded shadow p-6">
    <h2 className="text-lg font-semibold mb-4">Select repositories to scan</h2>
    <ul>
      {repos.map(repo => (
        <li key={repo.id} className="mb-2 flex items-center">
          <input
            id={`repo-${repo.id}`}
            type="checkbox"
            checked={selectedRepos.includes(repo.id)}
            onChange={() => onToggle(repo.id)}
            className="mr-2"
            aria-label={`Select ${repo.name}`}
          />
          <label htmlFor={`repo-${repo.id}`} className="cursor-pointer select-none">
            {repo.name}
          </label>
        </li>
      ))}
    </ul>
    <button
      className="mt-6 w-full py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
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

export default SelectReposStep 