import { useState, useRef, useEffect } from 'react'
import { getUserSession, listRepos, getGithubRepoInfo, type GithubRepoInfo } from '../../api'
import useUserSessions from '../../hooks/use-user-sessions'
import { useUserContext } from '../../hooks/use-user-context'
import { useQuery } from '@tanstack/react-query'
import type { TrackingPlanEvent } from '../../api'
import TrackingPlanSection from './TrackingPlanSection'

// Define type for session event
interface SessionEvent {
    id?: string
    author: string
    timestamp: number
    content?: {
        parts?: Array<{
            text?: string
            functionCall?: { name: string }
            functionResponse?: { response: unknown }
        }>
    }
}

// Helper for relative time
const getRelativeTime = (timestamp: number): string => {
    const now = Date.now() / 1000
    const diff = Math.floor(now - timestamp)
    if (diff < 5) return 'just now'
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return new Date(timestamp * 1000).toLocaleString()
}

const getEventText = (event: SessionEvent): string => {
    const part = event?.content?.parts?.[0]
    if (part?.text) return part.text
    if (part?.functionCall) return `Called function: ${part.functionCall.name}`
    if (part?.functionResponse) return `Function responded: ${JSON.stringify(part.functionResponse.response)}`
    return '[No message]'
}

const getAuthorColor = (author: string): string => {
    if (author === 'user') return 'bg-blue-500'
    if (author.endsWith('_agent')) return 'bg-green-500'
    return 'bg-gray-400'
}

// Type guard for tracking_plan
function hasTrackingPlan(state: unknown): state is { tracking_plans: TrackingPlanEvent[] } {
    return (
        typeof state === 'object' &&
        state !== null &&
        'tracking_plans' in state &&
        Array.isArray((state as { tracking_plans: unknown }).tracking_plans)
    )
}

