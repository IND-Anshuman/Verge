import type { ReactNode } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import clsx from 'clsx';
import { Button } from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-2xl',
};

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  size = 'md',
}: ModalProps) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        {/* Overlay */}
        <Dialog.Overlay className="fixed inset-0 bg-[color:var(--scrim)] transition-opacity duration-fast z-50" />

        {/* Content Container */}
        <div className="fixed inset-0 flex items-center justify-center p-4 z-50">
          <Dialog.Content
            className={clsx(
              'w-full bg-panel border border-line rounded-lg float-layer',
              'flex flex-col max-h-[85vh]',
              'focus:outline-none',
              sizeClasses[size]
            )}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-4 border-b border-line">
              <div className="flex flex-col gap-0.5">
                <Dialog.Title className="text-md font-semibold text-ink">
                  {title}
                </Dialog.Title>
                {description && (
                  <Dialog.Description className="text-xs text-ink-dim">
                    {description}
                  </Dialog.Description>
                )}
              </div>
              <Dialog.Close asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 hover:bg-panel-2"
                  aria-label="Close dialog"
                >
                  <X className="h-4 w-4" />
                </Button>
              </Dialog.Close>
            </div>

            {/* Scrollable Content Body */}
            <div className="flex-1 p-4 overflow-y-auto text-sm text-ink-dim">
              {children}
            </div>

            {/* Footer */}
            {footer && (
              <div className="flex items-center justify-end gap-2 p-4 border-t border-line bg-panel-2/50 rounded-b-lg">
                {footer}
              </div>
            )}
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
