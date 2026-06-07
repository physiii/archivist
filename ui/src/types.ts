export type SearchMode = "dense" | "bm25" | "hybrid";

export type SearchAdvancedOptions = {
  mode: SearchMode;
  limit: number;
  unique: boolean;
  path?: string;
  metric_type?: "L2" | "IP" | "COSINE" | string;
  nprobe?: number;
  hybrid_fusion?: "weighted" | "rrf";
  hybrid_dense_weight?: number;
  hybrid_sparse_weight?: number;
  hybrid_rrf_k?: number;
  max_distance?: number;
  per_collection_limit?: number;
};

export type SearchResult = {
  id: string | number;
  distance: number;
  text?: string;
  creation_date?: string;
  filehash?: string;
  path?: string;
  source_id?: string;
  chunk_duration_s?: number;
  level?: number;
  t_start_ms?: number;
  t_end_ms?: number;
  doc_type?: string;
  source_type?: string;
  collection?: string;
  collection_raw?: string;
  tags?: unknown;
};

export type CollectionCard = {
  name: string;
  raw_name: string;
  num_entities?: number;
  vector_dim?: number;
  has_sparse?: boolean;
  stats_error?: string;
};

export type CollectionField = {
  name: string;
  dtype: string;
  params?: Record<string, unknown>;
  is_primary?: boolean;
  auto_id?: boolean;
};

export type CollectionDetail = {
  name: string;
  raw_name: string;
  num_entities: number;
  fields: CollectionField[];
};

export type BackupTarget = {
  id: string;
  profile: string;
  source: string;
  destination: string;
  enabled: boolean;
};

export type BackupRun = {
  run_id: string;
  started_at: string;
  finished_at?: string | null;
  status?: string | null;
  archive_ok?: boolean | null;
  sync_total?: number | null;
  sync_failed?: number | null;
  last_line?: string | null;
};

export type BackupLogResponse = {
  main_log_tail: string;
  debug_log_tail: string;
  summary?: {
    status?: string;
    include_archive?: boolean;
    archive_ok?: boolean;
    archive_file?: string | null;
    sync_ok?: number;
    sync_total?: number;
    sync_failed?: number;
    snapshot_status?: string;
    errors?: string[];
    sync_results?: Array<{
      source: string;
      destination: string;
      ok: boolean;
      exit_code: number;
    }>;
  } | null;
};

export type BackupOverview = {
  status: {
    running: boolean;
    run_id?: string | null;
    started_at?: string | null;
    finished_at?: string | null;
    exit_code?: number | null;
    active_step?: string | null;
    progress_current?: number;
    progress_total?: number;
    progress_line?: string | null;
  };
  timer_schedule?: string;
  backup_pool?: string;
  archive_bwlimit?: string;
  rsync_bwlimit?: string;
  schedule: {
    enabled: boolean;
    time_of_day: string;
    timezone?: string;
    next_run_at?: string | null;
    last_triggered_at?: string | null;
  };
  target_mappings: BackupTarget[];
  target_health: Array<{
    profile: string;
    source: string;
    destination: string;
    ready: boolean;
    source_exists: boolean;
    source_readable: boolean;
    source_mount_ok?: boolean;
    destination_exists: boolean;
    destination_writable: boolean;
    destination_mount_ok?: boolean;
    destination_separate_mount?: boolean;
    last_backup_at?: string | null;
  }>;
  storage_ready: boolean;
  storage_diagnostics: {
    filesystems: Array<{
      filesystem: string;
      mount_point: string;
      total_bytes?: number | null;
      used_bytes?: number | null;
      free_bytes?: number | null;
      used_percent?: number | null;
    }>;
    sources: Array<{
      path: string;
      exists: boolean;
      readable: boolean;
      writable: boolean;
      mount_expected?: boolean;
      mount_ok?: boolean;
      mount_point?: string | null;
      total_bytes?: number | null;
      used_bytes?: number | null;
      free_bytes?: number | null;
      used_percent?: number | null;
    }>;
    destinations: Array<{
      path: string;
      exists: boolean;
      readable: boolean;
      writable: boolean;
      mount_expected?: boolean;
      mount_ok?: boolean;
      mount_point?: string | null;
      total_bytes?: number | null;
      used_bytes?: number | null;
      free_bytes?: number | null;
      used_percent?: number | null;
    }>;
    zfs: {
      host?: string | null;
      pool?: string | null;
      health?: string | null;
      status_ok?: boolean | null;
      status_summary?: string | null;
      used_bytes?: number | null;
      avail_bytes?: number | null;
      command_error?: string | null;
      errors: string[];
    };
  };
  recent_runs: BackupRun[];
  backup_files: Array<{
    name: string;
    bytes: number;
    modified_at: string;
  }>;
  snapshots: Array<{
    name: string;
    timestamp: string;
  }>;
  warning?: string;
};

