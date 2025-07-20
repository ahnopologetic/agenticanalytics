import { useState } from 'react'
import type { TrackingPlanEvent } from '../../api'

const locationToPermlink = (location: string) => {
    const line = location.split(':')[1]
    const file = location.split(':')[0]
    return `${file}#L${line}`
}

const DetectedEventsSection = ({ events, repoUrl }: { events: TrackingPlanEvent[], repoUrl?: string }) => {
    const [openIdx, setOpenIdx] = useState<number | null>(null)
    const [search, setSearch] = useState('')
    const filtered = events.filter(e =>
        e.event_name.toLowerCase().includes(search.toLowerCase()) ||
        e.context.toLowerCase().includes(search.toLowerCase()) ||
        e.file_path.toLowerCase().includes(search.toLowerCase())
    )
    return (
        <>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lg">Detected Events</h3>
                    <span className="badge badge-primary">{filtered.length}</span>
                </div>
                <input
                    type="text"
                    placeholder="Search events..."
                    className="input input-bordered input-sm w-48"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    aria-label="Search tracking plan events"
                />
            </div>
            <div className="space-y-3">
                {filtered.length === 0 && <div className="text-base-content/60">No events found.</div>}
                {filtered.map((event, idx) => {
                    const isOpen = openIdx === idx
                    return (
                        <div key={event.event_name + event.file_path} className="border rounded-lg bg-base-100 shadow-sm">
                            <button
                                className="w-full flex items-center gap-3 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40 transition"
                                onClick={() => setOpenIdx(isOpen ? null : idx)}
                                aria-expanded={isOpen}
                                aria-controls={`tracking-event-panel-${idx}`}
                            >
                                <div className="flex-1 text-left">
                                    <div className="font-semibold text-base-content line-clamp-1 flex items-center gap-2">
                                        <span className="inline-block w-2 h-2 rounded-full bg-primary mr-1" />
                                        {event.event_name}
                                    </div>
                                    <div className="text-base-content/70 text-sm line-clamp-1">{event.context}</div>
                                </div>
                                <div className="hidden md:block text-xs text-base-content/50 ml-2 whitespace-nowrap max-w-xs truncate">
                                    <span className="inline-flex items-center gap-1">
                                        <svg className="w-4 h-4 inline-block text-base-content/40" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7M16 3v4M8 3v4m-5 4h18" /></svg>
                                        <span className="font-mono">{event.file_path.split('/').slice(-1)[0]}</span>
                                    </span>
                                </div>
                                <a
                                    href={repoUrl + locationToPermlink(event.file_path)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn btn-xs btn-ghost ml-2"
                                    tabIndex={0}
                                    aria-label="View in GitHub"
                                    onClick={e => e.stopPropagation()}
                                >
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M14 3v2h3.59L7 15.59 8.41 17 19 6.41V10h2V3z" /><path d="M5 5v14h14v-7h-2v5H7V7h5V5z" /></svg>
                                </a>
                                <span className={`ml-2 transition-transform ${isOpen ? 'rotate-90' : ''}`}>▶</span>
                            </button>
                            <div
                                id={`tracking-event-panel-${idx}`}
                                className={`overflow-hidden transition-all duration-300 ${isOpen ? 'py-2 px-4' : 'max-h-0 p-0'}`}
                                aria-hidden={!isOpen}
                            >
                                {isOpen && (
                                    <div>
                                        <div className="mb-2">
                                            <span className="font-semibold">Context:</span> <span className="text-base-content/80">{event.context}</span>
                                        </div>
                                        <div className="mb-2">
                                            <span className="font-semibold">Location:</span> <span className="font-mono text-base-content/70">{event.file_path}</span>
                                            <a
                                                href={repoUrl + locationToPermlink(event.file_path)}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="ml-2 text-primary underline text-xs"
                                                tabIndex={0}
                                                aria-label="View in GitHub"
                                            >View in GitHub</a>
                                        </div>
                                        <div>
                                            <span className="font-semibold">Properties:</span>
                                            {Object.keys(event.tags).length === 0 ? (
                                                <span className="italic text-base-content/50 ml-2">No properties collected</span>
                                            ) : (
                                                <table className="table table-xs mt-2">
                                                    <thead>
                                                        <tr>
                                                            <th>Property</th>
                                                            <th>Value</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {Object.entries(event.tags).map(([key, value]) => (
                                                            <tr key={key}>
                                                                <td className="font-mono text-xs">{key}</td>
                                                                <td className="text-xs">{String(value)}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </>
    )
}

export default DetectedEventsSection 