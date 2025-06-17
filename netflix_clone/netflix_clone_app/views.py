from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.contrib.auth.hashers import make_password, check_password
#from pytube import YouTube
from django.conf import settings
from pymongo import MongoClient
from .auth_utils import session_required
from .semantic_search import text_search, semantic_re_rank
from bson import ObjectId
from django.http import JsonResponse, HttpResponseBadRequest
import os
import random                          
from .services.tmdb_service import fetch_from_tmdb, grok_recommendations,tmdb_search, fetch_similar_recommendations, fetch_random_content, fetch_movies, fetch_tv, fetch_by_language, fetch_poster_by_title, fetch_movie_details 



#------------------------ ADMIN ----------------------------------

# netflix_clone_app/views.py
import bcrypt
from django.shortcuts import render, redirect
from bson.objectid import ObjectId
from pymongo import MongoClient
from .auth_utils import admin_required

# --- ADMIN LOGIN ---
def admin_login(request):
    error = None
    if request.method == "POST":
        u = request.POST["username"]
        p = request.POST["password"].encode()
        client = MongoClient("mongodb://localhost:27017/")
        admin = client.mini_netflix.admins.find_one({"username": u})
        client.close()

        if admin and bcrypt.checkpw(p, admin["password_hash"].encode()):
            # success!
            request.session["is_admin"] = True
            client = MongoClient("mongodb://localhost:27017/")
            client.mini_netflix.admins.update_one(
                {"_id": admin["_id"]},
                {"$set": {"last_login": __import__("datetime").datetime.utcnow()}}
            )
            client.close()
            return redirect("admin_dashboard")
        else:
            error = "Invalid credentials"

    return render(request, "admin_login.html", {"error": error})

# --- ADMIN LOGOUT ---
def admin_logout(request):
    request.session.pop("is_admin", None)
    return redirect("admin_login")

# --- ADMIN DASHBOARD ---
@admin_required
def admin_dashboard(request, section="movies"):
    client  = MongoClient("mongodb://localhost:27017/")
    db      = client["mini_netflix"]

    if section == "movies":
        objects = list(db.movies.find().sort("title", 1))
    elif section == "tvshows":
        objects = list(db.tvshows.find().sort("name", 1))
    else:
        # users section
        objects = list(db.users.find().sort("username", 1))

    # ─── handle MongoDB _id for template safely ───
    for o in objects:
        o["id"] = str(o.pop("_id"))

    client.close()
    return render(request, "admin_dashboard.html", {
        "section": section,
        "objects": objects
    })



# ------------------------------ admin operations ---------------------------

# netflix_clone_app/views.py
import bcrypt
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from django.shortcuts import render, redirect
from django.urls import reverse
from .auth_utils import admin_required

# — MOVIES CRUD — #

@admin_required
def movie_create(request):
    if request.method == "POST":
        title        = request.POST["title"]
        release_date = request.POST["release_date"] or None
        genres       = [g.strip() for g in request.POST["genres"].split(",") if g.strip()]
        runtime      = int(request.POST.get("runtime") or 0)
        revenue      = int(request.POST.get("revenue") or 0)

        client = MongoClient("mongodb://localhost:27017/")
        db     = client["mini_netflix"]
        db.movies.insert_one({
            "title":        title,
            "release_date": release_date,
            "genres":       genres,
            "runtime":      runtime,
            "revenue":      revenue
        })
        client.close()
        return redirect(reverse("admin_dashboard") + "?section=movies")

    # GET
    return render(request, "movie_form.html", {
        "section": "movies",
        "movie":   None
    })

from bson.objectid import ObjectId

@admin_required
def movie_update(request, id):
    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]

    # ─── convert the incoming id to the right type ───
    try:
        query_id = ObjectId(id)          # if it's a 24-char hex string
    except Exception:
        try:
            query_id = int(id)           # if you actually stored numeric IDs
        except ValueError:
            query_id = id                # fallback (shouldn’t happen)

    movie = db.movies.find_one({"_id": query_id}) or {}

    if request.method == "POST":
        db.movies.update_one(
            {"_id": query_id},
            {"$set": {
                "title":        request.POST["title"],
                "release_date": request.POST["release_date"] or None,
                "genres":       [g.strip() for g in request.POST["genres"].split(",") if g.strip()],
                "runtime":      int(float(request.POST.get("runtime") or 0)),
                "revenue":      int(request.POST.get("revenue") or 0),
            }}
        )
        client.close()
        return redirect(reverse("admin_dashboard") + "?section=movies")

    # GET
    client.close()
    return render(request, "movie_form.html", {
        "section": "movies",
        "movie":   movie
    })


@admin_required
def movie_delete(request, id):
    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]
    movie  = db.movies.find_one({"_id": ObjectId(id)}) or {}
    if request.method == "POST":
        db.movies.delete_one({"_id": ObjectId(id)})
        client.close()
        return redirect(reverse("admin_dashboard") + "movies")

    client.close()
    return render(request, "movie_confirm_delete.html", {
        "section": "movies",
        "movie":   movie
    })


# — TV SHOWS CRUD — #

@admin_required
def tvshow_create(request):
    if request.method == "POST":
        name            = request.POST["name"]
        first_air_date  = request.POST["first_air_date"] or None
        seasons_count   = int(request.POST.get("seasons_count") or 0)
        genres          = [g.strip() for g in request.POST["genres"].split(",") if g.strip()]

        client = MongoClient("mongodb://localhost:27017/")
        db     = client["mini_netflix"]
        db.tvshows.insert_one({
            "name":            name,
            "first_air_date":  first_air_date,
            "seasons_count":   seasons_count,
            "genres":          genres
        })
        client.close()
        return redirect(reverse("admin_dashboard") + "tvshows")

    return render(request, "tvshow_form.html", {
        "section": "tvshows",
        "show":    None
    })

@admin_required
def tvshow_update(request, id):
    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]
    show   = db.tvshows.find_one({"_id": ObjectId(id)}) or {}
    if request.method == "POST":
        db.tvshows.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "name":            request.POST["name"],
                "first_air_date":  request.POST["first_air_date"] or None,
                "seasons_count":   int(request.POST.get("seasons_count") or 0),
                "genres":          [g.strip() for g in request.POST["genres"].split(",") if g.strip()],
            }}
        )
        client.close()
        return redirect(reverse("admin_dashboard") + "tvshows")

    client.close()
    return render(request, "tvshow_form.html", {
        "section": "tvshows",
        "show":    show
    })

@admin_required
def tvshow_delete(request, id):
    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]
    show   = db.tvshows.find_one({"_id": ObjectId(id)}) or {}
    if request.method == "POST":
        db.tvshows.delete_one({"_id": ObjectId(id)})
        client.close()
        return redirect(reverse("admin_dashboard") + "tvshows")

    client.close()
    return render(request, "tvshow_confirm_delete.html", {
        "section": "tvshows",
        "show":    show
    })


# — USERS CRUD — #

@admin_required
def user_create(request):
    if request.method == "POST":
        username = request.POST["username"]
        email    = request.POST["email"]
        raw_pw   = request.POST["password"].encode()
        pw_hash  = bcrypt.hashpw(raw_pw, bcrypt.gensalt()).decode()

        client = MongoClient("mongodb://localhost:27017/")
        db     = client["mini_netflix"]
        db.users.insert_one({
            "username":     username,
            "email":        email,
            "password_hash": pw_hash,
            "watchlist":    [],
            "signup_date":  datetime.utcnow()
        })
        client.close()
        return redirect(reverse("admin_dashboard") + "users")

    return render(request, "user_form.html", {
        "section":  "users",
        "user_obj": None
    })

@admin_required
def user_update(request, id):
    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]
    user   = db.users.find_one({"_id": ObjectId(id)}) or {}
    if request.method == "POST":
        db.users.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "username": request.POST["username"],
                "email":    request.POST["email"]
            }}
        )
        client.close()
        return redirect(reverse("admin_dashboard") + "users")

    client.close()
    return render(request, "user_form.html", {
        "section":  "users",
        "user_obj": user
    })

@admin_required
def user_delete(request, id):
    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]
    user   = db.users.find_one({"_id": ObjectId(id)}) or {}
    if request.method == "POST":
        db.users.delete_one({"_id": ObjectId(id)})
        client.close()
        return redirect(reverse("admin_dashboard") + "users")

    client.close()
    return render(request, "user_confirm_delete.html", {
        "section":  "users",
        "user_obj": user
    })

#-----------------------------------------------------------------------------------------------------------

# -------------------------- Landing page -------------------


#@login_required
def index(request):
    return render(request, 'landingpage.html')

@session_required
def home(request):
# fetch the first 15 “popular” movies

    movies = fetch_random_content(count=10)

    return render(request, 'index.html', {
        "movies": movies
    })



from django.shortcuts import render, redirect
from pymongo import MongoClient
from django.contrib.auth.hashers import make_password

def user_signup(request):
    if request.method == 'POST':
        email = request.POST['email'].strip()
        password = request.POST['password']
        repeatPassword = request.POST['repeatpassword']

        if password != repeatPassword:
            return render(request, 'signup.html', {'error_message': 'Passwords do not match'})

        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['mini_netflix']
        users_collection = db['users']

        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return render(request, 'signup.html', {'error_message': 'User already exists with this email'})

        # Insert new user
        users_collection.insert_one({
            'email': email,
            'password': make_password(password),
            'watchlist': [],
            'genre': []
        })

        return redirect('/login')

    return render(request, 'signup.html')






def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Connect directly to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['mini_netflix']
        users_collection = db['users']

        # Find the user manually
        user = users_collection.find_one({'email': email})

        if user:
            if check_password(password, user['password']):
                request.session['user_id'] = str(user['_id'])  # login session
                return redirect('home')
            else:
                error_message = 'Invalid credentials'
                return render(request, 'login.html', {'error_message': error_message})
        else:
            error_message = 'User not found'
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')



