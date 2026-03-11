import { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchMLConfig, saveMLConfig, resetMLConfig, fetchFeatureInventory } from '../api';
import {
  Loader2, Save, RotateCcw, AlertCircle, Check,
  Brain, Database, Layers, GraduationCap, Scale, Shield, BookOpen, Search,
  ArrowRight, ChevronDown, ChevronRight,
} from 'lucide-react';

const SUB_TABS = [
  { id: 'model', label: 'Model', icon: Brain },
  { id: 'data', label: 'Data & Target', icon: Database },
  { id: 'features', label: 'Features', icon: Layers },
  { id: 'training', label: 'Training', icon: GraduationCap },
  { id: 'loss', label: 'Loss & Scaling', icon: Scale },
  { id: 'policy', label: 'Policy & Risk', icon: Shield },
  { id: 'docs', label: 'Docs', icon: BookOpen },
];

function Toggle({ value, onChange, label }) {
  return (
    <label className="flex items-center justify-between gap-3 cursor-pointer group">
      <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
        {label}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={value}
        onClick={() => onChange(!value)}
        className={`relative inline-flex h-5 w-9 flex-shrink-0 rounded-full transition-colors ${
          value ? 'bg-blue-600' : 'bg-slate-700'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform mt-0.5 ${
            value ? 'translate-x-4 ml-0.5' : 'translate-x-0.5'
          }`}
        />
      </button>
    </label>
  );
}

function NumberInput({ value, onChange, label, step, nullable }) {
  const display = value === null || value === undefined ? '' : value;
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1">{label}</label>
      <input
        type="number"
        step={step || 'any'}
        value={display}
        onChange={(e) => {
          const raw = e.target.value;
          if (raw === '' && nullable) {
            onChange(null);
          } else {
            const n = step && step >= 1 ? parseInt(raw, 10) : parseFloat(raw);
            if (!isNaN(n)) onChange(n);
          }
        }}
        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30"
      />
    </div>
  );
}

function TextInput({ value, onChange, label, nullable }) {
  const display = value === null || value === undefined ? '' : value;
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1">{label}</label>
      <input
        type="text"
        value={display}
        onChange={(e) => {
          const raw = e.target.value;
          if (raw === '' && nullable) onChange(null);
          else onChange(raw);
        }}
        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30"
      />
    </div>
  );
}

function SelectInput({ value, onChange, label, options }) {
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1">{label}</label>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 appearance-none"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}

function ListInput({ value, onChange, label, type }) {
  const display = Array.isArray(value) ? value.join(', ') : '';
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1">
        {label}
        <span className="text-slate-600 ml-1 text-xs">(comma-separated)</span>
      </label>
      <input
        type="text"
        value={display}
        onChange={(e) => {
          const raw = e.target.value;
          if (raw.trim() === '') {
            onChange([]);
            return;
          }
          const parts = raw.split(',').map((s) => s.trim()).filter(Boolean);
          if (type === 'list_number' || type === 'list_int') {
            const nums = parts.map(Number).filter((n) => !isNaN(n));
            onChange(nums);
          } else {
            onChange(parts);
          }
        }}
        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30"
      />
    </div>
  );
}

function FieldRenderer({ fieldKey, meta, value, onChange, allValues }) {
  if (meta.show_when) {
    const visible = Object.entries(meta.show_when).every(([depKey, allowed]) => {
      return allowed.includes(allValues[depKey]);
    });
    if (!visible) return null;
  }

  const t = meta.type;
  if (t === 'bool') {
    return <Toggle label={meta.label} value={!!value} onChange={onChange} />;
  }
  if (t === 'select') {
    return <SelectInput label={meta.label} value={value} onChange={onChange} options={meta.options} />;
  }
  if (t === 'int') {
    return <NumberInput label={meta.label} value={value} onChange={onChange} step={1} />;
  }
  if (t === 'float') {
    return <NumberInput label={meta.label} value={value} onChange={onChange} />;
  }
  if (t === 'float_nullable') {
    return <NumberInput label={meta.label} value={value} onChange={onChange} nullable />;
  }
  if (t === 'string') {
    return <TextInput label={meta.label} value={value} onChange={onChange} />;
  }
  if (t === 'string_nullable') {
    return <TextInput label={meta.label} value={value} onChange={onChange} nullable />;
  }
  if (t.startsWith('list_')) {
    return <ListInput label={meta.label} value={value} onChange={onChange} type={t} />;
  }
  return <TextInput label={meta.label} value={JSON.stringify(value)} onChange={onChange} />;
}

