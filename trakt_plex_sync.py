import sys

import plex_library
import trakt_played


def main() -> None:
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


if __name__ == "__main__":
    main()
