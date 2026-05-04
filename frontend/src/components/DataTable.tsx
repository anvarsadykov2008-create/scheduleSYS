import React from 'react';
import { useLang } from '../context/LanguageContext';

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField?: keyof T;
  emptyMessage?: string;
  loading?: boolean;
}

export default function DataTable<T>({
  columns, data, keyField = 'id' as keyof T, emptyMessage, loading,
}: DataTableProps<T>) {
  const { t } = useLang();

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin h-8 w-8 rounded-full border-4 border-museum-accent border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-museum-md border border-museum-border bg-museum-surface">
      <table className="w-full min-w-full text-sm">
        <thead>
          <tr className="border-b border-museum-border bg-museum-surface-hover">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={`px-4 py-3 text-left text-xs font-semibold text-museum-text-secondary uppercase tracking-wide ${col.className ?? ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-12 text-center text-museum-text-muted">
                {emptyMessage ?? t.noData}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={String(row[keyField])}
                className="border-b border-museum-border/50 hover:bg-museum-surface-hover transition-colors"
              >
                {columns.map((col) => (
                  <td
                    key={String(col.key)}
                    className={`px-4 py-3 text-museum-text ${col.className ?? ''}`}
                  >
                    {col.render ? col.render(row) : String(row[col.key as keyof T] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
