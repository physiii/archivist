#!/usr/bin/env bash
# Post-reboot recovery after GPU 1 wedge.
# Context: GPU 1 (0000:2d:00.0) hung under ONNX workloads; immich ML was
# pinned there and kept kicking it. Fix: pin immich ML to GPU 0, let
# archivist use GPU 0, leave GPU 1 idle.
#
# Usage (after `sudo reboot`):
#   bash /home/andy/archivist/scripts/post-reboot-gpu0.sh

set -euo pipefail

log()  { printf '\033[1;34m[post-reboot]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[post-reboot]\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[1;31m[post-reboot]\033[0m %s\n' "$*" >&2; exit 1; }

log "Checking nvidia driver health..."
if ! nvidia-smi -i 0 >/dev/null 2>&1; then
  fail "nvidia-smi -i 0 failed. GPU 0 is not healthy; aborting."
fi
if ! nvidia-smi -i 1 >/dev/null 2>&1; then
  warn "GPU 1 still not responding. That's expected if we've chosen to retire it; continuing."
else
  log "GPU 1 responsive again (bonus)."
fi

log "Capping GPU 0 power limit to 350W (Xid 79 mitigation for power-sag drops)..."
log "  Default cap on RTX 4090 is 450W; reducing gives transient headroom."
if sudo -n nvidia-smi -i 0 -pm 1 >/dev/null 2>&1 && sudo -n nvidia-smi -i 0 -pl 350 >/dev/null 2>&1; then
  log "  Power limit applied."
else
  warn "  Could not apply power limit (needs sudo). Run manually:"
  warn "    sudo nvidia-smi -i 0 -pm 1 && sudo nvidia-smi -i 0 -pl 350"
fi
if nvidia-smi -i 1 >/dev/null 2>&1; then
  sudo -n nvidia-smi -i 1 -pm 1 >/dev/null 2>&1 || true
  sudo -n nvidia-smi -i 1 -pl 350 >/dev/null 2>&1 || true
fi

log "Removing stale archivist Created containers (if any)..."
for c in archivist archivist-recovery archivist-recovery2; do
  if docker inspect "$c" >/dev/null 2>&1; then
    docker rm -f "$c" >/dev/null 2>&1 || warn "Could not remove $c (may already be gone)"
  fi
done

log "Bringing archivist up on GPU 0 via compose..."
cd /home/andy/archivist
docker compose up -d archivist

log "Waiting for archivist health (port 5050) ..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:5050/health >/dev/null 2>&1; then
    log "archivist /health is responding."
    break
  fi
  sleep 2
done

log "Waiting for TTS WS server (port 5051) ..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:5051/tts/status >/dev/null 2>&1; then
    log "TTS status:"
    curl -s http://localhost:5051/tts/status | sed 's/^/  /'
    break
  fi
  sleep 2
done

log "Restarting immich-machine-learning on GPU 0 (IMMICH_ML_GPU_ID=0 in .env)..."
cd /home/andy/automation/immich/immich-app
docker compose up -d immich-machine-learning

log "Final GPU state:"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv || true

log "Done. Verify TTS with:"
cat <<'EOF'
  curl -s -X POST http://localhost:5051/tts \
    -H 'content-type: application/json' \
    -d '{"text":"XTTS is back online.","room":"default"}'
EOF
