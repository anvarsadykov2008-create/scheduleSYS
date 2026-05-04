import React from 'react';
import { clsx } from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export default function Input({ label, error, className, id, ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={id} className="block text-xs font-semibold text-museum-text-secondary mb-1.5 uppercase tracking-wide">
          {label}
        </label>
      )}
      <input
        id={id}
        className={clsx(
          'w-full px-3 py-2.5 bg-museum-surface border border-museum-border rounded-museum-sm text-museum-text placeholder-museum-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent/30 focus:border-museum-accent transition-colors',
          error && 'border-museum-danger focus:ring-museum-danger/30',
          className
        )}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-museum-danger">{error}</p>}
    </div>
  );
}
