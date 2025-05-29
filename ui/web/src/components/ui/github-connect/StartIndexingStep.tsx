type Repo = { id: number; name: string }

type StartIndexingStepProps = {
  selectedRepos: Repo[]
  repos: Repo[]
  repoLabels: { [repoId: number]: string }
  isIndexing: boolean
  indexingStarted: boolean
  onStartIndexing: () => void
}

const StartIndexingStep = ({ selectedRepos, repoLabels, isIndexing, indexingStarted, onStartIndexing }: StartIndexingStepProps) => (
  <div className="w-96 bg-white rounded shadow p-6 flex flex-col items-center">
    <h2 className="text-lg font-semibold mb-4">Ready to start indexing</h2>
    <ul className="mb-4 w-full">
      {selectedRepos.map(repo => {
        return (
          <li key={repo.id} className="mb-2">
            <span className="font-medium">{repo?.name}</span>
            <span className="ml-2 text-gray-500">{repoLabels[repo.id]}</span>
          </li>
        )
      })}
    </ul>
    <button
      className="w-full py-2 rounded bg-green-600 text-white font-semibold hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-400 disabled:opacity-50"
      onClick={onStartIndexing}
      tabIndex={0}
      aria-label="Start indexing"
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onStartIndexing() }}
      disabled={isIndexing || indexingStarted}
    >
      {isIndexing ? 'Indexing...' : indexingStarted ? 'Indexing Started!' : 'Start Indexing'}
    </button>
    {indexingStarted && <div className="mt-4 text-green-600 font-semibold">Indexing started!</div>}
  </div>
)

export default StartIndexingStep 