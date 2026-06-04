import { Box, Chip, ScopedCssBaseline, Stack, ThemeProvider } from "@mui/material";

import ConsoleWorkspace from "../console/ConsoleWorkspace";
import { consoleEndpoints } from "../console/config/endpoints";
import { useApi } from "../console/lib/useApi";
import { theme } from "../console/theme";

type ConsoleStatus = {
  flags?: {
    system_enabled?: boolean;
    speech_input_enabled?: boolean;
  };
  tasks?: {
    tests?: {
      running?: boolean;
    };
  };
};

function statusChip(label: string, tone: "default" | "warning" | "error" = "default") {
  const styles =
    tone === "error"
      ? {
          bgcolor: "rgba(239,68,68,0.10)",
          color: "#fecaca",
          borderColor: "rgba(239,68,68,0.35)",
        }
      : tone === "warning"
        ? {
            bgcolor: "rgba(251,191,36,0.10)",
            color: "#fde68a",
            borderColor: "rgba(251,191,36,0.35)",
          }
        : {
            bgcolor: "rgba(91,140,255,0.10)",
            color: "#dbeafe",
            borderColor: "rgba(91,140,255,0.30)",
          };

  return (
    <Chip
      label={label}
      size="small"
      sx={{
        height: 24,
        fontSize: "0.72rem",
        fontWeight: 700,
        border: "1px solid",
        ...styles,
      }}
    />
  );
}

export default function ConsolePage() {
  const { data: status } = useApi<ConsoleStatus>(consoleEndpoints.status, { pollMs: 5000 });
  const flags = status?.flags ?? {};
  const testsRunning = status?.tasks?.tests?.running;

  return (
    <ThemeProvider theme={theme}>
      <ScopedCssBaseline enableColorScheme>
        <Box
          className="agent-console-page"
          sx={{
            display: "flex",
            minHeight: { xs: "auto", md: "calc(100vh - 120px)" },
            flexDirection: "column",
            gap: 1.5,
          }}
        >
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={1}
            sx={{
              alignItems: { xs: "flex-start", sm: "center" },
              justifyContent: "space-between",
              px: 0.5,
            }}
          >
            <Box>
              <Box
                component="span"
                sx={{
                  display: "block",
                  color: "text.secondary",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  letterSpacing: 1.1,
                  textTransform: "uppercase",
                }}
              >
                Agent
              </Box>
              <Box
                component="h1"
                sx={{
                  m: 0,
                  fontSize: "1.5rem",
                  lineHeight: 1.1,
                  letterSpacing: -0.4,
                  fontWeight: 800,
                }}
              >
                Console
              </Box>
            </Box>
            <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", alignItems: "center" }}>
              {flags.system_enabled === false && statusChip("SYSTEM OFF", "error")}
              {flags.system_enabled !== false && flags.speech_input_enabled === false && statusChip("SPEECH OFF", "warning")}
              {testsRunning ? statusChip("TESTS RUNNING", "warning") : statusChip("READY")}
            </Stack>
          </Stack>
          <ConsoleWorkspace status={status} />
        </Box>
      </ScopedCssBaseline>
    </ThemeProvider>
  );
}
