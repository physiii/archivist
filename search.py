# search.py
import os
import sys
import logging
from datetime import datetime
from pymilvus import connections, Collection, utility, AnnSearchRequest, WeightedRanker, RRFRanker
import traceback
from uuid import uuid4

from utils import (
    DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, LOCAL_EMBEDDING_MODEL, LOCAL_EMBEDDING_DIM,
    embed_text_to_vector, validate_embeddings
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Constants Configuration
BATCH_SIZE = 10
NPROBE = 16
MAX_QUERY_LIMIT = 16384

def search_vectorstore(
    query,
    limit=10,
    path_filter="",
    unique=False,
    collection_name=None,
    ip_address="localhost",
    embedding_host="localhost",
    embedding_port=None,
    mode="dense",
    metric_type=None,
    nprobe=None,
    hybrid_fusion=None,
    hybrid_dense_weight=None,
    hybrid_sparse_weight=None,
    hybrid_rrf_k=None,
):
    start_time = datetime.now()
    logging.info(f"Starting search_vectorstore: query='{query}', collection={collection_name}, ip={ip_address}, mode={mode}")
    alias = f"search_{uuid4().hex}"
    
    try:
        logging.info(f"Connecting to Milvus at {ip_address}...")
        connections.connect(alias, host=ip_address, port='19530')
        logging.info("Connected to Milvus successfully")

        # Format collection name
        if collection_name:
            collection_name = f"documents_{collection_name}"
        else:
            collection_name = f"documents_{DEFAULT_EMBEDDING_MODEL.replace('-', '_')}"
        logging.info(f"Using collection: {collection_name}")

        # Check if collection exists
        if not utility.has_collection(collection_name, using=alias):
            logging.error(f"Collection {collection_name} does not exist.")
            return []

        # Open the collection
        collection = Collection(name=collection_name, using=alias)
        collection.load()
        logging.info(f"Collection loaded with {collection.num_entities} entities")

        # Determine search mode and required data format.
        mode_norm = str(mode or "dense").strip().lower()
        field_names = {f.name for f in collection.schema.fields}
        use_bm25 = mode_norm in {"bm25", "sparse"} and ("sparse" in field_names)
        use_hybrid = mode_norm in {"hybrid"} and ("sparse" in field_names) and ("vector" in field_names)

        # Build output_fields: path exists only in file-loaded schema, not text-loaded
        output_fields = ["text", "hash", "embedding_model", "creation_date"]
        if "path" in field_names:
            output_fields.append("path")

        # Build filter expression (used by hybrid and dense/bm25)
        expr = None
        if path_filter:
            expr = f'path == "{path_filter}"'
            logging.info(f"Using filter expression: {expr}")

        effective_metric_type = str(metric_type or os.environ.get("VECTORSTORE_METRIC_TYPE", "L2")).strip().upper()
        effective_nprobe = int(nprobe if nprobe is not None else os.environ.get("VECTORSTORE_NPROBE", NPROBE))

        if use_hybrid:
            logging.info("Using HYBRID search (dense + BM25 sparse).")

            # Dense vector query via local embedding server
            model = LOCAL_EMBEDDING_MODEL
            dim = LOCAL_EMBEDDING_DIM
            query_vectors = embed_text_to_vector(
                [query],
                model,
                is_local=True,
                ip_address=ip_address,
                embedding_host=embedding_host,
                embedding_port=embedding_port,
            )
            validated_query_vectors = validate_embeddings(query_vectors, dim)
            if not validated_query_vectors or validated_query_vectors[0] is None:
                logging.error("Failed to generate valid query vector (hybrid).")
                return []

            dense_req = AnnSearchRequest(
                data=[validated_query_vectors[0]],
                anns_field="vector",
                param={"metric_type": effective_metric_type, "params": {"nprobe": effective_nprobe}},
                limit=min(max(limit, 10) * 4, MAX_QUERY_LIMIT),
                expr=expr,
            )
            sparse_req = AnnSearchRequest(
                data=[str(query)],
                anns_field="sparse",
                param={"metric_type": "BM25", "params": {}},
                limit=min(max(limit, 10) * 4, MAX_QUERY_LIMIT),
                expr=expr,
            )

            # Default: weighted fusion (tunable via env)
            dense_w = (
                float(hybrid_dense_weight)
                if hybrid_dense_weight is not None
                else float(os.environ.get("VECTORSTORE_HYBRID_DENSE_WEIGHT", "0.65"))
            )
            sparse_w = (
                float(hybrid_sparse_weight)
                if hybrid_sparse_weight is not None
                else float(os.environ.get("VECTORSTORE_HYBRID_SPARSE_WEIGHT", "0.35"))
            )
            fusion = str(hybrid_fusion or os.environ.get("VECTORSTORE_HYBRID_FUSION", "weighted")).strip().lower()
            if fusion == "rrf":
                k = int(hybrid_rrf_k if hybrid_rrf_k is not None else os.environ.get("VECTORSTORE_HYBRID_RRF_K", "60"))
                rerank = RRFRanker(k=k)
            else:
                rerank = WeightedRanker(dense_w, sparse_w)

            out = []
            results = collection.hybrid_search(
                reqs=[dense_req, sparse_req],
                rerank=rerank,
                limit=min(limit, MAX_QUERY_LIMIT),
                output_fields=output_fields,
            )
            # hybrid_search returns a list of Hits for each query vector; we have exactly one query.
            for hit in (results[0] if results else []):
                out.append({
                    "id": hit.id,
                    "text": hit.get('text') or '',
                    "hash": hit.get('hash') or '',
                    "embedding_model": hit.get('embedding_model') or '',
                    "distance": hit.distance,
                    "creation_date": datetime.fromtimestamp(int(hit.get('creation_date') or 0)).isoformat(),
                    "path": hit.get('path') or '',
                })

            # Handle unique results if requested
            if unique and out:
                seen_hashes = set()
                unique_results = []
                for result in out:
                    if result['hash'] not in seen_hashes:
                        seen_hashes.add(result['hash'])
                        unique_results.append(result)
                out = unique_results

            return out

        if use_bm25:
            logging.info("Using BM25 sparse search.")
            search_data = [str(query)]
            anns_field = "sparse"
            search_param = {"metric_type": "BM25", "params": {}}
        else:
            # Dense vector search (local embeddings server)
            model = LOCAL_EMBEDDING_MODEL
            dim = LOCAL_EMBEDDING_DIM
            logging.info(f"Using embedding model: {model}")

            # Get embedding for the query
            logging.info("Generating embedding for query...")
            query_vectors = embed_text_to_vector(
                [query],
                model,
                is_local=True,
                ip_address=ip_address,
                embedding_host=embedding_host,
                embedding_port=embedding_port,
            )
            logging.info("Embedding generated successfully")
            
            # Validate embedding
            logging.info("Validating query embedding...")
            validated_query_vectors = validate_embeddings(query_vectors, dim)
            if not validated_query_vectors or validated_query_vectors[0] is None:
                logging.error("Failed to generate valid query vector.")
                return []
            logging.info("Query embedding validated successfully")

            search_data = [validated_query_vectors[0]]
            anns_field = "vector"
            search_param = {"metric_type": effective_metric_type, "params": {"nprobe": effective_nprobe}}

        # Perform search
        logging.info(f"Searching with limit={limit}...")
        search_params = {
            "data": search_data,
            "anns_field": anns_field,
            "param": search_param,
            "limit": min(limit, MAX_QUERY_LIMIT),
            "output_fields": output_fields,
            "expr": expr
        }

        search_start = datetime.now()
        search_results = collection.search(**search_params)
        search_time = datetime.now() - search_start
        logging.info(f"Search completed in {search_time.total_seconds():.2f}s")
        logging.info(f"Number of results returned: {len(search_results)}")

        # Process results
        results = []
        for hits in search_results:
            for hit in hits:
                results.append({
                    "id": hit.id,
                    "text": hit.get('text') or '',
                    "hash": hit.get('hash') or '',
                    "embedding_model": hit.get('embedding_model') or '',
                    "distance": hit.distance,
                    "creation_date": datetime.fromtimestamp(int(hit.get('creation_date') or 0)).isoformat(),
                    "path": hit.get('path') or '',
                })

        # Handle unique results if requested
        if unique and results:
            logging.info(f"Filtering for unique results. Before: {len(results)}")
            seen_hashes = set()
            unique_results = []
            for result in results:
                if result['hash'] not in seen_hashes:
                    seen_hashes.add(result['hash'])
                    unique_results.append(result)
            results = unique_results
            logging.info(f"After unique filtering: {len(results)}")

        return results
    except Exception as e:
        logging.error(f"An error occurred during search: {str(e)}")
        logging.error(traceback.format_exc())
        return []
    finally:
        try:
            connections.disconnect(alias)
            logging.info("Disconnected from Milvus")
        except:
            pass
        end_time = datetime.now()
        logging.info(f"Search operation completed in {end_time - start_time}.")

if __name__ == "__main__":
    # Example usage: python search.py "your query" [collection_name]
    query = sys.argv[1] if len(sys.argv) > 1 else "I want a drink"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else "amygdala"
    results = search_vectorstore(query, limit=5, collection_name=collection_name)

    if results:
        print(f"Found {len(results)} results:")
        for result in results:
            print(f"Text: {result['text']}")
            print(f"Distance: {result['distance']}")
            if result.get('path'):
                print(f"Path: {result['path']}")
            print(f"Embedding Model: {result['embedding_model']}")
            print(f"Creation Date: {result['creation_date']}")
            print("---")
    else:
        print("No results found.")
