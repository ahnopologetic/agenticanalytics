import { useState, useRef, useEffect } from 'react'
import { getUserSession } from '../../api'
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
    const { data: sessions, isLoading } = useUserSessions(user?.id ?? '')
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
    const activityEndRef = useRef<HTMLDivElement>(null)

    // Collapsible state: open event ids (or indices if no id)
    const [openEventIds, setOpenEventIds] = useState<(string | number)[]>([])

    const {
        data: session,
        isLoading: isSessionLoading,
    } = useQuery({
        queryKey: ['user-session', selectedSessionId],
        queryFn: () => selectedSessionId ? getUserSession(selectedSessionId) : Promise.resolve(null),
        enabled: !!selectedSessionId,
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
        const searchTerm = e.target.value
        setSelectedSessionId(sessions?.sessions.find(session => session.id.includes(searchTerm))?.id ?? null)
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
                    />
                </div>
                <ul className="menu menu-lg flex-1 overflow-y-auto w-full">
                    {isLoading ? (
                        <li>
                            <span className="loading loading-spinner loading-lg"></span>
                        </li>
                    ) : (
                        sessions?.sessions.map(session => (
                            <li key={session.id}>
                                <button
                                    className={`justify-start w-full text-left ${selectedSessionId === session.id ? 'text-primary' : ''}`}
                                    onClick={() => setSelectedSessionId(session.id)}
                                    tabIndex={0}
                                    aria-label={`Select repository ${session.id}`}
                                >
                                    <span className="truncate">{session.id}</span>
                                </button>
                            </li>
                        )))}
                </ul>
            </aside>
            {/* Main Content */}
            <main className="flex-1 flex flex-col items-center justify-start overflow-y-auto">
                {isSessionLoading ? (
                    <div className="text-base-content/60 text-lg">Loading session...</div>
                ) : session ? (
                    <div className="card w-full bg-base-100 shadow-xl h-full">
                        <div className="card-body h-full">
                            <div className="flex flex-col h-full">
                                <div className="flex items-center gap-4 mb-6">
                                    <h2 className="card-title text-2xl">{session.id}</h2>
                                    {typeof session.state === 'object' && session.state !== null && 'status' in session.state && (
                                        <div className="badge badge-primary">{(session.state as { status: string }).status}</div>
                                    )}
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                    <div className="stats shadow">
                                        <div className="stat">
                                            <div className="stat-title">Total Events</div>
                                            <div className="stat-value">89,400</div>
                                            <div className="stat-desc">21% more than last month</div>
                                        </div>
                                    </div>

                                    <div className="stats shadow">
                                        <div className="stat">
                                            <div className="stat-title">Active Users</div>
                                            <div className="stat-value">4,200</div>
                                            <div className="stat-desc text-success">↗︎ 400 (22%)</div>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex-1 bg-base-200 rounded-lg p-4 max-h-[300px] overflow-y-hidden flex flex-col">
                                    <div className="bg-base-200 pb-2 mb-2 flex items-center justify-between border-b border-base-300">
                                        <h3 className="font-semibold flex items-center gap-2">
                                            Recent Activity
                                            <span className="animate-pulse w-2 h-2 rounded-full bg-green-500" aria-label="Live"></span>
                                        </h3>
                                        <span className="badge badge-neutral text-xs font-semibold">{Array.isArray(session.events) ? session.events.length : 0}</span>
                                    </div>
                                    <div className="space-y-2 max-h-[300px] overflow-y-auto">
                                        {Array.isArray(session.events) && session.events.length > 0 ? (
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
                                    {/* Fade-in animation keyframes */}
                                    <style>{`
                                        @keyframes fadein {
                                            from { opacity: 0; transform: translateY(10px); }
                                            to { opacity: 1; transform: none; }
                                        }
                                        .animate-fadein {
                                            animation: fadein 0.5s ease;
                                        }
                                    `}</style>
                                </div>
                                {/* Tracking Plan Section - use real data */}
                                <TrackingPlanSection
                                    events={
                                        hasTrackingPlan(session.state)
                                            ? session.state?.tracking_plans
                                            : []
                                    }
                                    repoUrl={`https://github.com/${session.id}/blob/main/`}
                                />
                            </div>
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