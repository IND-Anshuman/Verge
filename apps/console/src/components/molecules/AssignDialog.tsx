import { useState } from 'react';
import type { RiskFinding } from '@/types';
import { transitionFinding } from '@/api';
import { Modal, Button } from '@/components/atoms';

interface AssignDialogProps {
  finding: RiskFinding | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const OPERATORS = [
  { id: 'maya', name: 'Maya (Safety Officer)', role: 'Safety Officer' },
  { id: 'sarah', name: 'Sarah (Shift Supervisor)', role: 'Shift Supervisor' },
  { id: 'john', name: 'John (Field Technician)', role: 'Field Technician' },
];

export function AssignDialog({ finding, isOpen, onClose, onSuccess }: AssignDialogProps) {
  const [assignee, setAssignee] = useState<string>('maya');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!finding) return null;

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      // Transition finding to 'assigned' state
      await transitionFinding(
        finding.findingId,
        'assigned',
        `Assigned finding to ${assignee}`
      );
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Assignment failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const footer = (
    <>
      <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
        Cancel
      </Button>
      <Button
        variant="primary"
        onClick={handleSubmit}
        loading={isSubmitting}
      >
        Confirm Assignment
      </Button>
    </>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Assign Finding Owner"
      description={`Select personnel responsible for resolved mitigation`}
      footer={footer}
      size="md"
    >
      <div className="flex flex-col gap-4">
        {error && (
          <div className="text-xs text-imminent bg-imminent/10 border border-imminent/20 p-2 rounded">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-ink-dim select-none">Available Operators</span>
          <div className="flex flex-col gap-2">
            {OPERATORS.map((op) => (
              <button
                key={op.id}
                type="button"
                onClick={() => setAssignee(op.id)}
                className={`flex items-center justify-between p-3 rounded border text-sm transition-all cursor-pointer text-left ${
                  assignee === op.id
                    ? 'bg-panel-2 border-ink text-ink'
                    : 'bg-panel-2 border-line text-ink hover:border-line/75'
                }`}
              >
                <div>
                  <div className="font-semibold">{op.name}</div>
                  <div className="text-xs text-ink-dim font-mono uppercase">{op.role}</div>
                </div>
                <div
                  className={`h-4 w-4 rounded-full border flex items-center justify-center ${
                    assignee === op.id ? 'border-ink' : 'border-line'
                  }`}
                >
                  {assignee === op.id && (
                    <span className="h-2 w-2 rounded-full bg-ink" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}
