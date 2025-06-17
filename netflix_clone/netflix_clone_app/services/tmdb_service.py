import requests
from django.conf import settings
import random
import requests
import json

BASE_API   = "https://api.themoviedb.org/3"
API_KEY    = settings.TMDB_API_KEY  # put your key in settings.py
IMG_BASE   = "https://image.tmdb.org/t/p/w500"

def fetch_poster_by_title(title):
    """Search TMDB for a movie or show by title and return full poster URL (or None)."""
    url  = f"{BASE_API}/search/multi"
    resp = requests.get(url, params={"api_key": API_KEY, "query": title, "page":1})
    results = resp.json().get("results", [])
    if not results:
        return None
    # pick the first result
    poster_path = results[0].get("poster_path")
    return IMG_BASE + poster_path if poster_path else None

def fetch_movies(category="popular", count=15):
    """Returns first `count` movies in given category, with full poster URLs."""
    url  = f"{BASE_API}/movie/{category}"
    resp = requests.get(url, params={"api_key": API_KEY, "language":"en-US","page":1})
    data = resp.json().get("results", [])[:count]
    # attach full_poster
    for m in data:
        m["full_poster"] = IMG_BASE + m.get("poster_path", "")
    return data



def fetch_random_content(count=15):
    """
    Fetches a mix of movies and TV shows from random category, skips 'latest', attaches full poster URLs.
    """
    movie_categories = ['popular', 'top_rated', 'now_playing', 'upcoming']
    tv_categories    = ['popular', 'top_rated', 'on_the_air', 'airing_today']

    # Choose randomly between movie or TV
    content_type = random.choice(['movie', 'tv'])
    if content_type == 'movie':
        category = random.choice(movie_categories)
        url = f"{BASE_API}/movie/{category}"
    else:
        category = random.choice(tv_categories)
        url = f"{BASE_API}/tv/{category}"

    resp = requests.get(url, params={"api_key": API_KEY, "language": "en-US", "page": 1})
    json_data = resp.json()
    results = json_data.get("results", [])[:count]

    # Add full poster path, safely
    for item in results:
        poster_path = item.get("poster_path")
        item["full_poster"] = IMG_BASE + poster_path if poster_path else ""

    return results



BASE_API = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

def fetch_similar_recommendations(seed_tmdb_id, kind="movie", count=5):
    """
    Call TMDB’s /movie/{id}/similar or /tv/{id}/similar, return up to `count` items.
    kind must be "movie" or "tv".
    """
    url = f"{BASE_API}/{kind}/{seed_tmdb_id}/similar"
    resp = requests.get(url, params={
        "api_key": API_KEY,
        "language": "en-US",
        "page": 1
    })
    results = resp.json().get("results", [])[:count]

    recs = []
    for item in results:
        # pick the right title field
        title = item.get("title") or item.get("name")
        # build poster URL (or fallback)
        poster_path = item.get("poster_path")
        poster = IMG_BASE + poster_path if poster_path else fetch_poster_by_title(title)

        recs.append({
            "title":       title,
            "full_poster": poster,
            "type":        "Movie" if kind == "movie" else "TV Show",
            "shared_cast": 0
        })
    return recs







# add these two helpers alongside fetch_movies()

def fetch_tv(category="popular", count=10):
    url  = f"{BASE_API}/tv/{category}"
    resp = requests.get(url, params={"api_key": API_KEY, "language":"en-US","page":1})
    data = resp.json().get("results", [])[:count]
    for t in data:
        t["full_poster"] = IMG_BASE + t.get("poster_path", "")
        t["title"]       = t.get("name")  # unify to "title"
    return data

def fetch_by_language(lang="en", count=10):
    # fetch “discover” with original_language filter
    url  = f"{BASE_API}/discover/movie"
    resp = requests.get(url, params={
        "api_key": API_KEY,
        "language":"en-US",
        "with_original_language": lang,
        "page":1
    })
    data = resp.json().get("results", [])[:count]
    for m in data:
        m["full_poster"] = IMG_BASE + m.get("poster_path", "")
    return data

def fetch_movie_details(title):
    """
    Search TMDb first as a movie, then as a TV show.
    Return the /full/ details JSON (including a "genres" list) or None.
    """
    # 1) Try movie search
    params = {"api_key": API_KEY, "query": title}
    mv = requests.get(f"{BASE_API}/search/movie", params=params).json().get("results", [])
    if mv:
        movie_id = mv[0]["id"]
        det = requests.get(f"{BASE_API}/movie/{movie_id}", params={"api_key": API_KEY})
        if det.ok:
            return det.json()

    # 2) Try TV search
    tv = requests.get(f"{BASE_API}/search/tv", params=params).json().get("results", [])
    if tv:
        tv_id = tv[0]["id"]
        det = requests.get(f"{BASE_API}/tv/{tv_id}", params={"api_key": API_KEY})
        if det.ok:
            return det.json()

    return None




BASE_API = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

