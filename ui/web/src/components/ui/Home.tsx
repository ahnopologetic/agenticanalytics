import { useEffect, useState } from 'react'
import { getUserSession, type UserSession } from '../../api'
import useUserSessions from '../../hooks/use-user-sessions'
import { useUserContext } from '../../hooks/use-user-context'

const Home = () => {
    const { user } = useUserContext()
    const { data: sessions, isLoading } = useUserSessions(user?.id ?? '')
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
    const [session, setSession] = useState<UserSession | null>(null)


    useEffect(() => {
        const fetchSession = async () => {
            if (!selectedSessionId) return
            const session = await getUserSession(selectedSessionId)
            setSession(session)
        }
        fetchSession()
    }, [selectedSessionId])

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
            <main className="flex-1 flex items-center justify-center">
                {session ? (
                    <div className="card w-full bg-base-100 shadow-xl h-full">
                        <div className="card-body h-full">
                            <div className="flex flex-col h-full">
                                <div className="flex items-center gap-4 mb-6">
                                    <h2 className="card-title text-2xl">{session.id}</h2>
                                    <div className="badge badge-primary">{session?.state?.status as string}</div>
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

                                <div className="flex-1 bg-base-200 rounded-lg p-4 max-h-64 overflow-y-auto">
                                    <h3 className="font-semibold mb-4">Recent Activity</h3>
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-2 h-2 bg-primary rounded-full"></div>
                                            <p className="text-base-content/70">Repository analytics initialized</p>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="w-2 h-2 bg-primary rounded-full"></div>
                                            <p className="text-base-content/70">Event tracking system deployed</p>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="w-2 h-2 bg-primary rounded-full"></div>
                                            <p className="text-base-content/70">Data collection started</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
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