function SectionCard({ title, children }) {
  const hasContent = Array.isArray(children)
    ? children.some(Boolean)
    : !!children;
  if (!hasContent) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
      <h4 className="text-sm font-semibold text-slate-300 border-b border-slate-800 pb-2">
        {title}
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {children}
      </div>
    </div>
  );
}

function Toast({ message, type, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3000);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all ${
      type === 'success'
        ? 'bg-emerald-900/90 text-emerald-200 border border-emerald-700'
        : 'bg-red-900/90 text-red-200 border border-red-700'
    }`}>
      {type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
      {message}
    </div>
  );
}

const STATUS_STYLES = {
  raw: 'bg-emerald-900/50 text-emerald-300 border-emerald-700',
  transformed: 'bg-blue-900/50 text-blue-300 border-blue-700',
  dropped: 'bg-red-900/50 text-red-300 border-red-700',
  dashboard: 'bg-amber-900/50 text-amber-300 border-amber-700',
};

const SOURCE_LABELS = {
  trend: 'Trend',
  volatility: 'Volatility',
  breadth: 'Breadth',
  cross_asset: 'Cross-Asset',
  macro: 'Macro',
  sentiment: 'Sentiment',
  rehab: 'Rehab (Transformed)',
  pipeline: 'Pipeline Internal',
  dashboard: 'Dashboard API',
};

function CollapsibleSection({ title, count, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-slate-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          {open ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
          <h4 className="text-sm font-semibold text-slate-300">{title}</h4>
          {count != null && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 font-mono">{count}</span>
          )}
        </div>
      </button>
      {open && <div className="px-5 pb-4 border-t border-slate-800">{children}</div>}
    </div>
  );
}

function FeaturesTab({ sectionFields, localValues, handleChange, allValues }) {
  const [featureData, setFeatureData] = useState(null);
  const [featureLoading, setFeatureLoading] = useState(true);
  const [featureSearch, setFeatureSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    let mounted = true;
    setFeatureLoading(true);
    fetchFeatureInventory()
      .then((data) => { if (mounted) setFeatureData(data); })
      .catch(() => {})
      .finally(() => { if (mounted) setFeatureLoading(false); });
    return () => { mounted = false; };
  }, []);

  const query = featureSearch.toLowerCase();

  const filteredInventory = useMemo(() => {
    if (!featureData) return [];
    return featureData.inventory.filter((f) => {
      if (statusFilter !== 'all' && f.status !== statusFilter) return false;
      if (query) {
        const hay = `${f.name} ${f.source} ${f.desc} ${f.status}`.toLowerCase();
        if (!hay.includes(query)) return false;
      }
      return true;
    });
  }, [featureData, query, statusFilter]);

  const groupedInventory = useMemo(() => {
    const g = {};
    for (const f of filteredInventory) {
      if (!g[f.source]) g[f.source] = [];
      g[f.source].push(f);
    }
    return g;
  }, [filteredInventory]);

  const sourceOrder = ['trend', 'volatility', 'breadth', 'cross_asset', 'macro', 'sentiment', 'rehab', 'pipeline', 'dashboard'];

  const statusCounts = useMemo(() => {
    if (!featureData) return {};
    const c = { raw: 0, transformed: 0, dropped: 0, dashboard: 0 };
    for (const f of featureData.inventory) c[f.status] = (c[f.status] || 0) + 1;
    return c;
  }, [featureData]);

  return (
    <div className="space-y-5">
      {/* Config controls */}
      <SectionCard title="Feature Engineering Settings">
        {sectionFields.map(([key, m]) => (
          <FieldRenderer
            key={key}
            fieldKey={key}
            meta={m}
            value={localValues[key]}
            onChange={(v) => handleChange(key, v)}
            allValues={allValues}
          />
        ))}
      </SectionCard>

      {featureLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="animate-spin text-blue-400" size={24} />
        </div>
      ) : featureData ? (
        <>
          {/* Status summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { key: 'raw', label: 'Raw Features', color: 'text-emerald-400' },
              { key: 'transformed', label: 'Transformed', color: 'text-blue-400' },
              { key: 'dropped', label: 'Dropped by Rehab', color: 'text-red-400' },
              { key: 'dashboard', label: 'Dashboard Only', color: 'text-amber-400' },
            ].map(({ key, label, color }) => (
              <div key={key} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-center">
                <p className={`text-2xl font-bold ${color}`}>{statusCounts[key] || 0}</p>
                <p className="text-xs text-slate-500 mt-1">{label}</p>
              </div>
            ))}
          </div>

          {/* Feature Inventory */}
          <CollapsibleSection title="Feature Inventory" count={filteredInventory.length} defaultOpen={true}>
            <div className="space-y-3 pt-3">
              {/* Search & filter bar */}
              <div className="flex items-center gap-3">
                <div className="relative flex-1">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search features..."
                    value={featureSearch}
                    onChange={(e) => setFeatureSearch(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 appearance-none"
                >
                  <option value="all">All statuses</option>
                  <option value="raw">Raw</option>
                  <option value="transformed">Transformed</option>
                  <option value="dropped">Dropped</option>
                  <option value="dashboard">Dashboard</option>
                </select>
              </div>

              {/* Grouped feature list */}
              {sourceOrder.map((src) => {
                const features = groupedInventory[src];
                if (!features || features.length === 0) return null;
                return (
                  <div key={src}>
                    <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold mt-3 mb-2">
                      {SOURCE_LABELS[src] || src} ({features.length})
                    </p>
                    <div className="space-y-1.5">
                      {features.map((f) => (
                        <div key={f.name} className="bg-slate-800/40 rounded-lg px-3 py-2.5 flex items-start gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-0.5">
                              <code className="text-xs font-semibold text-slate-200">{f.name}</code>
                              <span className={`text-[9px] px-1.5 py-0.5 rounded border font-medium ${STATUS_STYLES[f.status]}`}>
                                {f.status}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-relaxed">{f.desc}</p>
                            {f.transform_from && (
                              <p className="text-[10px] text-slate-500 mt-1">
                                <span className="text-slate-600">From:</span> {f.transform_from}
                                <span className="text-slate-600 ml-2">Via:</span> {f.transform_type}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}

              {filteredInventory.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-6">No features match your search.</p>
              )}
            </div>
          </CollapsibleSection>

          {/* Rehab Transformations */}
          <CollapsibleSection title="Rehab Pipeline Transformations" count={featureData.rehab_transforms.length}>
            <div className="pt-3 space-y-1.5">
              {featureData.rehab_transforms.map((t, i) => (
                <div key={i} className="bg-slate-800/40 rounded-lg px-3 py-2.5 flex items-center gap-2 text-xs">
                  <code className="text-slate-300 font-medium min-w-[140px]">{t.original}</code>
                  <ArrowRight size={12} className="text-slate-600 flex-shrink-0" />
                  <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 font-mono text-[10px] flex-shrink-0">
                    {t.transform}
                  </span>
                  <ArrowRight size={12} className="text-slate-600 flex-shrink-0" />
                  <code className={`font-medium min-w-[140px] ${t.result === '(dropped)' ? 'text-red-400' : 'text-blue-300'}`}>
                    {t.result}
                  </code>
                  <span className="text-slate-500 text-[10px] ml-auto hidden md:block">{t.reason}</span>
                </div>
              ))}
            </div>
          </CollapsibleSection>

          {/* Final Features */}
          <CollapsibleSection title="Final Model Features (Pipeline)" count={featureData.final_pipeline.length}>
            <div className="pt-3 flex flex-wrap gap-1.5">
              {featureData.final_pipeline.map((f) => (
                <span key={f} className="px-2 py-1 rounded bg-emerald-900/30 border border-emerald-800 text-emerald-300 text-[11px] font-mono">
                  {f}
                </span>
              ))}
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Final Model Features (Dashboard Ridge)" count={featureData.final_dashboard.length}>
            <div className="pt-3 flex flex-wrap gap-1.5">
              {featureData.final_dashboard.map((f) => (
                <span key={f} className="px-2 py-1 rounded bg-amber-900/30 border border-amber-800 text-amber-300 text-[11px] font-mono">
                  {f}
                </span>
              ))}
            </div>
          </CollapsibleSection>
        </>
      ) : null}
    </div>
  );
}

const GROUP_LABELS = {
  model: 'Model',
  data: 'Data & Target',
  features: 'Features',
  training: 'Training',
  loss: 'Loss & Scaling',
  policy: 'Policy & Risk',
};

const TYPE_BADGES = {
  select: 'dropdown',
  bool: 'toggle',
  int: 'integer',
  float: 'decimal',
  float_nullable: 'decimal?',
  string: 'text',
  string_nullable: 'text?',
  list_number: 'number list',
  list_int: 'int list',
  list_string: 'text list',
};

function DocsTab({ meta, values }) {
  const [search, setSearch] = useState('');
  const query = search.toLowerCase();

  const groups = useMemo(() => {
    const g = {};
    for (const [key, m] of Object.entries(meta)) {
      if (query) {
        const haystack = `${m.label} ${key} ${m.desc || ''} ${m.group}`.toLowerCase();
        if (!haystack.includes(query)) continue;
      }
      if (!g[m.group]) g[m.group] = [];
      g[m.group].push([key, m]);
    }
    return g;
  }, [meta, query]);

  const groupOrder = ['model', 'data', 'features', 'training', 'loss', 'policy'];

  const formatValue = (val) => {
    if (val === null || val === undefined) return 'null';
    if (Array.isArray(val)) return val.join(', ');
    if (typeof val === 'boolean') return val ? 'true' : 'false';
    return String(val);
  };

  return (
    <div className="space-y-5">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          placeholder="Search fields by name, key, or description..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30"
        />
      </div>

      {groupOrder.map((groupId) => {
        const fields = groups[groupId];
        if (!fields || fields.length === 0) return null;
        return (
          <div key={groupId} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <h4 className="text-sm font-semibold text-slate-300 border-b border-slate-800 pb-2 mb-4">
              {GROUP_LABELS[groupId] || groupId}
            </h4>
            <div className="space-y-3">
              {fields.map(([key, m]) => (
                <div key={key} className="bg-slate-800/40 rounded-lg px-4 py-3">
                  <div className="flex items-start justify-between gap-4 mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-sm font-medium text-slate-200">{m.label}</span>
                      <span className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-slate-700 text-slate-400 flex-shrink-0">
                        {TYPE_BADGES[m.type] || m.type}
                      </span>
                    </div>
                    <code className="text-[11px] text-slate-500 font-mono flex-shrink-0">{key}</code>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {m.desc || 'No description available.'}
                  </p>
                  <div className="mt-1.5 flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-600 uppercase tracking-wide">Current:</span>
                    <span className="text-[11px] text-blue-400 font-mono truncate max-w-xs">
                      {formatValue(values[key])}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {Object.keys(groups).length === 0 && (
        <div className="text-center py-12 text-slate-500 text-sm">
          No fields match your search.
        </div>
      )}
    </div>
  );
}

export default function MLConfig() {
  const [activeTab, setActiveTab] = useState('model');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const [serverValues, setServerValues] = useState({});
  const [meta, setMeta] = useState({});
  const [overrides, setOverrides] = useState({});
  const [localValues, setLocalValues] = useState({});

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchMLConfig();
      setServerValues(res.values);
      setMeta(res.meta);
      setOverrides(res.overrides || {});
      setLocalValues(res.values);
    } catch (err) {
      setError(err.message || 'Failed to load ML config');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadConfig(); }, [loadConfig]);

  const dirty = useMemo(() => {
    return Object.keys(localValues).some((k) => {
      const sv = serverValues[k];
      const lv = localValues[k];
      return JSON.stringify(sv) !== JSON.stringify(lv);
    });
  }, [localValues, serverValues]);

  const changedKeys = useMemo(() => {
    const keys = {};
    for (const k of Object.keys(localValues)) {
      if (JSON.stringify(serverValues[k]) !== JSON.stringify(localValues[k])) {
        keys[k] = localValues[k];
      }
    }
    return keys;
  }, [localValues, serverValues]);

  const handleChange = useCallback((key, val) => {
    setLocalValues((prev) => ({ ...prev, [key]: val }));
  }, []);

  const handleSave = useCallback(async () => {
    if (!dirty) return;
    setSaving(true);
    try {
      const res = await saveMLConfig(changedKeys);
      setOverrides(res.overrides || {});
      setServerValues((prev) => ({ ...prev, ...changedKeys }));
      setToast({ message: 'Configuration saved', type: 'success' });
    } catch (err) {
      setToast({ message: err.message || 'Save failed', type: 'error' });
    } finally {
      setSaving(false);
    }
  }, [dirty, changedKeys]);

  const handleResetSection = useCallback(async () => {
    const sectionKeys = Object.entries(meta)
      .filter(([, m]) => m.group === activeTab)
      .map(([k]) => k);
    const keysToReset = {};
    sectionKeys.forEach((k) => { keysToReset[k] = null; });

    try {
      const res = await resetMLConfig(keysToReset);
      setServerValues(res.values);
      setOverrides(res.overrides || {});
      setLocalValues((prev) => {
        const next = { ...prev };
        sectionKeys.forEach((k) => { next[k] = res.values[k]; });
        return next;
      });
      setToast({ message: 'Section reset to defaults', type: 'success' });
    } catch (err) {
      setToast({ message: err.message || 'Reset failed', type: 'error' });
    }
  }, [meta, activeTab]);

  const sectionFields = useMemo(() => {
    return Object.entries(meta).filter(([, m]) => m.group === activeTab);
  }, [meta, activeTab]);

  const groupedFields = useMemo(() => {
    if (activeTab !== 'model') return { _all: sectionFields };

    const core = [];
    const hyperparams = [];
    for (const [key, m] of sectionFields) {
      if (m.show_when) hyperparams.push([key, m]);
      else core.push([key, m]);
    }
    return { core, hyperparams };
  }, [activeTab, sectionFields]);

  const sectionHasOverrides = useMemo(() => {
    return sectionFields.some(([k]) => k in overrides);
  }, [sectionFields, overrides]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-400" size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-3">
          <AlertCircle className="mx-auto text-red-400" size={40} />
          <p className="text-red-300 text-sm">{error}</p>
          <button
            onClick={loadConfig}
            className="text-sm text-blue-400 hover:text-blue-300 underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">ML Configuration</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Manage machine learning pipeline settings
          </p>
        </div>
        <div className="flex items-center gap-2">
          {sectionHasOverrides && (
            <button
              onClick={handleResetSection}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700 border border-slate-700 transition-colors"
            >
              <RotateCcw size={14} />
              Reset Section
            </button>
          )}
        </div>
      </div>

      {/* Sub-tab navigation */}
      <div className="flex items-center gap-1 bg-slate-900/60 border border-slate-800 rounded-xl p-1.5">
        {SUB_TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === id
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {/* Fields */}
      {activeTab === 'model' ? (
        <div className="space-y-5">
          <SectionCard title="Model Selection">
            {groupedFields.core?.map(([key, m]) => (
              <FieldRenderer
                key={key}
                fieldKey={key}
                meta={m}
                value={localValues[key]}
                onChange={(v) => handleChange(key, v)}
                allValues={localValues}
              />
            ))}
          </SectionCard>
          <SectionCard title="Hyperparameters">
            {groupedFields.hyperparams?.map(([key, m]) => (
              <FieldRenderer
                key={key}
                fieldKey={key}
                meta={m}
                value={localValues[key]}
                onChange={(v) => handleChange(key, v)}
                allValues={localValues}
              />
            ))}
          </SectionCard>
        </div>
      ) : activeTab === 'data' ? (
        <div className="space-y-5">
          <SectionCard title="Data Source">
            {sectionFields
              .filter(([k]) => ['DATA_SOURCE', 'MONGODB_DB_NAME', 'DATA_FREQUENCY', 'MONTHLY_ANCHOR'].includes(k))
              .map(([key, m]) => (
                <FieldRenderer key={key} fieldKey={key} meta={m} value={localValues[key]} onChange={(v) => handleChange(key, v)} allValues={localValues} />
              ))}
          </SectionCard>
          <SectionCard title="Target Configuration">
            {sectionFields
              .filter(([k]) => ['TARGET_MODE', 'TARGET_HORIZON_DAYS', 'TARGET_COL', 'BIG_MOVE_THRESHOLD', 'BIG_MOVE_ALPHA'].includes(k))
              .map(([key, m]) => (
                <FieldRenderer key={key} fieldKey={key} meta={m} value={localValues[key]} onChange={(v) => handleChange(key, v)} allValues={localValues} />
              ))}
          </SectionCard>
          <SectionCard title="Macro Settings">
            {sectionFields
              .filter(([k]) => k.startsWith('MACRO_') || k === 'APPLY_MACRO_LAG')
              .map(([key, m]) => (
                <FieldRenderer key={key} fieldKey={key} meta={m} value={localValues[key]} onChange={(v) => handleChange(key, v)} allValues={localValues} />
              ))}
          </SectionCard>
        </div>
      ) : activeTab === 'training' ? (
        <div className="space-y-5">
          <SectionCard title="Data Splitting">
            {sectionFields
              .filter(([k]) => ['TEST_START_DATE', 'TRAIN_START_DATE', 'TRAIN_WINDOW_YEARS', 'VAL_WINDOW_MONTHS', 'EMBARGO_MODE', 'EMBARGO_ROWS_DAILY', 'EMBARGO_ROWS_MONTHLY'].includes(k))
              .map(([key, m]) => (
                <FieldRenderer key={key} fieldKey={key} meta={m} value={localValues[key]} onChange={(v) => handleChange(key, v)} allValues={localValues} />
              ))}
          </SectionCard>
          <SectionCard title="Walk-Forward">
            {sectionFields
              .filter(([k]) => k.startsWith('WF_') && !k.startsWith('WF_TUNE') && !k.startsWith('WF_THRESHOLD'))
              .map(([key, m]) => (
                <FieldRenderer key={key} fieldKey={key} meta={m} value={localValues[key]} onChange={(v) => handleChange(key, v)} allValues={localValues} />
              ))}
          </SectionCard>
          <SectionCard title="Optuna Tuning">
            {sectionFields
              .filter(([k]) => k === 'USE_OPTUNA' || k === 'OPTUNA_TRIALS' || k.startsWith('TUNE_'))
              .map(([key, m]) => (
                <FieldRenderer key={key} fieldKey={key} meta={m} value={localValues[key]} onChange={(v) => handleChange(key, v)} allValues={localValues} />
              ))}
          </SectionCard>
          <SectionCard title="Threshold Tuning">
            {sectionFields
              .filter(([k]) => k.startsWith('WF_TUNE') || k.startsWith('WF_THRESHOLD'))
              .map(([key, m]) => (
                <FieldRenderer key={key} fieldKey={key} meta={m} value={localValues[key]} onChange={(v) => handleChange(key, v)} allValues={localValues} />
              ))}
          </SectionCard>
        </div>
      ) : activeTab === 'features' ? (
        <FeaturesTab
          sectionFields={sectionFields}
          localValues={localValues}
          handleChange={handleChange}
          allValues={localValues}
        />
      ) : activeTab === 'docs' ? (
        <DocsTab meta={meta} values={localValues} />
      ) : (
        <SectionCard title={SUB_TABS.find((t) => t.id === activeTab)?.label || activeTab}>
          {sectionFields.map(([key, m]) => (
            <FieldRenderer
              key={key}
              fieldKey={key}
              meta={m}
              value={localValues[key]}
              onChange={(v) => handleChange(key, v)}
              allValues={localValues}
            />
          ))}
        </SectionCard>
      )}

      {/* Floating save bar */}
      {dirty && (
        <div className="fixed bottom-0 left-56 right-0 bg-slate-900/95 border-t border-slate-700 backdrop-blur-sm px-6 py-3 flex items-center justify-between z-40">
          <p className="text-sm text-slate-400">
            <span className="text-amber-400 font-medium">{Object.keys(changedKeys).length}</span>
            {' '}unsaved change{Object.keys(changedKeys).length !== 1 ? 's' : ''}
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setLocalValues(serverValues)}
              className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors"
            >
              Discard
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              Save Changes
            </button>
          </div>
        </div>
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDone={() => setToast(null)}
        />
      )}
    </div>
  );
}
