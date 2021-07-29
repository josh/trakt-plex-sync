import os

from tqdm import tqdm

import plex_library
import trakt_played

watched_guids = trakt_played.watched_guids()


for (guids, video) in tqdm(
    plex_library.videos(), total=plex_library.totalSize(), disable=os.getenv("CI")
):
    if not guids:
        continue

    isWatched = watched_guids.intersection(guids)

    if video.isWatched and not isWatched:
        print("+", video.title)
        video.markUnwatched()
    elif not video.isWatched and isWatched:
        print("-", video.title)
        video.markWatched()
