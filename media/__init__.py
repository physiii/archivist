"""Hierarchical media processing pipeline for Archivist.

The guiding shape is a provenance-first semantic funnel:

    raw media
      -> cleanup / filtering
      -> atomic events
      -> step-by-step ledger
      -> compressed contextual account
      -> portable projections

Current layers:

    L0  Raw evidence store     - intact media with IDs and timestamps
    L1  Filtering layer        - scene detection, VAD, blur/sharpness scoring
    L2  Atomic event layer     - timestamped, provenance-rich event records
    L3  Local recap layer      - per-segment step-by-step event ledgers
    L4  Contextual memory      - compressed context built on the ledger
    L5  Document composer      - presentation-specific documents

Chronology remains the canonical truth. Higher layers compress aggressively,
but preserve references back to source evidence for inspectability.
"""
