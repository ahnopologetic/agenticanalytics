import { useState } from 'react'
import type { DetectedEvent } from '../../api'
import { useAddReposToPlan, usePlans } from '../../hooks/use-plan'
import { useBulkCreateEvents } from '../../hooks/use-event'

const locationToPermlink = (location: string) => {
    const line = location.split(':')[1]
    const file = location.split(':')[0]
    return `${file}#L${line}`
}

const DetectedEventsSection = ({ events, repoUrl }: { events: DetectedEvent[], repoUrl?: string }) => {
    const [openIdx, setOpenIdx] = useState<number | null>(null)
    const [search, setSearch] = useState('')
    const [selected, setSelected] = useState<Set<string>>(new Set())
    const [showPlanDropdown, setShowPlanDropdown] = useState(false)
    const [selectedPlan, setSelectedPlan] = useState<string>('')
    const { data: plans = [] } = usePlans();
    const { mutate: addReposToPlan, isPending: isAddingRepos } = useAddReposToPlan();
    const { mutate: bulkCreateEvents, isPending: isSavingEvents } = useBulkCreateEvents();

    const filtered = events.filter(e =>
        e.name.toLowerCase().includes(search.toLowerCase()) ||
        e.description.toLowerCase().includes(search.toLowerCase()) ||
        e.location.toLowerCase().includes(search.toLowerCase())
    )

    const handleSelect = (eventKey: string) => {
        setSelected(prev => {
            const next = new Set(prev)
            if (next.has(eventKey)) {
                next.delete(eventKey)
            } else {
                next.add(eventKey)
            }
            return next
        })
    }

    const handleSelectAll = () => {
        if (selected.size === filtered.length) {
            setSelected(new Set())
        } else {
            setSelected(new Set(filtered.map(e => e.name + e.location)))
        }
    }

    const handleAddToPlan = () => {
        setShowPlanDropdown(v => !v)
    }

    const handlePlanSelect = (planId: string) => {
        setSelectedPlan(planId)
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedPlan) return
        const params = new URLSearchParams(window.location.search);
        const repoId = params.get('repo');
        if (!repoId) {
            return;
        }
        addReposToPlan({ planId: selectedPlan, repoIds: [repoId] }, {
            onSuccess: () => {
                setSelected(new Set())
                setShowPlanDropdown(false)
                setSelectedPlan('')
            }
        });
    }

    const handleSaveSelectedToRepo = () => {
        const params = new URLSearchParams(window.location.search);
        const repoId = params.get('repo');
        if (!repoId) {
            return;
        }
        // Find selected events
        const selectedEvents = filtered.filter(e => selected.has(e.name + e.location));
        if (selectedEvents.length === 0) {
            return;
        }
        // Map DetectedEvent to PlanEvent input (excluding id, created_at, updated_at)
        const eventsToCreate = selectedEvents.map(e => ({
            name: e.name,
            description: e.description,
            location: e.location,
            repo_id: repoId,
            properties: e.properties,
            // tags: e.tags || [],
        }));
        // Map DetectedEvent to match PlanEvent input requirements
        const formattedEvents = eventsToCreate.map(e => ({
            event_name: e.name,
            description: e.description,
            context: e.description, // Assuming context is similar to description; adjust as needed
            tags: [], // Add tags if available in your DetectedEvent
            location: e.location,
            file_path: '', // Provide file_path if available in your DetectedEvent
            line_number: 0, // Provide line_number if available in your DetectedEvent
            repo_id: e.repo_id,
            properties: e.properties,
        }));
        bulkCreateEvents(
            { events: formattedEvents },
            {
                onSuccess: () => {
                    setSelected(new Set());
                }
            }
        );
    }

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
            {filtered.length > 0 && (
                <div className="flex items-center mb-2 gap-2">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-xs"
                        checked={selected.size === filtered.length}
                        onChange={handleSelectAll}
                        aria-label="Select all events"
                        tabIndex={0}
                    />
                    <span className="text-xs text-base-content/60 select-none">Select all</span>
                    {selected.size > 0 && (
                        <div className="ml-auto flex items-center gap-2">
                            <button
                                className="btn btn-sm btn-primary"
                                onClick={handleAddToPlan}
                                aria-haspopup="listbox"
                                aria-expanded={showPlanDropdown}
                                tabIndex={0}
                                disabled={isAddingRepos}
                            >
                                Add to Tracking plan
                            </button>
                            <button
                                className="btn btn-sm btn-accent"
                                onClick={handleSaveSelectedToRepo}
                                tabIndex={0}
                                aria-label="Save selected events to repo"
                                disabled={isSavingEvents}
                            >
                                {isSavingEvents ? (
                                    <span className="flex items-center gap-2 justify-center">
                                        <span className="loading loading-spinner loading-xs" />
                                        Saving...
                                    </span>
                                ) : 'Save the selected to repo'}
                            </button>
                            {showPlanDropdown && (
                                <form onSubmit={handleSubmit} className="relative z-10">
                                    <div className="absolute right-0 mt-2 w-48 bg-base-100 border rounded shadow-lg p-3 flex flex-col gap-2">
                                        <label className="text-xs font-semibold mb-1">Select plan:</label>
                                        <select
                                            className="select select-sm select-bordered w-full mb-2"
                                            value={selectedPlan}
                                            onChange={e => handlePlanSelect(e.target.value)}
                                            aria-label="Select plan"
                                            tabIndex={0}
                                            required
                                        >
                                            <option value="" disabled>Select a plan</option>
                                            {plans.map(plan => (
                                                <option key={plan.id} value={plan.id}>{plan.name}</option>
                                            ))}
                                        </select>
                                        <button
                                            className="btn btn-sm btn-success w-full"
                                            type="submit"
                                            disabled={isAddingRepos || !selectedPlan}
                                            tabIndex={0}
                                            aria-label="Submit selected events to plan"
                                        >
                                            {isAddingRepos ? (
                                                <span className="flex items-center gap-2 justify-center">
                                                    <span className="loading loading-spinner loading-xs" />
                                                    Adding...
                                                </span>
                                            ) : 'Submit'}
                                        </button>
                                    </div>
                                </form>
                            )}
                        </div>
                    )}
                </div>
            )}
            <div className="space-y-3">
                {filtered.length === 0 && <div className="text-base-content/60">No events found.</div>}
                {filtered.map((event, idx) => {
                    const isOpen = openIdx === idx
                    const eventKey = event.name + event.location
                    const isChecked = selected.has(eventKey)
                    return (
                        <div key={eventKey} className={`border rounded-lg bg-base-100 shadow-sm relative group transition-all duration-200 ${isChecked ? 'ring-2 ring-primary/40' : ''}`}>
                            <div className="absolute left-2 top-2">
                                <input
                                    type="checkbox"
                                    className="checkbox checkbox-xs"
                                    checked={isChecked}
                                    onChange={() => handleSelect(eventKey)}
                                    aria-label={`Select event ${event.name}`}
                                    tabIndex={0}
                                />
                            </div>
                            <button
                                className="w-full flex items-center gap-3 px-7 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40 transition text-left"
                                onClick={() => setOpenIdx(isOpen ? null : idx)}
                                aria-expanded={isOpen}
                                aria-controls={`tracking-event-panel-${idx}`}
                                tabIndex={0}
                            >
                                <div className="flex-1 text-left">
                                    <div className="font-semibold text-base-content line-clamp-1 flex items-center gap-2">
                                        <span className="inline-block w-2 h-2 rounded-full bg-primary mr-1" />
                                        {event.name}
                                    </div>
                                    <div className="text-base-content/70 text-sm line-clamp-1">{event.description}</div>
                                </div>
                                <div className="hidden md:block text-xs text-base-content/50 ml-2 whitespace-nowrap max-w-xs truncate">
                                    <span className="inline-flex items-center gap-1">
                                        <svg className="w-4 h-4 inline-block text-base-content/40" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7M16 3v4M8 3v4m-5 4h18" /></svg>
                                        <span className="font-mono">{event.location.split('/').slice(-1)[0]}</span>
                                    </span>
                                </div>
                                <a
                                    href={repoUrl + locationToPermlink(event.location)}
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
                                            <span className="font-semibold">Context:</span> <span className="text-base-content/80">{event.description}</span>
                                        </div>
                                        <div className="mb-2">
                                            <span className="font-semibold">Location:</span> <span className="font-mono text-base-content/70">{event.location}</span>
                                            <a
                                                href={repoUrl + locationToPermlink(event.location)}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="ml-2 text-primary underline text-xs"
                                                tabIndex={0}
                                                aria-label="View in GitHub"
                                            >View in GitHub</a>
                                        </div>
                                        <div>
                                            <span className="font-semibold">Properties:</span>
                                            {Object.keys(event.properties).length === 0 ? (
                                                <span className="italic text-base-content/50 ml-2">No properties collected</span>
                                            ) : (
                                                <table className="table table-xs mt-2">
                                                    <thead>
                                                        <tr>
                                                            <th>Property</th>
                                                            <th>Type</th>
                                                            <th>Description</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {event.properties.map((value) => (
                                                            <tr key={value.property_name}>
                                                                <td className="font-mono text-xs">{value.property_name}</td>
                                                                <td className="text-xs">{value.property_type}</td>
                                                                <td className="text-xs">{value.property_description}</td>
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