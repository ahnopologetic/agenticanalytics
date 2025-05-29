type Repo = { id: number; name: string }

type LabelReposStepProps = {
  selectedRepos: Repo[]
  repos: Repo[]
  repoLabels: { [repoId: number]: string }
  onLabelChange: (repoId: number, value: string) => void
  onContinue: () => void
}

const LabelReposStep = ({ selectedRepos, repos, repoLabels, onLabelChange, onContinue }: LabelReposStepProps) => (
  <div className="w-96 bg-white rounded shadow p-6">
    <h2 className="text-lg font-semibold mb-4">Label or explain each repository</h2>
    <form onSubmit={e => { e.preventDefault(); onContinue() }}>
      {selectedRepos.map(repo => {
        return (
          <div key={repo.id} className="mb-4">
            <label htmlFor={`label-${repo.id}`} className="block font-medium mb-1">
              {repo.name}
            </label>
            <input
              id={`label-${repo.id}`}
              type="text"
              value={repoLabels[repo.id] || ''}
              onChange={e => onLabelChange(repo.id, e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Add a label or explanation"
              aria-label={`Label for ${repo.name}`}
            />
          </div>
        )
      })}
      <button
        type="submit"
        className="mt-4 w-full py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        aria-label="Continue to start indexing"
      >
        Continue
      </button>
    </form>
  </div>
)

export default LabelReposStep 