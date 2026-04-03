"""Hierarchical media processing pipeline for Archivist.

Implements a 6-layer architecture for processing raw media into searchable,
structured knowledge:

    L0  Raw evidence store     - intact media with IDs and timestamps
    L1  Filtering layer        - scene detection, VAD, blur/sharpness scoring
    L2  Atomic event layer     - timestamped structured event records
    L3  Local recap layer      - per-segment step-by-step accounts
    L4  Contextual memory      - compressed working memory for downstream tasks
    L5  Document composer      - task-specific output (chronology, minutes, report)

Each layer preserves references back to source media spans for inspectability.
"""
