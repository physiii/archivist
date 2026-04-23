import React from 'react'
import { Box } from '@mui/material'

export function DataTable({ children }: { children: React.ReactNode }) {
  return (
    <Box
      sx={{
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
        '& table': {
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: { xs: '0.75rem', sm: '0.8125rem' },
          fontFamily: '"IBM Plex Mono", monospace',
        },
        '& th': {
          textAlign: 'left',
          fontWeight: 700,
          fontSize: '0.6875rem',
          textTransform: 'uppercase',
          letterSpacing: 0.5,
          color: 'text.secondary',
          borderBottom: '1px solid',
          borderColor: 'divider',
          py: 1,
          px: { xs: 1, sm: 1.5 },
          whiteSpace: 'nowrap',
        },
        '& td': {
          py: 0.75,
          px: { xs: 1, sm: 1.5 },
          borderBottom: '1px solid',
          borderColor: 'rgba(255,255,255,0.035)',
          color: 'text.primary',
        },
        '& tr:last-child td': {
          borderBottom: 'none',
        },
        '& tr:hover td': {
          bgcolor: 'rgba(255,255,255,0.02)',
        },
      }}
    >
      {children}
    </Box>
  )
}

