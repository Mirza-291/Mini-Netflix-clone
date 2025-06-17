# semantic_search.py
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import faiss, pickle
import numpy as np
import os

# Load fan‑out text search pipeline
def text_search(db, phrase, top_k=100):
    pipeline = [
        {"$match": {"$text": {"$search": phrase}}},
        {"$project": {
            "score": {"$meta":"textScore"},
            "title":1,"overview":1
        }},
        {"$sort": {"score": -1}},
        {"$limit": top_k}
    ]
    return list(db.movies.aggregate(pipeline))

# Load FAISS index + IDs + model
# resolve the directory this file lives in:
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# build full paths to your FAISS assets:
MOVIE_IDS_PATH   = os.path.join(APP_DIR, "movie_index_ids.pkl")
MOVIE_INDEX_PATH = os.path.join(APP_DIR, "movie_faiss.index")

# now load them by absolute path:
with open(MOVIE_IDS_PATH, "rb") as f:
    all_ids = pickle.load(f)

index = faiss.read_index(MOVIE_INDEX_PATH)
#index = faiss.read_index("movie_faiss.index")
model = SentenceTransformer("all-MiniLM-L6-v2")

def semantic_re_rank(candidates, phrase, top_n=10):
    # Prepare candidate embeddings matrix
    idx_map = {mid:i for i,mid in enumerate(all_ids)}
    cand_idxs = [ idx_map[m["_id"]] for m in candidates if m["_id"] in idx_map ]
    cand_embs = index.reconstruct_n(0, index.ntotal)[cand_idxs]  # raw embeddings
    # Actually better to have stored embeddings separately; for demo only

    # Embed the query
    q_emb = model.encode([phrase], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)

    # Compute cosine sims
    sims = (cand_embs @ q_emb.T).squeeze()  # shape (len(cand),)
    
    # Attach and sort
    for m, sim in zip(candidates, sims):
        m["semanticScore"] = float(sim)
    return sorted(candidates, key=lambda m: m["semanticScore"], reverse=True)[:top_n]

if __name__ == "__main__":
    client = MongoClient()
    db = client.mini_netflix

    phrase = input("Enter story/mood/title phrase: ").strip()

    # Stage 1: keyword‐based retrieval
    hits = text_search(db, phrase, top_k=100)

    # Stage 2: semantic re‑ranking
    reranked = semantic_re_rank(hits, phrase, top_n=10)

    # Show results
    for i, m in enumerate(reranked, 1):
        print(f"\n{i}. {m['title']}  (semanticScore={m['semanticScore']:.3f})")
        print("   Overview:", (m["overview"] or "")[:150].replace("\n"," "), "…")

    client.close()






# # semantic_search.py
# import os
# import pickle

# from pymongo import MongoClient
# from sentence_transformers import SentenceTransformer
# import faiss
# import numpy as np

# # ——————————————————————————————
# # 1) fan-out text search across movies + tvshows
# # ——————————————————————————————
# def text_search(db, phrase, top_k=100):
#     # pipeline for movies
#     movie_pipe = [
#         { "$match": { "$text": {"$search": phrase} } },
#         { "$project": {
#             "score":   { "$meta": "textScore" },
#             "title":   1,
#             "overview":1,
#         }},
#         { "$sort":  { "score": -1 } },
#         { "$limit": top_k }
#     ]
#     movies = [
#         { **m, "type": "Movie" }
#         for m in db.movies.aggregate(movie_pipe)
#     ]

#     # pipeline for tvshows (rename `name` → `title`)
#     tv_pipe = [
#         { "$match": { "$text": {"$search": phrase} } },
#         { "$project": {
#             "score":    { "$meta": "textScore" },
#             "title":    "$name",
#             "overview": 1,
#         }},
#         { "$sort":   { "score": -1 } },
#         { "$limit":  top_k }
#     ]
#     shows = [
#         { **s, "type": "TV Show" }
#         for s in db.tvshows.aggregate(tv_pipe)
#     ]

#     # combine & return up to top_k from each (you can interleave or merge differently)
#     return movies + shows


# # ——————————————————————————————
# # 2) load your combined FAISS index + id map
# # ——————————————————————————————
# APP_DIR = os.path.dirname(os.path.abspath(__file__))

# IDS_PATH   = os.path.join(APP_DIR, "combined_index_ids.pkl")
# INDEX_PATH = os.path.join(APP_DIR, "combined_faiss.index")

# with open(IDS_PATH, "rb") as f:
#     # a list of tuples: [ ("movie", ObjectId(...)), ("tvshow", ObjectId(...)), … ]
#     IDX_MAP = pickle.load(f)

# INDEX = faiss.read_index(INDEX_PATH)
# MODEL = SentenceTransformer("all-MiniLM-L6-v2")


# # ——————————————————————————————
# # 3) semantic reranking
# # ——————————————————————————————
# def semantic_re_rank(candidates, phrase, top_n=10):
#     # build a quick lookup: ObjectId → index position in the FAISS index
#     pos_map = { oid: pos for pos, (_kind, oid) in enumerate(IDX_MAP) }

#     # filter candidates to those present in our index
#     cand_positions = [
#         pos_map[m["_id"]]
#         for m in candidates
#         if m["_id"] in pos_map
#     ]
#     if not cand_positions:
#         return []

#     # reconstruct just those embeddings
#     # NOTE: reconstruct_n(0, ntotal) gives all vectors—we slice out ours
#     all_embs = INDEX.reconstruct_n(0, INDEX.ntotal)
#     cand_embs = all_embs[cand_positions]

#     # embed the query
#     q_emb = MODEL.encode([phrase], convert_to_numpy=True)
#     faiss.normalize_L2(q_emb)

#     # cosine similarity
#     sims = (cand_embs @ q_emb.T).squeeze()

#     # attach & sort
#     reranked = []
#     for m, sim in zip([c for c in candidates if c["_id"] in pos_map], sims):
#         m["semanticScore"] = float(sim)
#         reranked.append(m)

#     reranked.sort(key=lambda x: x["semanticScore"], reverse=True)
#     return reranked[:top_n]


# # ——————————————————————————————
# # 4) quick test harness
# # ——————————————————————————————
# if __name__ == "__main__":
#     client = MongoClient("mongodb://localhost:27017/")
#     db     = client.mini_netflix
#     phrase = input("Search phrase: ").strip()

#     # 1) text search
#     hits = text_search(db, phrase, top_k=100)
#     print(f"Found {len(hits)} text hits, now semantic re-ranking…")

#     # 2) semantic re-rank
#     top = semantic_re_rank(hits, phrase, top_n=10)
#     for i, m in enumerate(top, start=1):
#         print(f"{i}. [{m['type']}] {m['title']} → score {m['semanticScore']:.3f}")
#     client.close()
