import os
import sys

from plexapi.myplex import MyPlexAccount
from tqdm import tqdm

import trakt_played

trakt_watched = trakt_played.watched_guids()

print("Logging into Plex", file=sys.stderr)
account = MyPlexAccount(
    username=os.environ["PLEX_USERNAME"],
    password=os.environ["PLEX_PASSWORD"],
    token=os.environ["PLEX_TOKEN"],
)
resource = account.resource(os.environ["PLEX_SERVER"])
plex = resource.connect()


movies = plex.library.section("Movies")
for video in tqdm(movies.all()):
    if not video.guids:
        continue

    isWatched = False
    for guid in video.guids:
        if guid.id in trakt_watched:
            isWatched = True

    if video.isWatched and not isWatched:
        print("+", video.title)
        video.markUnwatched()
    elif not video.isWatched and isWatched:
        print("-", video.title)
        video.markWatched()


shows = plex.library.section("TV Shows")
for show in tqdm(shows.all()):
    if not show.guids:
        continue

    for episode in show.episodes():
        isWatched = False
        for guid in show.guids:
            if "{}/{}".format(guid.id, episode.seasonEpisode) in trakt_watched:
                isWatched = True

        if episode.isWatched and not episode:
            print("+", show.title, episode.seasonEpisode)
            episode.markUnwatched()
        elif not episode.isWatched and isWatched:
            print("-", show.title, episode.seasonEpisode)
            episode.markWatched()
