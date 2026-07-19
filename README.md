# playlists

Every DJ set I've performed, as plain-text tracklists.

People kept asking for my tracklists, so here they all are. Browse a set,
take the whole thing, or pull the few tracks you were after. It's also my
own record of what I've actually played out.

**11 playlists · 566 tracks.** Every track links to
YouTube, Spotify and Apple Music, and a few sets are live Spotify playlists
you can hit play on.

| Playlist | Tracks | Spotify | Vibe |
|----------|-------:|:-------:|------|
| [70s Party](playlists/70s-party.md) | 95 | [▶](https://open.spotify.com/playlist/2LJHt0t8N4Vz6Lfx0CyHvw) | A whole 70s night played in order so it actually builds: disco into glam into the big singalong ballads. By the last track the room is shouting every word. |
| [Y2K Party](playlists/y2k-party.md) | 52 | — | The 2000s the way they actually sounded on the radio and on Disney Channel. Rap sitting right next to bubblegum pop, no shame. Low-rise-jeans energy. |
| [Gay Club Anthems](playlists/gay-club-anthems.md) | 60 | — | Straight-up dancefloor. Nothing here is a skip. This is the set for when the room just wants to let go. |
| [Arab House](playlists/arab-house.md) | 63 | [▶](https://open.spotify.com/playlist/0tyutJfPvMmWmntj2P0y9h) | Arabic vocals over house grooves. My crossover set, and the one that catches people off guard. |
| [Diwali Afterparty](playlists/diwali-after.md) | 72 | [▶](https://open.spotify.com/playlist/2aNSw7t97IE5xqPXwJcyKq) | The afterparty set, for when the main room's done. Bollywood hooks and Punjabi bangers, loud and sweaty. |
| [General Pop](playlists/general-pop.md) | 64 | — | My most all-over-the-place set (I played it once as "Festival of Nations"): disco to Tyler to Fred again, and it somehow holds a mixed crowd. My safe bet. |
| [South Asian](playlists/south-asian.md) | 37 | — | Desi party fuel. Full wedding-reception energy, the floor packed with everyone from cousins to aunties. |
| [Stuff I Like](playlists/stuff-i-like.md) | 27 | — | No crowd to read here, just what I actually put on for myself. House-leaning, with Arabic slipping in at the edges. |
| [DnB / Garage](playlists/dnb-garage.md) | 13 | [▶](https://open.spotify.com/playlist/4iE0IAFykOCuTNLlUzCpCR) | Fast UK stuff: drum & bass and garage rollers. Short set, no mercy. |
| [LVL](playlists/lvl.md) | 35 | — | Reggaeton and Latin heat, heavy on Bad Bunny. Hips-first. |
| [Reda](playlists/reda.md) | 48 | — | Deep, rolling minimal house. I built it for a friend, Reda, and it turned into its own set. |

*▶ = live Spotify playlist (4/11 up so far; the rest are landing soon).*

## How it's built

The whole repo is generated. A stdlib-only Python pipeline reads my Apple
Music m3u exports and playlist folders, pulls artist, title, BPM and year off
the tags, and writes each set out as a JSON file plus a markdown page. A
second script talks to the Spotify Web API to create the real playlists and
write their URLs back in. No dependencies, no framework, no database.

- Markdown is the output, not the source. Re-run the builder and every page
  and this README regenerate from the JSON in `data/`.
- Track links are search URLs built from artist and title, so they keep
  working even where I haven't matched an exact Spotify ID.
- BPMs come straight from the file tags where they exist (472 of 566 so far).
- The Spotify publisher is resumable: it skips sets already up and caps its
  retries, so re-running it never makes duplicates.

## What it doesn't do

- No audio lives here. It's links, not files, so there's nothing to host and
  nothing to take down.
- The per-track links are searches, not exact tracks. Usually the top hit is
  right, sometimes it's a different version.
- Only 4 of the 11 sets are live Spotify playlists so far. The rest are
  markdown only.
- BPMs aren't complete, and the sets are frozen exports, not playlists I keep
  updating.

## License

MIT. Take what you want.
