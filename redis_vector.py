import redis
import numpy as np

from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query


# ============================================================
# 1. CONNECT TO REDIS
# ============================================================

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=False,
    protocol=2
)

print("Connecting to Redis...")

try:
    r.ping()
    print("Redis connection successful!")
except Exception as e:
    print("Could not connect to Redis.")
    print(e)
    exit()


# ============================================================
# 2. CHECK REDIS SEARCH
# ============================================================

try:
    r.execute_command("FT._LIST")
    print("Redis Search is available!")

except redis.exceptions.ResponseError:
    print("\nERROR: Redis Search is not available.")
    print("Make sure Redis Stack is running on port 6379.")
    exit()


# ============================================================
# 3. DELETE OLD INDEX IF IT EXISTS
# ============================================================

try:
    r.ft("vector_idx").dropindex(True)
    print("Old index deleted.")

except redis.exceptions.ResponseError:
    print("No old index found.")


# ============================================================
# 4. CREATE VECTOR INDEX
# ============================================================

schema = (
    TextField("text"),

    VectorField(
        "embedding",
        "FLAT",
        {
            "TYPE": "FLOAT32",
            "DIM": 4,
            "DISTANCE_METRIC": "COSINE"
        }
    )
)

try:
    r.ft("vector_idx").create_index(
        schema,
        definition=IndexDefinition(
            prefix=["doc:"],
            index_type=IndexType.HASH
        )
    )

    print("Vector index created successfully!")

except Exception as e:
    print("Failed to create vector index:")
    print(e)
    exit()


# ============================================================
# 5. DOCUMENTS + DEMO EMBEDDINGS
# ============================================================

documents = {
    "doc:1": {
        "text": "I love programming in Python",
        "embedding": [0.90, 0.80, 0.10, 0.20]
    },

    "doc:2": {
        "text": "Python is used for machine learning",
        "embedding": [0.85, 0.75, 0.20, 0.30]
    },

    "doc:3": {
        "text": "I like playing football",
        "embedding": [0.10, 0.20, 0.90, 0.80]
    },

    "doc:4": {
        "text": "Football is my favorite sport",
        "embedding": [0.15, 0.25, 0.85, 0.75]
    }
}


# ============================================================
# 6. STORE DOCUMENTS
# ============================================================

for doc_id, data in documents.items():

    vector = np.array(
        data["embedding"],
        dtype=np.float32
    ).tobytes()

    r.hset(
        doc_id,
        mapping={
            "text": data["text"],
            "embedding": vector
        }
    )

print("Documents stored successfully!")


# ============================================================
# 7. QUERY VECTOR
# ============================================================

query_vector = np.array(
    [0.88, 0.78, 0.15, 0.25],
    dtype=np.float32
).tobytes()


# ============================================================
# 8. KNN QUERY
# ============================================================

query = (
    Query(
        "*=>[KNN 2 @embedding $vec AS score]"
    )
    .return_field("text")
    .return_field("score")
    .sort_by("score")
    .dialect(2)
)


# ============================================================
# 9. SEARCH
# ============================================================

try:

    results = r.ft("vector_idx").search(
        query,
        query_params={
            "vec": query_vector
        }
    )

except Exception as e:
    print("\nVector search failed:")
    print(e)
    exit()


# ============================================================
# 10. DISPLAY RESULTS
# ============================================================

print("\n==============================")
print("VECTOR SEARCH RESULTS")
print("==============================")

print("Total results:", results.total)

for doc in results.docs:

    print("\nText:", doc.text)
    print("Distance:", doc.score)


print("\nProgram completed successfully!")