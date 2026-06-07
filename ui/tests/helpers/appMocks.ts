import type { Locator, Page } from "@playwright/test";

export const TEST_COLLECTION_NAME = "transcripts";
export const TEST_MEDIA_ID = "media-001";

async function domClick(locator: Locator) {
  await locator.evaluate((node) => {
    if (node instanceof HTMLElement) node.click();
  });
}

function testReportPayload() {
  return {
    summary: {
      run_id: "focus-priorities-report",
      timestamp: "2026-04-23T19:40:00Z",
      total_tests: 15,
      passed: 15,
      failed: 0,
      pass_rate: 100,
      total_duration_s: 2.7,
    },
    test_duration_metrics: {
      p50_s: 0.18,
      p95_s: 0.33,
      slowest_tests: [
        { name: "tests/test_focus_priority_console_eval.py::test_focus_priority_performance_slow_executor_falls_back_without_locking_the_route", duration_s: 0.33 },
      ],
    },
    category_breakdown: {
      "focus-priorities": {
        total: 15,
        passed: 15,
        failed: 0,
        pass_rate: 100,
        p50_s: 0.18,
        p95_s: 0.33,
        failures: [],
      },
    },
    failure_analysis: {},
    performance_metrics: [],
    results: [
      {
        name: "tests/test_focus_priority_console_eval.py::test_focus_priority_eval_adds_personal_note_when_executor_is_unavailable",
        status: "passed",
        duration_s: 0.14,
        timestamp: "2026-04-23T19:40:00Z",
      },
    ],
  };
}

async function fulfillJson(
  route: Parameters<Page["route"]>[1] extends (route: infer T) => unknown ? T : never,
  payload: unknown,
  status = 200,
) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(payload),
  });
}

