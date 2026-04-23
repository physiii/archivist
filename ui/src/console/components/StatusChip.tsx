import { Chip, type ChipProps } from '@mui/material'

type Severity = 'ok' | 'warn' | 'bad' | 'default'

const colors: Record<Severity, { bg: string; border: string; color: string }> = {
  ok: { bg: 'rgba(45,212,191,0.10)', border: 'rgba(45,212,191,0.35)', color: '#c7f9e9' },
  warn: { bg: 'rgba(251,191,36,0.10)', border: 'rgba(251,191,36,0.35)', color: '#fde68a' },
  bad: { bg: 'rgba(239,68,68,0.10)', border: 'rgba(239,68,68,0.35)', color: '#fecaca' },
  default: { bg: 'rgba(15,23,42,0.55)', border: 'rgba(148,163,184,0.16)', color: 'rgba(148,163,184,0.8)' },
}

export function StatusChip({ severity = 'default', ...props }: { severity?: Severity } & Omit<ChipProps, 'sx'>) {
  const c = colors[severity]
  return (
    <Chip
      size="small"
      {...props}
      sx={{
        bgcolor: c.bg,
        borderColor: c.border,
        color: c.color,
        border: '1px solid',
        fontWeight: 700,
        fontSize: '0.75rem',
        height: 24,
      }}
    />
  )
}

