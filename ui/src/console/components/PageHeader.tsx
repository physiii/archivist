import React from 'react'
import { Box, Stack, Typography } from '@mui/material'
import type { StackProps } from '@mui/material/Stack'

type Props = {
  title: string
  subtitle?: string
  right?: React.ReactNode
} & StackProps

export function PageHeader({ title, subtitle, right, sx, ...stackProps }: Props) {
  return (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      spacing={1}
      sx={{
        alignItems: { xs: 'flex-start', sm: 'center' },
        justifyContent: 'space-between',
        mb: 2,
        pb: 1.5,
        borderBottom: '1px solid',
        borderColor: 'divider',
        ...sx,
      }}
      {...stackProps}
    >
      <Box sx={{ minWidth: 0 }}>
        <Typography variant="h5" component="h1">{title}</Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25, display: 'block' }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      {right && <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, flexWrap: 'wrap' }}>{right}</Box>}
    </Stack>
  )
}

