type ConnectGitHubStepProps = {
  onConnect: () => void
}

const ConnectGitHubStep = ({ onConnect }: ConnectGitHubStepProps) => (
  <button
    className="w-64 py-3 rounded text-white font-semibold shadow hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400"
    onClick={onConnect}
    tabIndex={0}
    aria-label="Connect GitHub"
    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onConnect() }}
  >
    Connect GitHub
  </button>
)

export default ConnectGitHubStep 