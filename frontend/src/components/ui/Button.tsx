import React from 'react';
import { clsx } from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export default function Button({ variant = 'primary', size = 'md', loading, children, className, disabled, ...props }: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center justify-center gap-2 font-semibold rounded-museum-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 uppercase tracking-wide disabled:opacity-50 disabled:cursor-not-allowed',
        {
          'bg-museum-accent text-white hover:bg-museum-accent-hover focus:ring-museum-accent': variant === 'primary',
          'bg-museum-surface text-museum-text-secondary border border-museum-border hover:bg-museum-surface-hover focus:ring-museum-border': variant === 'secondary',
          'bg-museum-danger text-white hover:bg-red-700 focus:ring-museum-danger': variant === 'danger',
          'text-museum-text-secondary hover:text-museum-text hover:bg-museum-surface-hover focus:ring-museum-border': variant === 'ghost',
          'text-xs px-3 py-1.5': size === 'sm',
          'text-sm px-4 py-2': size === 'md',
          'text-base px-6 py-3': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {loading ? <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" /> : null}
      {children}
    </button>
  );
}