const Home = () => {
    const { user } = useUserContext()
    useUserSessions(user?.id ?? '')
    const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null)
    const activityEndRef = useRef<HTMLDivElement>(null)
    const [openEventIds, setOpenEventIds] = useState<(string | number)[]>([])
    const [searchTerm, setSearchTerm] = useState('')

    // Repos state
    const {
        data: repos = [],
        isLoading: isReposLoading,
    } = useQuery({
        queryKey: ['repos'],
        queryFn: listRepos,
    })

    // Find selected repo object
    const selectedRepo = repos.find(r => r.id.toString() === selectedRepoId)

    // Fetch GitHub repo info (commit/status) for selected repo
    const {
        data: githubInfo,
        isLoading: isGithubInfoLoading,
        isError: isGithubInfoError,
        error: githubInfoError,
    } = useQuery<GithubRepoInfo, Error>({
        queryKey: ['github-info', selectedRepo?.url],
        queryFn: () => {
            if (!selectedRepo) throw new Error('No repo selected')
            // Extract owner/repo from URL (e.g., https://github.com/owner/repo)
            const match = selectedRepo.url.match(/github.com\/(.+\/[^/]+)/)
            if (!match) throw new Error('Invalid GitHub repo URL')
            return getGithubRepoInfo(match[1])
        },
        enabled: !!selectedRepo,
    })

    // Session for selected repo
    const {
        data: session,
        isLoading: isSessionLoading,
    } = useQuery({
        queryKey: ['user-session', selectedRepo?.session_id],
        queryFn: () => selectedRepo?.session_id ? getUserSession(selectedRepo.session_id) : Promise.resolve(null),
        enabled: !!selectedRepo?.session_id,
        refetchInterval: 5000,
    })

    // Scroll to bottom on new events
    useEffect(() => {
        if (activityEndRef.current) {
            activityEndRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [session?.events?.length])

    // Expand most recent event by default when session.events changes
    useEffect(() => {
        if (Array.isArray(session?.events) && session.events.length > 0) {
            const sorted = [...session.events].sort((a, b) => (a as SessionEvent).timestamp - (b as SessionEvent).timestamp)
            const firstId = (sorted[0] as SessionEvent).id ?? 0
            setOpenEventIds([firstId])
        } else {
            setOpenEventIds([])
        }
    }, [session?.events])

    const handleToggleEvent = (id: string | number) => {
        setOpenEventIds(prev => prev.includes(id) ? prev.filter(eid => eid !== id) : [...prev, id])
    }

    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value
        setSearchTerm(value)
        const foundRepo = repos.find(repo =>
            repo.name.toLowerCase().includes(value.toLowerCase()) || repo.id.toString().includes(value)
        )
        setSelectedRepoId(foundRepo ? foundRepo.id.toString() : null)
    }

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
                        onChange={handleSearch}
                        value={searchTerm}
                    />
                </div>
                <ul className="menu menu-lg flex-1 overflow-y-auto w-full">
                    {isReposLoading ? (
                        <li>
                            <span className="loading loading-spinner loading-lg"></span>
                        </li>
                    ) : (
                        repos.map(repo => (
                            <li key={repo.id}>
                                <button
                                    className={`justify-start w-full text-left ${selectedRepoId === repo.id.toString() ? 'text-primary' : ''}`}
                                    onClick={() => setSelectedRepoId(repo.id.toString())}
                                    tabIndex={0}
                                    aria-label={`Select repository ${repo.name}`}
                                >
                                    <span className="truncate">{repo.name}</span>
                                </button>
                            </li>
                        ))
                    )}
                </ul>
            </aside>
            {/* Main Content */}
            <main className="flex-1 flex flex-col items-center justify-start overflow-y-auto">
                {selectedRepo ? (
                    <div className="w-full max-w-6xl mx-auto p-6">
                        {/* Repo Info Section */}
                        <div className="flex flex-col gap-4 mb-6 border-b pb-4 lg:flex-row lg:items-center lg:justify-between">
                            <div className="flex items-center gap-3">
                                <h2 className="text-3xl font-bold">{selectedRepo.name}</h2>
                                <a
                                    href={selectedRepo.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    aria-label="View on GitHub"
                                    tabIndex={0}
                                    className="text-gray-500 hover:text-black"
                                >
                                    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                        <path d="M12 0.297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.387 0.6 0.113 0.82-0.258 0.82-0.577 0-0.285-0.011-1.04-0.017-2.04-3.338 0.726-4.042-1.416-4.042-1.416-0.546-1.387-1.333-1.756-1.333-1.756-1.089-0.745 0.083-0.729 0.083-0.729 1.205 0.084 1.84 1.237 1.84 1.237 1.07 1.834 2.809 1.304 3.495 0.997 0.108-0.775 0.418-1.305 0.762-1.605-2.665-0.305-5.466-1.334-5.466-5.931 0-1.311 0.469-2.381 1.236-3.221-0.124-0.303-0.535-1.523 0.117-3.176 0 0 1.008-0.322 3.301 1.23 0.957-0.266 1.983-0.399 3.003-0.404 1.02 0.005 2.047 0.138 3.006 0.404 2.291-1.553 3.297-1.23 3.297-1.23 0.653 1.653 0.242 2.873 0.118 3.176 0.77 0.84 1.235 1.91 1.235 3.221 0 4.609-2.803 5.624-5.475 5.921 0.43 0.371 0.823 1.102 0.823 2.222 0 1.606-0.015 2.898-0.015 3.293 0 0.322 0.216 0.694 0.825 0.576 4.765-1.589 8.199-6.085 8.199-11.386 0-6.627-5.373-12-12-12z" />
                                    </svg>
                                </a>
                            </div>
                            <div className="flex flex-col gap-2 lg:items-end lg:flex-row lg:items-center">
                                {selectedRepo.description && (
                                    <div className="text-base-content/80 text-sm max-w-md line-clamp-2">{selectedRepo.description}</div>
                                )}
                                {/* Commit and status info */}
                                {isGithubInfoLoading && (
                                    <div className="text-xs text-base-content/60">Loading commit info...</div>
                                )}
                                {isGithubInfoError && (
                                    <div className="text-xs text-error">{githubInfoError?.message || 'Failed to load commit info'}</div>
                                )}
                                {githubInfo && (
                                    <div className="flex flex-wrap items-center gap-2 text-xs">
                                        <span className="font-mono bg-base-200 px-2 py-1 rounded">{githubInfo.sha.slice(0, 7)}</span>
                                        <button
                                            className="font-semibold truncate max-w-[200px] text-left hover:underline focus:underline focus:outline-none cursor-pointer"
                                            onClick={() => {
                                                const commitUrl = `${selectedRepo.url}/commit/${githubInfo.sha}?from=agentic-analytics`
                                                window.open(commitUrl, '_blank', 'noopener,noreferrer')
                                            }}
                                            aria-label={`View commit ${githubInfo.sha} on GitHub`}
                                            tabIndex={0}
                                        >
                                            {githubInfo.message}
                                        </button>
                                        <span className="text-base-content/60">by {githubInfo.author} on {new Date(githubInfo.date).toLocaleString()}</span>
                                        {githubInfo.status && (
                                            <span className={`badge ${githubInfo.status === 'success' ? 'badge-success' : githubInfo.status === 'failure' ? 'badge-error' : 'badge-warning'}`}>{githubInfo.status}</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                        {/* Main Grid: Recent Activity & Tracking Plan */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Recent Activity */}
                            <section className="bg-base-100 rounded-lg p-4 shadow flex flex-col max-h-[400px]">
                                <div className="flex items-center justify-between border-b pb-2 mb-2">
                                    <h3 className="font-semibold flex items-center gap-2">
                                        Recent Activity
                                        <span className="animate-pulse w-2 h-2 rounded-full bg-green-500" aria-label="Live"></span>
                                    </h3>
                                    <span className="badge badge-neutral text-xs font-semibold">{Array.isArray(session?.events) ? session.events.length : 0}</span>
                                </div>
                                <div className="space-y-2 overflow-y-auto">
                                    {isSessionLoading ? (
                                        <div className="text-base-content/60">Loading session...</div>
                                    ) : Array.isArray(session?.events) && session.events.length > 0 ? (
                                        [...session.events]
                                            .sort((a, b) => (a as SessionEvent).timestamp - (b as SessionEvent).timestamp)
                                            .map((event, idx) => {
                                                const ev = event as SessionEvent
                                                const isOpen = openEventIds.includes(ev.id ?? idx)
                                                return (
                                                    <div key={ev.id ?? idx} className="border rounded-lg bg-base-100 shadow-sm">
                                                        <button
                                                            className="w-full flex items-center gap-3 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40 transition"
                                                            onClick={() => handleToggleEvent(ev.id ?? idx)}
                                                            aria-expanded={isOpen}
                                                            aria-controls={`event-panel-${ev.id ?? idx}`}
                                                        >
                                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${getAuthorColor(ev.author)}`}
                                                                title={ev.author}
                                                                aria-label={ev.author}
                                                            >
                                                                {ev.author?.[0]?.toUpperCase() || '?'}
                                                            </div>
                                                            <div className="flex-1 text-left">
                                                                <div className="text-base-content font-medium line-clamp-1">{ev.author}</div>
                                                                <div className="text-base-content/80 text-sm line-clamp-1">{getEventText(ev)}</div>
                                                            </div>
                                                            <div className="text-xs text-base-content/50 ml-2 whitespace-nowrap">{getRelativeTime(ev.timestamp)}</div>
                                                            <span className={`ml-2 transition-transform ${isOpen ? 'rotate-90' : ''}`}>▶</span>
                                                        </button>
                                                        <div
                                                            id={`event-panel-${ev.id ?? idx}`}
                                                            className={`overflow-hidden transition-all duration-300 ${isOpen ? 'py-2 px-4' : 'max-h-0 p-0'}`}
                                                            aria-hidden={!isOpen}
                                                        >
                                                            {isOpen && (
                                                                <div>
                                                                    <div className="text-base-content/80 whitespace-pre-line break-words mb-2">{getEventText(ev)}</div>
                                                                    <div className="text-xs text-base-content/50">Event ID: {ev.id ?? idx}</div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )
                                            })
                                    ) : (
                                        <div className="text-base-content/60">No activity yet.</div>
                                    )}
                                    <div ref={activityEndRef} />
                                </div>
                            </section>
                            {/* Tracking Plan Section */}
                            <section className="bg-base-100 rounded-lg p-4 shadow flex flex-col max-h-[400px] overflow-y-auto">
                                <TrackingPlanSection
                                    events={
                                        hasTrackingPlan(session?.state)
                                            ? session?.state?.tracking_plans
                                            : []
                                    }
                                    repoUrl={selectedRepo.url + '/blob/main/'}
                                />
                            </section>
                        </div>
                    </div>
                ) : (
                    <div className="text-base-content/60 text-lg h-full flex items-center justify-center">Select a repository from the left to view details.</div>
                )}
            </main>
        </div>
    )
}

export default Home 