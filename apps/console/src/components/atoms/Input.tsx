import { forwardRef, type InputHTMLAttributes } from 'react';
import clsx from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, id, type = 'text', ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
    const helperId = helperText ? `${inputId}-helper` : undefined;
    const errorId = error ? `${inputId}-error` : undefined;

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-medium text-ink-dim select-none"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          type={type}
          aria-describedby={clsx(helperId, errorId)}
          aria-invalid={error ? 'true' : 'false'}
          className={clsx(
            'h-8 px-3 rounded border text-sm bg-panel-2 text-ink',
            'transition-colors duration-fast',
            error ? 'border-imminent focus:border-imminent focus:ring-1 focus:ring-imminent' : 'border-line focus:border-accent focus:ring-1 focus:ring-accent',
            'placeholder:text-ink-dim/40',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'focus:outline-none focus:ring-0',
            className
          )}
          {...props}
        />
        {error ? (
          <span id={errorId} className="text-xs text-imminent font-medium">
            {error}
          </span>
        ) : helperText ? (
          <span id={helperId} className="text-xs text-ink-dim">
            {helperText}
          </span>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';
