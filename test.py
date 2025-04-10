# test.py
import requests
import json
import argparse
import time
import statistics
from datetime import datetime
import random
import sys
import os

TEST_QUERIES = [
    "I want a drink of water",
    "Feeling thirsty and need hydration",
    "Looking for something to quench my thirst",
    "Water is essential for hydration",
    "Need to stay hydrated during exercise",
    "The importance of drinking water regularly",
    "Benefits of staying well hydrated",
    "Dehydration symptoms and prevention",
    "Water versus sports drinks for hydration",
    "Best practices for daily water intake"
]

TEST_TEXTS = [
    "I am thirsty and want a drink of water. Water is essential for human survival.",
    "Staying hydrated is important for overall health and wellbeing. Experts recommend drinking at least eight glasses of water daily.",
    "Water makes up about 60% of the human body and is necessary for many bodily functions including digestion and temperature regulation.",
    "Dehydration can cause headaches, fatigue, and difficulty concentrating. It's important to drink water regularly throughout the day.",
    "Many people don't drink enough water and may be chronically dehydrated without realizing it."
]

def measure_time(func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    return result, execution_time

def format_time(seconds):
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.2f} s"

def check_services(args):
    """Check that all required services are running and accessible"""
    print("=== CHECKING SERVICES ===")
    
    # Check API server
    api_url = f"http://{args.host}:{args.port}/vectorstore"
    try:
        response = requests.get(api_url, timeout=args.timeout)
        print(f"✓ API server: {args.host}:{args.port} - Status: {response.status_code}")
        print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ API server: {args.host}:{args.port} - Error: {str(e)}")
        return False
        
    # Check embedding server with timing
    embed_url = f"http://{args.host}:8000/embed"
    try:
        start_time = time.time()
        response = requests.post(
            embed_url, 
            json={"text": "test embedding service"}, 
            headers={"Content-Type": "application/json"},
            timeout=args.timeout
        )
        end_time = time.time()
        embed_time = end_time - start_time
        print(f"✓ Embedding server: {args.host}:8000 - Status: {response.status_code}")
        print(f"  Embedding time: {format_time(embed_time)}")
        if 'embedding' in response.json():
            print(f"  Valid embedding response received (length: {len(response.json()['embedding'])})")
        if response.status_code != 200:
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Embedding server: {args.host}:8000 - Error: {str(e)}")
        print("Note: The embedding server must be accessible from the API server.")
        return False
    
    # Check direct Milvus connection if possible
    print("\nTesting Milvus connection...")
    try:
        # Send a specialized test request to check Milvus connection
        test_payload = {
            "type": "milvus_check",
            "ip_address": "milvus"
        }
        
        response = requests.post(
            api_url, 
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_payload),
            timeout=args.timeout
        )
        
        print(f"Milvus check response: {response.text}")
        
    except Exception as e:
        print(f"Failed to test Milvus connection: {str(e)}")
    
    # Check Milvus connection via mini-load (more direct test)
    print("\nTesting minimal load operation...")
    try:
        mini_payload = {
            "type": "load",
            "text": "This is a very small test string for Milvus.",
            "collection": "milvus_test",
            "ip_address": "milvus",  # Use Docker internal hostname
            "debug": True
        }
        
        response = requests.post(
            api_url, 
            headers={"Content-Type": "application/json"},
            data=json.dumps(mini_payload),
            timeout=60  # Use 60s timeout for this specific test
        )
        
        result = response.json()
        if "error" in result:
            print(f"✗ Mini-load test failed: {result.get('error')}")
            if "details" in result:
                print(f"  Error details: {result.get('details')}")
            print("  This indicates a problem with the Milvus database or connection.")
            return False
        else:
            print(f"✓ Mini-load test succeeded: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"✗ Mini-load test failed with exception: {str(e)}")
        print("  This could indicate a timeout or connection issue with Milvus.")
        return False
    
    print("\nAll service checks completed.")
    return True

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test vectorstore API")
    parser.add_argument('--host', default='localhost', help='Server hostname or IP (default: localhost)')
    parser.add_argument('--port', default=5050, type=int, help='Server port (default: 5050)')
    parser.add_argument('--queries', type=int, default=5, help='Number of test queries to run (default: 5, max: 10)')
    parser.add_argument('--texts', type=int, default=3, help='Number of test texts to load (default: 3, max: 5)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--skip-clear', action='store_true', help='Skip clearing the collection (for benchmarking existing data)')
    parser.add_argument('--timeout', type=float, default=10.0, help='Timeout for requests in seconds (default: 10.0)')
    parser.add_argument('--check-only', action='store_true', help='Only check services and exit')
    parser.add_argument('--short-text', action='store_true', help='Use a very short text for testing (2-3 words)')
    parser.add_argument('--milvus-test', action='store_true', help='Run a specific Milvus test with debugging')
    parser.add_argument('--file-test', action='store_true', help='Test loading from a file rather than direct text')
    parser.add_argument('--test-file-path', help='Path to use for test file (defaults to ./test_data.txt)')
    args = parser.parse_args()
    
    # Special Milvus test mode
    if args.milvus_test:
        print("=== MILVUS CONNECTION TEST ===")
        api_url = f"http://{args.host}:{args.port}/vectorstore"
        headers = {'Content-Type': 'application/json'}
        
        # Use 'milvus' as the hostname when testing against the container
        milvus_hostname = "milvus"
        
        print("1. Testing Milvus connection...")
        try:
            payload = {
                "type": "milvus_check",
                "ip_address": milvus_hostname
            }
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=args.timeout
            )
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("\n2. Testing minimal insertion...")
        try:
            payload = {
                "type": "load",
                "text": "Test text for Milvus.",
                "collection": "milvus_test",
                "ip_address": milvus_hostname,
                "debug": True
            }
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=args.timeout
            )
            print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("\n3. Testing search...")
        try:
            payload = {
                "type": "search",
                "query": "Test search",
                "collection": "milvus_test",
                "ip_address": milvus_hostname,
                "debug": True
            }
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=args.timeout
            )
            print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        sys.exit(0)
    
    # Check if services are available
    if not check_services(args):
        print("\nService check failed. Please ensure all services are running.")
        if not args.check_only:
            user_input = input("Services check failed. Continue anyway? (y/N): ").strip().lower()
            if user_input != 'y':
                sys.exit(1)
    
    if args.check_only:
        sys.exit(0)
    
    # Limit the number of queries and texts
    num_queries = min(args.queries, len(TEST_QUERIES))
    num_texts = min(args.texts, len(TEST_TEXTS))
    
    # Use very short texts if requested (for testing Milvus quickly)
    test_texts = TEST_TEXTS
    if args.short_text:
        print("Using short test texts")
        test_texts = [
            "Test text one.",
            "Test text two.",
            "Test text three.",
            "Test text four.",
            "Test text five."
        ]
    
    base_url = f'http://{args.host}:{args.port}/vectorstore'
    headers = {'Content-Type': 'application/json'}
    
    total_start_time = time.time()
    print(f"\nStarting comprehensive vectorstore test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server: {args.host}:{args.port}")
    print(f"Testing with {num_texts} texts and {num_queries} queries\n")

    # Dictionary to store all timing results
    timing_results = {
        'clear': [],
        'load': [],
        'load_file': [],
        'search': []
    }

    test_file_path = None
    if args.file_test:
        # Create a test file
        test_file_path = args.test_file_path or os.path.join(os.getcwd(), "test_data.txt")
        print(f"Creating test file at {test_file_path}")
        try:
            with open(test_file_path, "w") as f:
                f.write("\n\n".join(test_texts[:num_texts]))
            print(f"Created test file with {num_texts} text entries")
        except Exception as e:
            print(f"Error creating test file: {e}")
            sys.exit(1)

    # Add a helper variable for the Milvus hostname within Docker
    milvus_hostname = "milvus"

    # Clear the collection (unless skipped)
    if not args.skip_clear:
        print("=== CLEARING COLLECTION ===")
        clear_payload = {
            "type": "clear",
            "collection": "test",
            "ip_address": milvus_hostname  # Added ip_address
        }
        
        # Ensure we pass ip_address to the clear endpoint if needed
        # Adjusting the measure_time call might be needed if clear_payload
        # needs to be modified based on the endpoint's expectation
        response, execution_time = measure_time(
            requests.post, 
            base_url, 
            headers=headers, 
            data=json.dumps(clear_payload),
            timeout=args.timeout
        )
        
        timing_results['clear'].append(execution_time)
        
        try:
            result = response.json()
            print(f"Clear operation completed in {format_time(execution_time)}")
            print(f"Response: {json.dumps(result, indent=2)}\n")
        except requests.exceptions.JSONDecodeError:
            print(f"Error: Could not decode JSON response. Status code: {response.status_code}")
            print(f"Response content: {response.text}\n")

    # Load data into the collection (via text)
    if not args.file_test:
        print("=== LOADING TEST DATA (TEXT) ===")
        load_times = []
        
        for i in range(num_texts):
            text = test_texts[i]
            if args.verbose:
                print(f"\nLoading text {i+1}/{num_texts}: {text[:50]}...")
            else:
                print(f"Loading text {i+1}/{num_texts}...")
            
            load_payload = {
                "type": "load",
                "text": text,
                "collection": "test",
                "ip_address": milvus_hostname
            }
            
            response, execution_time = measure_time(
                requests.post, 
                base_url, 
                headers=headers, 
                data=json.dumps(load_payload),
                timeout=args.timeout
            )
            
            timing_results['load'].append(execution_time)
            load_times.append(execution_time)
            
            try:
                result = response.json()
                if args.verbose:
                    print(f"Load operation completed in {format_time(execution_time)}")
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"  Completed in {format_time(execution_time)}")
            except requests.exceptions.JSONDecodeError:
                print(f"Error: Could not decode JSON response. Status code: {response.status_code}")
                print(f"Response content: {response.text}")
        
        print("\nLoad statistics:")
        if load_times:
            print(f"  Average load time: {format_time(statistics.mean(load_times))}")
            print(f"  Minimum load time: {format_time(min(load_times))}")
            print(f"  Maximum load time: {format_time(max(load_times))}")
            if len(load_times) > 1:
                print(f"  Standard deviation: {format_time(statistics.stdev(load_times))}")
        else:
            print("  No load operations performed")
        print()
    
    # Load data from file
    if args.file_test and test_file_path:
        print("=== LOADING TEST DATA (FILE) ===")
        
        load_payload = {
            "type": "load",
            "path": test_file_path,
            "collection": "test",
            "ip_address": milvus_hostname,
            "local": True,
            "recursive": False,
            "line_by_line": False
        }
        
        response, execution_time = measure_time(
            requests.post, 
            base_url, 
            headers=headers, 
            data=json.dumps(load_payload),
            timeout=args.timeout
        )
        
        timing_results['load_file'].append(execution_time)
        
        try:
            result = response.json()
            print(f"File load operation completed in {format_time(execution_time)}")
            print(f"Response: {json.dumps(result, indent=2)}")
        except requests.exceptions.JSONDecodeError:
            print(f"Error: Could not decode JSON response. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
            
        print(f"\nFile load time: {format_time(execution_time)}")
        print()

    # Perform searches
    print("=== RUNNING TEST QUERIES ===")
    search_times = []
    
    for i in range(num_queries):
        query = TEST_QUERIES[i]
        if args.verbose:
            print(f"\nQuery {i+1}/{num_queries}: \"{query}\"")
        else:
            print(f"Query {i+1}/{num_queries}: \"{query}\"")
        
        search_payload = {
            "type": "search",
            "query": query,
            "collection": "test",
            "ip_address": milvus_hostname,
            "limit": 5
        }
        
        response, execution_time = measure_time(
            requests.post, 
            base_url, 
            headers=headers, 
            data=json.dumps(search_payload),
            timeout=args.timeout
        )
        
        timing_results['search'].append(execution_time)
        search_times.append(execution_time)
        
        try:
            result = response.json()
            num_results = len(result.get('results', []))
            if args.verbose:
                print(f"Search completed in {format_time(execution_time)}")
                print(f"Found {num_results} results:")
                for j, r in enumerate(result.get('results', [])[:3]):  # Show top 3 results in verbose mode
                    print(f"  {j+1}. Distance: {r.get('distance', 'N/A'):.4f}")
                    text = r.get('text', 'N/A')
                    print(f"     Text: {text[:100]}..." if len(text) > 100 else f"     Text: {text}")
                if num_results > 3:
                    print(f"  ... and {num_results - 3} more results")
            else:
                print(f"  Found {num_results} results in {format_time(execution_time)}")
        except requests.exceptions.JSONDecodeError:
            print(f"Error: Could not decode JSON response. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
    
    print("\nSearch statistics:")
    if search_times:
        print(f"  Average search time: {format_time(statistics.mean(search_times))}")
        print(f"  Minimum search time: {format_time(min(search_times))}")
        print(f"  Maximum search time: {format_time(max(search_times))}")
        if len(search_times) > 1:
            print(f"  Standard deviation: {format_time(statistics.stdev(search_times))}")
    else:
        print("  No search operations performed")
    
    # Test a more complex query with filters
    if not args.skip_clear and num_texts > 1:
        print("\n=== TESTING UNIQUE RESULT FILTERING ===")
        search_payload = {
            "type": "search",
            "query": "water hydration",
            "collection": "test",
            "ip_address": milvus_hostname,
            "limit": 10,
            "unique": True
        }
        
        response, execution_time = measure_time(
            requests.post, 
            base_url, 
            headers=headers, 
            data=json.dumps(search_payload),
            timeout=args.timeout
        )
        
        timing_results['search'].append(execution_time)
        
        try:
            result = response.json()
            num_results = len(result.get('results', []))
            print(f"Unique filtered search completed in {format_time(execution_time)}")
            print(f"Found {num_results} unique results")
            if args.verbose and num_results > 0:
                for j, r in enumerate(result.get('results', [])[:3]):
                    print(f"  {j+1}. Distance: {r.get('distance', 'N/A'):.4f}")
                    text = r.get('text', 'N/A')
                    print(f"     Text: {text[:100]}..." if len(text) > 100 else f"     Text: {text}")
        except requests.exceptions.JSONDecodeError:
            print(f"Error: Could not decode JSON response. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
    
    # Clean up test file if created
    if args.file_test and test_file_path and os.path.exists(test_file_path):
        try:
            os.remove(test_file_path)
            print(f"\nTest file {test_file_path} removed.")
        except Exception as e:
            print(f"\nWarning: Could not remove test file {test_file_path}: {e}")
    
    # Overall performance summary
    total_time = time.time() - total_start_time
    print("\n=== PERFORMANCE SUMMARY ===")
    print(f"Total test execution time: {format_time(total_time)}")
    
    if timing_results['clear']:
        print(f"Clear operation: {format_time(statistics.mean(timing_results['clear']))}")
    
    if timing_results['load']:
        print(f"Load operations (text) (avg of {len(timing_results['load'])}): {format_time(statistics.mean(timing_results['load']))}")
    
    if timing_results['load_file']:
        print(f"Load operation (file): {format_time(statistics.mean(timing_results['load_file']))}")
    
    if timing_results['search']:
        print(f"Search operations (avg of {len(timing_results['search'])}): {format_time(statistics.mean(timing_results['search']))}")
    
    # Test completion
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
