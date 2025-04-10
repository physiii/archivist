# load.py
import os
import logging
from datetime import datetime
from hashlib import sha256
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from tqdm import tqdm
import traceback

from utils import (
    DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, LOCAL_EMBEDDING_MODEL, LOCAL_EMBEDDING_DIM,
    SNIPPET_LENGTH, INDEX_TYPE, METRIC_TYPE, NLIST,
    embed_text_to_vector, validate_embeddings, count_files, load_files,
    ensure_collection_exists, delete_old_entries, process_file, extract_snippet,
    file_hash, get_creation_date, process_and_insert_lines
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def clear_collection(collection_name):
    if utility.has_collection(collection_name):
        collection = Collection(name=collection_name)
        collection.drop()
        logging.info(f"Vector store {collection_name} cleared.")
    else:
        logging.info(f"Collection {collection_name} does not exist. Nothing to clear.")

def clear_vectorstore_collection(collection_name, ip_address="localhost"):
    connections.connect("default", host=ip_address, port='19530')

    # Standardize collection naming
    collection_name = f"documents_{collection_name}"

    clear_collection(collection_name)
    logging.info(f"Collection '{collection_name}' has been cleared.")

    connections.disconnect("default")

def load_to_vectorstore(args):
    start_time = datetime.now()
    connections.connect("default", host='localhost', port='19530')

    if args.clear:
        if not args.clear_collection:
            logging.error("When using --clear, you must specify a collection name with --clear-collection")
            return
        clear_collection(args.clear_collection)
        logging.info(f"Collection '{args.clear_collection}' has been cleared.")
        connections.disconnect("default")
        return

    if not args.path:
        logging.error("You must specify a path when not using --clear")
        return

    embedding_model = args.model if not args.local else LOCAL_EMBEDDING_MODEL
    is_local = embedding_model == LOCAL_EMBEDDING_MODEL
    embedding_dim = EMBEDDING_DIMENSIONS.get(embedding_model, LOCAL_EMBEDDING_DIM)

    collection_name = args.collection if args.collection else f"documents_{embedding_model.replace('-', '_')}"

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
        FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="snippet", dtype=DataType.VARCHAR, max_length=SNIPPET_LENGTH),
        FieldSchema(name="filehash", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="embedding_model", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="creation_date", dtype=DataType.INT64)
    ]
    schema = CollectionSchema(fields, description="Document Collection")

    collection = ensure_collection_exists(collection_name, schema)

    logging.debug(f"Using collection: {collection_name}")
    logging.debug(f"Schema set with embedding dimension: {embedding_dim}")

    if not collection.has_index():
        index_params = {"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}}
        collection.create_index(field_name="vector", index_params=index_params)

    collection.load()

    path = os.path.abspath(args.path)

    if os.path.isdir(path):
        total_files = count_files(path)
        progress_bar = tqdm(total=total_files, desc="Processing files")
        for filepath, filehash, creation_date in load_files(path, args.recursive):
            try:
                expr = f"filehash == '{filehash}'"
                results = collection.query(expr, output_fields=["filehash"])
                if results:
                    logging.debug(f"Skipping {filepath} as it is unchanged.")
                    continue

                logging.debug(f"Processing {filepath} as it is new or modified.")
                if args.line_by_line:
                    process_and_insert_lines(filepath, collection, embedding_model, embedding_dim, is_local)
                else:
                    # Delete old entries before processing
                    delete_old_entries(collection, filepath)
                    chunks = process_file(filepath)
                    if chunks:
                        text_snippets = [extract_snippet(chunk) for chunk in chunks]
                        vectors = embed_text_to_vector(chunks, embedding_model, is_local)
                        validated_vectors = validate_embeddings(vectors, embedding_dim)
                        if validated_vectors:
                            # Adjust data format to match Milvus's expectations
                            data = [
                                [vector for vector in validated_vectors if vector is not None],  # vector field data
                                [filepath] * len(validated_vectors),                             # path field data
                                text_snippets,                                                    # snippet field data
                                [filehash] * len(validated_vectors),                              # filehash field data
                                [embedding_model] * len(validated_vectors),                       # embedding_model field data
                                [creation_date] * len(validated_vectors)                          # creation_date field data
                            ]
                            fields = ["vector", "path", "snippet", "filehash", "embedding_model", "creation_date"]
                            logging.info(f"Number of entities before insertion: {collection.num_entities}")
                            collection.insert(data, fields=fields)
                            collection.flush()  # Flush after insertion
                            collection.load()
                            logging.info(f"Number of entities after insertion: {collection.num_entities}")
                            logging.info(f"Successfully inserted vectors and snippets for {filepath}")
            except Exception as e:
                logging.error(f"Error processing {filepath}: {e}")
                logging.error(traceback.format_exc())
            finally:
                progress_bar.update(1)
        progress_bar.close()
    elif os.path.isfile(path):
        try:
            filehash = file_hash(path)
            creation_date = get_creation_date(path)
            expr = f"filehash == '{filehash}'"
            results = collection.query(expr, output_fields=["filehash"])
            if results:
                logging.debug(f"Skipping {path} as it is unchanged.")
            else:
                logging.debug(f"Processing {path} as it is new or modified.")
                if args.line_by_line:
                    process_and_insert_lines(path, collection, embedding_model, embedding_dim, is_local)
                else:
                    # Delete old entries before processing
                    delete_old_entries(collection, path)
                    chunks = process_file(path)
                    if chunks:
                        text_snippets = [extract_snippet(chunk) for chunk in chunks]
                        vectors = embed_text_to_vector(chunks, embedding_model, is_local)
                        validated_vectors = validate_embeddings(vectors, embedding_dim)
                        if validated_vectors:
                            # Adjust data format to match Milvus's expectations
                            data = [
                                [vector for vector in validated_vectors if vector is not None],  # vector field data
                                [path] * len(validated_vectors),                                 # path field data
                                text_snippets,                                                    # snippet field data
                                [filehash] * len(validated_vectors),                              # filehash field data
                                [embedding_model] * len(validated_vectors),                       # embedding_model field data
                                [creation_date] * len(validated_vectors)                          # creation_date field data
                            ]
                            fields = ["vector", "path", "snippet", "filehash", "embedding_model", "creation_date"]
                            logging.info(f"Number of entities before insertion: {collection.num_entities}")
                            collection.insert(data, fields=fields)
                            collection.flush()  # Flush after insertion
                            collection.load()
                            logging.info(f"Number of entities after insertion: {collection.num_entities}")
                            logging.info(f"Successfully inserted vectors and snippets for {path}")
        except Exception as e:
            logging.error(f"Error processing {path}: {e}")
            logging.error(traceback.format_exc())

    connections.disconnect("default")
    end_time = datetime.now()
    logging.info(f"Operation completed in {end_time - start_time}.")

def load_text_to_vectorstore(text, collection_name=None, embedding_model=None,
                             line_by_line=False, chunk_size=1000, overlap=0, ip_address="localhost", embedding_host="localhost"):
    logging.info(f"Starting load_text_to_vectorstore: collection={collection_name}, model={embedding_model}, ip={ip_address}")
    
    try:
        logging.info("Connecting to Milvus...")
        connections.connect("default", host=ip_address, port='19530')
        logging.info("Connected to Milvus successfully")

        # Use local embedding model as default
        embedding_model = embedding_model or LOCAL_EMBEDDING_MODEL
        is_local = embedding_model == LOCAL_EMBEDDING_MODEL
        logging.info(f"Using embedding model: {embedding_model}, is_local={is_local}")

        # Standardize collection naming
        if collection_name:
            collection_name = f"documents_{collection_name}"
        else:
            collection_name = f"documents_{embedding_model.replace('-', '_')}"
        logging.info(f"Using collection name: {collection_name}")

        # Use local embedding dimension if using local model
        embedding_dim = LOCAL_EMBEDDING_DIM if is_local else EMBEDDING_DIMENSIONS.get(embedding_model, LOCAL_EMBEDDING_DIM)
        logging.info(f"Embedding dimension: {embedding_dim}")

        # Check if collection exists and has the correct dimension. Drop if incorrect.
        if utility.has_collection(collection_name):
            logging.info(f"Collection {collection_name} exists. Checking schema...")
            existing_collection = Collection(name=collection_name)
            existing_schema = existing_collection.schema
            vector_field_exists = False
            correct_dimension = False
            for field in existing_schema.fields:
                if field.name == "vector":
                    vector_field_exists = True
                    if field.params.get('dim') == embedding_dim:
                        correct_dimension = True
                    else:
                        logging.warning(f"Existing collection '{collection_name}' vector field dimension ({field.params.get('dim')}) does not match expected dimension ({embedding_dim}).")
                    break
            
            if not vector_field_exists:
                logging.warning(f"Existing collection '{collection_name}' does not have a 'vector' field. Dropping collection.")
                existing_collection.drop()
                logging.info(f"Collection '{collection_name}' dropped.")
            elif not correct_dimension:
                logging.warning(f"Existing collection '{collection_name}' has incorrect vector dimension. Dropping collection.")
                existing_collection.drop()
                logging.info(f"Collection '{collection_name}' dropped.")
            else:
                logging.info(f"Existing collection '{collection_name}' has correct schema.")

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="hash", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="embedding_model", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="creation_date", dtype=DataType.INT64)
        ]
        schema = CollectionSchema(fields, description="Text Collection")
        logging.info(f"Using schema with fields: {[f.name for f in fields]}")

        # SIMPLIFIED COLLECTION HANDLING - No reload
        if utility.has_collection(collection_name):
            logging.info(f"Collection {collection_name} already exists - using it")
            collection = Collection(name=collection_name)
        else:
            logging.info(f"Collection {collection_name} does not exist - creating it")
            collection = Collection(name=collection_name, schema=schema)
            # Create index if collection is new
            if not collection.has_index():
                logging.info("Creating index on new collection...")
                index_params = {"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}}
                collection.create_index(field_name="vector", index_params=index_params)
                logging.info("Index created successfully")

        # ⚠️ IMPORTANT: Load collection ONLY ONCE at the beginning
        logging.info("Loading collection (once)...")
        collection.load()
        logging.info("Collection loaded successfully")

        # Get the entity count at the start
        try:
            initial_count = collection.num_entities
            logging.info(f"Initial entity count: {initial_count}")
        except Exception as e:
            logging.warning(f"Unable to get initial entity count: {e}")
            initial_count = 0

        results = []
        creation_date = int(datetime.now().timestamp())

        # Generate embeddings for all chunks at once instead of one by one
        if line_by_line:
            logging.info("Processing text line by line")
            chunks = [line for line in text.split('\n') if line.strip()]
        else:
            logging.info(f"Chunking text with size={chunk_size}, overlap={overlap}")
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]
        
        logging.info(f"Generated {len(chunks)} chunks")
        
        # Generate all hashes
        logging.info("Generating text hashes...")
        hashes = [sha256(chunk.encode()).hexdigest() for chunk in chunks]
        
        # Get embeddings for all chunks at once
        logging.info("Getting embeddings for all chunks...")
        vectors = embed_text_to_vector(chunks, embedding_model, is_local, ip_address=ip_address, embedding_host=embedding_host)
        logging.info(f"Got {len(vectors)} embeddings")
        
        # Validate all embeddings
        logging.info("Validating embeddings...")
        validated_vectors = validate_embeddings(vectors, embedding_dim)
        valid_count = sum(1 for v in validated_vectors if v is not None)
        logging.info(f"Validated embeddings: {valid_count} valid out of {len(validated_vectors)}")

        logging.info(f"Preparing {len(validated_vectors)} valid vectors for insertion.")
        if not validated_vectors:
            logging.warning("No valid vectors generated for insertion.")
            return {"message": "No valid vectors to insert", "details": []}

        # Ensure data structure matches schema field order: vector, text, hash, embedding_model, creation_date
        data = [
            validated_vectors, # vector
            chunks,             # text (original chunks)
            hashes,            # hash
            [embedding_model] * len(validated_vectors), # embedding_model
            [creation_date] * len(validated_vectors)    # creation_date
        ]
        logging.info(f"Inserting data into collection {collection_name}")
        
        try:
            mr = collection.insert(data)
            logging.info(f"Insertion result: {mr}")
            # Check IDs to confirm insertion
            inserted_ids = mr.primary_keys
            results.append(f"Inserted {len(inserted_ids)} entities.")
            logging.info(f"Successfully inserted {len(inserted_ids)} vectors for text batch.")

            # Flush data immediately after insert
            logging.info("Flushing inserted data...")
            collection.flush()
            logging.info("Data flushed successfully.")

        except Exception as e:
            logging.error(f"Error during Milvus insertion or flush: {str(e)}")
            logging.error(traceback.format_exc())
            # Return error details if insertion fails
            return {"error": "Milvus insertion failed", "details": str(e), "traceback": traceback.format_exc()}

    finally:
        try:
            connections.disconnect("default")
            logging.info("Disconnected from Milvus")
        except Exception as e:
            # Log if disconnection fails but don't raise further
            logging.warning(f"Failed to disconnect from Milvus: {str(e)}")
            
    return {"message": "Text loaded successfully", "details": results}
