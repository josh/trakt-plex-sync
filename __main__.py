import os
import sys

import requests
from plexapi.myplex import MyPlexAccount
from tqdm import tqdm

print("Logging into Plex", file=sys.stderr)
account = MyPlexAccount(
    username=os.environ["PLEX_USERNAME"],
    password=os.environ["PLEX_PASSWORD"],
    token=os.environ["PLEX_TOKEN"],
)
resource = account.resource(os.environ["PLEX_SERVER"])
plex = resource.connect()

print("Fetching Trakt watched movies", file=sys.stderr)
resp = requests.get(
    url="https://api.trakt.tv/users/me/watched/movies",
    headers={
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": os.environ["TRAKT_CLIENT_ID"],
        "Authorization": "Bearer " + os.environ["TRAKT_ACCESS_TOKEN"],
    },
)

trakt_watched = set()
for entry in resp.json():
    trakt_watched.add("tmdb://{}".format(entry["movie"]["ids"]["tmdb"]))
    trakt_watched.add("imdb://{}".format(entry["movie"]["ids"]["imdb"]))
assert trakt_watched

print("Loading Plex movies library", file=sys.stderr)
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


print("Fetching Trakt watched TV shows", file=sys.stderr)
resp = requests.get(
    url="https://api.trakt.tv/users/me/watched/shows",
    headers={
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": os.environ["TRAKT_CLIENT_ID"],
        "Authorization": "Bearer " + os.environ["TRAKT_ACCESS_TOKEN"],
    },
)

trakt_watched = set()
for entry in resp.json():
    for season in entry["seasons"]:
        for episode in season["episodes"]:
            for service in ["imdb", "tmdb", "tvdb"]:
                trakt_watched.add(
                    "{}://{}/s{:02d}e{:02d}".format(
                        service,
                        entry["show"]["ids"][service],
                        season["number"],
                        episode["number"],
                    )
                )
assert trakt_watched


print("Loading Plex TV show library", file=sys.stderr)
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
