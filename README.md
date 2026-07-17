# playlists

My playlists as open data — every set I've built and DJ'd, published as
clean track lists instead of rotting in a folder of `.m3u` files.

**11 playlists · 566 tracks.**

Each playlist is a human-readable page in [`playlists/`](playlists/) and a
machine-readable JSON file in [`data/`](data/). Party sets keep their
curated play order. No audio lives here — just the recipes, with a
YouTube search link per track so any of them is one click from playable.

| Playlist | Tracks | Vibe |
|----------|-------:|------|
| [70s Party](playlists/70s-party.md) | 95 | ABBA, Queen, Bowie, MJ, Bee Gees, Blondie — a full 70s night in order. |
| [Y2K Party](playlists/y2k-party.md) | 52 | Eminem to Hannah Montana. Low-rise jeans energy. |
| [Gay Club Anthems](playlists/gay-club-anthems.md) | 60 | Certified dancefloor liberation. No skips allowed. |
| [Arab House](playlists/arab-house.md) | 63 | Arabic vocals over house grooves — the crossover set. |
| [Diwali Afterparty](playlists/diwali-after.md) | 72 | The afterparty set — Bollywood and Punjabi bangers. |
| [General Pop](playlists/general-pop.md) | 64 | The crowd-pleaser set (played as "Festival of Nations") — disco to Tyler to Fred again. |
| [South Asian](playlists/south-asian.md) | 37 | Desi party pool, wedding-tier energy. |
| [Stuff I Like](playlists/stuff-i-like.md) | 27 | The personal rotation. House-leaning, Arabic accents. |
| [DnB / Garage](playlists/dnb-garage.md) | 13 | UK rollers — drum & bass and garage cuts. |
| [LVL](playlists/lvl.md) | 35 | Reggaeton and Latin heat — Bad Bunny-forward. |
| [Reda](playlists/reda.md) | 48 | Deep, rolling minimal house — a set built for a friend. |

## Data format

```json
{
  "slug": "70s-party",
  "name": "70s Party",
  "source": "m3u",
  "track_count": 95,
  "tracks": [
    {
      "artist": "ABBA",
      "title": "Dancing Queen",
      "year": "1976"
    }
  ]
}
```

`source: m3u` means the track order is the curated set order;
`source: folder` playlists are alphabetical pools. Some tracks in the
deeper crates have `artist: null` — the filename didn't say and I
didn't guess.

## How it's built

The pipeline lives in [`tools/`](tools/):

1. `extract_playlists.py` reads the local `.m3u` files and playlist
   folders, parses artist/title out of filenames (and audio tags via
   `ffprobe` when the files are materialized locally — cloud placeholders
   are skipped rather than force-downloaded), and applies
   `overrides.json`, a hand-curated metadata file for tracks whose
   filenames don't carry the artist.
2. `build_repo.py` renders the markdown pages, the JSON data files,
   and this README.
