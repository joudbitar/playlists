#!/usr/bin/env python3
"""Create/update the Spotify playlists from data/*.json. Idempotent:
slug -> playlist id is stored in spotify_playlists.json; reruns replace
the playlist contents instead of duplicating. Stdlib only.

Usage: python3 tools/spotify_publish.py [slug ...]   (no args = all)
"""
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
SECRETS = json.loads((ROOT / ".secrets.json").read_text())
MAP_FILE = ROOT / "spotify_playlists.json"
API = "https://api.spotify.com/v1"


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
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


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
            with urllib.request.urlopen(req) as r:
                data = r.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", "2")) + 1)
                continue
            if e.code >= 500 and attempt < retries - 1:
                time.sleep(2)
                continue
            raise
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
        res = call("GET", "/search", params={"q": q, "type": "track", "limit": 1})
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

        uris, misses = [], []
        for t in pl["tracks"]:
            uri, label = find_track(t["artist"], t["title"])
            if uri and uri not in uris:
                uris.append(uri)
            elif not uri:
                misses.append(f"{t['artist'] or '?'} — {t['title']}")
            time.sleep(0.1)

        entry = mapping.get(pl["slug"])
        if entry:
            pid = entry["id"]
        else:
            created = call("POST", f"/users/{me['id']}/playlists", body={
                "name": pl["name"], "public": True,
                "description": "Open-sourced at github.com/joudbitar/playlists"})
            pid = created["id"]
            mapping[pl["slug"]] = {"id": pid,
                                   "url": created["external_urls"]["spotify"]}

        call("PUT", f"/playlists/{pid}/tracks", body={"uris": uris[:100]})
        for i in range(100, len(uris), 100):
            call("POST", f"/playlists/{pid}/tracks", body={"uris": uris[i:i+100]})

        MAP_FILE.write_text(json.dumps(mapping, indent=2) + "\n")
        print(f"{pl['slug']}: {len(uris)}/{pl['track_count']} matched -> "
              f"{mapping[pl['slug']]['url']}")
        for m in misses:
            print(f"   miss: {m}")


if __name__ == "__main__":
    main()
