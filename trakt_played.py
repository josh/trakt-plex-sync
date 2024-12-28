import json
import os
import urllib.request
from typing import Any

_HTTP_HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": os.environ["TRAKT_CLIENT_ID"],
    "Authorization": "Bearer " + os.environ["TRAKT_ACCESS_TOKEN"],
}


def watched_movie_guids() -> set[str]:
    url = "https://api.trakt.tv/users/me/watched/movies"
    entries = _get_json(url)

    guids = set()
    for entry in entries:
        guids.add("tmdb://{}".format(entry["movie"]["ids"]["tmdb"]))
        guids.add("imdb://{}".format(entry["movie"]["ids"]["imdb"]))
    return guids


def watched_shows_guids() -> set[str]:
    url = "https://api.trakt.tv/users/me/watched/shows"
    entries = _get_json(url)

    guids = set()
    for entry in entries:
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


def watched_guids() -> set[str]:
    return watched_movie_guids().union(watched_shows_guids())


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers=_HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = response.read()
        assert isinstance(data, bytes)
        return json.loads(data)


if __name__ == "__main__":
    for guid in watched_guids():
        print(guid)
