import os

import requests

headers = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": os.environ["TRAKT_CLIENT_ID"],
    "Authorization": "Bearer " + os.environ["TRAKT_ACCESS_TOKEN"],
}


def watched_movie_guids():
    url = "https://api.trakt.tv/users/me/watched/movies"
    r = requests.get(url=url, headers=headers)
    r.raise_for_status()

    guids = set()
    for entry in r.json():
        guids.add("tmdb://{}".format(entry["movie"]["ids"]["tmdb"]))
        guids.add("imdb://{}".format(entry["movie"]["ids"]["imdb"]))
    return guids


def watched_shows_guids():
    url = "https://api.trakt.tv/users/me/watched/shows"
    r = requests.get(url=url, headers=headers)
    r.raise_for_status()

    guids = set()
    for entry in r.json():
        for season in entry["seasons"]:
            for episode in season["episodes"]:
                for service in ["imdb", "tmdb", "tvdb"]:
                    guids.add(
                        "{}://{}/s{:02d}e{:02d}".format(
                            service,
                            entry["show"]["ids"][service],
                            season["number"],
                            episode["number"],
                        )
                    )
    return guids


def watched_guids():
    return watched_movie_guids().union(watched_shows_guids())


if __name__ == "__main__":
    for guid in watched_guids():
        print(guid)
