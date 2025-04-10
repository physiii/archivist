# main.py
from flask import Flask, request, jsonify
from load import load_to_vectorstore, load_text_to_vectorstore, clear_vectorstore_collection
from search import search_vectorstore
import argparse
import logging
import traceback
from pymilvus import connections, utility
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Get service host values from environment variables
MILVUS_HOST = os.environ.get('MILVUS_HOST', 'localhost')
EMBEDDING_HOST = os.environ.get('EMBEDDING_HOST', 'localhost')

@app.route('/vectorstore', methods=['GET', 'POST'])
def handle_vectorstore_request():
    if request.method == 'GET':
        return jsonify({"message": "Vectorstore is running. Use POST for operations."}), 200

    data = request.json
    operation_type = data.get('type')

    logging.info(f"Received request: {data}")

    # Special diagnostic endpoint for Milvus health check
    if operation_type == 'milvus_check':
        ip_address = data.get('ip_address', MILVUS_HOST)
        try:
            # Try connecting to Milvus directly
            connections.connect("default", host=ip_address, port='19530')
            status = connections.get_connection_addr("default")
            is_connected = connections.has_connection("default")
            
            # Get list of collections to verify Milvus is operational
            collections = []
            if is_connected:
                collections = utility.list_collections()
            
            result = {
                "status": "connected" if is_connected else "error",
                "connection_details": status,
                "collections": collections
            }
            
            connections.disconnect("default")
            return jsonify(result)
        except Exception as e:
            logging.error(f"Milvus connection check failed: {str(e)}")
            logging.error(traceback.format_exc())
            return jsonify({
                "status": "error", 
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    if operation_type == 'load':
        if 'text' in data:
            text = data.get('text')
            collection_name = data.get('collection')
            embedding_model = data.get('model')
            # Use environment variable for IP address if not provided
            ip_address = data.get('ip_address', MILVUS_HOST)
            # Use environment variable for embedding host
            embedding_host = data.get('embedding_host', EMBEDDING_HOST)
            line_by_line = data.get('line_by_line', False)
            chunk_size = data.get('chunk_size', 1000)
            overlap = data.get('overlap', 0)
            debug = data.get('debug', False)

            try:
                result = load_text_to_vectorstore(
                    text,
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                    ip_address=ip_address,
                    embedding_host=embedding_host,
                    line_by_line=line_by_line,
                    chunk_size=chunk_size,
                    overlap=overlap
                )
                
                # For debug requests, add detailed diagnostics
                if debug:
                    # Try to fetch the collection info to verify it worked
                    connections.connect("default", host=ip_address, port='19530')
                    collection_name_formatted = f"documents_{collection_name}" if collection_name else "documents_local_model"
                    collection_exists = utility.has_collection(collection_name_formatted)
                    entity_count = 0
                    
                    if collection_exists:
                        from pymilvus import Collection
                        collection = Collection(collection_name_formatted)
                        entity_count = collection.num_entities
                    
                    debug_info = {
                        "collection_exists": collection_exists,
                        "entity_count": entity_count,
                        "collection_name": collection_name_formatted
                    }
                    connections.disconnect("default")
                    return jsonify({"message": "Text loaded successfully", "details": result, "debug": debug_info})
                
                return jsonify({"message": "Text loaded successfully", "details": result})
            except Exception as e:
                logging.error(f"Load operation failed: {str(e)}")
                logging.error(traceback.format_exc())
                return jsonify({
                    "error": "An unexpected error occurred", 
                    "details": str(e),
                    "traceback": traceback.format_exc() if debug else None
                }), 500
        elif 'path' in data:
            args = argparse.Namespace(**data)
            
            # Set default IP address to environment variable if not provided
            if not hasattr(args, 'ip_address') or not args.ip_address:
                args.ip_address = MILVUS_HOST
            
            # Set default embedding host to environment variable if not provided
            if not hasattr(args, 'embedding_host') or not args.embedding_host:
                args.embedding_host = EMBEDDING_HOST
                
            load_to_vectorstore(args)
            return jsonify({"message": "Documents loaded successfully"})
        else:
            return jsonify({"error": "No text or path provided for loading"}), 400

    elif operation_type == 'search':
        query = data.get('query')
        if not query:
            return jsonify({"error": "No query provided for searching"}), 400

        # Extract additional search parameters
        limit = data.get('limit', 10)
        path_filter = data.get('path', "")
        unique = data.get('unique', False)
        collection_name = data.get('collection')
        ip_address = data.get('ip_address', MILVUS_HOST)
        embedding_host = data.get('embedding_host', EMBEDDING_HOST)

        try:
            results = search_vectorstore(
                query,
                limit=limit,
                path_filter=path_filter,
                unique=unique,
                collection_name=collection_name,
                ip_address=ip_address,
                embedding_host=embedding_host
            )
            return jsonify({"results": results})
        except Exception as e:
            logging.error(f"Search operation failed: {str(e)}")
            logging.error(traceback.format_exc())
            return jsonify({
                "error": "An unexpected error occurred",
                "details": str(e),
                "traceback": traceback.format_exc() if data.get('debug', False) else None
            }), 500

    elif operation_type == 'clear':
        collection_name = data.get('collection')
        if not collection_name:
            return jsonify({"error": "No collection name provided for clearing"}), 400

        try:
            clear_vectorstore_collection(collection_name, ip_address=data.get('ip_address', MILVUS_HOST))
            return jsonify({"message": f"Collection '{collection_name}' cleared successfully"})
        except Exception as e:
            logging.error(f"Clear operation failed: {str(e)}")
            logging.error(traceback.format_exc())
            return jsonify({
                "error": "An unexpected error occurred during clear operation",
                "details": str(e),
                "traceback": traceback.format_exc() if data.get('debug', False) else None
            }), 500

    else:
        return jsonify({"error": "Invalid operation type"}), 400

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    app.logger.error(f"Unhandled exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    # Return JSON instead of HTML for HTTP errors
    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
