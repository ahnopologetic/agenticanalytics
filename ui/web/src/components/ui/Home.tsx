import { useState } from 'react'

// Mocked repo data (replace with real data from backend later)
const mockRepos = [
  { id: 1, name: 'agenticanlaytics/analytics-core' },
  { id: 2, name: 'agenticanlaytics/event-tracker' },
  { id: 3, name: 'agenticanlaytics/website' },
  { id: 4, name: 'agenticanlaytics/docs' },
]

const Home = () => {
  const [selectedRepoId, setSelectedRepoId] = useState<number | null>(null)
  const selectedRepo = mockRepos.find(r => r.id === selectedRepoId)

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-base-200">
      {/* Sidebar */}
      <aside className="w-80 min-w-[18rem] border-r bg-base-100 flex flex-col">
        <div className="p-4 border-b">
          <span className="font-bold text-lg">Repositories</span>
        </div>
        <div className="p-2">
          <input
            type="text"
            placeholder="Search repos..."
            className="input input-bordered w-full mb-2"
            tabIndex={0}
            aria-label="Search repositories"
            disabled
          />
        </div>
        <ul className="menu menu-lg flex-1 overflow-y-auto">
          {mockRepos.map(repo => (
            <li key={repo.id}>
              <button
                className={`justify-start w-full text-left ${selectedRepoId === repo.id ? 'active' : ''}`}
                onClick={() => setSelectedRepoId(repo.id)}
                tabIndex={0}
                aria-label={`Select repository ${repo.name}`}
              >
                <span className="truncate">{repo.name}</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>
      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center">
        {selectedRepo ? (
          <div className="card w-full max-w-2xl bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title text-xl mb-2">{selectedRepo.name}</h2>
              <p className="text-base-content/70">Repository analytics and event tracking details will appear here.</p>
            </div>
          </div>
        ) : (
          <div className="text-base-content/60 text-lg">Select a repository from the left to view details.</div>
        )}
      </main>
    </div>
  )
}

export default Home 