def tmdb_search(title):
    """Try movie then TV search; return dict with tmdb_id, kind, genres, cast_names."""
    for kind in ("movie", "tv"):
        resp = requests.get(f"{BASE_API}/search/{kind}", params={
            "api_key": API_KEY,
            "query":   title,
            "language":"en-US",
            "page":    1
        })
        results = resp.json().get("results", [])
        if not results:
            continue
        seed = results[0]
        tmdb_id = seed["id"]
        # grab genres
        details = requests.get(f"{BASE_API}/{kind}/{tmdb_id}", params={
            "api_key": API_KEY,
            "language":"en-US"
        }).json()
        genres = [g["name"] for g in details.get("genres", [])]
        # grab cast
        credits = requests.get(f"{BASE_API}/{kind}/{tmdb_id}/credits", params={
            "api_key": API_KEY
        }).json().get("cast", [])
        cast_names = [c["name"] for c in credits if c.get("name")]
        return {
            "tmdb_id":   tmdb_id,
            "kind":      kind,
            "genres":    genres,
            "cast":      cast_names
        }
    return None



from openai import OpenAI
from groq import Groq

client = Groq(
    api_key='your api',
)






import re

def grok_recommendations(watchlist, db, n=5):
    """
    Call the Grok API to recommend `n` titles based on the last two items
    in the user's watchlist. Returns a list of dicts with keys:
      - title
      - full_poster
      - type
      - shared_cast (always 0 here)
    """
    # pick up to two seed titles
    seeds = watchlist[-2:]
    # build prompt
    lines = ["You are a savvy streaming service. A user likes:"]
    for idx, title in enumerate(seeds, start=1):
        # fetch genres
        doc = (db.movies.find_one({"title": title}, {"genres":1})
               or db.tvshows.find_one({"name": title}, {"genres":1}))
        if doc and doc.get("genres"):
            genres = [g["name"] for g in doc["genres"] if isinstance(g, dict) and "name" in g]
        else:
            remote = tmdb_search(title)
            genres = remote.get("genres", []) if remote else []
        genre_str = ", ".join(g.lower() for g in genres[:3])
        lines.append(f"{idx}. {title} ({genre_str})")
    lines.append("")
    lines.append(f"Recommend {n} titles (movies or TV shows).")
# Force the model to output only JSON, no markdown or commentary
    prompt = (
        "\n".join(lines)
        + "\n\nReturn only a JSON object with two keys—"
        "`movies` and `tv_shows`—each an array of title strings. "
        "Do not include any markdown fences, numbering, or extra text."
    )

    print("prompt: ",prompt)

    # call Grok API

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print("chat: ",chat_completion)
    #raw = chat_completion.choices[0].message.content.strip().splitlines()
    payload =  chat_completion.choices[0].message.content.strip()


    # parse JSON
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        # fallback to old regex approach or empty
        return []

    recs = []
    for kind, titles in (("Movie", data.get("movies", [])),
                         ("TV Show", data.get("tv_shows", []))):
        for title in titles[:n]:
            # lookup poster
            poster = fetch_poster_by_title(title)
            pp_doc = (db.movies if kind=="Movie" else db.tvshows).find_one(
                { "title" if kind=="Movie" else "name": title },
                {"poster_path":1}
            )
            if pp_doc and pp_doc.get("poster_path"):
                poster = IMG_BASE + pp_doc["poster_path"]

            recs.append({
                "title":       title,
                "full_poster": poster,
                "type":        kind,
                "shared_cast": 0
            })
    print("recs: ",recs)
    return recs


# netflix_clone_app/utils.py
import requests


TMDB_BASE_URL   = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def fetch_from_tmdb(title: str, collection: str) -> dict:
    """
    Given a title and a collection type ("Movie" or "TV Show"),
    hit TMDb to return a dict with keys:
      - overview, genres (list of names), poster (full URL),
      - cast (list), crew (list)
    Returns {} on failure.
    """
    api_key = API_KEY
    # pick the right search endpoint
    search_url = (
        f"{TMDB_BASE_URL}/search/movie"
        if collection == "Movie"
        else f"{TMDB_BASE_URL}/search/tv"
    )
    resp = requests.get(search_url, params={"api_key": api_key, "query": title})
    results = resp.json().get("results", [])
    if not results:
        return {}

    tmdb_id    = results[0]["id"]
    kind_path  = "movie" if collection == "Movie" else "tv"
    detail_url = f"{TMDB_BASE_URL}/{kind_path}/{tmdb_id}"
    cred_url   = f"{detail_url}/credits"

    # fetch detail & credits in parallel
    detail = requests.get(detail_url, params={"api_key": api_key}).json()
    credits = requests.get(cred_url,   params={"api_key": api_key}).json()

    return {
        "overview": detail.get("overview", ""),
        "genres":   [g["name"] for g in detail.get("genres", [])],
        "poster":   (TMDB_IMAGE_BASE + detail["poster_path"])
                     if detail.get("poster_path") else None,
        "cast":     credits.get("cast", []),
        "crew":     credits.get("crew", []),
    }

