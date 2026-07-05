import type { ReactNode } from 'react';
import clsx from 'clsx';
import type { LeadTimeBand, DataQuality, FindingState } from '@/types';

export type BadgeVariant = 'band' | 'sensor' | 'state' | 'generic';

interface BadgeBaseProps {
  children: ReactNode;
  className?: string;
}

interface BandBadgeProps extends BadgeBaseProps {
  variant: 'band';
  band: LeadTimeBand;
}

interface SensorBadgeProps extends BadgeBaseProps {
  variant: 'sensor';
  state: DataQuality;
}

interface StateBadgeProps extends BadgeBaseProps {
  variant: 'state';
  state: FindingState;
}

interface GenericBadgeProps extends BadgeBaseProps {
  variant: 'generic';
  color?: 'accent' | 'ok' | 'imminent' | 'near' | 'watch' | 'unknown';
}

type BadgeProps = BandBadgeProps | SensorBadgeProps | StateBadgeProps | GenericBadgeProps;

const bandStyles: Record<LeadTimeBand, string> = {
  IMMINENT: 'bg-imminent/12 text-imminent border-imminent/30',
  NEAR: 'bg-near/12 text-near border-near/30',
  WATCH: 'bg-watch/12 text-watch border-watch/30',
  UNKNOWN: 'bg-unknown/12 text-unknown border-unknown/30',
};

const sensorStyles: Record<DataQuality, string> = {
  live: 'bg-ok/12 text-ok border-ok/30',
  stale: 'bg-near/12 text-near border-near/30',
  'stuck-at-value': 'bg-imminent/12 text-imminent border-imminent/30',
  'out-of-range': 'bg-imminent/12 text-imminent border-imminent/30',
  'clock-skewed': 'bg-near/12 text-near border-near/30',
  missing: 'bg-unknown/12 text-unknown border-unknown/30',
};

const stateStyles: Record<FindingState, string> = {
  'new': 'bg-imminent/12 text-imminent border-imminent/30',
  acknowledged: 'bg-near/12 text-near border-near/30',
  assigned: 'bg-watch/12 text-watch border-watch/30',
  'in-progress': 'bg-accent/12 text-accent border-accent/30',
  snoozed: 'bg-unknown/12 text-unknown border-unknown/30',
  escalated: 'bg-imminent/12 text-imminent border-imminent/30',
  'suppressed-as-duplicate': 'bg-unknown/12 text-unknown border-unknown/30',
  resolved: 'bg-ok/12 text-ok border-ok/30',
  closed: 'bg-unknown/12 text-ink-dim border-unknown/30',
  reopened: 'bg-near/12 text-near border-near/30',
};

const genericColorStyles: Record<string, string> = {
  accent: 'bg-accent/12 text-accent border-accent/30',
  ok: 'bg-ok/12 text-ok border-ok/30',
  imminent: 'bg-imminent/12 text-imminent border-imminent/30',
  near: 'bg-near/12 text-near border-near/30',
  watch: 'bg-watch/12 text-watch border-watch/30',
  unknown: 'bg-unknown/12 text-unknown border-unknown/30',
};

function getVariantStyles(props: BadgeProps): string {
  switch (props.variant) {
    case 'band':
      return bandStyles[props.band];
    case 'sensor':
      return sensorStyles[props.state];
    case 'state':
      return stateStyles[props.state];
    case 'generic':
      return genericColorStyles[props.color ?? 'unknown'];
  }
}

export function Badge(props: BadgeProps): JSX.Element {
  const { children, className } = props;

  return (
    <span
      className={clsx(
        'inline-flex items-center',
        'px-2 py-0.5',
        'text-xs font-semibold',
        'border rounded-sm',
        'whitespace-nowrap select-none',
        'tabular-nums',
        getVariantStyles(props),
        className
      )}
    >
      {children}
    </span>
  );
}