export type IndexingTarget = {
  id: string;
  path: string;
  enabled: boolean;
  recursive: boolean;
  transcript_files: number;
  last_scanned_at?: string | null;
  last_indexed_at?: string | null;
  last_error?: string | null;
};

export type IndexingOverview = {
  status: {
    running: boolean;
    run_id?: string | null;
    started_at?: string | null;
    finished_at?: string | null;
    exit_code?: number | null;
    active_step?: string | null;
    progress_current?: number;
    progress_total?: number;
    progress_line?: string | null;
    elapsed_seconds?: number;
    eta_seconds?: number | null;
    files_done?: number;
    files_total?: number;
    chunks_done?: number;
    chunks_total?: number;
    current_path?: string | null;
  };
  timer_schedule?: string;
  schedule: {
    source?: string;
    enabled: boolean;
    time_of_day: string;
    timezone?: string;
    next_run_at?: string | null;
    last_triggered_at?: string | null;
  };
  targets: IndexingTarget[];
  target_health: Array<
    IndexingTarget & {
      exists: boolean;
      readable: boolean;
      ready: boolean;
      resolved_path: string;
      used_host_fallback?: boolean;
      excluded_child_targets?: string[];
    }
  >;
  storage_ready: boolean;
  recent_runs: Array<{
    run_id: string;
    started_at: string;
    finished_at?: string | null;
    status?: string | null;
    last_line?: string | null;
    files_total?: number | null;
    files_indexed?: number | null;
    chunks_total?: number | null;
    chunks_indexed?: number | null;
  }>;
  warning?: string;
};

export type IndexingLogResponse = {
  main_log_tail: string;
  debug_log_tail: string;
  summary?: {
    status?: string;
    files_total?: number;
    files_indexed?: number;
    files_skipped?: number;
    files_failed?: number;
    chunks_total?: number;
    chunks_indexed?: number;
    errors?: string[];
    last_line?: string;
    started_at?: string;
    finished_at?: string;
  } | null;
};

export type McpIntegration = {
  id: string;
  key?: string;
  name: string;
  description: string;
  connected: boolean;
  status: "connected" | "needs_auth" | "error" | "timeout" | "not_installed" | "no_response" | "unknown";
  error?: string | null;
  account?: string;
  account_id?: string;
  server_name?: string;
  server_version?: string;
};

export type GoogleAccountServiceStatus = {
  id: string;
  name: string;
  description?: string;
  connected: boolean;
  status: "connected" | "needs_auth" | "error" | "timeout" | "not_installed" | "no_response" | "unknown";
  error?: string | null;
};

export type GoogleEnabledService = {
  key: string;
  id: string;
  name: string;
  description: string;
  scopes: string[];
};

export type GoogleAccountStatus = {
  id: string;
  label: string;
  account?: string | null;
  token_path?: string | null;
  legacy?: boolean;
  connected: boolean;
  fully_connected: boolean;
  connected_services: number;
  service_count: number;
  services: GoogleAccountServiceStatus[];
};

