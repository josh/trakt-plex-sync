import json
import os
import time
import urllib.parse
import urllib.request
from importlib.metadata import version
from typing import Any

_VERSION = version("trakt-plex-sync")

_HTTP_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": f"trakt-plex-sync/{_VERSION}",
    "trakt-api-version": "2",
    "trakt-api-key": os.environ["TRAKT_CLIENT_ID"],
    "Authorization": "Bearer " + os.environ["TRAKT_ACCESS_TOKEN"],
}

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2
_PAGE_LIMIT = 250


def watched_movie_guids() -> set[str]:
    entries = _get_all_pages("https://api.trakt.tv/users/me/watched/movies")

    guids = set()
    for entry in entries:
        guids.add("tmdb://{}".format(entry["movie"]["ids"]["tmdb"]))
        guids.add("imdb://{}".format(entry["movie"]["ids"]["imdb"]))
    return guids


def watched_shows_guids() -> set[str]:
    entries = _get_all_pages(
        "https://api.trakt.tv/users/me/watched/shows",
        {"extended": "progress"},
    )

    guids = set()
    for entry in entries:
        for season in entry["seasons"]:
            for episode in season["episodes"]:
                if episode.get("completed") is False:
                    continue
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


def _get_all_pages(url: str, params: dict[str, str] | None = None) -> list[Any]:
    query: dict[str, str] = dict(params or {})
    query["limit"] = str(_PAGE_LIMIT)

    entries: list[Any] = []
    page = 1
    page_count = 1
    while page <= page_count:
        query["page"] = str(page)
        page_url = f"{url}?{urllib.parse.urlencode(query)}"
        body, page_count = _get_json_with_retry(page_url, _MAX_RETRIES)
        assert isinstance(body, list)
        entries.extend(body)
        page += 1
    return entries


def _get_json(url: str) -> tuple[Any, int]:
    req = urllib.request.Request(url, headers=_HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = response.read()
        assert isinstance(data, bytes)
        page_count = int(response.headers.get("X-Pagination-Page-Count") or "1")
        return json.loads(data), page_count


def _get_json_with_retry(url: str, count: int) -> tuple[Any, int]:
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
