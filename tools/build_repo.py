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
    "70s-party": "A whole 70s night played in order so it actually builds: disco into glam into the big singalong ballads. By the last track the room is shouting every word.",
    "y2k-party": "The 2000s the way they actually sounded on the radio and on Disney Channel. Rap sitting right next to bubblegum pop, no shame. Low-rise-jeans energy.",
    "arab-house": "Arabic vocals over house grooves. My crossover set, and the one that catches people off guard.",
    "gay-club-anthems": "Straight-up dancefloor. Nothing here is a skip. This is the set for when the room just wants to let go.",
    "diwali-after": "The afterparty set, for when the main room's done. Bollywood hooks and Punjabi bangers, loud and sweaty.",
    "general-pop": "My most all-over-the-place set (I played it once as \"Festival of Nations\"): disco to Tyler to Fred again, and it somehow holds a mixed crowd. My safe bet.",
    "south-asian": "Desi party fuel. Full wedding-reception energy, the floor packed with everyone from cousins to aunties.",
    "dnb-garage": "Fast UK stuff: drum & bass and garage rollers. Short set, no mercy.",
    "stuff-i-like": "No crowd to read here, just what I actually put on for myself. House-leaning, with Arabic slipping in at the edges.",
    "lvl": "Reggaeton and Latin heat, heavy on Bad Bunny. Hips-first.",
    "reda": "Deep, rolling minimal house. I built it for a friend, Reda, and it turned into its own set.",
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
          "People kept asking for my tracklists, so here they all are. Browse a set,",
          "take the whole thing, or pull the few tracks you were after. It's also my",
          "own record of what I've actually played out.", "",
          f"**{len(playlists)} playlists · {total_tracks} tracks.** Every track links to",
          "YouTube, Spotify and Apple Music, and a few sets are live Spotify playlists",
          "you can hit play on.", "",
          "| Playlist | Tracks | Spotify | Vibe |",
          "|----------|-------:|:-------:|------|"]
    for p in playlists:
        blurb = BLURBS.get(p["slug"]) or ""
        sp = f"[▶]({SPOTIFY[p['slug']]})" if SPOTIFY.get(p["slug"]) else "—"
        md.append(f"| [{p['name']}](playlists/{p['slug']}.md) | {p['track_count']} "
                  f"| {sp} | {blurb} |")
    if 0 < n_sp < len(playlists):
        md += ["",
               f"*▶ = live Spotify playlist ({n_sp}/{len(playlists)} up so far; "
               "the rest are landing soon).*"]

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
        f"- Only {n_sp} of the {len(playlists)} sets are live Spotify playlists so far. The rest are",
        "  markdown only.",
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
