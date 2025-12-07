#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-milvus-standalone}"
BACKUP_DIR="/backup"
BACKUP_FILE="${BACKUP_FILE:-milvus_backup.tar}"
DEFAULT_HOST_BACKUP_FILE="./milvus_backup.tar"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DELETE_BEFORE=0

usage() {
  echo "Usage: $0 [-d] [backup_file]" >&2
  echo "  -d           docker compose down before restore" >&2
  echo "  backup_file  path to backup tar on host (default: ${DEFAULT_HOST_BACKUP_FILE})" >&2
}

while getopts "d" opt; do
  case "${opt}" in
    d)
      DELETE_BEFORE=1
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done
shift $((OPTIND-1))

HOST_BACKUP_FILE="${1:-${DEFAULT_HOST_BACKUP_FILE}}"

cd "${SCRIPT_DIR}"

if [[ ! -f "${HOST_BACKUP_FILE}" ]]; then
  echo "Backup file not found: ${HOST_BACKUP_FILE}" >&2
  exit 1
fi

if [[ "${DELETE_BEFORE}" -eq 1 ]]; then
  echo "Stopping Milvus stack (docker compose down)..."
  docker compose down
fi

echo "Starting Milvus service..."
docker compose up -d milvus

echo "Creating backup directory inside container..."
docker exec "${CONTAINER_NAME}" mkdir -p "${BACKUP_DIR}"

echo "Copying backup archive into container..."
docker cp "${HOST_BACKUP_FILE}" "${CONTAINER_NAME}:${BACKUP_DIR}/${BACKUP_FILE}"

echo "Restoring data inside container..."
docker exec "${CONTAINER_NAME}" tar xvf "${BACKUP_DIR}/${BACKUP_FILE}" -C /

echo "Restarting Milvus service..."
docker compose restart milvus

echo "Restore completed successfully from: ${HOST_BACKUP_FILE}" 