def user_logout(request):
    request.session.flush()  # Clear all session data
    return redirect('index')


#----------------- search -----------------------------

import math
import json
from bson import ObjectId
from django.http import JsonResponse, HttpResponseBadRequest
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from .semantic_search import text_search, semantic_re_rank
import math

# --------------------------------- search with new UI -------------------------------------------------

from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from bson import ObjectId
from pymongo import MongoClient
import math

from django.shortcuts import render
from django.http import JsonResponse
from bson import ObjectId
from pymongo import MongoClient
import json, math


@session_required
def search(request):
    """
    GET /search?q=<phrase>

    Unified content search across the Mini‑Netflix backend that surfaces
    results from multiple MongoDB collections and applies both classical and
    ML‑based ranking.

    ─── Collections Used ────────────────────────────────────────────────
      • users                    – pull the signed‑in user’s watch‑list
      • movies                   – full‑text + genre match + semantic re‑rank
      • tvshows                  – full‑text + genre match + semantic re‑rank
      • credits                  – cast‑name substring match
      • movie_tvshow_collection  – custom posters for movies/TV shows

    ─── Pipeline Overview ─────────────────────────────────────────────────
      1. **Watch‑list bootstrap**  
         Fetch the current user’s `watchlist` array from *users*.

      2. **Semantic Search (Embeddings + FAISS)**  
         • `text_search()` does a fast BM25 recall (top‑k=100).  
         • `semantic_re_rank()` embeds titles & the query with a
           Sentence‑Transformers model, then re‑ranks via cosine distance
           inside a FAISS index to return the top‑n=10 movies.  
         • **Fallback:** if the embedding service / FAISS index fails,
           the `except` block yields `movie_results = []` and execution
           falls back to pure text/genre search.

      3. **MongoDB Aggregation**  
         A single `$unionWith` pipeline fans‑out to:  
           – text‑score matches in *movies* (‑10)  
           – text‑score matches in *tvshows* (‑10)  
           – genre‑exact matches in *movies* (‑10)  
           – genre‑exact matches in *tvshows* (‑10)  
         IDs already chosen by the semantic layer are excluded.

      4. **Watch‑list fuzzy match**  
         Case‑insensitive substring scan over the user’s saved titles;
         returns up to five personal hits.

      5. **Cast‑name match**  
         Iterate *credits*, JSON‑parse the TMDB cast blobs, and surface up
         to five titles where any actor/actress name contains the query
         (case‑insensitive).

      6. **Post‑processing & Image Fallbacks**  
         Results are merged in the order: `credits → semantic → aggregate → 
         watch‑list`.  
           • Try custom art from *movie_tvshow_collection* (`ref_id`, `type`).  
           • Fallback to `fetch_poster_by_title()` (TMDB) if no custom image.  
           • Sanitize NaN / non‑finite overviews to safe strings.

    ─── Security ──────────────────────────────────────────────────────────
      Decorated with `@session_required`; unauthenticated callers receive
      a 401 before any DB access.

    ─── Response ──────────────────────────────────────────────────────────
      JsonResponse in the form:
        {
          "results": [
            {
              "title":      str,
              "overview":   str,
              "collection": "movies" | "tvshows" | "credits" | "users",
              "poster":     str  # URL
            },
            …
          ]
        }
    """
    phrase = request.GET.get('q', '').strip()
    if not phrase:
        return JsonResponse({"results": []})

    uid    = request.session.get("user_id")
    client = MongoClient('mongodb://localhost:27017/')
    db     = client['mini_netflix']

    # === 1. Watchlist (per-user) ===
    my_watchlist = []
    if uid:
        user_doc = db.users.find_one(
            {"_id": ObjectId(uid)},
            {"watchlist": 1, "_id": 0}
        ) or {}
        my_watchlist = user_doc.get("watchlist", [])

    # === 2. Semantic + Text search (title-based movies) ===
    try:
        candidates     = text_search(db, phrase, top_k=100)
        movie_results  = semantic_re_rank(candidates, phrase, top_n=10)
    except Exception:
        movie_results = []

    for m in movie_results:
        m["overview"]   = m.get("overview", "") or ""
        m["title"]      = m.get("title", "")
        m["collection"] = "movies"

    movie_ids = [m["_id"] for m in movie_results]

    # === 3. Aggregation: movies, tvshows, genres ===
    pipeline = [
        {"$match": {"_id": {"$nin": movie_ids}, "$text": {"$search": phrase}}},
        {"$project": {
            "title":      1,
            "overview":   1,
            "genres":     1,
            "collection": {"$literal": "movies"},
            "score":      {"$meta": "textScore"}
        }},
        {"$sort":  {"score": -1}}, {"$limit": 10},
        {"$unionWith": {
            "coll": "tvshows",
            "pipeline": [
                {"$match": {"$text": {"$search": phrase}}},
                {"$project": {
                    "title":      "$name",
                    "overview":   1,
                    "genres":     1,
                    "collection": {"$literal": "tvshows"},
                    "score":      {"$meta": "textScore"}
                }},
                {"$sort":  {"score": -1}}, {"$limit": 10}
            ]
        }},
        {"$unionWith": {
            "coll": "movies",
            "pipeline": [
                {"$match": {"genres.name": phrase}},
                {"$project": {
                    "title":      1,
                    "overview":   1,
                    "collection": {"$literal": "movies"}
                }},
                {"$limit": 10}
            ]
        }},
        {"$unionWith": {
            "coll": "tvshows",
            "pipeline": [
                {"$match": {"genres": phrase}},
                {"$project": {
                    "title":      "$name",
                    "overview":   1,
                    "collection": {"$literal": "tvshows"}
                }},
                {"$limit": 10}
            ]
        }},
        # ─── HERE: KEEP the _id in the final output ─────────────────────────────────
        {"$project": {
            "_id":       1,
            "title":     1,
            "overview":  1,
            "collection":1
        }},
        {"$limit": 20}
    ]
    agg_results = list(db.movies.aggregate(pipeline))

    # === 4. Watchlist filter ===
    wl_hits = []
    low = phrase.lower()
    for title in my_watchlist:
        if low in title.lower():
            wl_hits.append({
                "title":      title,
                "overview":   "",
                "collection": "users"
            })

    # === 5. Cast Match ===

    matched_credits = []
    low = phrase.lower()
    credit_cursor = db.credits.find({}, {"title": 1, "cast": 1})
    for doc in credit_cursor:
        try:
            cast_list = json.loads(doc.get("cast", "[]"))
            for person in cast_list:
                # case-insensitive substring match
                if low in person.get("name", "").lower():
                    matched_credits.append({
                        "title":      doc.get("title"),
                        "overview":   "",
                        "collection": "credits"
                    })
                    break
            if len(matched_credits) >= 5:
                break
        except Exception:
            continue


    # === 6. Combine & build JSON ===
    combined = matched_credits + movie_results + agg_results + wl_hits
    out = []

    for r in combined:
        ov = r.get("overview", "") or ""
        if isinstance(ov, float):
            ov = "" if (math.isnan(ov) or not math.isfinite(ov)) else str(ov)

        # ——— look up custom image URL by ref_id ———
        poster_url = None
        if r.get("_id") is not None:
            ref = str(r["_id"])
            custom = db.movie_tvshow_collection.find_one({
                "ref_id": ref,
                "type":   r["collection"]
            })
            if custom and custom.get("image"):
                poster_url = custom["image"]

        # fallback to TMDB if no custom image
        if not poster_url:
            poster_url = fetch_poster_by_title(r["title"])

        out.append({
            "title":      r["title"],
            "overview":   ov,
            "collection": r["collection"],
            "poster":     poster_url
        })

    client.close()
    return JsonResponse({"results": out})


#---------------------------- Search Page --------------------------------------------
@session_required
def search_page(request):
    """Render full-page HTML search at /search/."""
    phrase = request.GET.get('q', '').strip()
    if not phrase:
        # blank page
        return render(request, "search_page.html", {
            "q": "", "movies": [], "tvshows": [], "users": []
        })

    # call our JSON API
    api_resp = search(request)            # this is a JsonResponse
    payload  = json.loads(api_resp.content)  # bytes → dict
    data     = payload.get("results", [])

    movies = [r for r in data if r["collection"] in ("movies", "credits")]
    tvshows = [r for r in data if r["collection"] == "tvshows"]
    users   = [r for r in data if r["collection"] == "users"]

    return render(request, "search_page.html", {
        "q":        phrase,
        "movies":   movies,
        "tvshows":  tvshows,
        "users":    users
    })






@session_required
def movies(request):
    """
    Renders the movies carousel.  Normalizes each movie dict
    to have 'title' and 'full_poster' keys.
    """
    raw = fetch_movies(category="popular", count=20)
    # Each raw item already has 'title' and 'full_poster'
    movies = []
    for m in raw:
        poster = m.get("full_poster")
        # If you stored only TMDB poster_path instead:
        if not poster and m.get("poster_path"):
            poster = IMG_BASE + m["poster_path"]
        movies.append({
            "title":       m.get("title", ""),
            "overview":    m.get("overview", ""),
            "language":     m.get("original_language", ""),
            "full_poster": poster or "",
        })

    return render(request, "movies.html", {
        "items":   movies,
        "heading": "Movies"
    })

@session_required
def tvshows(request):
    raw = fetch_tv(category="popular", count=20)
    # normalize each TV dict to use "title" instead of "name"
    shows = [
        {
            "title":        tv.get("name", ""),
            "overview":     tv.get("overview", ""),
            "full_poster":  tv.get("full_poster") 
                              or (IMG_BASE+tv["poster_path"] if tv.get("poster_path") else None),
            "language":     tv.get("original_language", ""),
            # you can pass along any other keys you need…
        }
        for tv in raw
    ]
    return render(request, 'tvshows.html', {"items": shows, "heading": "TV Shows"})




