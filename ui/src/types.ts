export type MilvusField = {
  name: string;
  dtype: string;
  params: Record<string, unknown>;
  is_primary: boolean;
  auto_id: boolean;
};

export type MilvusIndex = {
  field: string | null;
  index_type?: string | null;
  metric_type?: string | null;
  params?: unknown;
};

export type CollectionCard = {
  name: string;
  raw_name: string;
  num_entities?: number;
  fields?: MilvusField[];
  indexes?: MilvusIndex[];
  has_sparse?: boolean;
  vector_dim?: number | null;
  stats_error?: string;
};

export type CollectionsResponse = {
  collections: CollectionCard[];
};

export type CollectionDetail = {
  name: string;
  raw_name: string;
  num_entities: number;
  fields: MilvusField[];
};

export type SearchResult = {
  id: number | string;
  text: string;
  distance: number;
  hash?: string;
  embedding_model?: string;
  creation_date?: string;
  path?: string;
  collection?: string;
  collection_raw?: string;
};

export type SearchResponse = {
  results: SearchResult[];
  total_candidates?: number;
};

export type SearchMode = "dense" | "bm25" | "hybrid" | "sparse";

export type SearchAdvancedOptions = {
  mode: SearchMode;
  limit: number;
  unique: boolean;
  path?: string;
  metric_type?: string;
  nprobe?: number;
  hybrid_fusion?: "weighted" | "rrf";
  hybrid_dense_weight?: number;
  hybrid_sparse_weight?: number;
  hybrid_rrf_k?: number;
};

export type InsertResponse = {
  message: string;
  details: unknown;
};

export type BackupSourceStatus = {
  label: string;
  path: string;
  exists: boolean;
  readable: boolean;
};

export type BackupTarget = {
  id: string;
  profile: string;
  source: string;
  destination: string;
  enabled: boolean;
};

export type BackupTargetHealth = {
  profile: string;
  source: string;
  destination: string;
  source_exists: boolean;
  source_readable: boolean;
  destination_exists: boolean;
  destination_writable: boolean;
  destination_separate_mount: boolean;
  ready: boolean;
};

export type StoragePathUsage = {
  path: string;
  exists: boolean;
  mount_point: string | null;
  total_bytes: number | null;
  used_bytes: number | null;
  free_bytes: number | null;
  used_percent: number | null;
  readable: boolean;
  writable: boolean;
};

export type FilesystemUsage = {
  filesystem: string;
  mount_point: string;
  total_bytes: number | null;
  used_bytes: number | null;
  free_bytes: number | null;
  used_percent: number | null;
};

export type ZfsDiagnostics = {
  available: boolean;
  pool: string | null;
  health: string | null;
  status_ok: boolean | null;
  status_summary: string | null;
  errors: string[];
  command_error: string | null;
  used_bytes: number | null;
  avail_bytes: number | null;
  mount_point: string | null;
};

export type BackupStorageDiagnostics = {
  sources: StoragePathUsage[];
  destinations: StoragePathUsage[];
  filesystems: FilesystemUsage[];
  zfs: ZfsDiagnostics;
};

export type BackupStatus = {
  running: boolean;
  pid: number | null;
  run_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  exit_code: number | null;
  active_step?: string | null;
  progress_current?: number;
  progress_total?: number;
  progress_line: string | null;
};

export type BackupSchedule = {
  enabled: boolean;
  time_of_day: string;
  timezone: string;
  next_run_at: string | null;
  last_triggered_at: string | null;
};

export type BackupRunSummary = {
  run_id: string;
  started_at: string;
  main_log_path: string;
  debug_log_path: string;
  last_line: string | null;
  finished_at?: string | null;
  status?: string | null;
  archive_ok?: boolean | null;
  sync_total?: number | null;
  sync_failed?: number | null;
};

export type BackupFile = {
  name: string;
  bytes: number;
  modified_at: string;
};

export type BackupOverview = {
  backup_pool?: string | null;
  rsync_bwlimit?: string | null;
  sleep_seconds?: number | null;
  storage_ready: boolean;
  sources: BackupSourceStatus[];
  targets: string[];
  target_mappings: BackupTarget[];
  target_health: BackupTargetHealth[];
  storage_diagnostics: BackupStorageDiagnostics;
  timer_schedule: string | null;
  snapshots: Array<{ name: string; timestamp: string; source: string; run_id: string | null }>;
  status: BackupStatus;
  schedule: BackupSchedule;
  recent_runs: BackupRunSummary[];
  backup_files: BackupFile[];
};

export type BackupLogResponse = {
  main_log_tail: string;
  debug_log_tail?: string;
  summary?: {
    run_id: string;
    started_at: string | null;
    finished_at: string | null;
    status: string;
    archive_ok: boolean;
    archive_file: string;
    archive_error?: string | null;
    sync_total: number;
    sync_ok: number;
    sync_failed: number;
    sync_results: Array<{
      profile?: string;
      source: string;
      destination: string;
      dest_path?: string;
      exit_code: number;
      ok: boolean;
      last_line?: string | null;
    }>;
    snapshot_status?: string;
    snapshot_name?: string | null;
    snapshot_error?: string | null;
    errors?: string[];
    last_line?: string | null;
  } | null;
};

