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

BLURBS = {
    "70s-party": "ABBA, Queen, Bowie, MJ, Bee Gees, Blondie — a full 70s night in order.",
    "y2k-party": "Eminem to Hannah Montana. Low-rise jeans energy.",
    "arab-house": "Arabic vocals over house grooves — the crossover set.",
    "gay-club-anthems": "Certified dancefloor liberation. No skips allowed.",
    "diwali-after": "The afterparty set — Bollywood and Punjabi bangers.",
    "general-pop": "The crowd-pleaser set (played as \"Festival of Nations\") — disco to Tyler to Fred again.",
    "south-asian": "Desi party pool, wedding-tier energy.",
    "dnb-garage": "UK rollers — drum & bass and garage cuts.",
    "stuff-i-like": "The personal rotation. House-leaning, Arabic accents.",
    "lvl": "Reggaeton and Latin heat — Bad Bunny-forward.",
    "reda": "Deep, rolling minimal house — a set built for a friend.",
}


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
    blurb = BLURBS.get(pl["slug"])
    if blurb:
        lines += [f"> {blurb}", ""]
    has_dur = pl["total_duration_sec"] > 0
    order = "curated set order" if pl["source"] == "m3u" else "A–Z pool"
    stats = [f"{pl['track_count']} tracks"]
    if has_dur:
        stats.append(fmt_dur(pl["total_duration_sec"]))
    stats.append(order)
    tail = [f"[JSON](../data/{pl['slug']}.json)"]
    if SPOTIFY.get(pl["slug"]):
        tail.insert(0, f"[▶ Open in Spotify]({SPOTIFY[pl['slug']]})")
    lines += [f"**{' · '.join(stats)}** · {' · '.join(tail)}", ""]
    dur_h = " Length |" if has_dur else ""
    dur_s = ":------:|" if has_dur else ""
    lines += [f"| # | Track | Artist | Year |{dur_h} |",
              f"|--:|-------|--------|:----:|{dur_s}--|"]
    for i, t in enumerate(pl["tracks"], 1):
        title = esc(t["title"]) or esc(t["source_file"])
        artist = esc(t["artist"]) or "—"
        year = t["year"] or "—"
        link = track_links(t["artist"], t["title"])
        dur_c = f" {fmt_dur(t['duration_sec'])} |" if has_dur else ""
        lines.append(f"| {i} | {title} | {artist} | {year} |{dur_c} {link} |")
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

    md = ["# playlists", "",
          "This is a collection of all the DJ sets I've performed. I decided to",
          "open source them in case anyone wants to listen to them or to perform",
          "them.", "",
          f"**{len(playlists)} playlists · {total_tracks} tracks.** Every track links",
          "to YouTube, Spotify and Apple Music.", "",
          "| Playlist | Tracks | Spotify | Vibe |",
          "|----------|-------:|:-------:|------|"]
    for p in playlists:
        blurb = BLURBS.get(p["slug"]) or ""
        sp = f"[▶]({SPOTIFY[p['slug']]})" if SPOTIFY.get(p["slug"]) else "—"
        md.append(f"| [{p['name']}](playlists/{p['slug']}.md) | {p['track_count']} "
                  f"| {sp} | {blurb} |")
    n_sp = sum(1 for p in playlists if SPOTIFY.get(p["slug"]))
    if 0 < n_sp < len(playlists):
        md += ["",
               f"*▶ = live Spotify playlist ({n_sp}/{len(playlists)} up so far; "
               "the rest are landing soon).*"]
    md.append("")
    (REPO / "README.md").write_text("\n".join(md))
    print(f"Repo built at {REPO}: {len(playlists)} playlists, {total_tracks} tracks")


if __name__ == "__main__":
    main()