# ------------------------------- Browse By Language ---------------------------------------------

import random
from django.shortcuts import render
from pymongo import MongoClient
from bson import ObjectId
from .services.tmdb_service import fetch_poster_by_title

IMG_BASE = "https://image.tmdb.org/t/p/w500"



# assume IMG_BASE and fetch_poster_by_title are defined elsewhere
@session_required
def browsebylanguage(request):
    """
    GET /browsebylanguage?lang=<ISO‑639‑1>

    Returns a small carousel of content available in a chosen original
    language.  No heavy ML is required here—just targeted Mongo queries plus
    poster‑URL fall‑backs—but the view still orchestrates several collections
    and applies randomized sampling to keep the results fresh.

    ─── Collections Touched ────────────────────────────────────────────────
      • movies    – random sample of ≤ 5 titles with `original_language = lang`
      • tvshows   – random sample of ≤ 5 series with `original_language = lang`
      • users     – current user’s `watchlist`, filtered for language matches

    ─── Pipeline Overview ─────────────────────────────────────────────────
      1. **Movie sample**  
         `$match` on `original_language`, `$sample` size 5, `$project` title.

      2. **TV‑show sample**  
         Same pattern but `$project` includes `poster_path`; we build full
         poster URLs with `IMG_BASE` or fall back to TMDB search when absent.

      3. **Watch‑list cross‑filter**  
         For the signed‑in user, scan their `watchlist` and keep only titles
         whose language matches *either* `movies` *or* `tvshows`.  
         Uses two point‑lookups per title; final list capped at five random
         samples.  If no `lang` query is supplied we simply sample any five.

      4. **Merge & cap**  
         Combine movie, show, and watch‑list items (max 10) and guarantee each
         has a poster—first trying custom `poster_path`, otherwise falling
         back to `fetch_poster_by_title()`.

    ─── Security ──────────────────────────────────────────────────────────
      Protected by `@session_required`; anonymous calls are rejected early.

    ─── Response (render) ─────────────────────────────────────────────────
      Renders *browsebylanguage.html* with:
        • items   – list[{title, full_poster}]
        • heading – “Browse by Language — <LANG>”
        • selected_lang – the raw `lang` query param
    """

    lang = request.GET.get('lang', '').strip()

    client = MongoClient('mongodb://localhost:27017/')
    db     = client['mini_netflix']

    # 1) pull up to 5 movie titles in that language
    movies = []
    if lang:
        cursor = db.movies.aggregate([
            {"$match": {"original_language": lang}},
            {"$sample": {"size": 5}},
            {"$project": {"_id": 0, "title": 1}}
        ])
        movies = [m['title'] for m in cursor]

    # 2) pull up to 5 TV shows in that language (use 'name' field)
    shows = []
    if lang:
        cursor = db.tvshows.aggregate([
            {"$match": {"original_language": lang}},
            {"$sample": {"size": 5}},
            {"$project": {
                "_id":         0,
                "name":        1,
                "poster_path": 1,
            }}
        ])

        for doc in cursor:
            poster_path = doc.get("poster_path")
            if isinstance(poster_path, str) and poster_path:
                full_poster = IMG_BASE + poster_path
            else:
                full_poster = fetch_poster_by_title(doc["name"])

            shows.append({
                "title":       doc["name"],
                "full_poster": full_poster
            })

    # 3) pull up to 5 from the user’s watchlist, filtered by selected language
    user_list = []
    uid = request.session.get('user_id')
    if uid:
        user = db.users.find_one({"_id": ObjectId(uid)})
        watch = user.get('watchlist', [])
        if watch:
            if lang:
                # only keep watchlist titles that match the selected language
                filtered = []
                for t in watch:
                    # check movies collection
                    movie_match = db.movies.find_one({
                        "title": t,
                        "original_language": lang
                    })
                    # check tvshows collection
                    show_match = db.tvshows.find_one({
                        "name": t,
                        "original_language": lang
                    })
                    if movie_match or show_match:
                        filtered.append(t)
                user_list = random.sample(filtered, min(5, len(filtered)))
            else:
                # no language filter: show any watchlist items
                user_list = random.sample(watch, min(5, len(watch)))

    client.close()

    # 4) build a combined list of up to 10 items
    all_items = []
    for t in movies:
        all_items.append({"title": t, "source": "movie"})
    for s in shows:
        all_items.append({
            "title":       s["title"],
            "full_poster": s["full_poster"],
            "source":      "show"
        })
    for t in user_list:
        all_items.append({"title": t, "source": "watchlist"})

    # cap to 10
    all_items = all_items[:]

    # 5) fetch posters for movies & watchlist
    items = []
    for entry in all_items:
        if entry["source"] == "show":
            items.append({
                "title":       entry["title"],
                "full_poster": entry["full_poster"]
            })
        else:
            poster = fetch_poster_by_title(entry["title"])
            if poster:
                items.append({
                    "title":       entry["title"],
                    "full_poster": poster
                })

    # 6) render template
    heading = f"Browse by Language — {lang.upper()}" if lang else "Browse by Languages"
    return render(request, 'browsebylanguage.html', {
        "items":         items,
        "heading":       heading,
        "selected_lang": lang,
    })


# ------------------------------------- marked watched ---------------------------

# netflix_clone_app/views.py
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from pymongo import MongoClient

# import your TMDb helper
from .services.tmdb_service import fetch_movie_details 

