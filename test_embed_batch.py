import argparse
import time

from utils import (
    embed_text_to_vector,
    validate_embeddings,
    LOCAL_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_DIM,
)


def main():
    parser = argparse.ArgumentParser(
        description="Smoke-test the batched embedding client against the /embed_batch endpoint."
    )
    parser.add_argument(
        "--embedding-host",
        default="localhost",
        help="Hostname of the embedding service (default: localhost)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of test texts to embed (default: 50)",
    )
    args = parser.parse_args()

    texts = [f"Test sentence number {i}, used to verify batched embeddings." for i in range(args.count)]

    print(f"Testing batched embeddings against http://{args.embedding_host}:8000/embed_batch")
    print(f"- Model: {LOCAL_EMBEDDING_MODEL}")
    print(f"- Expected embedding dim: {LOCAL_EMBEDDING_DIM}")
    print(f"- Text count: {len(texts)}")

    start = time.time()
    vectors = embed_text_to_vector(
        texts,
        model=LOCAL_EMBEDDING_MODEL,
        is_local=True,
        embedding_host=args.embedding_host,
    )
    elapsed = time.time() - start

    print(f"\nCall completed in {elapsed:.3f}s")
    print(f"Returned {len(vectors)} embeddings (including any None entries)")

    valid_vectors = validate_embeddings(vectors, LOCAL_EMBEDDING_DIM)
    valid_count = sum(1 for v in valid_vectors if v is not None)

    print(f"Valid embeddings with correct dimension: {valid_count}/{len(texts)}")

    if len(vectors) != len(texts):
        print("❌ Mismatch between number of input texts and returned embeddings.")
        raise SystemExit(1)

    if valid_count != len(texts):
        print("⚠️ Some embeddings were invalid or missing. Check the embed server logs.")
        raise SystemExit(1)

    print("✅ Batched embedding client appears to be working correctly.")


if __name__ == "__main__":
    main()


