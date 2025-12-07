# utils.py
import os
import logging
import hashlib
import requests
import webvtt
from nltk.tokenize import sent_tokenize
from datetime import datetime

# Constants Configuration
CHUNK_SIZE = 6
OVERLAP = 2

# Number of text lines processed per Milvus insert batch (line-by-line mode).
BATCH_SIZE = 10

# Embedding batching / timeout configuration for calls to the embedding service.
# These are independent from Milvus insert batching above.
EMBED_BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "500"))  # texts per /embed_batch call
EMBED_TIMEOUT_SECONDS = int(os.environ.get("EMBED_TIMEOUT_SECONDS", "120"))
INDEX_TYPE = "IVF_FLAT"
METRIC_TYPE = "L2"
NLIST = 1024
SNIPPET_LENGTH = 1500  # Length of text snippet to store with each document

# Embedding Model Configuration
LOCAL_EMBEDDING_MODEL = "local_model"
# Updated to match the new local embedding service output dimension (see embedding server logs).
LOCAL_EMBEDDING_DIM = 1024
DEFAULT_EMBEDDING_MODEL = LOCAL_EMBEDDING_MODEL
EMBEDDING_DIMENSIONS = {
    "local_model": LOCAL_EMBEDDING_DIM,
    "text-embedding-3-large": 3072,
}

# Configure logging
logging.basicConfig(level=logging.DEBUG)


