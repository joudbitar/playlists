#!/usr/bin/env python3
"""Build the public playlists repo (markdown + data) from extracted JSON."""
import json
import sys
import urllib.parse
from pathlib import Path

SRC = Path(sys.argv[1])   # dir with <slug>.json + index.json
REPO = Path(sys.argv[2])  # repo root to write into

# slug -> live Spotify playlist url (written by tools/spotify_publish.py)
_map_file = REPO / "spotify_playlists.json"
SPOTIFY = {k: v["url"] for k, v in
           (json.loads(_map_file.read_text()) if _map_file.exists() else {}).items()}


def fmt_dur(sec):
    if not sec:
        return "—"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def track_links(artist, title):
    q = " ".join(x for x in (artist, title) if x)
    yt = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q)
    sp = "https://open.spotify.com/search/" + urllib.parse.quote(q)
    am = "https://music.apple.com/us/search?term=" + urllib.parse.quote_plus(q)
    return f"[YouTube]({yt}) · [Spotify]({sp}) · [Apple]({am})"


def esc(s):
    return (s or "").replace("|", "\\|")


def playlist_md(pl):
    lines = [f"# {pl['name']}", ""]
    has_dur = pl["total_duration_sec"] > 0
    tail = [f"[JSON](../data/{pl['slug']}.json)"]
    if SPOTIFY.get(pl["slug"]):
        tail.insert(0, f"[▶ Open in Spotify]({SPOTIFY[pl['slug']]})")
    lines += [" · ".join(tail), ""]
    dur_h = " Length |" if has_dur else ""
    dur_s = ":------:|" if has_dur else ""
    lines += [f"| # | Track | Artist | BPM |{dur_h} |",
              f"|--:|-------|--------|:---:|{dur_s}--|"]
    for i, t in enumerate(pl["tracks"], 1):
        title = esc(t["title"]) or esc(t["source_file"])
        artist = esc(t["artist"]) or "—"
        bpm = t.get("bpm") or "—"
        link = track_links(t["artist"], t["title"])
        dur_c = f" {fmt_dur(t['duration_sec'])} |" if has_dur else ""
        lines.append(f"| {i} | {title} | {artist} | {bpm} |{dur_c} {link} |")
    lines.append("")
    return "\n".join(lines)


def main():
    playlists = []
    for f in sorted(SRC.glob("*.json")):
        if f.name == "index.json":
            continue
        playlists.append(json.loads(f.read_text()))

    # order: parties first, then pools, then personal
    order = ["70s-party", "y2k-party", "gay-club-anthems", "arab-house",
             "diwali-after", "general-pop", "south-asian",
             "stuff-i-like", "dnb-garage", "lvl", "reda"]
    playlists.sort(key=lambda p: order.index(p["slug"]) if p["slug"] in order else 99)

    (REPO / "playlists").mkdir(parents=True, exist_ok=True)
    (REPO / "data").mkdir(parents=True, exist_ok=True)

    for pl in playlists:
        (REPO / "playlists" / f"{pl['slug']}.md").write_text(playlist_md(pl))
        (REPO / "data" / f"{pl['slug']}.json").write_text(
            json.dumps(pl, indent=2, ensure_ascii=False) + "\n")

    total_tracks = sum(p["track_count"] for p in playlists)
    n_bpm = sum(1 for p in playlists for t in p["tracks"] if t.get("bpm"))
    n_sp = sum(1 for p in playlists if SPOTIFY.get(p["slug"]))

    md = ["# playlists", "",
          "Every DJ set I've performed, as plain-text tracklists.", "",
          f"**{len(playlists)} playlists · {total_tracks} tracks.** Every track links to",
          "YouTube, Spotify and Apple Music, and every set is a live Spotify playlist"
          if n_sp == len(playlists) else
          "YouTube, Spotify and Apple Music, and some sets are live Spotify playlists",
          "you can hit play on.", "",
          "| Playlist | Tracks | Spotify |",
          "|----------|-------:|:-------:|"]
    for p in playlists:
        sp = f"[▶]({SPOTIFY[p['slug']]})" if SPOTIFY.get(p["slug"]) else "—"
        md.append(f"| [{p['name']}](playlists/{p['slug']}.md) | {p['track_count']} | {sp} |")
    if 0 < n_sp < len(playlists):
        md += ["",
               f"*▶ = live Spotify playlist ({n_sp}/{len(playlists)} up so far; "
               "the rest are landing soon).*"]

    not_live = [
        f"- Only {n_sp} of the {len(playlists)} sets are live Spotify playlists so far. The rest are",
        "  markdown only.",
    ] if n_sp < len(playlists) else []

    md += [
        "",
        "## How it's built",
        "",
        "The whole repo is generated. A stdlib-only Python pipeline reads my Apple",
        "Music m3u exports and playlist folders, pulls artist, title, BPM and year off",
        "the tags, and writes each set out as a JSON file plus a markdown page. A",
        "second script talks to the Spotify Web API to create the real playlists and",
        "write their URLs back in. No dependencies, no framework, no database.",
        "",
        "- Markdown is the output, not the source. Re-run the builder and every page",
        "  and this README regenerate from the JSON in `data/`.",
        "- Track links are search URLs built from artist and title, so they keep",
        "  working even where I haven't matched an exact Spotify ID.",
        f"- BPMs come straight from the file tags where they exist ({n_bpm} of {total_tracks} so far).",
        "- The Spotify publisher is resumable: it skips sets already up and caps its",
        "  retries, so re-running it never makes duplicates.",
        "",
        "## What it doesn't do",
        "",
        "- No audio lives here. It's links, not files, so there's nothing to host and",
        "  nothing to take down.",
        "- The per-track links are searches, not exact tracks. Usually the top hit is",
        "  right, sometimes it's a different version.",
        *not_live,
        "- BPMs aren't complete, and the sets are frozen exports, not playlists I keep",
        "  updating.",
        "",
        "## License",
        "",
        "MIT. Take what you want.",
        "",
    ]
    (REPO / "README.md").write_text("\n".join(md))
    print(f"Repo built at {REPO}: {len(playlists)} playlists, {total_tracks} tracks")


if __name__ == "__main__":
    main()
