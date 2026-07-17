import { Cpu, FileText, Wrench, Camera, Activity } from 'lucide-react';
import clsx from 'clsx';

/* Evidence lineage chip — one grammar for contributing signals wherever
   they appear (board card, detail cockpit). Mono ID, ink-dim glyph keyed to
   the signal KIND (shape carries meaning, not color — color = state only),
   hairline that darkens on hover: looks actionable, never decorative. */

export function lineageIcon(label: string) {
  const lc = label.toLowerCase();
  const cls = 'h-3 w-3 shrink-0 text-ink-dim';
  if (
    lc.includes('sensor') ||
    lc.includes('reading') ||
    lc.includes('temp') ||
    lc.includes('gas') ||
    lc.includes('pres')
  ) {
    return <Cpu className={cls} />;
  }
  if (lc.includes('permit') || lc.includes('ptw')) {
    return <FileText className={cls} />;
  }
  if (lc.includes('maintenance') || lc.includes('maint') || lc.includes('work')) {
    return <Wrench className={cls} />;
  }
  if (lc.includes('cctv') || lc.includes('camera') || lc.includes('frame')) {
    return <Camera className={cls} />;
  }
  return <Activity className={cls} />;
}

interface LineageChipProps {
  label: string;
  onClick?: () => void;
  className?: string;
  title?: string;
}

export function LineageChip({ label, onClick, className, title }: LineageChipProps) {
  const Tag = onClick ? 'button' : 'span';
  return (
    <Tag
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      title={title ?? label}
      className={clsx(
        'inline-flex items-center gap-1 bg-panel-2 border border-line px-1.5 py-0.5 rounded-sm',
        'text-micro text-ink-dim font-mono max-w-full',
        'transition-colors duration-fast',
        onClick
          ? 'hover:text-ink hover:border-line-2 cursor-pointer'
          : 'hover:text-ink hover:border-line-2',
        className,
      )}
    >
      {lineageIcon(label)}
      <span className="truncate">{label}</span>
    </Tag>
  );
}