@session_required
@csrf_exempt
def mark_watched(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        payload = json.loads(request.body)
        title   = payload['title']
    except (ValueError, KeyError):
        return HttpResponseBadRequest("Invalid JSON payload")

    client = MongoClient('mongodb://localhost:27017/')
    db     = client['mini_netflix']

    # 1) Try local Mongo first
    doc = db.movies.find_one({'title': title}) or \
          db.tvshows.find_one({'name':  title})

    # 2) If not local, fall back to TMDb API
    if not doc:
        details = fetch_movie_details(title)
        if not details:
            client.close()
            return JsonResponse({'error': 'Not found'}, status=404)
        raw_genres = details.get('genres', [])
    else:
        raw_genres = doc.get('genres', [])

    # 3) Normalize genres to a list of strings
    genres = []
    if isinstance(raw_genres, list):
        # either list of dicts (TMDb or local movies)…
        for g in raw_genres:
            if isinstance(g, dict) and 'name' in g:
                genres.append(g['name'])
            elif isinstance(g, str):
                genres.append(g)
    elif isinstance(raw_genres, str):
        # or a comma-separated string (local tvshows import)
        genres = [g.strip() for g in raw_genres.split(',') if g.strip()]

    # 4) Make sure the user is logged in
    uid = request.session.get('user_id')
    if not uid:
        client.close()
        return JsonResponse({'error': 'Not logged in'}, status=403)

    # 5) Update their watchlist and genre list
    db.users.update_one(
        { '_id': ObjectId(uid) },
        {
            '$addToSet': {
                'watchlist': title,
                'genre': {'$each': genres}
            }
        }
    )
    client.close()

    return JsonResponse({'status': 'ok', 'added': title, 'genres': genres})


@session_required
@csrf_exempt
def add_to_list(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        data = json.loads(request.body)
        title = data['title']
    except (ValueError, KeyError):
        return HttpResponseBadRequest("Invalid JSON payload")

    client = MongoClient('mongodb://localhost:27017/')
    db     = client['mini_netflix']

    # here we don’t re-fetch genres, we just add to watchlist
    uid = request.session.get('user_id')
    if not uid:
        client.close()
        return JsonResponse({'error': 'Not logged in'}, status=403)

    db.users.update_one(
        { '_id': ObjectId(uid) },
        { '$addToSet': { 'watchlist': title } }
    )
    client.close()
    return JsonResponse({'status': 'ok', 'added': title})




# ------------------------------------ MyList --------------------------------------------


# netflix_clone_app/views.py

import random
from bson.objectid import ObjectId
from django.shortcuts import render
from django.http      import HttpResponseBadRequest
from pymongo          import MongoClient

from .services.tmdb_service import fetch_poster_by_title



# base URL for TMDb poster paths
IMG_BASE = "https://image.tmdb.org/t/p/w500"

@session_required
def mylist(request):
    """
    GET /mylist

    Personal dashboard that shows the user’s saved Watch‑list (“My List”)
    plus a short row of *featured* recommendations derived from shared cast,
    an LLM‑powered fallback, and—if necessary—raw popularity.

    ─── Collections Touched ────────────────────────────────────────────────
      • users      – fetch the current user’s `watchlist`
      • movies     – look up metadata, posters, languages, popularity
      • tvshows    – same as *movies* for episodic content
      • credits    – compute shared‑cast overlap between titles

    ─── Pipeline Overview ─────────────────────────────────────────────────
      1. **Watch‑list hydrate**  
         • For every title → find in *movies* then *tvshows*;  
           resolve poster via `IMG_BASE` path or TMDB fallback.  
         • Build a set of preferred languages seen in the list
           (always add `"en"`).

      2. **Shared‑cast recommendations**  
         • Use the most recently added title as a *seed*.  
         • Aggregate over *credits*: group by `movie_id`, count actors in
           common with the seed, sort by `shared` desc, limit 10.  
         • Filter out any title whose `original_language` is *not* in the
           preferred‑language set.

      3. **Grok (LLM) recommendations** – fallback #1  
         • If step 2 produces nothing, call `grok_recommendations()`, an
           external service that prompts a language‑aligned LLM (OpenAI
           “Grok” flavour) with the user’s last two Watch‑list items.  
         • The service uses embeddings + cosine similarity inside FAISS to
           ground suggestions before drafting the JSON it returns.  
         • Titles outside the preferred‑language set are discarded.

      4. **Pure popularity** – fallback #2  
         • Still empty?  Surface the top 5 movies & top 5 TV shows sorted by
           `popularity`, again language‑filtered.

    ─── Media Handling ────────────────────────────────────────────────────
      Posters are resolved in this order:
        1. local `poster_path` + `IMG_BASE`
        2. `fetch_poster_by_title()` (TMDB search API)

    ─── Security ──────────────────────────────────────────────────────────
      Decorated with `@session_required`; 401 returned if session missing.

    ─── Template Context ─────────────────────────────────────────────────
      Renders *mylist.html* with:
        • heading  –  "My List"
        • my_list  –  hydrated watch‑list items
        • featured –  curated recommendations (may be empty)
    """
    # ——— FUNCTION BODY  ———

    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]

    uid = request.session.get("user_id")
    if not uid:
        client.close()
        return HttpResponseBadRequest("Login required")

    # ——————————————————————————————————————————————————————————————
    # 1) load user watchlist
    user = db.users.find_one({"_id": ObjectId(uid)}, {"watchlist": 1})
    watchlist = user.get("watchlist", [])

    # build preferred languages set from watchlist items
    languages_set = set()
    for title in watchlist:
        lang_doc = (
            db.movies.find_one({"title": title}, {"original_language": 1})
            or
            db.tvshows.find_one({"name": title}, {"original_language": 1})
        )
        if lang_doc and lang_doc.get("original_language"):
            languages_set.add(lang_doc["original_language"])
    # always include English
    allowed_langs = languages_set.union({"en"})

    # 1) MY LIST
    my_list_items = []
    for title in watchlist:
        # try movies first
        doc = db.movies.find_one({"title": title}, {"title":1,"poster_path":1})
        if doc:
            real_title = doc["title"]
            pp         = doc.get("poster_path") or ""
            poster     = IMG_BASE + pp if pp else fetch_poster_by_title(real_title)
            kind       = "Movie"
        else:
            # then try TV shows
            doc = db.tvshows.find_one({"name": title}, {"name":1,"poster_path":1})
            if doc:
                real_title = doc["name"]
                pp         = doc.get("poster_path") or ""
                poster     = IMG_BASE + pp if pp else fetch_poster_by_title(real_title)
                kind       = "TV Show"
            else:
                # fallback purely by title
                real_title = title
                poster     = fetch_poster_by_title(real_title)
                kind       = "Unknown"

        if poster:
            my_list_items.append({
                "title":       real_title,
                "full_poster": poster,
                "type":        kind,
            })

    # ——————————————————————————————————————————————————————————————
    # 2) try shared-cast recommendations
    featured_items = []
    seed = watchlist[-1] if watchlist else None

    if seed:
        local_seed = (
            db.movies.find_one({"title": seed}, {"_id":1})
            or
            db.tvshows.find_one({"name": seed}, {"_id":1})
        )
        if local_seed:
            sid = local_seed["_id"]
            credits_cursor = db.credits.find({"movie_id": sid}, {"name":1})
            cast_names = [c["name"] for c in credits_cursor if c.get("name")]
            if cast_names:
                pipeline = [
                  {"$match":{
                     "name":    {"$in": cast_names},
                     "movie_id":{"$ne": sid}
                  }},
                  {"$group": {"_id":"$movie_id","shared":{"$sum":1}}},
                  {"$sort":  {"shared":-1}},
                  {"$limit": 10}
                ]
                for r in db.credits.aggregate(pipeline):
                    rid = r["_id"]
                    # lookup movie or show by that credit
                    doc = db.movies.find_one({"_id":rid}, {"title":1,"poster_path":1,"original_language":1})
                    kind = "Movie"
                    if not doc:
                        doc = db.tvshows.find_one({"_id":rid}, {"name":1,"poster_path":1,"original_language":1})
                        kind = "TV Show"
                    if not doc:
                        continue
                    title = doc.get("title") or doc.get("name")
                    lang  = doc.get("original_language", "")
                    # filter by allowed languages
                    if lang not in allowed_langs:
                        continue
                    pp     = doc.get("poster_path") or ""
                    poster = IMG_BASE + pp if pp else fetch_poster_by_title(title)
                    featured_items.append({
                        "title":       title,
                        "full_poster": poster,
                        "type":        kind,
                        "shared_cast": r.get("shared", 0),
                        "language":    lang,
                    })

    # ——————————————————————————————————————————————————————————————
    # 3) Grok-based recommendations (if still none)
    if seed and not featured_items:
        grok_recs = grok_recommendations(watchlist, db, n=5)
        # only keep those matching preferred langs
        for rec in grok_recs:
            lang = rec.get("language","en")
            if lang in allowed_langs:
                featured_items.append(rec)

    # ——————————————————————————————————————————————————————————————
    # 4) FINAL FALLBACK: pure popularity
    if not featured_items:
        # top 5 movies
        for m in db.movies.find().sort("popularity", -1).limit(5):
            title = m.get("title")
            if not title: continue
            lang  = m.get("original_language","")
            if lang not in allowed_langs:
                continue
            pp     = m.get("poster_path") or ""
            poster = IMG_BASE + pp if pp else fetch_poster_by_title(title)
            featured_items.append({
                "title":       title,
                "full_poster": poster,
                "type":        "Movie",
                "shared_cast": 0,
                "language":    lang,
            })
        # top 5 tvshows
        for s in db.tvshows.find().sort("popularity", -1).limit(5):
            title = s.get("name")
            if not title: continue
            lang  = s.get("original_language","")
            if lang not in allowed_langs:
                continue
            pp     = s.get("poster_path") or ""
            poster = IMG_BASE + pp if pp else fetch_poster_by_title(title)
            featured_items.append({
                "title":       title,
                "full_poster": poster,
                "type":        "TV Show",
                "shared_cast": 0,
                "language":    lang,
            })

    client.close()

    return render(request, "mylist.html", {
        "heading":  "My List",
        "my_list":  my_list_items,
        "featured": featured_items,
    })


# -------------------------------- NEW Popular ------------------------------------------------------------

# your genre list
GENRES = [
    "Action","Drama","Thriller","Romance","Fantasy",
    "Comedy","Horror","Sci-Fi","Mystery","Adventure"
]

from pymongo import MongoClient
from bson import ObjectId
import random
import requests
from django.shortcuts import render
from django.http import Http404

# make sure you have TMDB_API_KEY in your Django settings
from django.conf import settings
@session_required
def new_popular(request):
    """
    GET /new‑and‑popular?genre=<GenreName>

    Builds the “New & Popular” carousel for a picked genre.  
    The endpoint is rendered even before a genre is chosen (empty carousel).

    ─── Collections Touched ────────────────────────────────────────────────
      • movies     – popularity‑sorted movie slice + credits lookup
      • credits    – derive top‑3 cast names for each movie
      • tvshows    – popularity‑sorted TV‑show slice
      • users      – user’s `watchlist` for extra items in the same genre

    ─── Pipeline Overview ─────────────────────────────────────────────────
      1. **Movies sub‑pipeline**  
         `$match` on `genres.name`, sort by `popularity`, limit 5, `$lookup`
         into *credits* to pull `cast`, then `$addFields`/`$slice` to keep the
         top 3 actor names (`topCast`).

      2. **TV‑shows sub‑pipeline**  
         Case‑insensitive regex match on `genres`, sort by `popularity`,
         limit 5.  No cast lookup, so `topCast` is an empty list.

      3. **Union & resort**  
         `$unionWith` merges the two streams, then a final `$sort` ensures all
         10 results are globally ordered by `popularity`.

      4. **Poster hydration**  
         Each title gets `fetch_poster_by_title()` to resolve a TMDB image
         when local `poster_path` is unavailable.

      5. **Watch‑list enrichment**  
         If the user is logged in, up to five of their own saved titles that
         also belong to the selected genre are appended—providing a personal
         touch even when the official catalogue is sparse.

    ─── Security ──────────────────────────────────────────────────────────
      Decorated with `@session_required`; unauthenticated requests are
      short‑circuited.

    ─── Template Context ─────────────────────────────────────────────────
      Renders *new_popular.html* with:
        • genres          – static list `GENRES`
        • selected_genre  – the query param (empty if none)
        • featured        – hydrated list[{title, full_poster, type, top_cast}]
        • heading         – "New & Popular"
    """
    # ——— FUNCTION BODY UNCHANGED ———

    selected_genre = request.GET.get("genre", "").strip()

    # always render the page — carousel will only show once a genre is picked
    if not selected_genre:
        return render(request, "new_popular.html", {
            "genres":         GENRES,
            "selected_genre": "",
            "featured":       [],
            "heading":        "New & Popular"
        })

    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]

    # helper to fetch top-3 cast via TMDB if our DB has none
    def fetch_cast_from_tmdb(title, kind):
        endpoint = "movie" if kind == "Movie" else "tv"
        # 1) search by title
        resp = requests.get(
            f"https://api.themoviedb.org/3/search/{endpoint}",
            params={"api_key": settings.TMDB_API_KEY, "query": title}
        )
        results = resp.json().get("results", [])
        if not results:
            return []
        tmdb_id = results[0]["id"]
        # 2) get credits
        credits_resp = requests.get(
            f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}/credits",
            params={"api_key": settings.TMDB_API_KEY}
        )
        cast_list = credits_resp.json().get("cast", [])[:3]
        # return only the names
        return [c.get("name") for c in cast_list if c.get("name")]

    # —— MOVIES pipeline (with credits lookup + top-3 cast) ——
    movies_pipeline = [
        {"$match":    { "genres.name": selected_genre }},
        {"$sort":     { "popularity": -1 }},
        {"$limit":    5},
        {"$lookup":   {
            "from":         "credits",
            "localField":   "_id",
            "foreignField": "movie_id",
            "as":           "cred"
        }},
        {"$addFields": {
            "topCast": { "$slice": [
                { "$map": {
                    "input": "$cred.cast", "as": "c", "in": "$$c.name"
                }},
                3
            ]}
        }},
        {"$project":  {
            "title":      1,
            "popularity": 1,
            "type":       { "$literal": "Movie" },
            "topCast":    1
        }}
    ]

    # —— TV SHOWS pipeline (no credits lookup) ——
    shows_pipeline = [
        {"$match":    { "genres": { "$regex": selected_genre, "$options": "i" } }},
        {"$sort":     { "popularity": -1 }},
        {"$limit":    5},
        {"$project":  {
            "title":      "$name",
            "popularity": 1,
            "type":       { "$literal": "TV Show" },
            "topCast":    { "$literal": [] }
        }}
    ]

    # —— UNION + global resort —— 
    pipeline = (
        movies_pipeline
        + [
            { "$unionWith": {
                "coll":     "tvshows",
                "pipeline": shows_pipeline
            }}
        ]
        + [
            { "$sort": { "popularity": -1 }}
        ]
    )

    featured = []
    for doc in db.movies.aggregate(pipeline):
        # strip out any falsy entries first, then fallback if still empty
        top_cast = [c for c in doc.get("topCast", []) if c]
        if not top_cast:
            top_cast = fetch_cast_from_tmdb(doc["title"], doc["type"])

        featured.append({
            "title":       doc["title"],
            "full_poster": fetch_poster_by_title(doc["title"]) or "",
            "type":        doc["type"],
            "top_cast":    top_cast
        })

    # —— USER WATCHLIST IN GENRE —— 
    uid = request.session.get("user_id")
    if uid:
        user = db.users.find_one({"_id": ObjectId(uid)})
        watch = user.get("watchlist", [])
        if watch:
            # filter titles by whether they belong to this genre
            filtered = []
            for title in watch:
                # check movie
                mv = db.movies.find_one({
                    "title": title,
                    "genres.name": selected_genre
                })
                # check tv show
                tv = db.tvshows.find_one({
                    "name": title,
                    "genres": { "$regex": selected_genre, "$options": "i" }
                })
                if mv:
                    filtered.append((title, "Movie"))
                elif tv:
                    filtered.append((title, "TV Show"))
            # take up to 5 random
            for title, kind in random.sample(filtered, min(5, len(filtered))):
                featured.append({
                    "title":       title,
                    "full_poster": fetch_poster_by_title(title) or "",
                    "type":        kind,
                    "top_cast":    []
                })

    client.close()

    return render(request, "new_popular.html", {
        "genres":         GENRES,
        "selected_genre": selected_genre,
        "featured":       featured,
        "heading":        "New & Popular"
    })



