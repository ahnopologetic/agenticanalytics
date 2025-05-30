import { useEffect, useState } from 'react'
import { useUserContext } from '../../hooks/use-user-context'
import { useNavigate } from 'react-router-dom'
import { getUserSessions, type UserSession } from '../../api'

const Home = () => {
    const navigate = useNavigate()
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
    const { user } = useUserContext()
    const [sessions, setSessions] = useState<UserSession[]>([])
    if (!user) {
        navigate('/login')
    }

    useEffect(() => {
        const checkSessions = async () => {
            const res = await getUserSessions(user!.id)
            if (res.sessions && res.sessions.length > 0) {
                setSessions(res.sessions)
                setSelectedSessionId(res.sessions[0].id)
            }
        }
        checkSessions()
    }, [user])

    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        const searchTerm = e.target.value
        const filteredSessions = sessions.filter(session => session.id.includes(searchTerm))
        setSessions(filteredSessions)
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
                <ul className="menu menu-lg flex-1 overflow-y-auto">
                    {sessions?.map(session => (
                        <li key={session.id}>
                            <button
                                className={`justify-start w-full text-left ${selectedSessionId === session.id ? 'active' : ''}`}
                                onClick={() => setSelectedSessionId(session.id)}
                                tabIndex={0}
                                aria-label={`Select repository ${session.id}`}
                            >
                                <span className="truncate">{session.id}</span>
                            </button>
                        </li>
                    ))}
                </ul>
            </aside>
            {/* Main Content */}
            <main className="flex-1 flex items-center justify-center">
                {selectedSessionId ? (
                    <div className="card w-full max-w-2xl bg-base-100 shadow-xl">
                        <div className="card-body">
                            <h2 className="card-title text-xl mb-2">{sessions.find(s => s.id === selectedSessionId)?.id}</h2>
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