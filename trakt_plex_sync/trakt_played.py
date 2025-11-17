import json
import os
import time
import urllib.request
from typing import Any

_HTTP_HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": os.environ["TRAKT_CLIENT_ID"],
    "Authorization": "Bearer " + os.environ["TRAKT_ACCESS_TOKEN"],
}

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2


def watched_movie_guids() -> set[str]:
    url = "https://api.trakt.tv/users/me/watched/movies"
    entries = _get_json_with_retry(url, _MAX_RETRIES)

    guids = set()
    for entry in entries:
        guids.add("tmdb://{}".format(entry["movie"]["ids"]["tmdb"]))
        guids.add("imdb://{}".format(entry["movie"]["ids"]["imdb"]))
    return guids


def watched_shows_guids() -> set[str]:
    url = "https://api.trakt.tv/users/me/watched/shows"
    entries = _get_json_with_retry(url, _MAX_RETRIES)

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


def _get_json_with_retry(url: str, count: int) -> Any:
    last_error: TimeoutError | None = None
    for attempt in range(1, count + 1):
        try:
            return _get_json(url)
        except TimeoutError as error:
            last_error = error
            if attempt == count:
                raise
            time.sleep(_RETRY_DELAY_SECONDS * attempt)
    assert last_error is not None, (
        "Retry loop exited unexpectedly without raising TimeoutError"
    )
    raise last_error


if __name__ == "__main__":
    for guid in watched_guids():
        print(guid)
