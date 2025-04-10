import os
import logging
from pymilvus import connections, Collection, utility
import subprocess

logging.basicConfig(level=logging.DEBUG)
print('Testing direct Milvus connection...')
try:
    connections.connect('default', host='192.168.1.40', port='19530')
    print(f'Connected: {connections.has_connection("default")}')
    print(f'Collections: {utility.list_collections()}')
    
    # Try loading a collection that exists
    coll_name = 'documents_test'
    if utility.has_collection(coll_name):
        print(f'Loading collection {coll_name}')
        coll = Collection(coll_name)
        coll.load()
        print(f'Collection entities: {coll.num_entities}')
        
        # Try a minimal query
        expr = 'id > 0'
        res = coll.query(expr, limit=1, output_fields=['hash'])
        print(f'Query result: {res}')
    
    # Check memory usage of Milvus
    try:
        cmd = "docker stats --no-stream milvus-standalone"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        print(f'Milvus resource usage:\n{result}')
    except Exception as e:
        print(f'Error checking Milvus stats: {e}')
        
except Exception as e:
    print(f'Error: {str(e)}') 