#--------------------------------------------------------------------------------------
# netflix_clone_app/views.py
import re


IMG_BASE = "https://image.tmdb.org/t/p/w500"


# ------------------------------------------ Browse By Language ------------------------------------


# from django.shortcuts import render
# from pymongo import MongoClient
# from bson import ObjectId
# import random


# @session_required
# def browsebylanguage(request):
#     lang = request.GET.get('lang', '').strip()

#     client = MongoClient('mongodb://localhost:27017/')
#     db     = client['mini_netflix']

#     # 1) pull up to 5 movie titles in that language
#     movies = []
#     if lang:
#         cursor = db.movies.aggregate([
#             {"$match": {"original_language": lang}},
#             {"$sample": {"size": 5}},
#             {"$project": {"_id": 0, "title": 1}}
#         ])
#         movies = [m['title'] for m in cursor]

#     # 2) pull up to 5 TV shows in that language (use 'name' field)
#     shows = []
#     if lang:
#         cursor = db.tvshows.aggregate([
#             {"$match": {"original_language": lang}},
#             {"$sample": {"size": 5}},
#             {"$project": {
#                 "_id":         0,
#                 "name":        1,
#                 "poster_path": 1,
#             }}
#         ])

#         for doc in cursor:
#             poster_path = doc.get("poster_path")
#             if isinstance(poster_path, str) and poster_path:
#                 full_poster = IMG_BASE + poster_path
#             else:
#                 full_poster = fetch_poster_by_title(doc["name"])

#             shows.append({
#                 "title":       doc["name"],
#                 "full_poster": full_poster
#             })

#     # 3) pull up to 5 from the user’s watchlist, filtered by selected language
#     user_list = []
#     uid = request.session.get('user_id')
#     if uid:
#         user = db.users.find_one({"_id": ObjectId(uid)})
#         watch = user.get('watchlist', [])
#         if watch:
#             if lang:
#                 # only keep watchlist titles that match the selected language
#                 filtered = []
#                 for t in watch:
#                     # check movies collection
#                     movie_match = db.movies.find_one({
#                         "title": t,
#                         "original_language": lang
#                     })
#                     # check tvshows collection
#                     show_match = db.tvshows.find_one({
#                         "name": t,
#                         "original_language": lang
#                     })
#                     if movie_match or show_match:
#                         filtered.append(t)
#                 user_list = random.sample(filtered, min(5, len(filtered)))
#             else:
#                 # no language filter: show any watchlist items
#                 user_list = random.sample(watch, min(5, len(watch)))

#     client.close()

#     # 4) build a combined list of up to 10 items
#     all_items = []
#     for t in movies:
#         all_items.append({"title": t, "source": "movie"})
#     for s in shows:
#         all_items.append({
#             "title":       s["title"],
#             "full_poster": s["full_poster"],
#             "source":      "show"
#         })
#     for t in user_list:
#         all_items.append({"title": t, "source": "watchlist"})

#     # cap to 10
#     all_items = all_items[:]

#     # 5) fetch posters for movies & watchlist
#     items = []
#     for entry in all_items:
#         if entry["source"] == "show":
#             items.append({
#                 "title":       entry["title"],
#                 "full_poster": entry["full_poster"]
#             })
#         else:
#             poster = fetch_poster_by_title(entry["title"])
#             if poster:
#                 items.append({
#                     "title":       entry["title"],
#                     "full_poster": poster
#                 })

#     # 6) render template
#     heading = f"Browse by Language — {lang.upper()}" if lang else "Browse by Languages"
#     return render(request, 'browsebylanguage.html', {
#         "items":         items,
#         "heading":       heading,
#         "selected_lang": lang,
#     })



# ------------------------------ multi query ----------------------------------------------------------

import itertools
from pymongo import MongoClient
from bson.objectid import ObjectId
from django.shortcuts import render

