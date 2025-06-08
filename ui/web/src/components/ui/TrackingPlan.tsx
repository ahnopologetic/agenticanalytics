import { useEffect, useState, useCallback, useRef } from 'react';
import { AgGridReact } from 'ag-grid-react';
import type { ColDef, CellValueChangedEvent, ICellRendererParams, ValueFormatterParams, ValueParserParams } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import {
  listRepos,
  listPlans,
  listPlanEvents,
  createPlanEvent,
  updatePlanEvent,
  deletePlanEvent,
  exportPlanEvents,
  importPlanEvents,
  type Plan,
  type PlanEvent,
} from '../../api';

const defaultNewEvent = (plan_id: string, repo_id: string): Omit<PlanEvent, 'id' | 'created_at' | 'updated_at'> => ({
  plan_id,
  repo_id,
  event_name: '',
  context: '',
  tags: [],
  file_path: '',
  line_number: 0,
});

const TrackingPlan = () => {
  const [repos, setRepos] = useState<{ id: string; name: string }[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [plans, setPlans] = useState<Plan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [rowData, setRowData] = useState<PlanEvent[]>([]);
  const [editRows, setEditRows] = useState<Record<string, Partial<PlanEvent>>>({});
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch repos on mount
  useEffect(() => {
    (async () => {
      try {
        const repoList = await listRepos();
        setRepos(repoList.map(r => ({ id: r.id?.toString?.() ?? r.id, name: r.name })));
        if (repoList.length > 0) setSelectedRepo(repoList[0].id?.toString?.() ?? repoList[0].id);
      } catch (e) {
        setError(`Failed to load repos: ${e}`);
      }
    })();
  }, []);

  // Fetch plans when repo changes
  useEffect(() => {
    if (!selectedRepo) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const planList = await listPlans(selectedRepo);
        setPlans(planList);
        setSelectedPlan(planList.length > 0 ? planList[0] : null);
      } catch (e) {
        setError(`Failed to load plans: ${e}`);
      } finally {
        setLoading(false);
      }
    })();
  }, [selectedRepo]);

  // Fetch events when plan changes
  const fetchEvents = useCallback(async () => {
    if (!selectedPlan) return;
    setLoading(true);
    setError(null);
    try {
      const events = await listPlanEvents(selectedPlan.id);
      setRowData(events);
    } catch (e) {
      setError(`Failed to load events: ${e}`);
    } finally {
      setLoading(false);
    }
  }, [selectedPlan]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleCellEdit = useCallback((params: CellValueChangedEvent<PlanEvent>) => {
    const { id } = params.data;
    if (!id) return;
    setEditRows(prev => ({ ...prev, [id]: { ...prev[id], ...params.data } }));
  }, []);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this event?')) return;
    try {
      await deletePlanEvent(id);
      setRowData(data => data.filter(e => e.id !== id));
      setEditRows(prev => { const copy = { ...prev }; delete copy[id]; return copy; });
    } catch (e) {
      setError(`Failed to delete event: ${e}`);
    }
  };

  const handleAdd = async () => {
    if (!selectedPlan) { setError('No plan selected'); return; }
    try {
      const newEvent = await createPlanEvent(defaultNewEvent(selectedPlan.id, selectedPlan.repo_id));
      setRowData(data => [...data, newEvent]);
    } catch (e) {
      setError(`Failed to add event: ${e}`);
    }
  };

  const handleSaveAll = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all(Object.entries(editRows).map(([id, changes]) => updatePlanEvent(id, changes)));
      setEditRows({});
      await fetchEvents();
    } catch (e) {
      setError(`Failed to save changes: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!selectedPlan) return;
    setExporting(true);
    setError(null);
    try {
      const blob = await exportPlanEvents(selectedPlan.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plan_events.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(`Failed to export: ${e}`);
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedPlan || !e.target.files?.[0]) return;
    setImporting(true);
    setError(null);
    try {
      await importPlanEvents(selectedPlan.id, e.target.files[0]);
      await fetchEvents();
    } catch (e) {
      setError(`Failed to import: ${e}`);
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const columns: ColDef<PlanEvent>[] = [
    { headerName: 'Event Name', field: 'event_name', editable: true, flex: 1 },
    { headerName: 'Context', field: 'context', editable: true, flex: 2 },
    {
      headerName: 'Tags',
      field: 'tags',
      editable: true,
      flex: 1,
      valueFormatter: (p: ValueFormatterParams<PlanEvent>) => (Array.isArray(p.value) ? p.value.join(', ') : ''),
      valueParser: (p: ValueParserParams) => typeof p.newValue === 'string' ? p.newValue.split(',').map((t: string) => t.trim()) : [],
    },
    { headerName: 'Repo', field: 'repo_id', editable: false, flex: 1 },
    { headerName: 'File', field: 'file_path', editable: true, flex: 1 },
    { headerName: 'Line', field: 'line_number', editable: true, flex: 0.5, type: 'number' },
    {
      headerName: 'Created',
      field: 'created_at',
      editable: false,
      flex: 1,
      valueFormatter: (p: ValueFormatterParams<PlanEvent>) => p.value ? new Date(p.value as string).toLocaleString() : '',
    },
    {
      headerName: 'Delete',
      field: 'plan_id',
      cellRenderer: (params: ICellRendererParams<PlanEvent>) => (
        <button
          className="btn btn-xs btn-error"
          onClick={() => handleDelete(params.data?.id ?? '')}
          tabIndex={0}
          aria-label="Delete event"
        >Delete</button>
      ),
      editable: false,
      flex: 0.5,
    },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Tracking Plan</h1>
      <div className="flex gap-4 mb-4 items-center">
        <label className="font-semibold">Repo:</label>
        <select
          className="select select-bordered"
          value={selectedRepo}
          onChange={e => setSelectedRepo(e.target.value)}
          aria-label="Select repo"
        >
          {repos.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
        <label className="font-semibold ml-4">Plan:</label>
        <select
          className="select select-bordered"
          value={selectedPlan?.id || ''}
          onChange={e => setSelectedPlan(plans.find(p => p.id === e.target.value) || null)}
          aria-label="Select plan"
        >
          {plans.map(p => <option key={p.id} value={p.id}>{p.name} (v{p.version})</option>)}
        </select>
        {selectedPlan && (
          <span className="ml-4 text-sm text-base-content/60">Status: <span className="font-semibold">{selectedPlan.status}</span> | Version: <span className="font-semibold">{selectedPlan.version}</span> | Imported: <span className="font-semibold">{selectedPlan.import_source || 'N/A'}</span></span>
        )}
      </div>
      <div className="flex gap-2 mb-4">
        <button className="btn btn-primary" onClick={handleAdd} tabIndex={0} aria-label="Add event" disabled={!selectedPlan}>Add Event</button>
        <button className="btn btn-success" onClick={handleSaveAll} disabled={Object.keys(editRows).length === 0 || loading || !selectedPlan} tabIndex={0} aria-label="Save all changes">Save All</button>
        <button className="btn btn-outline" onClick={handleExport} disabled={exporting || !selectedPlan} tabIndex={0} aria-label="Export plan events">Export</button>
        <label className="btn btn-outline" tabIndex={0} aria-label="Import plan events">
          Import
          <input type="file" accept=".csv" className="hidden" ref={fileInputRef} onChange={handleImport} disabled={importing || !selectedPlan} />
        </label>
      </div>
      {error && <div className="alert alert-error mb-2">{error}</div>}
      <div className="ag-theme-quartz" style={{ width: '100%', minHeight: 400 }}>
        <AgGridReact<PlanEvent>
          rowData={rowData}
          columnDefs={columns}
          onCellValueChanged={handleCellEdit}
          domLayout="autoHeight"
          stopEditingWhenCellsLoseFocus={true}
          editType="fullRow"
          getRowId={params => params.data?.id ?? ''}
        />
      </div>
      {loading && <div className="mt-4 text-base-content/60">Loading...</div>}
    </div>
  );
};

export default TrackingPlan; 