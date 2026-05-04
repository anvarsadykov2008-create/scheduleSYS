import React, { useState, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { ChevronDown, Check } from 'lucide-react';

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  error?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
}

export default function Select({ label, error, className, id, children, value, onChange, ...props }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const allOptions: { value: string; label: string }[] = [];
  React.Children.toArray(children).forEach((child) => {
    if (React.isValidElement(child) && child.type === 'option') {
      const p = child.props as any;
      allOptions.push({
        value: p.value !== undefined ? p.value.toString() : '',
        label: p.children ? p.children.toString() : '',
      });
    }
  });

  const placeholder = allOptions.find(o => o.value === '');
  const options = allOptions.filter(o => o.value !== '');
  const selectedOption = options.find(o => o.value === value?.toString());
  const hasValue = !!selectedOption;

  const handleSelect = (optValue: string) => {
    setIsOpen(false);
    if (onChange) {
      const event = {
        target: { value: optValue, name: props.name || '' },
        currentTarget: { value: optValue, name: props.name || '' },
      } as unknown as React.ChangeEvent<HTMLSelectElement>;
      onChange(event);
    }
  };

  return (
    <div className="w-full relative" ref={wrapperRef}>
      <select id={id} value={value} onChange={onChange} className="hidden" {...props}>
        {children}
      </select>

      {/* Trigger */}
      <div
        className={clsx(
          'w-full flex items-center justify-between cursor-pointer select-none',
          'px-4 h-14 rounded-2xl transition-all duration-200',
          'bg-museum-surface border shadow-sm',
          isOpen
            ? 'border-museum-accent ring-2 ring-museum-accent/20 shadow-lg'
            : 'border-museum-border hover:border-museum-border-hover hover:shadow-md',
          error && 'border-museum-danger ring-2 ring-museum-danger/20',
          className
        )}
        onClick={() => setIsOpen(prev => !prev)}
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setIsOpen(prev => !prev); }}
        role="combobox"
        aria-expanded={isOpen}
      >
        <div className="flex flex-col justify-center min-w-0 flex-1 overflow-hidden">
          {hasValue ? (
            <>
              {label && (
                <span className="text-[10px] font-bold uppercase tracking-widest text-museum-accent leading-none mb-0.5">
                  {label}
                </span>
              )}
              <span className="text-[15px] font-semibold text-museum-text truncate leading-tight">
                {selectedOption!.label}
              </span>
            </>
          ) : (
            <span className="text-[15px] text-museum-text-muted truncate">
              {placeholder?.label ?? label ?? 'Выберите...'}
            </span>
          )}
        </div>

        <ChevronDown
          className={clsx(
            'w-4 h-4 flex-shrink-0 ml-3 transition-transform duration-300',
            isOpen ? 'rotate-180 text-museum-accent' : 'text-museum-text-muted'
          )}
        />
      </div>

      {/* Animated Dropdown */}
      <div
        className={clsx(
          'absolute z-50 w-full mt-2 rounded-2xl border border-museum-border',
          'bg-museum-surface shadow-[0_8px_32px_rgba(0,0,0,0.25)] overflow-hidden',
          'transition-all duration-200 origin-top',
          isOpen ? 'opacity-100 scale-y-100 pointer-events-auto' : 'opacity-0 scale-y-95 pointer-events-none'
        )}
      >
        <div className="py-2 max-h-64 overflow-y-auto">
          {options.map((opt, i) => {
            const isSelected = value?.toString() === opt.value;
            return (
              <div
                key={i}
                className={clsx(
                  'flex items-center justify-between mx-2 px-3.5 py-2.5 rounded-xl cursor-pointer text-[14px] font-medium transition-all duration-150',
                  isSelected
                    ? 'bg-museum-accent text-white'
                    : 'text-museum-text hover:bg-museum-accent-soft hover:text-museum-accent'
                )}
                onClick={() => handleSelect(opt.value)}
              >
                <span>{opt.label}</span>
                {isSelected && <Check className="w-4 h-4 flex-shrink-0 ml-2" />}
              </div>
            );
          })}
        </div>
      </div>

      {error && (
        <p className="mt-1.5 text-[12px] text-museum-danger font-semibold">
          {error}
        </p>
      )}
    </div>
  );
}
