# embed_index.py
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import pickle

def embed_index():
    # 1. Load the sentence‑transformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 2. Connect to MongoDB and fetch all movies
    client = MongoClient("mongodb://localhost:27017/")
    db = client.mini_netflix
    movies = list(db.movies.find(
        {}, 
        {"_id": 1, "title": 1, "overview": 1, "tagline": 1}
    ))

    # 3. Build corpus of cleaned texts to embed
    texts = []
    ids   = []
    for m in movies:
        # only keep actual non‑empty strings
        fields    = [m.get("title"), m.get("tagline"), m.get("overview")]
        str_parts = [f.strip() for f in fields if isinstance(f, str) and f.strip()]
        txt       = " ".join(str_parts)
        texts.append(txt)
        ids.append(m["_id"])

    # 4. Compute embeddings
    embeddings = model.encode(
        texts, 
        show_progress_bar=True, 
        convert_to_numpy=True
    )

    # 5. Build a FAISS index for cosine similarity
    d     = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    # 6. Persist the index and the ID mapping
    with open("movie_index_ids.pkl", "wb") as f:
        pickle.dump(ids, f)
    faiss.write_index(index, "movie_faiss.index")

    print("✅ Built and saved embeddings + FAISS index.")

if __name__ == "__main__":
    embed_index()

# import multiprocessing
# from pymongo import MongoClient
# from sentence_transformers import SentenceTransformer
# import faiss
# import pickle

# def embed_index():
#     # 1) Load the sentence-transformer model
#     model = SentenceTransformer("all-MiniLM-L6-v2")

#     # 2) Fetch all movies + tv shows from your mini_netflix DB
#     client = MongoClient("mongodb://localhost:27017/")
#     db     = client.mini_netflix

#     movies = list(db.movies.find(
#         {}, 
#         {"_id": 1, "title": 1, "overview": 1, "tagline": 1}
#     ))
#     shows  = list(db.tvshows.find(
#         {}, 
#         {"_id": 1, "name": 1, "overview": 1, "tagline": 1}
#     ))
#     client.close()

#     # 3) Build a corpus of texts + record (kind, _id) pairs
#     texts  = []
#     idx_map = []  # [(kind, ObjectId), ...]

#     for m in movies:
#         parts = [m.get("title"), m.get("tagline"), m.get("overview")]
#         txt   = " ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())
#         if txt:
#             texts.append(txt)
#             idx_map.append(("movie", m["_id"]))

#     for s in shows:
#         parts = [s.get("name"), s.get("tagline"), s.get("overview")]
#         txt   = " ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())
#         if txt:
#             texts.append(txt)
#             idx_map.append(("tvshow", s["_id"]))

#     # 4) Compute embeddings (no progress bar → no extra processes)
#     embeddings = model.encode(
#         texts,
#         show_progress_bar=False,
#         convert_to_numpy=True
#     )

#     # 5) Build a FAISS index for cosine similarity
#     d     = embeddings.shape[1]
#     index = faiss.IndexFlatIP(d)
#     faiss.normalize_L2(embeddings)
#     index.add(embeddings)

#     # 6) Persist both the FAISS index and the ID map
#     with open("combined_index_ids.pkl", "wb") as f:
#         pickle.dump(idx_map, f)

#     faiss.write_index(index, "combined_faiss.index")

#     print("✅ Built and saved combined movies+tvshows FAISS index + ID map.")

# if __name__ == "__main__":
#     # macOS multiprocessing fix
#     multiprocessing.set_start_method("fork")
#     embed_index()
