# playlists

Every DJ set I've performed, as plain-text tracklists.

**11 playlists · 566 tracks.** Every track links to
YouTube, Spotify and Apple Music, and every set is a live Spotify playlist
you can hit play on.

| Playlist | Tracks | Spotify |
|----------|-------:|:-------:|
| [70s Party](playlists/70s-party.md) | 95 | [▶](https://open.spotify.com/playlist/2LJHt0t8N4Vz6Lfx0CyHvw) |
| [Y2K Party](playlists/y2k-party.md) | 52 | [▶](https://open.spotify.com/playlist/3RboKptvG0jGXOw4IkHhcB) |
| [Gay Club Anthems](playlists/gay-club-anthems.md) | 60 | [▶](https://open.spotify.com/playlist/5PirVcNZFzXMaA0Z352ziN) |
| [Arab House](playlists/arab-house.md) | 63 | [▶](https://open.spotify.com/playlist/0tyutJfPvMmWmntj2P0y9h) |
| [Diwali Afterparty](playlists/diwali-after.md) | 72 | [▶](https://open.spotify.com/playlist/2aNSw7t97IE5xqPXwJcyKq) |
| [General Pop](playlists/general-pop.md) | 64 | [▶](https://open.spotify.com/playlist/5QZAqDH4ySNWRP1riaPxFN) |
| [South Asian](playlists/south-asian.md) | 37 | [▶](https://open.spotify.com/playlist/2iV5FHgacclLMNtDMkuqxh) |
| [Stuff I Like](playlists/stuff-i-like.md) | 27 | [▶](https://open.spotify.com/playlist/1XLF2woDQ1BidpRxuvHSe0) |
| [DnB / Garage](playlists/dnb-garage.md) | 13 | [▶](https://open.spotify.com/playlist/4iE0IAFykOCuTNLlUzCpCR) |
| [LVL](playlists/lvl.md) | 35 | [▶](https://open.spotify.com/playlist/4mnuRPT3buHZUat5BrOoAO) |
| [Reda](playlists/reda.md) | 48 | [▶](https://open.spotify.com/playlist/4Be1J4q6VBhMJ7STv7UcV1) |

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
- BPMs aren't complete, and the sets are frozen exports, not playlists I keep
  updating.

## License

MIT. Take what you want.
