#!/usr/bin/env python3
"""Create/update the Spotify playlists from data/*.json. Idempotent:
slug -> playlist id is stored in spotify_playlists.json; reruns replace
the playlist contents instead of duplicating. Stdlib only.

Usage: python3 tools/spotify_publish.py [slug ...]   (no args = all)
"""
import base64
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# python.org builds lack root certs; fall back to the macOS system bundle
_cafile = "/etc/ssl/cert.pem" if Path("/etc/ssl/cert.pem").exists() else None
SSL_CTX = ssl.create_default_context(cafile=_cafile)

ROOT = Path(__file__).parent.parent
SECRETS = json.loads((ROOT / ".secrets.json").read_text())
MAP_FILE = ROOT / "spotify_playlists.json"
API = "https://api.spotify.com/v1"

# one-sentence description per playlist, set on the Spotify playlist at create
DESCRIPTIONS = {
    "70s-party": "Disco, funk and glitter — a full 70s night, from ABBA and "
                 "Bowie to the Bee Gees and Michael Jackson.",
    "y2k-party": "2000s chart heat — Eminem, 50 Cent, Usher and low-rise-jeans pop.",
    "gay-club-anthems": "Certified dancefloor liberation, no skips allowed.",
    "arab-house": "Arabic vocals riding house grooves — the crossover set.",
    "diwali-after": "The afterparty set — Bollywood and Punjabi bangers back to back.",
    "general-pop": "The crowd-pleaser set — disco classics to Tyler to Fred again.",
    "south-asian": "Desi party pool, wedding-tier energy start to finish.",
    "stuff-i-like": "My personal rotation — house-leaning with Arabic accents.",
    "dnb-garage": "UK rollers — drum and bass and garage cuts.",
    "lvl": "Reggaeton and Latin heat, Bad Bunny-forward.",
    "reda": "Deep, rolling minimal house — a set built for a friend.",
}


def refresh_access_token():
    basic = base64.b64encode(
        f"{SECRETS['client_id']}:{SECRETS['client_secret']}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": SECRETS["refresh_token"]}).encode(),
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"})
    return json.loads(
        urllib.request.urlopen(
            req, context=SSL_CTX, timeout=30).read())["access_token"]


TOKEN = None


def call(method, path, body=None, params=None, retries=3):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(
        url, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as r:
                data = r.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # cap Retry-After: Spotify can return minutes-long values that
                # would silently freeze the whole run
                wait = min(int(e.headers.get("Retry-After", "2")) + 1, 20)
                print(f"   [rate-limited, waiting {wait}s]", flush=True)
                time.sleep(wait)
                continue
            if e.code >= 500 and attempt < retries - 1:
                time.sleep(2)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            # network stall / timeout — retry rather than hang forever
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise RuntimeError(f"network error on {method} {path}: {e}")
    raise RuntimeError(f"gave up on {method} {path}")


def find_track(artist, title):
    """Search catalog; returns (uri, 'Artist — Title') or (None, None)."""
    queries = []
    if artist and title:
        queries.append(f'track:"{title}" artist:"{artist}"')
        queries.append(f"{artist} {title}")
    queries.append(title or artist or "")
    for q in queries:
        if not q.strip():
            continue
        try:
            res = call("GET", "/search",
                       params={"q": q, "type": "track", "limit": 1})
        except RuntimeError as e:
            # persistent rate-limit / network fail on this query — count as a
            # miss instead of crashing the whole run
            print(f"   [search failed: {e}]", flush=True)
            return None, None
        items = res.get("tracks", {}).get("items", [])
        if items:
            t = items[0]
            label = f"{t['artists'][0]['name']} — {t['name']}"
            return t["uri"], label
    return None, None


def main():
    global TOKEN
    TOKEN = refresh_access_token()
    me = call("GET", "/me")
    print(f"Authed as {me.get('display_name') or me['id']}")

    mapping = json.loads(MAP_FILE.read_text()) if MAP_FILE.exists() else {}
    only = set(sys.argv[1:])

    for f in sorted((ROOT / "data").glob("*.json")):
        if f.name == "index.json":
            continue
        pl = json.loads(f.read_text())
        if only and pl["slug"] not in only:
            continue

        # skip playlists already populated on Spotify (resume across runs)
        entry = mapping.get(pl["slug"])
        if entry:
            existing = call("GET", f"/playlists/{entry['id']}/items",
                            params={"limit": 1}).get("total", 0)
            if existing > 0:
                print(f"{pl['slug']}: already filled ({existing} items), skip "
                      f"-> {entry['url']}", flush=True)
                continue

        print(f"{pl['slug']}: searching {pl['track_count']} tracks…", flush=True)
        uris, misses = [], []
        for t in pl["tracks"]:
            uri, label = find_track(t["artist"], t["title"])
            if uri and uri not in uris:
                uris.append(uri)
            elif not uri:
                misses.append(f"{t['artist'] or '?'} — {t['title']}")
            time.sleep(0.1)

        if entry:
            pid = entry["id"]
        else:
            # /users/{id}/playlists 403s on new dev-mode apps; /me/playlists works
            created = call("POST", "/me/playlists", body={
                "name": pl["name"], "public": True,
                "description": DESCRIPTIONS.get(pl["slug"], "")})
            pid = created["id"]
            mapping[pl["slug"]] = {"id": pid,
                                   "url": created["external_urls"]["spotify"]}
            MAP_FILE.write_text(json.dumps(mapping, indent=2) + "\n")

        # /tracks was removed in Spotify's March 2026 migration; use /items
        call("PUT", f"/playlists/{pid}/items", body={"uris": uris[:100]})
        for i in range(100, len(uris), 100):
            call("POST", f"/playlists/{pid}/items", body={"uris": uris[i:i+100]})

        print(f"{pl['slug']}: {len(uris)}/{pl['track_count']} matched -> "
              f"{mapping[pl['slug']]['url']}", flush=True)
        for m in misses:
            print(f"   miss: {m}", flush=True)


if __name__ == "__main__":
    main()
