import { useState, useEffect, useCallback } from 'react';
import { useLang } from '../context/LanguageContext';
import { apiClient } from '../api/client';
import DataTable from '../components/DataTable';
import { Search } from 'lucide-react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

interface AuditLog {
  id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  entity: string;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export default function AuditLogs() {
  const { t, lang } = useLang();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ action: '', entity: '' });

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      let url = '/audit';
      const params = new URLSearchParams();
      if (filter.action) params.append('action', filter.action);
      if (filter.entity) params.append('entity', filter.entity);
      if (params.toString()) url += `?${params.toString()}`;

      const data = await apiClient.get<AuditLog[]>(url);
      setLogs(data);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  }, [filter.action, filter.entity]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const columns = [
    {
      key: 'created_at',
      header: t.auditTime,
      render: (l: AuditLog) => (
        <span className="text-xs">
          {new Date(l.created_at).toLocaleString(lang === 'ru' ? 'ru-RU' : 'kk-KZ')}
        </span>
      ),
      className: 'w-40',
    },
    {
      key: 'user',
      header: t.auditUser,
      render: (l: AuditLog) => l.username || 'System',
    },
    {
      key: 'action',
      header: t.auditAction,
      render: (l: AuditLog) => (
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
          l.action === 'CREATE' ? 'bg-green-100 text-green-700' :
          l.action === 'DELETE' ? 'bg-red-100 text-red-700' :
          l.action === 'UPDATE' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
        }`}>
          {l.action}
        </span>
      ),
      className: 'w-32',
    },
    { key: 'entity', header: t.auditEntity, className: 'w-32' },
    {
      key: 'details',
      header: t.auditDetails,
      render: (l: AuditLog) => (
        <span className="text-xs text-museum-text-muted font-mono truncate max-w-xs block">
          {JSON.stringify(l.details)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-museum-text">{t.auditTitle}</h1>

      <div className="flex gap-4 bg-museum-surface border border-museum-border rounded-museum-md p-4">
        <div className="w-1/4">
          <Input 
            placeholder={t.auditActionPlaceholder} 
            value={filter.action} 
            onChange={e => setFilter({ ...filter, action: e.target.value })} 
          />
        </div>
        <div className="w-1/4">
          <Input 
            placeholder={t.auditEntityPlaceholder} 
            value={filter.entity} 
            onChange={e => setFilter({ ...filter, entity: e.target.value })} 
          />
        </div>
        <Button onClick={fetchLogs}>
          <Search className="h-4 w-4 mr-2" />
          {t.search}
        </Button>
      </div>

      <DataTable columns={columns} data={logs} loading={loading} emptyMessage={t.noRecords} />
    </div>
  );
}
