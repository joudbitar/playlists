#!/usr/bin/env python3
"""Build the public playlists repo (markdown + data) from extracted JSON."""
import json
import sys
import urllib.parse
from pathlib import Path

SRC = Path(sys.argv[1])   # dir with <slug>.json + index.json
REPO = Path(sys.argv[2])  # repo root to write into

BLURBS = {
    "70s-party": "A whole 70s night played in order so it actually builds — disco into glam into the big singalong ballads. By the last track the room is shouting every word.",
    "y2k-party": "The 2000s the way they actually sounded on the radio and on Disney Channel — rap sitting right next to bubblegum pop, no shame. Low-rise-jeans energy.",
    "arab-house": "Arabic vocals over house grooves. My crossover set, and the one that catches people off guard.",
    "gay-club-anthems": "Straight-up dancefloor. Nothing here is a skip — this is the set for when the room just wants to let go.",
    "diwali-after": "The afterparty set, for once the main room's done — Bollywood hooks and Punjabi bangers, loud and sweaty.",
    "general-pop": "My most all-over-the-place set (I played it once as \"Festival of Nations\") — disco to Tyler to Fred again, and it somehow holds a mixed crowd. My safe bet.",
    "south-asian": "Desi party fuel — full wedding-reception energy, the floor packed with everyone from cousins to aunties.",
    "dnb-garage": "Fast UK stuff — drum & bass and garage rollers. Short set, no mercy.",
    "stuff-i-like": "No crowd to read here, just what I actually put on for myself — house-leaning, with Arabic slipping in at the edges.",
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
    lines += [f"[JSON](../data/{pl['slug']}.json)", ""]
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

    md = ["# playlists", "",
          "This is a collection of all the DJ sets I've performed. I decided to",
          "open source them in case anyone wants to listen to them or to perform",
          "them.", "",
          f"**{len(playlists)} playlists · {total_tracks} tracks.** Every track links",
          "to YouTube, Spotify and Apple Music.", "",
          "| Playlist | Tracks | Vibe |",
          "|----------|-------:|------|"]
    for p in playlists:
        blurb = BLURBS.get(p["slug"]) or ""
        md.append(f"| [{p['name']}](playlists/{p['slug']}.md) | {p['track_count']} | {blurb} |")
    md.append("")
    (REPO / "README.md").write_text("\n".join(md))
    print(f"Repo built at {REPO}: {len(playlists)} playlists, {total_tracks} tracks")


if __name__ == "__main__":
    main()
