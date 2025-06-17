import requests
from collections import Counter, defaultdict
from django.conf import settings

TMDB_KEY = settings.TMDB_API_KEY
BASE_URL  = "https://api.themoviedb.org/3"

def _search_tmdb(title: str, kind: str):
    """Return the first TMDb result for a movie or TV show by title."""
    url = f"{BASE_URL}/search/{ 'movie' if kind=='movie' else 'tv' }"
    r = requests.get(url, params={"api_key": TMDB_KEY, "query": title, "page": 1})
    results = r.json().get("results", [])
    return results[0] if results else None

def _get_credits(tmd_id: int, kind: str):
    """Return credits JSON for a given TMDb movie/tv id."""
    url = f"{BASE_URL}/{kind}/{tmd_id}/credits"
    r = requests.get(url, params={"api_key": TMDB_KEY})
    return r.json()

def _get_details(tmd_id: int, kind: str):
    """Return details JSON for a given TMDb movie/tv id."""
    url = f"{BASE_URL}/{kind}/{tmd_id}"
    r = requests.get(url, params={"api_key": TMDB_KEY})
    return r.json()

def fallback_top_actors(titles):
    cnt = Counter()
    for t in titles:
        res = _search_tmdb(t, "movie")
        if not res: continue
        creds = _get_credits(res["id"], "movie").get("cast", [])
        for c in creds:
            name = c.get("name")
            if name:
                cnt[name] += 1
    top10 = cnt.most_common(10)
    table = [{"actor": a, "appearances": v} for a,v in top10]
    labels = [a for a,_ in top10]
    values = [v for _,v in top10]
    return table, labels, values

def fallback_top_directors(titles):
    revs = Counter()
    for t in titles:
        res = _search_tmdb(t, "movie")
        if not res: continue
        creds = _get_credits(res["id"], "movie").get("crew", [])
        det   = _get_details(res["id"], "movie")
        revenue = det.get("revenue", 0) or 0
        for c in creds:
            if c.get("job")=="Director" and c.get("name"):
                revs[c["name"]] += revenue
    top5 = revs.most_common(5)
    table = [{"director": d, "revenue": r} for d,r in top5]
    labels = [d for d,_ in top5]
    values = [r for _,r in top5]
    return table, labels, values

def fallback_avg_runtime(titles):
    sums, counts = defaultdict(int), defaultdict(int)
    for t in titles:
        res = _search_tmdb(t, "movie")
        if not res: continue
        det = _get_details(res["id"], "movie")
        rt  = det.get("runtime")
        if rt is None:
            ert = det.get("episode_run_time", [])
            rt  = ert[0] if isinstance(ert,list) and ert else 0
        for g in det.get("genres", []):
            name = g.get("name")
            if name:
                sums[name]   += rt or 0
                counts[name] += 1
    rows = []
    for g in sums:
        if counts[g]:
            avg = round(sums[g]/counts[g],1)
            rows.append({"genre": g, "avg_runtime": avg})
    rows.sort(key=lambda x: x["avg_runtime"], reverse=True)
    labels = [r["genre"] for r in rows]
    values = [r["avg_runtime"] for r in rows]
    return rows, labels, values

def fallback_yearly_stats(titles):
    years = Counter()
    for t in titles:
        # try movie then tv
        for kind in ("movie","tv"):
            res = _search_tmdb(t, kind)
            if not res: continue
            det = _get_details(res["id"], kind)
            rd  = det.get("release_date") or det.get("first_air_date") or ""
            try:
                y = int(rd.split("-")[0])
            except:
                continue
            years[y] += 1
            break
    table = [{"year": y, "count": years[y]} for y in sorted(years)]
    labels = [r["year"] for r in table]
    values = [r["count"] for r in table]
    return table, labels, values

def fallback_actor_coappearances(titles):
    pairs = Counter()
    for t in titles:
        res = _search_tmdb(t, "movie")
        if not res: continue
        creds = _get_credits(res["id"], "movie").get("cast", [])
        names = [c["name"] for c in creds if c.get("name")]
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                key = tuple(sorted([names[i],names[j]]))
                pairs[key] += 1
    top10 = pairs.most_common(10)
    table = [{"pair": f"{a} & {b}", "count": c} for (a,b),c in top10]
    labels = [f"{a} & {b}" for (a,b),_ in top10]
    values = [c for _,c in top10]
    return table, labels, values

def fallback_top3_movies(titles):
    group = defaultdict(list)
    for t in titles:
        res = _search_tmdb(t, "movie")
        if not res: continue
        creds = _get_credits(res["id"], "movie").get("crew", [])
        det   = _get_details(res["id"], "movie")
        rev   = det.get("revenue", 0) or 0
        for c in creds:
            if c.get("job")=="Director" and c.get("name"):
                group[c["name"]].append((t, rev))
    table, flat = [], []
    for d, lst in group.items():
        for title, rev in sorted(lst, key=lambda x: x[1], reverse=True)[:3]:
            table.append({"director": d, "title": title, "revenue": rev})
            flat.append({"label": f"{d}: {title}", "value": rev})
    return table, [f["label"] for f in flat], [f["value"] for f in flat]
