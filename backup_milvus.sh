#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-milvus-standalone}"
BACKUP_DIR="/backup"
BACKUP_FILE="milvus_backup.tar"
HOST_BACKUP_FILE="${HOST_BACKUP_FILE:-./milvus_backup.tar}"

echo "Creating backup inside container ${CONTAINER_NAME}..."
docker exec "${CONTAINER_NAME}" mkdir -p "${BACKUP_DIR}"

echo "Archiving Milvus data inside container..."
docker exec "${CONTAINER_NAME}" tar cvf "${BACKUP_DIR}/${BACKUP_FILE}" \
  /var/lib/milvus /run/milvus /tmp/milvus /milvus

echo "Copying backup to host (${HOST_BACKUP_FILE})..."
docker cp "${CONTAINER_NAME}:${BACKUP_DIR}/${BACKUP_FILE}" "${HOST_BACKUP_FILE}"

echo "Milvus backup completed successfully. Backup file: ${HOST_BACKUP_FILE}" 
