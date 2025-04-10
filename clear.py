# clear.py
import requests
import json
import argparse

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Clear a specific collection in vectorstore.")
    parser.add_argument('--collection', required=True, help='The name of the collection to clear')
    args = parser.parse_args()

    base_url = 'http://127.0.0.1:5000/vectorstore'
    headers = {'Content-Type': 'application/json'}

    # Clear the specified collection
    print(f"About to clear the collection '{args.collection}'...\n")
    clear_payload = {
        "type": "clear",
        "collection": args.collection
    }
    response = requests.post(base_url, headers=headers, data=json.dumps(clear_payload))
    
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Failed to clear the collection. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    main()