export async function mockAppApis(page: Page) {
  await page.route("**/health", async (route) => {
    await fulfillJson(route, { status: "healthy", components: {} });
  });

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const { pathname, searchParams } = url;

    if (pathname === "/api/integrations/status") {
      return fulfillJson(route, {
        integrations: [
          { id: "gmail", key: "gmail", name: "Gmail", description: "mail", connected: false, status: "needs_auth" },
          { id: "google-calendar", key: "calendar", name: "Google Calendar", description: "calendar", connected: false, status: "needs_auth" },
          { id: "google-drive", key: "drive", name: "Google Drive", description: "drive", connected: false, status: "needs_auth" },
        ],
        google: {
          connected: false,
          connectedAccountCount: 0,
          accounts: [],
          services: [
            { id: "gmail", name: "Gmail", connected: false, status: "needs_auth" },
            { id: "google-calendar", name: "Google Calendar", connected: false, status: "needs_auth" },
          ],
          enabledServices: [],
          requestedScopes: [],
          import: { running: false, message: "Import idle" },
          archive: {
            available: true,
            gmailMessages: 12,
            calendarEvents: 5,
            driveFiles: 2,
            chatMessages: 3,
            dayCount: 1,
            lastImportedAt: "2026-04-23T18:55:00Z",
          },
        },
        github: {
          connected: false,
          error: "Set GITHUB_TOKEN environment variable to enable GitHub integration.",
        },
      });
    }

    if (pathname === "/api/integrations/authorize") {
      return fulfillJson(route, { auth_url: "https://example.test/google-auth", message: "Continue authorization in the Google window." });
    }

    if (pathname === "/api/google/import" || pathname === "/api/google/import/status") {
      return fulfillJson(route, { ok: true, running: false, message: "Google history import is idle." });
    }

    if (pathname === "/api/chat/sessions") {
      return fulfillJson(route, { sessions: [], agent_sessions: [] });
    }

    if (/^\/api\/chat\/sessions\/.+\/messages$/.test(pathname)) {
      return fulfillJson(route, { messages: [] });
    }

    if (pathname === "/api/status") {
      return fulfillJson(route, {
        flags: { system_enabled: true, speech_input_enabled: true },
        integrations: {
          probes: [
            { name: "Agent Knowledge Base", ok: true, status: 200, target: "/media/mass/agents", latency_ms: 12 },
            { name: "Backup Service", ok: true, status: 200, target: "internal", latency_ms: 4 },
            { name: "Indexing Service", ok: true, status: 200, target: "internal", latency_ms: 5 },
          ],
        },
        mcp: {
          tools: [
            {
              name: "search_documents",
              description: "Query indexed documents and transcripts",
              inputSchema: { properties: { query: { type: "string" }, limit: { type: "number" } } },
            },
          ],
        },
        mcp_resources: { resources: [] },
        recent_tool_calls: [],
        tasks: {
          backup: { running: false },
          indexing: { running: false },
          media: { running: false },
          tests: { running: false },
        },
        repairs: {
          agent_runtime: {
            available: true,
            backend: "agents-repository",
            binary: "/media/mass/agents",
            model: "agents/operator-chat",
            workspace_path: "/home/andy/archivist",
            workspace_mounted: true,
            console_agent_id: "operator-chat",
            registered: true,
            errors: [],
          },
        },
      });
    }

    if (pathname === "/api/agent/config") {
      return fulfillJson(route, {
        consoleAgentId: "operator-chat",
        visibleAgentIds: ["operator-chat", "runtime-health-monitor", "verification-worker"],
        executorUrl: "/media/mass/agents",
        executorTokenConfigured: true,
        workspacePath: "/home/andy/archivist",
        registeredAgents: ["operator-chat", "runtime-health-monitor", "verification-worker"],
        teamAgents: [],
        runtime: {
          available: true,
          backend: "agents-repository",
          binary: "/media/mass/agents",
          model: "agents/operator-chat",
          registered_agents: ["operator-chat", "runtime-health-monitor", "verification-worker"],
        },
      });
    }

    if (pathname === "/api/agents/fleet") {
      return fulfillJson(route, {
        fleet_summary: {
          active_agents: 3,
          total_findings: 1,
          open_findings: 1,
          open_tickets: 1,
          critical_findings: 0,
          operational_score: 98,
          eval_score: 100,
        },
        lanes: [
          {
            id: "system",
            label: "System",
            description: "System agents are the durable control plane for Archivist.",
            summary: {
              active_agents: 2,
              total_findings: 1,
              open_tickets: 1,
              critical_findings: 0,
              operational_score: 98,
              eval_score: 100,
            },
            agents: [
              {
                id: "operator-chat",
                name: "Archivist Main",
                description: "Human-facing operator",
                status: "active",
                role: "operator",
                summary: "Primary control-plane operator for the Archivist console and chat surfaces.",
                workspace: "/media/mass/agents/agents/operator-chat",
                registered: true,
                group_label: "operator",
                lane: "system",
                chat_enabled: true,
                stats: { critical: 0, high: 0, open: 0, fixed: 0 },
                findings: [],
                recent_activity: [{ timestamp: "2026-04-23T19:35:00Z", action: "session", detail: "Workspace verification" }],
                activity: [],
                tickets: [],
              },
              {
                id: "verification-worker",
                name: "Archivist Verifier",
                description: "Validation gate for Archivist builds, tests, and runtime checks.",
                status: "active",
                role: "verifier",
                summary: "Owns targeted sign-off for backend, console, and focus-priority regressions.",
                workspace: "/media/mass/agents/agents/verification-worker",
                registered: true,
                group_label: "verifier",
                lane: "system",
                chat_enabled: true,
                stats: { critical: 0, high: 1, open: 1, fixed: 0 },
                findings: [
                  {
                    ticket_id: "focus-priorities-stale",
                    title: "Focus priority evals stale",
                    category: "verification",
                    severity: "high",
                    status: "open",
                    created_at: "2026-04-23T19:20:00Z",
                  },
                ],
                recent_activity: [{ timestamp: "2026-04-23T19:20:00Z", action: "verification", detail: "focus-priorities stale" }],
                activity: [],
                tickets: [
                  {
                    ticket_id: "focus-priorities-stale",
                    summary: "Focus priority evals are stale (75.0 minutes old).",
                    status: "open",
                    severity: "high",
                    authority: "verification-worker",
                    created_at: "2026-04-23T19:20:00Z",
                    last_seen_at: "2026-04-23T19:20:00Z",
                  },
                ],
              },
            ],
          },
          {
            id: "specialist",
            label: "Specialist",
            description: "Specialist agents own focused runtime or domain lanes.",
            agents: [
              {
                id: "priority-specialist",
                name: "Priority Specialist",
                description: "Focus and planning specialist lane.",
                status: "active",
                role: "specialist",
                summary: "Handles focus-specific analysis and revisions.",
                workspace: "/media/mass/agents/agents/priority-specialist",
                registered: true,
                group_label: "specialist",
                lane: "specialist",
                chat_enabled: true,
                stats: { critical: 0, high: 0, open: 0, fixed: 0 },
                findings: [],
                recent_activity: [{ timestamp: "2026-04-23T19:10:00Z", action: "session", detail: "Focus lane review" }],
                activity: [],
                tickets: [],
              },
            ],
          },
        ],
      });
    }

    if (pathname === "/api/automations/status") {
      return fulfillJson(route, {
        ok: true,
        tickets_open: 1,
        tickets: [
          {
            ticket_id: "focus-priorities-stale",
            summary: "Focus priority evals are stale (75.0 minutes old).",
            status: "open",
            severity: "high",
            authority: "verification-worker",
            created_at: "2026-04-23T19:20:00Z",
            last_seen_at: "2026-04-23T19:20:00Z",
            details: { profile: "focus-priorities", age_minutes: 75 },
          },
        ],
        agents: {
          available: true,
          binary: "/media/mass/agents",
          model: "agents/operator-chat",
          version: "test",
        },
        experiments: { completed: ["focus-priorities (scheduled)"], current: null },
        repair_runs: [],
        verification: {
          "focus-priorities": {
            profile: "focus-priorities",
            label: "Focus Priority Evals",
            status: "stale",
            owner_agents: ["verification-worker", "runtime-health-monitor"],
            stale_after_minutes: 45,
            latest: {
              run_id: "focus-priorities-report",
              timestamp: "2026-04-23T18:05:00Z",
              passed: 15,
              failed: 0,
              total_tests: 15,
              pass_rate: 100,
              age_minutes: 75,
            },
            tickets: [
              {
                ticket_id: "focus-priorities-stale",
                summary: "Focus priority evals are stale (75.0 minutes old).",
                status: "open",
                severity: "high",
                authority: "verification-worker",
                last_seen_at: "2026-04-23T19:20:00Z",
                details: { examples: ["tests/test_focus_priority_console_eval.py::test_focus_priority_eval_query_overview_surfaces_personal_manual_focus_first"] },
              },
            ],
            auto_run: { scheduled: false, reason: null, run_id: null },
            task: { running: false, trigger: "", run_id: "" },
          },
        },
      });
    }

    if (pathname === "/api/agent/sessions") {
      return fulfillJson(route, [
        {
          id: "agent:operator-chat:main:web:test-session@operator-chat",
          source: "local",
          status: "active",
          createdAt: 1712400000_000,
          updatedAt: 1712403600_000,
          messageCount: 2,
          lastMessage: "Workspace is /home/andy/archivist.",
          title: "Confirm the workspace path",
          agentId: "operator-chat",
          sessionKey: "main:web:test-session@operator-chat",
          surface: "console",
          historyScope: "main-chat",
        },
        {
          id: "agent:verification-worker:main:web:fleet-verification-worker@verification-worker",
          source: "local",
          status: "active",
          createdAt: 1712403800_000,
          updatedAt: 1712403900_000,
          messageCount: 2,
          lastMessage: "Focus priority evals are stale.",
          title: "Verifier lane follow-up",
          agentId: "verification-worker",
          sessionKey: "main:web:fleet-verification-worker@verification-worker",
          surface: "console",
          historyScope: "fleet-system",
        },
      ]);
    }

    if (/^\/api\/agent\/sessions\/.+$/.test(pathname)) {
      const isVerifier = pathname.includes("verification-worker");
      return fulfillJson(route, {
        id: isVerifier
          ? "agent:verification-worker:main:web:fleet-verification-worker@verification-worker"
          : "agent:operator-chat:main:web:test-session@operator-chat",
        agentId: isVerifier ? "verification-worker" : "operator-chat",
        sessionKey: isVerifier ? "main:web:fleet-verification-worker@verification-worker" : "main:web:test-session@operator-chat",
        source: "local",
        surface: "console",
        historyScope: isVerifier ? "fleet-system" : "main-chat",
        messages: isVerifier
          ? [
              { role: "user", text: "What is failing?", ts: 1712403800_000 },
              { role: "assistant", text: "Focus priority evals are stale and should be rerun.", ts: 1712403900_000 },
            ]
          : [
              { role: "user", text: "What is your workspace?", ts: 1712400000_000 },
              { role: "assistant", text: "My workspace is `/home/andy/archivist`.", ts: 1712403600_000 },
            ],
      });
    }

    if (pathname === "/api/tests/profiles") {
      return fulfillJson(route, {
        profiles: [
          { id: "focus-priorities", label: "Focus Priority Evals" },
        ],
      });
    }

    if (pathname === "/api/tests/status") {
      return fulfillJson(route, {
        tasks: {
          tests: {
            running: false,
            profile: "focus-priorities",
            run_id: "focus-priorities-report",
            started_at: "2026-04-23T19:40:00Z",
            finished_at: "2026-04-23T19:40:03Z",
            returncode: 0,
            progress_percent: 100,
            progress_line: "Completed",
            cancel_requested: false,
            tail: ["[focus-priorities] 15 passed in 2.68s"],
          },
        },
      });
    }

    if (pathname === "/api/tests/run" || pathname === "/api/tests/cancel") {
      return fulfillJson(route, { ok: true });
    }

    if (pathname === "/api/tests/summarize") {
      return fulfillJson(route, {
        ok: true,
        summary: "Focus priority evals are green. Add/remove/reorder/query flows passed and no freeze-budget regressions were detected.",
      });
    }

    if (pathname === "/api/test-reports/latest") {
      const report = testReportPayload();
      return fulfillJson(route, {
        reports: {
          all: { ok: true, report, report_mtime_iso: "2026-04-23T19:40:04Z" },
          "focus-priorities": { ok: true, report, report_mtime_iso: "2026-04-23T19:40:04Z" },
        },
      });
    }

    if (pathname === "/api/test-reports/history") {
      return fulfillJson(route, {
        reports: [
          {
            file: "20260423_focus-priorities.json",
            profile_id: "focus-priorities",
            report_mtime_iso: "2026-04-23T19:40:04Z",
            summary: testReportPayload().summary,
          },
        ],
      });
    }

    if (pathname === "/api/test-report/by-file") {
      return fulfillJson(route, {
        ok: true,
        file: "20260423_focus-priorities.json",
        profile_id: "focus-priorities",
        report: testReportPayload(),
      });
    }

    if (pathname === "/api/collections") {
      return fulfillJson(route, {
        collections: [
          {
            name: TEST_COLLECTION_NAME,
            raw_name: TEST_COLLECTION_NAME,
            num_entities: 42,
            vector_dim: 1024,
            has_sparse: true,
          },
        ],
      });
    }

    if (pathname === "/api/search/global") {
      return fulfillJson(route, {
        results: [
          {
            id: "row-1",
            distance: 0.12,
            text: "Transcript match",
            path: "/data/transcripts/demo.txt",
            collection: TEST_COLLECTION_NAME,
          },
        ],
        total_candidates: 1,
      });
    }

    if (pathname === `/api/collections/${encodeURIComponent(TEST_COLLECTION_NAME)}`) {
      return fulfillJson(route, {
        name: TEST_COLLECTION_NAME,
        raw_name: TEST_COLLECTION_NAME,
        num_entities: 42,
        fields: [
          { name: "id", dtype: "int64", is_primary: true, auto_id: false },
          { name: "text", dtype: "varchar" },
        ],
      });
    }

    if (pathname === `/api/collections/${encodeURIComponent(TEST_COLLECTION_NAME)}/search`) {
      return fulfillJson(route, {
        results: [
          {
            id: "row-1",
            distance: 0.12,
            text: "Transcript result",
            path: "/data/transcripts/demo.txt",
            creation_date: "2026-04-06",
          },
        ],
      });
    }

    if (pathname === `/api/collections/${encodeURIComponent(TEST_COLLECTION_NAME)}/embeddings-preview`) {
      return fulfillJson(route, {
        collection: TEST_COLLECTION_NAME,
        raw_name: TEST_COLLECTION_NAME,
        vector_dim: 1024,
        points: [
          { id: "row-1", vector: [0.1, 0.2, 0.3], text: "Transcript result", label: "row-1" },
        ],
        meta: {
          projection_method: "pca",
          axis_labels: ["X", "Y", "Z"],
        },
      });
    }

    if (pathname === "/api/backups/overview") {
      return fulfillJson(route, {
        status: { running: false, progress_line: null, active_step: null, progress_current: 0, progress_total: 0 },
        timer_schedule: "0 2 * * *",
        backup_pool: "tank/backups",
        rsync_bwlimit: "8m",
        schedule: { enabled: true, time_of_day: "02:00", next_run_at: "2026-04-24T02:00:00Z", last_triggered_at: "2026-04-23T02:00:00Z" },
        target_mappings: [
          { id: "backup-1", profile: "nas", source: "/src/docs", destination: "/dst/docs", enabled: true },
        ],
        target_health: [
          {
            profile: "nas",
            source: "/src/docs",
            destination: "/dst/docs",
            ready: true,
            source_exists: true,
            source_readable: true,
            destination_exists: true,
            destination_writable: true,
            destination_mount_ok: true,
            destination_separate_mount: true,
            last_backup_at: "2026-04-05T12:00:00Z",
          },
        ],
        storage_ready: true,
        storage_diagnostics: {
          filesystems: [{ filesystem: "tank", mount_point: "/dst", used_bytes: 1000, free_bytes: 9000, used_percent: 10 }],
          sources: [{ path: "/src/docs", exists: true, readable: true, writable: false, mount_ok: true, free_bytes: 4000, used_percent: 20, mount_point: "/src" }],
          destinations: [{ path: "/dst/docs", exists: true, readable: true, writable: true, mount_ok: true, free_bytes: 9000, used_percent: 10, mount_point: "/dst" }],
          zfs: { pool: "tank", health: "ONLINE", status_ok: true, used_bytes: 1000, avail_bytes: 9000, errors: [] },
        },
        recent_runs: [{ run_id: "backup-run-1", started_at: "2026-04-05T12:00:00Z", finished_at: "2026-04-05T12:05:00Z", status: "ok", archive_ok: true, sync_total: 1, sync_failed: 0 }],
        backup_files: [{ name: "backup-run-1.tar.zst", bytes: 1048576, modified_at: "2026-04-05T12:05:00Z" }],
        snapshots: [{ name: "auto-2026-04-05", timestamp: "2026-04-05T12:05:00Z" }],
      });
    }

    if (/^\/api\/backups\/runs\/.+\/logs$/.test(pathname)) {
      return fulfillJson(route, {
        main_log_tail: "backup started\nbackup finished",
        debug_log_tail: "debug trace",
        summary: {
          status: "ok",
          include_archive: true,
          archive_ok: true,
          archive_file: "backup-run-1.tar.zst",
          sync_ok: 1,
          sync_total: 1,
          sync_failed: 0,
          snapshot_status: "ok",
          errors: [],
          sync_results: [{ source: "/src/docs", destination: "/dst/docs", ok: true, exit_code: 0 }],
        },
      });
    }

    if (pathname === "/api/indexing/overview") {
      return fulfillJson(route, {
        status: {
          running: false,
          progress_line: null,
          active_step: null,
          progress_current: 0,
          progress_total: 0,
          elapsed_seconds: 0,
          eta_seconds: 0,
          current_path: null,
        },
        timer_schedule: "0 3 * * *",
        schedule: { enabled: true, time_of_day: "03:00", next_run_at: "2026-04-24T03:00:00Z", last_triggered_at: "2026-04-23T03:00:00Z" },
        targets: [
          {
            id: "target-1",
            path: "/data/indexing",
            enabled: true,
            recursive: true,
            transcript_files: 9,
            last_scanned_at: "2026-04-05T10:00:00Z",
            last_indexed_at: "2026-04-05T10:05:00Z",
          },
        ],
        target_health: [
          {
            id: "target-1",
            path: "/data/indexing",
            enabled: true,
            recursive: true,
            transcript_files: 9,
            last_scanned_at: "2026-04-05T10:00:00Z",
            last_indexed_at: "2026-04-05T10:05:00Z",
            exists: true,
            readable: true,
            ready: true,
            resolved_path: "/data/indexing",
            used_host_fallback: false,
            excluded_child_targets: [],
          },
        ],
        storage_ready: true,
        recent_runs: [{ run_id: "index-run-1", started_at: "2026-04-05T10:00:00Z", finished_at: "2026-04-05T10:04:00Z", status: "ok", files_total: 9, files_indexed: 9, chunks_total: 18, chunks_indexed: 18 }],
      });
    }

    if (/^\/api\/indexing\/runs\/.+\/logs$/.test(pathname)) {
      return fulfillJson(route, {
        main_log_tail: "indexing started\nindexing finished",
        debug_log_tail: "debug trace",
        summary: {
          status: "ok",
          files_total: 9,
          files_indexed: 9,
          files_skipped: 0,
          files_failed: 0,
          chunks_total: 18,
          chunks_indexed: 18,
          errors: [],
          last_line: "Indexed 9 files.",
          started_at: "2026-04-05T10:00:00Z",
          finished_at: "2026-04-05T10:04:00Z",
        },
      });
    }

    if (pathname === "/api/media/assets") {
      return fulfillJson(route, {
        assets: [
          {
            media_id: TEST_MEDIA_ID,
            path: "/media/demo/meeting.mkv",
            filename: "meeting.mkv",
            modality: "video",
            duration_s: 600,
            file_hash: "hash-1",
            file_size_bytes: 1048576,
            created_at: 1712400000,
            indexed_at: 1712403600,
            codec: "h264",
            pipeline_current: true,
            subject_line: "Team reviews a processed meeting file.",
            has_result: true,
          },
        ],
      });
    }

    if (pathname === "/api/media/jobs") {
      return fulfillJson(route, {
        jobs: [
          {
            job_id: "job-1",
            media_id: TEST_MEDIA_ID,
            status: "done",
            current_layer: "L7_subject_line",
            progress: 1,
            started_at: 1712400000,
            finished_at: 1712403600,
            error: "",
            artifacts_count: 4,
            events_count: 1,
            recaps_count: 1,
          },
        ],
      });
    }

    if (pathname === "/api/media/pipeline/compat-status") {
      return fulfillJson(route, { current: 1, stale: 0, broken: 0, total: 1 });
    }

    if (pathname === "/api/media/sources/status") {
      return fulfillJson(route, {
        configured: [
          {
            id: "office",
            enabled: true,
            kind: "camera",
            location: "office",
            has_audio: true,
            has_video_main: true,
            has_video_sub: true,
            motion_enabled: true,
            transcription_enabled: true,
            segment_format: "mp4",
          },
          {
            id: "office_mic",
            enabled: true,
            kind: "mic",
            location: "office",
            has_audio: true,
            has_video_main: false,
            has_video_sub: false,
            motion_enabled: false,
            transcription_enabled: true,
            segment_format: "mp4",
          },
        ],
        rtsp: [
          { id: "office", state: "reconnecting", segments_written: 12, kind: "camera", location: "office", last_error: "RTSP reconnecting" },
          { id: "office_mic", state: "up", segments_written: 14, kind: "mic", location: "office", last_error: null },
        ],
        streaming: [
          { source: "office_mic", submitted: 8, dropped: 0, qsize: 0, alive: true },
        ],
        motion: [
          { source: "office", events_published: 4, frames_seen: 80 },
        ],
        vision: [
          { source: "office", detections: 2, embeddings: 1, frames_seen: 20 },
          { clip_available: true, yolo_available: true },
        ],
        archive: { alive: true, enabled: true, last_pass: { scanned: 27, moved: 2 } },
        retention: { alive: true, enabled: true },
      });
    }

    if (pathname === "/api/media/process" || pathname === "/api/media/pipeline/migrate") {
      return fulfillJson(route, { ok: true, migrated: 1 });
    }

    if (pathname === `/api/media/pipeline/${TEST_MEDIA_ID}`) {
      return fulfillJson(route, {
        media_id: TEST_MEDIA_ID,
        artifact_count: 4,
        trace_artifact_count: 1,
        trace_artifact_counts: { transcript: 1 },
        subject_line: "Team reviews a processed meeting file.",
        document: {
          title: "Meeting walkthrough",
          format: "meeting_minutes",
          sections: [
            { heading: "Context Overview", kind: "context", content: "The team reviewed the processed meeting outputs." },
            { heading: "Walkthrough", kind: "walkthrough", content: "1. Opened the file.\n2. Read the summary.\n3. Confirmed the transcript." },
          ],
          full_text: "## Context Overview\n\nThe team reviewed the processed meeting outputs.\n\n## Walkthrough\n\n1. Opened the file.\n2. Read the summary.\n3. Confirmed the transcript.",
        },
        transcript: {
          text: "Hello team. We are reviewing the processed file.",
          segments: [{ text: "Hello team." }, { text: "We are reviewing the processed file." }],
          vtt_text: "WEBVTT\n\n00:00.000 --> 00:02.000\nHello team.",
        },
        injection: {
          transcript_stream_embedded: true,
          artifact_bundle_attached: true,
          transcript_sidecar_path: "/media/demo/meeting.vtt",
        },
        layers: {
          L7_subject_line: { ready: true },
          L4_memory: { open_loops_count: 1, context_overview: "The team reviewed the processed meeting outputs." },
        },
      });
    }

    if (pathname === `/api/media/artifacts/${TEST_MEDIA_ID}`) {
      const scope = searchParams.get("scope");
      if (scope === "trace") {
        return fulfillJson(route, {
          artifacts: [
            { artifact_id: "trace-1", kind: "transcript", start_s: 0, end_s: 2, content: "Hello team.", confidence: 1, metadata: {}, source_refs: [] },
          ],
        });
      }
      return fulfillJson(route, {
        artifacts: [
          { artifact_id: "subject-1", kind: "subject_line", start_s: 0, end_s: 0, content: "Team reviews a processed meeting file.", confidence: 1, metadata: {}, source_refs: [] },
          { artifact_id: "doc-1", kind: "document", start_s: 0, end_s: 600, content: "Meeting walkthrough", confidence: 1, metadata: {}, source_refs: [] },
          { artifact_id: "transcript-1", kind: "transcript", start_s: 0, end_s: 600, content: "Hello team. We are reviewing the processed file.", confidence: 1, metadata: {}, source_refs: [] },
          { artifact_id: "memory-1", kind: "memory", start_s: 0, end_s: 600, content: JSON.stringify({ context_overview: "The team reviewed the processed meeting outputs.", main_actors: ["Andy", "Team"], inferred_themes: ["Review", "Transcript"], final_takeaways: ["Outputs looked correct."], open_loops: ["Share follow-up notes."] }), confidence: 1, metadata: {}, source_refs: [] },
        ],
      });
    }

    return route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ error: `Unhandled test route: ${pathname}` }),
    });
  });
}

export async function clickSidebarNav(page: Page, label: string) {
  const menuButton = page.getByRole("button", { name: "Open menu" });
  if (await menuButton.isVisible().catch(() => false)) {
    await domClick(menuButton);
    await page.waitForSelector(".sidebar-mobile.open");
    await domClick(page.locator(".sidebar-mobile.open .sidebar-nav-item").filter({ hasText: label }).first());
    return;
  }
  await domClick(page.locator(".sidebar-nav-item").filter({ hasText: label }).first());
}

export async function waitForRowsOrEmpty(page: Page, rows: Locator, emptyState: Locator) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (await rows.count()) return "rows";
    if (await emptyState.count() && (await emptyState.first().isVisible())) return "empty";
    await page.waitForTimeout(250);
  }
  throw new Error("Timed out waiting for rows or empty state.");
}