def embed_text_to_vector(text_chunks, model, is_local=True, ip_address="localhost", embedding_host="localhost"):
    """
    Generate embeddings for a list of text chunks.

    - For local models, this uses the batched /embed_batch endpoint on the embedding service.
    - For remote models (OpenAI, etc.), this function can be extended later.

    Returns a list of embeddings aligned 1:1 with `text_chunks`. Any failures are
    represented as None and will be filtered out by validate_embeddings().
    """
    if not text_chunks:
        return []

    vectors = []

    # Currently only the local embedding path is implemented.
    if not is_local:
        logging.error("Non-local embedding model requested, but remote embedding is not implemented yet.")
        return [None] * len(text_chunks)

    for i in range(0, len(text_chunks), EMBED_BATCH_SIZE):
        batch = text_chunks[i:i + EMBED_BATCH_SIZE]
        try:
            response = requests.post(
                f'http://{embedding_host}:8000/embed_batch',
                json={'texts': batch},
                headers={'Content-Type': 'application/json'},
                timeout=EMBED_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            body = response.json()
            embeddings = body.get('embeddings')

            if not isinstance(embeddings, list) or len(embeddings) != len(batch):
                logging.error(
                    "Embedding service returned mismatched embeddings length. "
                    f"Expected {len(batch)}, got {len(embeddings) if isinstance(embeddings, list) else 'non-list'}"
                )
                # Preserve alignment: mark this whole sub-batch as failed.
                vectors.extend([None] * len(batch))
                continue

            # Normalize each embedding in the sub-batch (handle accidental extra nesting).
            for emb, text_sample in zip(embeddings, batch):
                try:
                    if isinstance(emb, list) and len(emb) == 1 and isinstance(emb[0], list):
                        emb = emb[0]
                    vectors.append(emb)
                except Exception as inner_e:
                    logging.error(
                        f"Failed to normalize embedding for chunk '{text_sample[:50]}...' "
                        f"using model {model}: {inner_e}"
                    )
                    vectors.append(None)

        except Exception as e:
            logging.error(
                f"Embedding generation failed for batch starting at index {i} "
                f"using model {model}: {e}"
            )
            # Preserve alignment for this sub-batch on failure.
            vectors.extend([None] * len(batch))

    # Safety: ensure we always return exactly one embedding entry per input chunk.
    if len(vectors) != len(text_chunks):
        logging.error(
            f"Embedding vector count mismatch after batching. "
            f"Expected {len(text_chunks)}, got {len(vectors)}. Truncating or padding with None."
        )
        if len(vectors) > len(text_chunks):
            vectors = vectors[:len(text_chunks)]
        else:
            vectors.extend([None] * (len(text_chunks) - len(vectors)))

    return vectors

def validate_embeddings(vectors, expected_dim):
    valid_vectors = []
    for v in vectors:
        if isinstance(v, list) and len(v) == expected_dim:
            valid_vectors.append(v)
        else:
            logging.error(f"Invalid vector dimension received. Expected: {expected_dim}, Received: {len(v) if isinstance(v, list) else 'None'}")
            valid_vectors.append(None)
    return valid_vectors

def load_vtt_to_text(filepath):
    captions = webvtt.read(filepath)
    return " ".join(caption.text for caption in captions)

def chunk_text_with_overlap(text, initial_chunk_size=CHUNK_SIZE, max_length=SNIPPET_LENGTH):
    sentences = sent_tokenize(text)
    chunks = []
    i = 0

    while i < len(sentences):
        chunk_size = initial_chunk_size
        valid_chunk_formed = False
        while chunk_size > 0:
            chunk = ' '.join(sentences[i:i + chunk_size])
            if len(chunk) > max_length:
                logging.debug(f"Oversized chunk (size {len(chunk)}): {chunk[:500]}...")
                chunk_size -= 1
                if chunk_size == 0:
                    logging.error("Chunk size reduced to 0, unable to create valid chunks.")
                    i += 1  # Move to the next sentence to avoid infinite loop
                    break
            else:
                chunks.append(chunk)
                logging.debug(f"Final chunk (size {len(chunk)}): {chunk[:500]}...")
                valid_chunk_formed = True
                break  # Break once a valid chunk is formed

        if valid_chunk_formed:
            i += chunk_size  # Increment i by the size of the chunk that was added
        elif chunk_size == 0:
            i += 1  # Force increment if no valid chunk could be formed

    return chunks

def extract_snippet(text):
    if len(text) > SNIPPET_LENGTH:
        logging.warning(f"Snippet length ({len(text)}) exceeds max length ({SNIPPET_LENGTH}). Truncating.")
        return text[:SNIPPET_LENGTH]
    return text

def process_file(filepath):
    if filepath.endswith('.vtt'):
        text = load_vtt_to_text(filepath)
    elif filepath.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
    else:
        return []
    return chunk_text_with_overlap(text)

def file_hash(filepath):
    hash_obj = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    computed_hash = hash_obj.hexdigest()
    logging.debug(f"Hash for {filepath}: {computed_hash}")
    return computed_hash

def get_creation_date(filepath):
    stat_info = os.stat(filepath)
    return int(stat_info.st_ctime)

def count_files(directory):
    total_files = 0
    for root, dirs, files in os.walk(directory):
        total_files += len(files)
    return total_files

def load_files(directory, recursive):
    directory = os.path.abspath(directory)  # Ensure directory is an absolute path
    for root, dirs, files in os.walk(directory) if recursive else [(directory, [], os.listdir(directory))]:
        for file in files:
            filepath = os.path.join(root, file)
            filepath = os.path.abspath(filepath)  # Ensure filepath is an absolute path
            if os.path.isfile(filepath):
                # Skip unsupported files
                if not (filepath.endswith('.txt') or filepath.endswith('.vtt')):
                    logging.debug(f"Skipping {filepath} as it is not a supported file type.")
                    continue

                filehash = file_hash(filepath)
                yield filepath, filehash, get_creation_date(filepath)

def ensure_collection_exists(collection_name, schema):
    from pymilvus import Collection, utility

    if utility.has_collection(collection_name):
        collection = Collection(name=collection_name)
        # Check if the schema matches
        existing_fields = {field.name: field for field in collection.schema.fields}
        required_fields = {field.name: field for field in schema.fields}

        # Check if the vector field exists and has the correct dimension
        if 'vector' in existing_fields and 'vector' in required_fields:
            existing_dim = existing_fields['vector'].params['dim']
            required_dim = required_fields['vector'].params['dim']
            if existing_dim != required_dim:
                logging.debug(f"Collection exists but has incorrect dimension. Dropping and recreating collection.")
                collection.drop()
                collection = Collection(name=collection_name, schema=schema)
            else:
                logging.debug(f"Collection exists with correct dimension.")
        else:
            logging.debug(f"Collection exists but schema doesn't match. Dropping and recreating collection.")
            collection.drop()
            collection = Collection(name=collection_name, schema=schema)
    else:
        collection = Collection(name=collection_name, schema=schema)
        logging.debug(f"Created new collection with fields: {[field.name for field in schema.fields]}")

    return collection

def delete_old_entries(collection, filepath):
    expr = f'path == "{filepath}"'
    collection.delete(expr)
    logging.info(f"Deleted old entries for {filepath}")

def process_and_insert_lines(filepath, collection, embedding_model, embedding_dim, use_local=True, embedding_host="localhost"):
    filehash = file_hash(filepath)
    creation_date = get_creation_date(filepath)

    # Delete old entries before inserting new ones
    delete_old_entries(collection, filepath)

    with open(filepath, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]

    for i in range(0, len(lines), BATCH_SIZE):
        batch = lines[i:i + BATCH_SIZE]
        vectors = embed_text_to_vector(batch, embedding_model, use_local, embedding_host=embedding_host)
        validated_vectors = validate_embeddings(vectors, embedding_dim)

        # Filter out any failed embeddings
        batch_pairs = [(v, s) for v, s in zip(validated_vectors, batch) if v is not None]
        if not batch_pairs:
            logging.warning(f"No valid embeddings for batch starting at line {i} in {filepath}")
            continue

        filtered_vectors, filtered_snippets = zip(*batch_pairs)

        data = {
            "vector": list(filtered_vectors),
            "path": [filepath] * len(filtered_vectors),
            "snippet": [s[:SNIPPET_LENGTH] for s in filtered_snippets],
            "filehash": [filehash] * len(filtered_vectors),
            "embedding_model": [embedding_model] * len(filtered_vectors),
            "creation_date": [creation_date] * len(filtered_vectors)
        }

        collection.insert(data)
        logging.info(f"Inserted {len(filtered_vectors)} vectors for lines from {filepath}")
