import sys

import plex_library
import plex_watchlist
import trakt_played

watched_guids = trakt_played.watched_guids()

watched_count = 0
unwatched_count = 0

for guids, video in plex_library.videos():
    if not guids:
        continue

    isPlayed = watched_guids.intersection(guids)

    if video.isPlayed and not isPlayed:
        video.markUnwatched()
        unwatched_count += 1
    elif not video.isPlayed and isPlayed:
        video.markPlayed()
        watched_count += 1

if watched_count:
    print(f"+{watched_count} watched", file=sys.stderr)

if unwatched_count:
    print(f"-{unwatched_count} unwatched", file=sys.stderr)


(watchlist_add, watchlist_remove) = plex_watchlist.compare_trakt_plex_watchlist()

if watchlist_add:
    print(f"+{len(watchlist_add)} watchlist", file=sys.stderr)
    for plex_item in watchlist_add:
        if not plex_item.onWatchlist():
            plex_item.addToWatchlist()

if watchlist_remove:
    print(f"-{len(watchlist_remove)} watchlist", file=sys.stderr)
    for plex_item in watchlist_remove:
        if plex_item.onWatchlist():
            plex_item.removeFromWatchlist()