export type GoogleIntegrationsSummary = {
  connected: boolean;
  configured: boolean;
  accountCount: number;
  connectedAccountCount: number;
  fullyConnectedAccountCount: number;
  accounts: GoogleAccountStatus[];
  services: GoogleAccountServiceStatus[];
  enabledServices?: GoogleEnabledService[];
  requestedScopes?: string[];
  archive?: {
    available: boolean;
    accountCount: number;
    gmailMessages: number;
    calendarEvents: number;
    driveFiles?: number;
    chatMessages?: number;
    dayCount: number;
    lastImportedAt?: string | null;
  };
  import?: {
    running: boolean;
    message?: string | null;
    startedAt?: string | null;
    finishedAt?: string | null;
    accounts?: Array<{
      account?: string;
      gmailMessages?: number;
      calendarEvents?: number;
      driveFiles?: number;
      chatMessages?: number;
      dayCount?: number;
      error?: string;
      errors?: string[];
    }>;
  };
  tokenPaths?: string[];
  clientSecretPath?: string | null;
};

export type GitHubIntegrationStatus = {
  connected: boolean;
  login?: string;
  name?: string;
  avatar_url?: string;
  expires_at?: string;
  scopes?: string;
  rate_limit?: number;
  rate_remaining?: number;
  error?: string | null;
};

export type IntegrationsStatusResponse = {
  integrations: McpIntegration[];
  google?: GoogleIntegrationsSummary;
  github?: GitHubIntegrationStatus;
  token_path?: string | null;
  token_paths?: string[];
  client_secret_path?: string | null;
};

export type EmbeddingsPreviewPoint = {
  id: string | number;
  vector: number[];
  text?: string;
  tags?: unknown;
  label?: string | null;
  cluster?: string | number | null;
  similarity?: number | null;
  query_distance?: number | null;
  metadata?: Record<string, unknown>;
};

export type EmbeddingsPreviewResponse = {
  collection: string;
  raw_name: string;
  vector_dim: number;
  points: EmbeddingsPreviewPoint[];
  query_point?: {
    vector: number[];
    label: string;
    text?: string;
    distance?: number;
  } | null;
  query?: string;
  query_error?: string | null;
  meta?: {
    returned?: number;
    metric_type?: string;
    projection_method?: string;
    axis_labels?: string[];
  };
};

export type MediaAsset = {
  media_id: string;
  path: string;
  filename: string;
  modality: string;
  duration_s: number;
  file_hash: string;
  file_size_bytes: number;
  created_at: number;
  indexed_at: number;
  codec?: string;
  sample_rate?: number;
  width?: number;
  height?: number;
  fps?: number;
  metadata?: Record<string, unknown>;
  pipeline_current?: boolean;
  pipeline_version?: string | null;
  subject_line?: string | null;
  has_result?: boolean;
};

export type MediaPipelineJob = {
  job_id: string;
  media_id: string;
  status: string;
  current_layer: string;
  progress: number;
  started_at: number;
  finished_at: number;
  error: string;
  artifacts_count: number;
  events_count: number;
  recaps_count: number;
};

export type MediaArtifact = {
  artifact_id: string;
  kind: string;
  start_s: number;
  end_s: number;
  content: string;
  confidence: number;
  metadata: Record<string, unknown>;
  source_refs: string[];
};

export type MediaDocumentSection = {
  heading: string;
  content?: string;
  kind?: string;
  source_refs?: string[];
};

export type MediaPipelineResult = {
  media_id?: string;
  artifact_count?: number;
  trace_artifact_count?: number;
  trace_artifact_counts?: Record<string, number>;
  layers?: Record<string, Record<string, unknown>>;
  document?: {
    title?: string;
    format?: string;
    sections?: MediaDocumentSection[];
    full_text?: string;
    subject_line?: string;
  } | null;
  subject_line?: string;
  transcript?: {
    text?: string;
    segments?: Array<{ text?: string }>;
    vtt_text?: string;
  } | null;
  injection?: Record<string, unknown> | null;
  [key: string]: unknown;
};
