#!/usr/bin/env python3
"""Extract playlist metadata from m3u files + folder playlists into JSON."""
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

MUSIC_LIB = Path("/Users/joudbitar/Library/Mobile Documents/com~apple~CloudDocs/Music Library")
M3U_DIR = MUSIC_LIB / "_Playlists"
MASON = Path("/Users/joudbitar/Library/CloudStorage/OneDrive-TrinityCollege/Mason")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./out")

AUDIO_EXT = {".mp3", ".flac", ".m4a", ".wav", ".aiff", ".ogg", ".opus"}

# m3u playlists to include: file name -> (slug, display name)
M3U_PLAYLISTS = {
    "COMPLETED PARTIES - 70s_party.m3u": ("70s-party", "70s Party"),
    "COMPLETED PARTIES - Y2K PARTY.m3u": ("y2k-party", "Y2K Party"),
    "COMPLETED PARTIES - arab_house.m3u": ("arab-house", "Arab House"),
    # identical track set to the OneDrive "General Pop" folder — published once, m3u order
    "COMPLETED PARTIES - festival_of_nations.m3u": ("general-pop", "General Pop"),
    "COMPLETED PARTIES - gay_club_anthems.m3u": ("gay-club-anthems", "Gay Club Anthems"),
    "diwali_after.m3u": ("diwali-after", "Diwali Afterparty"),
    "lvl.m3u": ("lvl", "LVL"),
    "reda.m3u": ("reda", "Reda"),
    "stuff i like.m3u": ("stuff-i-like", "Stuff I Like"),
    "stuff i like - dnb-garage.m3u": ("dnb-garage", "DnB / Garage"),
}

# Folder playlists (no m3u counterpart) -> (slug, display name)
FOLDER_PLAYLISTS = {
    "South Asian": ("south-asian", "South Asian"),
}

OVERRIDES = json.loads(
    (Path(__file__).parent / "overrides.json").read_text())


def is_dataless(path: Path):
    """Cloud placeholder — reading it would force a full download."""
    try:
        return path.stat().st_blocks == 0
    except OSError:
        return True


def ffprobe_tags(path: Path):
    if is_dataless(path):
        return {}
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return {}
        fmt = json.loads(r.stdout).get("format", {})
        tags = {k.lower(): v for k, v in fmt.get("tags", {}).items()}
        dur = fmt.get("duration")
        return {
            "artist": tags.get("artist") or tags.get("album_artist"),
            "title": tags.get("title"),
            "album": tags.get("album"),
            "year": (tags.get("date") or tags.get("year") or "")[:4] or None,
            "duration": round(float(dur)) if dur else None,
        }
    except Exception:
        return {}


FILENAME_JUNK = re.compile(
    r"^\s*(?:\d{1,4}[\s.\-_]+)+"  # leading track numbers like "0007 - ", "01. ", "1-01 "
)


def parse_filename(name: str, by_split: bool = True):
    stem = Path(name).stem
    stem = re.sub(r"\s*(\(\d\)|copy)\s*$", "", stem)  # dupe-file suffixes
    stem = FILENAME_JUNK.sub("", stem)
    stem = re.sub(r"\[\d{4}\]", "", stem)  # [2009]
    stem = re.sub(r"\(Official.*?\)", "", stem, flags=re.I)
    stem = stem.replace("_", " ").strip(" -.")
    if " - " in stem:
        artist, title = stem.split(" - ", 1)
        return artist.strip(), title.strip()
    if by_split:
        # "Jara by Ahmed Ben Ali" -> title "Jara", artist "Ahmed Ben Ali"
        m = re.match(r"^(.{2,}?) by ([A-Z].+)$", stem)
        if m:
            return m.group(2).strip(), m.group(1).strip()
    return None, stem.strip()


def track_record(path: Path):
    meta = ffprobe_tags(path) if path.exists() else {}
    fa, ft = parse_filename(path.name)
    artist = (meta.get("artist") or fa or "").strip() or None
    title = (meta.get("title") or ft or "").strip() or None
    year = meta.get("year")
    if year and not year.isdigit():
        year = None
    # manual overrides: exact file key wins, then the raw (pre-by-split) title key
    _, raw_title = parse_filename(path.name, by_split=False)
    ov = OVERRIDES.get(f"file:{path.name}") or OVERRIDES.get(raw_title) or {}
    if isinstance(ov, dict) and ov:
        artist = ov.get("artist", artist)
        title = ov.get("title", title)
        year = ov.get("year", year)
    return {
        "artist": artist,
        "title": title,
        "album": meta.get("album"),
        "year": year,
        "duration_sec": meta.get("duration"),
        "source_file": path.name,
        "tagged": bool(meta.get("title")),
        "missing": not path.exists(),
    }


def read_m3u(path: Path):
    files = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # entries are relative to _Playlists (e.g. ../song.mp3)
        files.append((M3U_DIR / line).resolve())
    return files


def read_folder(path: Path):
    return sorted(
        [p for p in path.iterdir() if p.suffix.lower() in AUDIO_EXT],
        key=lambda p: unicodedata.normalize("NFC", p.name.lower()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_playlists = []

    jobs = []
    for fname, (slug, title) in M3U_PLAYLISTS.items():
        p = M3U_DIR / fname
        if p.exists():
            jobs.append((slug, title, "m3u", read_m3u(p)))
        else:
            print(f"!! missing m3u: {fname}", file=sys.stderr)
    for folder, (slug, title) in FOLDER_PLAYLISTS.items():
        p = MASON / folder
        if p.exists():
            jobs.append((slug, title, "folder", read_folder(p)))
        else:
            print(f"!! missing folder: {folder}", file=sys.stderr)

    for slug, title, kind, files in jobs:
        tracks, seen = [], set()
        for f in files:
            t = track_record(f)
            key = ((t["artist"] or "").lower(), (t["title"] or "").lower())
            if key in seen:
                continue
            seen.add(key)
            tracks.append(t)
        pl = {
            "slug": slug,
            "name": title,
            "source": kind,
            "track_count": len(tracks),
            "total_duration_sec": sum(t["duration_sec"] or 0 for t in tracks),
            "tracks": tracks,
        }
        all_playlists.append(pl)
        (OUT / f"{slug}.json").write_text(
            json.dumps(pl, indent=2, ensure_ascii=False) + "\n")
        n_tagged = sum(t["tagged"] for t in tracks)
        n_missing = sum(t["missing"] for t in tracks)
        print(f"{slug}: {len(tracks)} tracks, {n_tagged} tagged, {n_missing} missing files")

    index = [{k: p[k] for k in ("slug", "name", "source", "track_count", "total_duration_sec")}
             for p in all_playlists]
    (OUT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(all_playlists)} playlists to {OUT}")


if __name__ == "__main__":
    main()
