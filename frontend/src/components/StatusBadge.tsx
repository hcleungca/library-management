import React from 'react';
import { BookStatus } from '../types';
import { CheckCircle2, BookOpen, Clock, RefreshCw } from 'lucide-react';

export type EffectiveStatus = BookStatus | 'OVERDUE';

export interface StatusBadgeProps {
  status: EffectiveStatus;
  isOverdue?: boolean;
  className?: string;
}

interface StatusConfig {
  label: string;
  badgeClass: string;
  iconClass: string;
  dotClass: string;
  Icon: React.ElementType;
  pulse?: boolean;
}

const STATUS_CONFIG_MAP: Record<EffectiveStatus, StatusConfig> = {
  AVAILABLE: {
    label: 'AVAILABLE',
    badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    iconClass: 'text-emerald-600',
    dotClass: 'bg-emerald-500',
    Icon: CheckCircle2,
  },
  CHECKED_OUT: {
    label: 'CHECKED OUT',
    badgeClass: 'bg-sky-50 text-sky-700 border-sky-200',
    iconClass: 'text-sky-600',
    dotClass: 'bg-sky-500',
    Icon: BookOpen,
  },
  OVERDUE: {
    label: 'OVERDUE',
    badgeClass: 'bg-rose-50 text-rose-700 border-rose-300 shadow-2xs',
    iconClass: 'text-rose-600',
    dotClass: 'bg-rose-500',
    Icon: Clock,
    pulse: true,
  },
  IN_PROCESSING: {
    label: 'IN PROCESSING',
    badgeClass: 'bg-amber-50 text-amber-800 border-amber-300',
    iconClass: 'text-amber-600',
    dotClass: 'bg-amber-500',
    Icon: RefreshCw,
  },
};

export function StatusBadge({ status, isOverdue = false, className = '' }: StatusBadgeProps) {
  // Overdue status check has precedence over CHECKED_OUT
  const effectiveStatus: EffectiveStatus = isOverdue || status === 'OVERDUE' ? 'OVERDUE' : status;

  const config = STATUS_CONFIG_MAP[effectiveStatus] || STATUS_CONFIG_MAP.AVAILABLE;
  const { label, badgeClass, iconClass, Icon, pulse } = config;

  return (
    <span
      role="status"
      aria-label={`Status: ${label}`}
      className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border tracking-wide transition-colors ${badgeClass} ${className}`}
    >
      <Icon className={`w-3.5 h-3.5 ${iconClass} ${pulse ? 'badge-pulse' : ''}`} aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}

export default StatusBadge;