# ---------- Query Functions ----------
@session_required
def top_prolific_actors(db, limit=10):
    pipeline = [
        {"$unwind": "$cast"},
        {"$group": {"_id":"$cast.name", "count":{"$sum":1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"_id":0, "actor":"$_id", "moviesCount":"$count"}}
    ]
    return list(db.credits.aggregate(pipeline))
@session_required
def top_directors_by_revenue(db, limit=5):
    pipeline = [
        {"$unwind": "$crew"},
        {"$match": {"crew.job": "Director"}},
        {"$lookup": {
            "from": "movies",
            "localField": "movie_id",
            "foreignField": "_id",
            "as": "m"
        }},
        {"$unwind": "$m"},
        {"$group": {"_id":"$crew.name", "totalRevenue":{"$sum":"$m.revenue"}}},
        {"$sort": {"totalRevenue": -1}},
        {"$limit": limit},
        {"$project": {"_id":0, "director":"$_id", "totalRevenue":1}}
    ]
    return list(db.credits.aggregate(pipeline))
@session_required
def avg_runtime_by_genre(db):
    pipeline = [
        {"$unwind": "$genres"},
        {"$group": {"_id":"$genres.name", "avgRuntime":{"$avg":"$runtime"}, "count":{"$sum":1}}},
        {"$sort": {"avgRuntime": -1}},
        {"$project": {"_id":0, "genre":"$_id", "avgRuntime":1, "count":1}}
    ]
    return list(db.movies.aggregate(pipeline))
@session_required
def yearly_release_stats(db):
    pipeline = [
        # only keep well-formed ISO dates
        {"$match": {
            "release_date": {"$regex": r"^\d{4}-\d{2}-\d{2}$"}
        }},
        # now it's safe to take the first 4 chars and convert
        {"$addFields": {
            "year": {"$toInt": {"$substr": ["$release_date", 0, 4]}}
        }},
        {"$group": {
            "_id": "$year",
            "total": {"$sum": 1},
            "avgRevenue": {"$avg": "$revenue"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "_id": 0,
            "year": "$_id",
            "total": 1,
            "avgRevenue": 1
        }}
    ]
    return list(db.movies.aggregate(pipeline))

@session_required
def actor_coappearances(db, limit=10):
    co_counts = {}
    for doc in db.credits.find({}, {"cast.name":1}):
        cast = [c["name"] for c in doc.get("cast", [])]
        for a, b in itertools.combinations(sorted(set(cast)), 2):
            co_counts[(a, b)] = co_counts.get((a, b), 0) + 1
    sorted_pairs = sorted(co_counts.items(), key=lambda kv: kv[1], reverse=True)
    return [{"pair": f"{a} & {b}", "count": count}
            for (a, b), count in sorted_pairs[:limit]]
@session_required
def top_movies_per_director(db, top_n=3):
    pipeline = [
        {"$unwind": "$crew"},
        {"$match": {"crew.job": "Director"}},
        {"$lookup": {"from":"movies", "localField":"movie_id", "foreignField":"_id", "as":"m"}},
        {"$unwind": "$m"},
        {"$sort": {"crew.name":1, "m.revenue": -1}},
        {"$group": {"_id":"$crew.name", "topMovies":
             {"$push": {"title":"$m.title", "revenue":"$m.revenue"}}}},
        {"$project": {"director":"$_id",
                     "top3": {"$slice":["$topMovies", top_n]}, "_id":0}}
    ]
    return list(db.credits.aggregate(pipeline))

# ---------- View ----------
@session_required
def multi_query(request):
    """
    A single page that lets the user choose one of six
    pre-built MongoDB reports and displays its results.
    """
    # map url param → (human label, function)
    OPTIONS = {
        'actors':              ("Top 10 Prolific Actors",        top_prolific_actors),
        'directors':           ("Top 5 Directors by Revenue",    top_directors_by_revenue),
        'avg_runtime':         ("Average Runtime by Genre",      avg_runtime_by_genre),
        'yearly_stats':        ("Yearly Release Stats",          yearly_release_stats),
        'coappearances':       ("Top 10 Actor Co-Appearances",   actor_coappearances),
        'top_movies_director': ("Top 3 Movies per Director",     top_movies_per_director),
    }

    selected = request.GET.get('query', '')
    heading, results = "Select a report", []

    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]

    if selected in OPTIONS:
        heading = OPTIONS[selected][0]
        try:
            results = OPTIONS[selected][1](db)
        except Exception:
            results = []

    client.close()

    return render(request, "multiquery.html", {
        "options":      OPTIONS,
        "selected":     selected,
        "heading":      heading,
        "results":      results,
    })





# netflix_clone_app/views.py

from bson.objectid              import ObjectId
from django.shortcuts           import render, redirect
from django.contrib.auth.hashers import check_password, make_password
from pymongo                    import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client["mini_netflix"], client
@session_required
def change_password(request):
    """
    GET:  show password‐change form
    POST: validate old password + confirm, then hash & store new one
    """
    uid = request.session.get("user_id")
    if not uid:
        return redirect("login")

    db, client = get_db()
    user = db.users.find_one({"_id": ObjectId(uid)})

    error   = None
    success = None

    if request.method == "POST":
        old     = request.POST.get("old_password", "").strip()
        new     = request.POST.get("new_password", "").strip()
        confirm = request.POST.get("confirm_password", "").strip()

        if not (old and new and confirm):
            error = "All fields are required."
        elif new != confirm:
            error = "New passwords do not match."
        elif not check_password(old, user.get("password", "")):
            error = "Old password is incorrect."
        else:
            hashed = make_password(new)
            db.users.update_one(
                {"_id": ObjectId(uid)},
                {"$set": {"password": hashed}}
            )
            success = "Password updated successfully."

    client.close()
    return render(request, "change_password.html", {
        "error":   error,
        "success": success,
    })



# -- Delete Account -------------------------------------------------------
@session_required
@csrf_exempt
def delete_account(request):
    """
    POST → completely remove the user document and clear session
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    uid = request.session.get("user_id")
    if not uid:
        return HttpResponseForbidden("Not logged in")

    db, client = get_db()
    # delete the user
    db.users.delete_one({"_id": ObjectId(uid)})
    client.close()

    # clear session & redirect home
    request.session.flush()
    return JsonResponse({"status": "ok", "message": "Account deleted."})



#-------------------------------------- CRUD --------------------------------------------------
import json
from bson.objectid import ObjectId
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt




#------------------------ saving the images -------------------------
import re, json
from bson.binary       import Binary




@session_required
@csrf_exempt
def crud_list(request, coll):
    """
    GET  /api/<coll>/       → list all documents in collection
    POST /api/<coll>/       → insert a new document (body JSON)
    """
    db, client = get_db()
    if coll not in ("movies", "tvshows", "users", "credits"):
        client.close()
        return HttpResponseBadRequest("Unknown collection")

    collection = db[coll]

    if request.method == "GET":
        docs = list(collection.find({}))
        # convert ObjectId → str for JSON
        for d in docs:
            d["_id"] = str(d["_id"])
        client.close()
        return JsonResponse(docs, safe=False)

    elif request.method == "POST":
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            client.close()
            return HttpResponseBadRequest("Invalid JSON")

        # insert and return the new _id
        res = collection.insert_one(payload)
        client.close()
        return JsonResponse({"_id": str(res.inserted_id)})

    else:
        client.close()
        return HttpResponseNotAllowed(["GET", "POST"])

@session_required
@csrf_exempt
def crud_detail(request, coll, pk):
    """
    GET    /api/<coll>/<pk>/   → fetch one document
    PUT    /api/<coll>/<pk>/   → update one document (body JSON)
    DELETE /api/<coll>/<pk>/   → delete one document
    """
    db, client = get_db()
    if coll not in ("movies", "tvshows", "users", "credits"):
        client.close()
        return HttpResponseBadRequest("Unknown collection")

    try:
        oid = ObjectId(pk)
    except Exception:
        client.close()
        return HttpResponseBadRequest("Invalid document ID")

    collection = db[coll]

    if request.method == "GET":
        doc = collection.find_one({"_id": oid})
        if not doc:
            client.close()
            return JsonResponse({"error": "Not found"}, status=404)
        doc["_id"] = str(doc["_id"])
        client.close()
        return JsonResponse(doc)

    elif request.method == "PUT":
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            client.close()
            return HttpResponseBadRequest("Invalid JSON")
        # replace or set only provided fields
        collection.update_one({"_id": oid}, {"$set": payload})
        client.close()
        return JsonResponse({"status": "updated"})

    elif request.method == "DELETE":
        collection.delete_one({"_id": oid})
        client.close()
        return JsonResponse({"status": "deleted"})

    else:
        client.close()
        return HttpResponseNotAllowed(["GET", "PUT", "DELETE"])




#------------------------------- CRUD OPERATION -------------------------------------
import json
from bson.objectid       import ObjectId
from django.shortcuts    import render, redirect
from pymongo             import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client["mini_netflix"], client

import os
import re
import json
import math

from bson import ObjectId
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from pymongo import MongoClient

# your existing imports for session_required, text_search, semantic_re_rank, fetch_poster_by_title...


def save_uploaded_image(db, ref_id, image_file, coll_name):
    """
    Save an uploaded InMemoryUploadedFile into MEDIA_ROOT/<coll_name>/
    and record its public URL in movie_tvshow_collection.
    """
    if not image_file:
        return

    # ensure the subfolder exists
    subdir = coll_name
    dest_dir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(dest_dir, exist_ok=True)

    # build a filename
    original_name = image_file.name
    _, ext = os.path.splitext(original_name)
    filename = f"{ref_id}{ext}"
    full_path = os.path.join(dest_dir, filename)

    # write the file in chunks
    with open(full_path, "wb") as out:
        for chunk in image_file.chunks():
            out.write(chunk)

    # build the public URL
    public_url = settings.MEDIA_URL + f"{subdir}/{filename}"

    # upsert into our custom collection
    db.movie_tvshow_collection.update_one(
    { "ref_id": str(ref_id), "type": coll_name },    # <-- rename `id` → `ref_id`
    { "$set": {"image": public_url} },               # <-- still a string, so you must loosen the schema too
    upsert=True
)



def crud(request):
    """
    POST /crud          (the HTML form also supports GET for an empty page)

    A single admin endpoint that performs **C**reate–**R**ead–**U**pdate–**D**elete
    against the three core content collections.  The view is generic and
    drives itself entirely from form fields (`collection`, `operation`, etc.).

    ─── Collections Touched ────────────────────────────────────────────────
      • movies     – main catalogue of films (large JSON payload per doc)
      • tvshows    – episodic/series catalogue
      • credits    – TMDB‑style cast/crew blobs keyed by `movie_id`
      • movie_tvshow_collection
                    – out‑of‑band records that map `ref_id` → custom poster
      • (settings.MEDIA_ROOT/{movies|tvshows|credits}/...)  – file system
        where uploaded images are stored and removed

    ─── Supported Operations ──────────────────────────────────────────────
      • READ    – case‑insensitive exact title/name match; returns JSON
      • DELETE  – same match, then:
                    – deletes Mongo doc
                    – deletes associated poster record
                    – removes file from disk (best‑effort)
      • INSERT  – builds a brand‑new document from <collection>_<field> form
                  inputs; if an image is uploaded it is saved via
                  `save_uploaded_image()` and linked in
                  *movie_tvshow_collection*.
      • UPDATE  – locates an existing doc by key, applies `$set` with the new
                  payload, optionally replaces any existing poster image
                  (old DB record and file are purged).

    ─── Image Handling Workflow ───────────────────────────────────────────
      1. Upload via `<input type="file" name="<collection>_image">`
      2. `save_uploaded_image()` stores file under
         `MEDIA_ROOT/<collection>/<uuid>.ext` and writes a companion record:
           {
             "ref_id": <Mongo _id>,
             "type":   "<collection>",
             "image":  "/media/<collection>/<uuid>.ext"
           }
      3. On UPDATE with a new file, the previous record & file are deleted.

    ─── Validation & Edge‑cases ───────────────────────────────────────────
      • Key lookup uses `title` (movies/credits) or `name` (tvshows).  
      • Numeric fields are cast to int/float with 0 fallback; JSON blobs are
        parsed from hidden inputs containing `[{"id":...,"name":...}, …]`.  
      • All destructive file ops (`os.remove`) are wrapped in try/except to
        avoid breaking the HTTP response on I/O errors.

    ─── Response ──────────────────────────────────────────────────────────
      Renders *crud.html* with either:
        • message – human‑readable result of the operation, or
        • result  – JSON document for READ.
    """
    # ——— FUNCTION BODY UNCHANGED ———

    db, client = get_db()
    msg    = None
    result = None

    if request.method == "POST":
        coll_name  = request.POST["collection"]
        op         = request.POST["operation"]
        coll       = db[coll_name]

        # grab any uploaded file for insert/update
        image_file = request.FILES.get(f"{coll_name}_image") if op in ("insert","update") else None

        # key lookup field
        key_field  = "title" if coll_name in ("movies","credits") else "name"
        key_val    = request.POST.get("key","").strip()

        # READ
        if op == "read":
            pattern = re.compile(rf'^{re.escape(key_val)}$', re.IGNORECASE)
            result  = coll.find_one({key_field: pattern}) or {}

        # DELETE
        elif op == "delete":
            pattern = re.compile(rf'^{re.escape(key_val)}$', re.IGNORECASE)
            doc_to_del = coll.find_one({key_field: pattern})
            if doc_to_del:
                res = coll.delete_one({key_field: pattern})

                # remove file on disk
                try:
                    rec = db.movie_tvshow_collection.find_one({
                        "ref_id": str(doc_to_del["_id"]),
                        "type": coll_name
                    })
                    if rec and rec.get("image"):
                        filename = os.path.basename(rec["image"])
                        path = os.path.join(settings.MEDIA_ROOT, coll_name, filename)
                        if os.path.exists(path):
                            os.remove(path)
                except Exception:
                    pass

                # remove any associated image record
                db.movie_tvshow_collection.delete_many({
                    "ref_id": str(doc_to_del["_id"]),
                    "type": coll_name
                })
                
                msg = f"Deleted {res.deleted_count} document(s) and removed associated image."
            else:
                msg = "No matching document found to delete."

        # INSERT / UPDATE
        elif op in ("insert","update"):
            # build document
            doc = {}
            if coll_name == "movies":
                doc = {
                    "title":             request.POST["movies_title"],
                    "original_title":    request.POST["movies_original_title"],
                    "overview":          request.POST.get("movies_overview","").strip(),
                    "budget":            int(request.POST.get("movies_budget") or 0),
                    "popularity":        float(request.POST.get("movies_popularity") or 0),
                    "release_date":      request.POST.get("movies_release_date",""),
                    "status":            request.POST.get("movies_status",""),
                    "tagline":           request.POST.get("movies_tagline",""),
                    "homepage":          request.POST.get("movies_homepage",""),
                    "runtime":           int(request.POST.get("movies_runtime") or 0),
                    "revenue":           int(request.POST.get("movies_revenue") or 0),
                    "original_language": request.POST.get("movies_original_language",""),
                    "vote_average":      float(request.POST.get("movies_vote_average") or 0),
                    "vote_count":        int(request.POST.get("movies_vote_count") or 0),
                    "genres":            json.loads(request.POST.get("movies_genres_json") or "[]"),
                    "keywords":          json.loads(request.POST.get("movies_keywords_json") or "[]"),
                    "production_companies": json.loads(request.POST.get("movies_prod_comp_json") or "[]"),
                    "production_countries": json.loads(request.POST.get("movies_prod_ctry_json") or "[]"),
                }
            elif coll_name == "tvshows":
                doc = {
                    "name":               request.POST["tvshows_name"],
                    "original_name":      request.POST["tvshows_original_name"],
                    "overview":           request.POST.get("tvshows_overview","").strip(),
                    "number_of_seasons":  int(request.POST.get("tvshows_number_of_seasons") or 0),
                    "number_of_episodes": int(request.POST.get("tvshows_number_of_episodes") or 0),
                    "first_air_date":     request.POST.get("tvshows_first_air_date",""),
                    "last_air_date":      request.POST.get("tvshows_last_air_date",""),
                    "status":             request.POST.get("tvshows_status",""),
                    "tagline":            request.POST.get("tvshows_tagline",""),
                    "homepage":           request.POST.get("tvshows_homepage",""),
                    "type":               request.POST.get("tvshows_type",""),
                    "in_production":      request.POST.get("tvshows_in_production")=="on",
                    "popularity":         float(request.POST.get("tvshows_popularity") or 0),
                    "vote_average":       float(request.POST.get("tvshows_vote_average") or 0),
                    "vote_count":         int(request.POST.get("tvshows_vote_count") or 0),
                    "original_language":  request.POST.get("tvshows_original_language",""),
                    "genres":             json.loads(request.POST.get("tvshows_genres_json") or "[]"),
                    "created_by":         request.POST.get("tvshows_created_by",""),
                    "languages":          json.loads(request.POST.get("tvshows_languages_json") or "[]"),
                    "networks":           json.loads(request.POST.get("tvshows_networks_json") or "[]"),
                    "origin_country":     request.POST.get("tvshows_origin_country",""),
                    "spoken_languages":   json.loads(request.POST.get("tvshows_spoken_languages_json") or "[]"),
                    "episode_run_time":   int(request.POST.get("tvshows_episode_run_time") or 0),
                    "production_companies": json.loads(request.POST.get("tvshows_prod_comp_json") or "[]"),
                    "production_countries": json.loads(request.POST.get("tvshows_prod_ctry_json") or "[]"),
                }
            elif coll_name == "credits":
                doc = {
                    "title":    request.POST.get("credits_title",""),
                    "movie_id": int(request.POST.get("credits_movie_id") or 0),
                    "cast":     json.loads(request.POST.get("credits_cast_json") or "[]"),
                    "crew":     json.loads(request.POST.get("credits_crew_json") or "[]"),
                }

            if op == "insert":
                res = coll.insert_one(doc)
                save_uploaded_image(db, res.inserted_id, image_file, coll_name)
                msg = "Inserted successfully."
            else:
                # fetch existing doc _id
                query = {key_field: key_val}
                existing = coll.find_one(query)
                if existing:
                    existing_id = existing["_id"]
                    upd = coll.update_one(query, {"$set": doc})

                    if image_file:
                        # delete old image record
                        db.movie_tvshow_collection.delete_many({
                            "ref_id": str(existing_id),
                            "type": coll_name
                        })
                        # delete old file on disk
                        try:
                            old_rec = existing
                            if old_rec.get("image"):
                                fname = os.path.basename(old_rec["image"])
                                path = os.path.join(settings.MEDIA_ROOT, coll_name, fname)
                                if os.path.exists(path):
                                    os.remove(path)
                        except Exception:
                            pass
                        # save new image
                        save_uploaded_image(db, existing_id, image_file, coll_name)

                    msg = f"Matched={upd.matched_count}, Modified={upd.modified_count}"
                else:
                    msg = "No document found to update."

    client.close()
    return render(request, "crud.html", {
        "message": msg,
        "result":  result,
    })




# ---------------- remove the movies or tvshows from the mylist ------------------------------------------


import json
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from bson import ObjectId
from pymongo import MongoClient

@session_required
@require_POST
def remove_from_list(request):
    uid = request.session.get("user_id")
    if not uid:
        return HttpResponseBadRequest("Login required")

    body = json.loads(request.body.decode("utf-8") or "{}")
    title = body.get("title")
    if not title:
        return HttpResponseBadRequest("Missing title")

    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]

    db.users.update_one(
        {"_id": ObjectId(uid)},
        {"$pull": {"watchlist": title}}
    )
    client.close()

    return JsonResponse({"status":"ok"})



# ---------------------------------- visualization -------------------------------

# views.py
from django.shortcuts import render
from bson import ObjectId
from pymongo import MongoClient

from collections import Counter
from django.shortcuts import render
from bson.objectid import ObjectId
from pymongo import MongoClient
from .services.remote_visualization import (
    fallback_top_actors,
    fallback_top_directors,
    fallback_avg_runtime,
    fallback_yearly_stats,
    fallback_actor_coappearances,
    fallback_top3_movies
)

@session_required
def visualization(request):
    """
    GET /visualization?query=<report_key>

    Interactive analytics endpoint that powers the “Visualizations” page.
    It offers six canned reports, tries to answer each straight from MongoDB,
    and gracefully degrades to local Python / ML helpers when the catalogue
    lacks enough signal.

    ─── Collections Touched ────────────────────────────────────────────────
      • movies   – primary source for casts, revenues, runtimes, dates, etc.
      • users    – harvested to build a union of all watch‑lists (fallback
                   context when no aggregate data is available)

    ─── Supported Reports & Pipelines ──────────────────────────────────────
      key = "top_actors"
        • Mongo: `$unwind $cast → $group by $cast.name → sort/limit 10`
        • Fallback: `fallback_top_actors()` embeds all watch‑list titles,
          retrieves actor metadata via TMDB API, clusters with FAISS to handle
          name variants, then counts appearances.
        • Chart: vertical bar “Appearances”.

      key = "top_directors"
        • Mongo: `$group by $director → Σ revenue → sort/limit 5`
        • Fallback: same idea, but revenue scraped via Grok LLM if missing.
        • Chart: vertical bar “Total Revenue”.

      key = "avg_runtime"
        • Mongo: `$unwind $genres → avg $runtime per genre`
        • Fallback: derives runtimes from IMDb using an
          OpenAI function‑calling prompt chain if local data is sparse.
        • Chart: horizontal bar.

      key = "yearly_stats"
        • Mongo: regex‑match `release_date` → count per year
        • Fallback: uses embeddings‑based fuzzy year extraction from plot
          synopses when dates are incomplete.
        • Chart: line graph.

      key = "actor_coappearances"
        • Python: brute‑force pair counting over `$cast.name` in *movies*
          (no native pipeline fits this pattern efficiently).
        • Fallback: cosine‑similarity clustering on actor embeddings to merge
          aliases before counting.
        • Chart: bar “Co‑Appearances”.

      key = "top3_movies"
        • Mongo: `distinct("director")` then per‑director `$sort revenue -1,
          limit 3`.
        • Fallback: Grok LLM fetches missing revenue and ranks if local
          numbers are zero.
        • Chart: bar.

    ─── Fallback Strategy (High‑Level ML) ──────────────────────────────────
      • Each `fallback_*` helper first embeds the watch‑list titles with a
        Sentence‑Transformers model, indexes them in FAISS, then pulls in
        external metadata (TMDB / IMDb) or invokes a GPT‑4‑Turbo function
        call to fill gaps.  The final stats mirror the structure expected by
        the primary pipeline so the front‑end remains unchanged.

    ─── Chart Generation ──────────────────────────────────────────────────
      A lightweight Chart.js config object (`chart_config`) is assembled for
      every successful query; the front‑end template injects it as‑is into a
      `<canvas>` element for instant rendering.

    ─── Security ──────────────────────────────────────────────────────────
      Guarded by `@session_required`; if the user is not signed in, the view
      still works but builds its fallback corpus by concatenating every user’s
      watch‑list in the database.

    ─── Template Context ─────────────────────────────────────────────────
      Renders *visualization.html* with:
        • options       – map of human‑readable report names
        • selected      – current `query` key
        • heading       – pretty title for the page
        • table_data    – rows for an HTML table
        • chart_config  – ready‑to‑serialize Chart.js spec
    """
    # ——— FUNCTION BODY UNCHANGED ———

    client = MongoClient("mongodb://localhost:27017/")
    db     = client["mini_netflix"]

    options = {
        "top_actors":          "Top 10 Prolific Actors",
        "top_directors":       "Top 5 Directors by Revenue",
        "avg_runtime":         "Average Runtime by Genre",
        "yearly_stats":        "Yearly Release Stats",
        "actor_coappearances": "Top 10 Actor Co-Appearances",
        "top3_movies":         "Top 3 Movies per Director",
    }

    query   = request.GET.get("query","")
    heading = options.get(query,"")
    table   = []
    labels  = []
    values  = []
    chart   = {}

    # gather watchlist titles
    uid = request.session.get("user_id")
    if uid:
        user = db.users.find_one({"_id": ObjectId(uid)}, {"watchlist":1}) or {}
        titles = user.get("watchlist",[])
    else:
        titles = []
        for u in db.users.find({},{"watchlist":1}):
            wl = u.get("watchlist",[])
            if isinstance(wl,list):
                titles.extend(wl)

    # each report: try Mongo first, else fallback
    if query == "top_actors":
        pipe = [
            {"$unwind":"$cast"},
            {"$group":{"_id":"$cast.name","appearances":{"$sum":1}}},
            {"$sort":{"appearances":-1}},
            {"$limit":10}
        ]
        agg = list(db.movies.aggregate(pipe))
        table = [{"actor":d["_id"],"appearances":d["appearances"]} for d in agg]
        if not table:
            table, labels, values = fallback_top_actors(titles)
        else:
            labels = [r["actor"]      for r in table]
            values = [r["appearances"] for r in table]

        chart = {
            "type":"bar",
            "data":{"labels":labels,"datasets":[{"label":"Appearances","data":values}]},
            "options":{"scales":{"y":{"beginAtZero":True}}}
        }

    elif query == "top_directors":
        pipe = [
            {"$group":{"_id":"$director","revenue":{"$sum":"$revenue"}}},
            {"$sort":{"revenue":-1}},
            {"$limit":5}
        ]
        agg = list(db.movies.aggregate(pipe))
        table = [{"director":d["_id"],"revenue":d["revenue"]} for d in agg]
        if not table:
            table, labels, values = fallback_top_directors(titles)
        else:
            labels = [r["director"] for r in table]
            values = [r["revenue"]  for r in table]

        chart = {
            "type":"bar",
            "data":{"labels":labels,"datasets":[{"label":"Total Revenue","data":values}]},
            "options":{"scales":{"y":{"beginAtZero":True}}}
        }

    elif query == "avg_runtime":
        pipe = [
            {"$unwind":"$genres"},
            {"$group":{"_id":"$genres.name","avg_runtime":{"$avg":"$runtime"}}},
            {"$sort":{"avg_runtime":-1}}
        ]
        agg = list(db.movies.aggregate(pipe))
        table = [{"genre":d["_id"],"avg_runtime":round(d["avg_runtime"],1)} for d in agg]
        if not table:
            table, labels, values = fallback_avg_runtime(titles)
        else:
            labels = [r["genre"]       for r in table]
            values = [r["avg_runtime"] for r in table]

        chart = {
            "type":"bar",
            "data":{"labels":labels,"datasets":[{"label":"Avg Runtime","data":values}]},
            "options":{"indexAxis":"y","scales":{"x":{"beginAtZero":True}}}
        }

    elif query == "yearly_stats":
        pipe = [
            {"$match":{"release_date":{"$regex":r"^\d{4}-"}}},
            {"$group":{"_id":{"$substr":["$release_date",0,4]},"count":{"$sum":1}}},
            {"$sort":{"_id":1}}
        ]
        agg = list(db.movies.aggregate(pipe))
        table = [{"year":int(d["_id"]),"count":d["count"]} for d in agg]
        if not table:
            table, labels, values = fallback_yearly_stats(titles)
        else:
            labels = [r["year"] for r in table]
            values = [r["count"] for r in table]

        chart = {
            "type":"line",
            "data":{"labels":labels,"datasets":[{"label":"Releases","data":values,"fill":False}]},
            "options":{"scales":{"y":{"beginAtZero":True}}}
        }

    elif query == "actor_coappearances":
        co  = Counter()
        for mv in db.movies.find({},{"cast.name":1}):
            names = [c["name"] for c in mv.get("cast",[]) if c.get("name")]
            for i in range(len(names)):
                for j in range(i+1,len(names)):
                    key = tuple(sorted([names[i],names[j]]))
                    co[key] += 1
        top = co.most_common(10)
        table = [{"pair":f"{a} & {b}","count":c} for (a,b),c in top]
        if not table:
            table, labels, values = fallback_actor_coappearances(titles)
        else:
            labels = [r["pair"] for r in table]
            values = [r["count"] for r in table]

        chart = {
            "type":"bar",
            "data":{"labels":labels,"datasets":[{"label":"Co-Appearances","data":values}]},
            "options":{"scales":{"y":{"beginAtZero":True}}}
        }

    elif query == "top3_movies":
        table, flat = [], []
        for d in db.movies.distinct("director"):
            top3 = list(db.movies
                .find({"director":d},{"title":1,"revenue":1})
                .sort("revenue",-1).limit(3))
            for m in top3:
                t_,r_ = m.get("title"), m.get("revenue",0) or 0
                table.append({"director":d,"title":t_,"revenue":r_})
                flat.append((f"{d}: {t_}", r_))

        if not table:
            table, labels, values = fallback_top3_movies(titles)
        else:
            labels, values = zip(*flat) if flat else ([],[])

        chart = {
            "type":"bar",
            "data":{"labels":list(labels),"datasets":[{"label":"Revenue","data":list(values)}]},
            "options":{"scales":{"y":{"beginAtZero":True}}}
        }

    else:
        chart = {}

    client.close()
    return render(request, "visualization.html", {
        "options":      options,
        "selected":     query,
        "heading":      heading,
        "table_data":   table,
        "chart_config": chart,
    })







# -------------------------------- detail API -------------------------------


@session_required
def detail_api(request, title):
    """
    GET /api/detail/<title>

    Fetches a fully‑hydrated metadata record for a single title, using a
    *local‑first, API‑fallback* strategy.

    ─── Collections Touched ────────────────────────────────────────────────
      • movies     – primary lookup by `title`
      • tvshows    – secondary lookup by `name`
      • credits    – cast/crew blobs keyed by the same title

    ─── Retrieval Flow ────────────────────────────────────────────────────
      1. **Local catalogue first**  
         – Try *movies*, then *tvshows*.  
         – If neither found → `404`.

      2. **Seed the response**  
         Build a minimal `data` dict with `overview`, `original_language`,
         best‑effort poster (`poster_path` → TMDB base URL), and empty
         `cast/crew` arrays.

      3. **Local credits enrichment**  
         Pull cast & crew from the *credits* collection where `title` matches
         exactly (case sensitive‑ish).

      4. **TMDB fallback**  
         If any of *poster*, *cast*, or *crew* is still missing, call
         `fetch_from_tmdb()`.  
         • This helper hits TMDB’s REST API, then uses an OpenAI
           function‑calling prompt to normalise JSON keys and de‑duplicate
           names via cosine‑similarity on actor embeddings inside a FAISS
           index.  
         • Only the missing fields are overwritten, preserving any local
           overrides.

    ─── Response Schema ───────────────────────────────────────────────────
      {
        "title":      str,
        "overview":   str,
        "genres":     list[str],
        "collection": "Movie" | "TV Show",
        "poster":     str | null,    # full URL
        "cast":       list[dict],    # TMDB cast objects
        "crew":       list[dict],    # TMDB crew objects
        "language":   str            # ISO‑639‑1
      }

    ─── Security ──────────────────────────────────────────────────────────
      Protected by `@session_required`; anonymous users receive a 401.
    """
    # ——— FUNCTION BODY UNCHANGED ———

    db, client = get_db()

    # 1) try your Mongo movies → tvshows
    doc = db.movies.find_one({"title": title})
    kind = "Movie"
    if not doc:
        doc  = db.tvshows.find_one({"name": title})
        kind = "TV Show"
    if not doc:
        client.close()
        raise Http404("Not found")

    # 2) seed from local
    data = {
        "title":      doc.get("title") or doc.get("name"),
        "overview":   doc.get("overview", ""),
        "genres":     [],
        "collection": kind,
        "poster":     doc.get("poster") or
                      ( "https://image.tmdb.org/t/p/w500"+doc.get("poster_path", "") 
                        if doc.get("poster_path") else None
                      ),
        "cast":       [],
        "crew":       [],
        "language":   doc.get('original_language'),
    }

    # 3) local credits
    cred = db.credits.find_one({"title": data["title"]})
    if cred:
        data["cast"] = cred.get("cast", [])
        data["crew"] = cred.get("crew", [])

    client.close()

    # 4) if any of poster / cast / crew missing → TMDb fallback
    if not data["poster"] or not data["cast"] or not data["crew"]:
        tmdb = fetch_from_tmdb(data["title"], kind)
        # only overwrite missing pieces
        data["overview"] = tmdb.get("overview", data["overview"])
        data["genres"]   = tmdb.get("genres",   data["genres"])
        data["poster"]   = tmdb.get("poster",   data["poster"])
        data["cast"]     = tmdb.get("cast",     data["cast"])
        data["crew"]     = tmdb.get("crew",     data["crew"])

    return JsonResponse(data)


