import { createTheme, alpha } from '@mui/material'

const surface = {
  bg: '#0a0e14',
  0: '#0d1117',
  1: '#111820',
  2: '#151e2a',
}

const accent = {
  primary: '#5b8cff',
  secondary: '#2dd4bf',
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
}

const border = 'rgba(255,255,255,0.07)'

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: accent.primary },
    secondary: { main: accent.secondary },
    success: { main: accent.success },
    warning: { main: accent.warning },
    error: { main: accent.error },
    background: {
      default: surface.bg,
      paper: surface[1],
    },
    text: {
      primary: 'rgba(255,255,255,0.92)',
      secondary: 'rgba(180,195,210,0.68)',
    },
    divider: border,
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: '"IBM Plex Sans", "Inter", system-ui, sans-serif',
    h4: { fontWeight: 760, letterSpacing: -0.5, fontSize: '1.75rem' },
    h5: { fontWeight: 720, letterSpacing: -0.4, fontSize: '1.25rem' },
    h6: { fontWeight: 700, letterSpacing: -0.2, fontSize: '1.05rem' },
    subtitle1: { fontWeight: 700, letterSpacing: -0.15, fontSize: '0.925rem' },
    subtitle2: { fontWeight: 700, letterSpacing: -0.1, fontSize: '0.85rem' },
    body1: { lineHeight: 1.55, fontSize: '0.9375rem' },
    body2: { lineHeight: 1.5, fontSize: '0.875rem' },
    caption: { fontSize: '0.8125rem', letterSpacing: 0.15 },
    overline: { fontSize: '0.75rem', letterSpacing: 1.1, fontWeight: 700 },
    button: { fontWeight: 700, letterSpacing: -0.05, textTransform: 'none', fontSize: '0.875rem' },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: surface.bg,
          backgroundImage: 'none',
        },
        '::selection': {
          backgroundColor: alpha(accent.primary, 0.28),
        },
        '::-webkit-scrollbar': { width: 5, height: 5 },
        '::-webkit-scrollbar-track': { background: 'transparent' },
        '::-webkit-scrollbar-thumb': { background: 'rgba(255,255,255,0.08)', borderRadius: 3 },
        '::-webkit-scrollbar-thumb:hover': { background: 'rgba(255,255,255,0.15)' },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: surface[1],
          border: `1px solid ${border}`,
          borderRadius: 10,
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: surface[1],
          border: `1px solid ${border}`,
          borderRadius: 10,
          transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
          '&:hover': {
            borderColor: 'rgba(255,255,255,0.10)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
          },
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 20,
          '&:last-child': { paddingBottom: 20 },
          '@media (max-width:600px)': {
            padding: 16,
            '&:last-child': { paddingBottom: 16 },
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
          backgroundColor: surface[0],
          borderRight: `1px solid ${border}`,
        },
      },
    },
    MuiListItemIcon: {
      styleOverrides: {
        root: { minWidth: 36, color: 'rgba(255,255,255,0.5)' },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          marginLeft: 8,
          marginRight: 8,
          marginTop: 2,
          marginBottom: 2,
          padding: '8px 12px',
          '&.Mui-selected': {
            backgroundColor: alpha(accent.primary, 0.10),
            '& .MuiListItemIcon-root': { color: accent.primary },
          },
          '&.Mui-selected:hover': {
            backgroundColor: alpha(accent.primary, 0.14),
          },
          '&:hover': {
            backgroundColor: 'rgba(255,255,255,0.04)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          paddingInline: 16,
          minHeight: 40,
        },
        sizeSmall: {
          minHeight: 36,
          paddingInline: 12,
          fontSize: '0.8125rem',
          borderRadius: 6,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none' },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: 6,
          height: 28,
          fontSize: '0.8125rem',
        },
        sizeSmall: {
          height: 24,
          fontSize: '0.75rem',
          borderRadius: 4,
        },
        filled: {
          backgroundColor: 'rgba(255,255,255,0.06)',
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: { minWidth: 44, minHeight: 44 },
        sizeSmall: { minWidth: 36, minHeight: 36 },
      },
    },
    MuiAccordion: {
      styleOverrides: {
        root: {
          borderRadius: '10px !important',
          border: `1px solid ${border}`,
          backgroundImage: 'none',
          backgroundColor: surface[1],
          '&:before': { display: 'none' },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          backgroundColor: 'rgba(255,255,255,0.02)',
          fontSize: '0.875rem',
          '& fieldset': { borderColor: 'rgba(255,255,255,0.08)' },
          '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.16)' },
          '&.Mui-focused fieldset': { borderColor: accent.primary },
        },
      },
    },
    MuiContainer: {
      defaultProps: { maxWidth: 'xl' },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 8, fontSize: '0.8125rem' },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          backgroundColor: surface[1],
          border: `1px solid ${border}`,
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: { padding: 6 },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          minHeight: 40,
        },
      },
    },
  },
})

