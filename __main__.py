import sys

import plex_library
import plex_watchlist
import trakt_played

watched_guids = trakt_played.watched_guids()

watched_count = 0
unwatched_count = 0

for (guids, video) in plex_library.videos():
    if not guids:
        continue

    isWatched = watched_guids.intersection(guids)

    if video.isWatched and not isWatched:
        video.markUnwatched()
        unwatched_count += 1
    elif not video.isWatched and isWatched:
        video.markWatched()
        watched_count += 1

if watched_count:
    print("+{} watched".format(watched_count), file=sys.stderr)

if unwatched_count:
    print("-{} unwatched".format(unwatched_count), file=sys.stderr)


(watchlist_add, watchlist_remove) = plex_watchlist.compare_trakt_plex_watchlist()

if watchlist_add:
    print("+{} watchlist".format(len(watchlist_add)), file=sys.stderr)
    for plex_item in watchlist_add:
        if not plex_item.onWatchlist():
            plex_item.addToWatchlist()

if watchlist_remove:
    print("-{} watchlist".format(len(watchlist_remove)), file=sys.stderr)
    for plex_item in watchlist_remove:
        if plex_item.onWatchlist():
            plex_item.removeFromWatchlist()
