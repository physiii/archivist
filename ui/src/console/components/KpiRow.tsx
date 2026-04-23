import { Box, Stack, Typography, useTheme } from '@mui/material'

export type KpiItem = {
  label: string
  value: string | number | null | undefined
  unit?: string
  color?: 'good' | 'warn' | 'bad' | 'default'
  onClick?: () => void
}

export function KpiRow({ items }: { items: KpiItem[] }) {
  const t = useTheme()
  const colorMap = {
    good: t.palette.success.main,
    warn: t.palette.warning.main,
    bad: t.palette.error.main,
    default: t.palette.text.primary,
  }

  return (
    <Stack
      direction="row"
      sx={{
        flexWrap: 'wrap',
        gap: { xs: 1, sm: 1.5, md: 2 },
        py: 1,
      }}
    >
      {items.map((kpi) => (
        <Box
          key={kpi.label}
          onClick={kpi.onClick}
          sx={{
            minWidth: { xs: 72, sm: 90, md: 100 },
            flex: { xs: '1 1 72px', sm: '1 1 90px', md: '1 1 100px' },
            textAlign: 'center',
            py: { xs: 0.75, md: 1 },
            px: 0.5,
            borderRadius: 1.5,
            bgcolor: 'rgba(255,255,255,0.02)',
            border: '1px solid',
            borderColor: 'divider',
            cursor: kpi.onClick ? 'pointer' : 'default',
            transition: 'border-color 0.15s, background 0.15s',
            '&:hover': {
              borderColor: kpi.onClick ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.10)',
              bgcolor: kpi.onClick ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.03)',
            },
          }}
        >
          <Typography
            sx={{
              fontWeight: 800,
              fontFamily: '"IBM Plex Mono", monospace',
              color: colorMap[kpi.color ?? 'default'],
              lineHeight: 1.2,
              fontSize: { xs: '1rem', sm: '1.15rem', md: '1.25rem' },
            }}
          >
            {kpi.value ?? '\u2014'}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              display: 'block',
              mt: 0.25,
              fontSize: { xs: '0.6875rem', sm: '0.75rem' },
              lineHeight: 1.3,
            }}
          >
            {kpi.label}
          </Typography>
          {kpi.unit && (
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.625rem', opacity: 0.5 }}>
              {kpi.unit}
            </Typography>
          )}
        </Box>
      ))}
    </Stack>
  )
}
