from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    Collection,
    DataType,
    utility
)
import numpy as np

# Connect to Milvus on the default port 19530
connections.connect(host="127.0.0.1", port="19530")
print("Connected to Milvus!")

# Define the dimension of your embeddings (adjust as needed)
embedding_dim = 768  # Change this if your embeddings have a different dimension

# Define the schema for the collection
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=512)
]
schema = CollectionSchema(fields, description="Test collection for Milvus")
collection_name = "test_collection"

# If the collection already exists, drop it first
if utility.has_collection(collection_name):
    utility.drop_collection(collection_name)

# Create the collection
collection = Collection(name=collection_name, schema=schema)
print(f"Created collection: {collection.name}")

# Prepare a sample document
# For testing purposes, we'll generate a random vector. In your real use case, use your actual embedding.
embedding = np.random.random((1, embedding_dim)).tolist()  
text = ["I am thirsty and want a drink of water"]

# Insert the document
data = [embedding, text]  # data is a list of columns corresponding to the non-auto fields
insert_result = collection.insert(data)
print("Insert result:", insert_result)

# Flush to ensure data is written
print("About to flush...")
collection.flush()
print("Flush completed.")

# Create an index on the vector field (optional but recommended for efficient search)
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128},
}
collection.create_index(field_name="embedding", index_params=index_params)
print("Index created.")

# Perform a search using the same embedding as a query
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
results = collection.search(
    data=embedding, 
    anns_field="embedding", 
    param=search_params, 
    limit=1, 
    output_fields=["text"]
)
print("Search results:")
for hits in results:
    for hit in hits:
        print(hit)
