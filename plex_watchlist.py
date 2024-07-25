import os
import re
from typing import Any

import requests
from plexapi.myplex import MyPlexAccount  # type: ignore
from plexapi.video import Video  # type: ignore


def _trakt_watchlist() -> Any:
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": os.environ["TRAKT_CLIENT_ID"],
        "Authorization": "Bearer " + os.environ["TRAKT_ACCESS_TOKEN"],
    }
    url = "https://api.trakt.tv/sync/watchlist"
    r = requests.get(url=url, headers=headers)
    r.raise_for_status()
    return r.json()


_IMDB_TO_PLEX_QUERY = """
SELECT DISTINCT ?plex_id WHERE {
  VALUES ?imdb_id { ?imdb_ids }
  ?item wdt:P345 ?imdb_id; wdt:P11460 ?plex_id.
}
"""

_TMDB_MOVIE_TO_PLEX_QUERY = """
SELECT DISTINCT ?plex_id WHERE {
  VALUES ?tmdb_movie_id { ?tmdb_movie_ids }
  ?item wdt:P4947 ?tmdb_movie_id; wdt:P11460 ?plex_id.
}
"""

_TMDB_TV_TO_PLEX_QUERY = """
SELECT DISTINCT ?plex_id WHERE {
  VALUES ?tmdb_tv_id { ?tmdb_tv_ids }
  ?item wdt:P4983 ?tmdb_tv_id; wdt:P11460 ?plex_id.
}
"""

_RATING_KEY_RE = r"^[a-f0-9]{24}$"


def _sparql_values_str(values: set[str | int]) -> str:
    return " ".join([f'"{v}"' for v in values])

_WIKIDATA_USER_AGENT = "TraktPlexBot/0.0 (https://github.com/josh/trakt-plex-sync)"

def _sparql(query: str) -> Any:
    r = requests.post(
        "https://query.wikidata.org/sparql",
        data={"query": query},
        headers={"Accept": "application/json", "User-Agent": _WIKIDATA_USER_AGENT},
        timeout=(1, 90),
    )
    r.raise_for_status()
    data = r.json()
    return data


def _wd_trakt_to_plex_ids(trakt_items: list[dict[str, Any]]) -> set[str]:
    imdb_ids = set()
    tmdb_movie_ids = set()
    tmdb_tv_ids = set()
    plex_ids = set()

    for trakt_item in trakt_items:
        if trakt_item["type"] == "movie":
            ids = trakt_item["movie"]["ids"]
            if imdb_id := ids.get("imdb"):
                imdb_ids.add(imdb_id)
            if tmdb_id := ids.get("tmdb"):
                tmdb_movie_ids.add(tmdb_id)
        elif trakt_item["type"] == "show":
            ids = trakt_item["show"]["ids"]
            if imdb_id := ids.get("imdb"):
                imdb_ids.add(imdb_id)
            if tmdb_id := ids.get("tmdb"):
                tmdb_tv_ids.add(tmdb_id)

    queries = [
        _IMDB_TO_PLEX_QUERY.replace("?imdb_ids", _sparql_values_str(imdb_ids)),
        _TMDB_MOVIE_TO_PLEX_QUERY.replace(
            "?tmdb_movie_ids", _sparql_values_str(tmdb_movie_ids)
        ),
        _TMDB_TV_TO_PLEX_QUERY.replace("?tmdb_tv_ids", _sparql_values_str(tmdb_tv_ids)),
    ]

    for query in queries:
        data = _sparql(query)
        for result in data["results"]["bindings"]:
            plex_id = result["plex_id"]["value"]
            if re.match(_RATING_KEY_RE, plex_id):
                plex_ids.add(plex_id)

    return plex_ids


def _find_by_plex_guid(account: MyPlexAccount, ratingkey: str) -> Video:
    return account.fetchItem(
        f"https://metadata.provider.plex.tv/library/metadata/{ratingkey}"
    )


def compare_trakt_plex_watchlist() -> tuple[list[Video], list[Video]]:
    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )

    plex_keys: set[str] = set(
        [item.key.replace("/library/metadata/", "") for item in account.watchlist()]
    )
    trakt_keys: set[str] = _wd_trakt_to_plex_ids(_trakt_watchlist())

    add_videos = [_find_by_plex_guid(account, key) for key in trakt_keys - plex_keys]
    remove_videos = [_find_by_plex_guid(account, key) for key in plex_keys - trakt_keys]
    return list(add_videos), list(remove_videos)


if __name__ == "__main__":
    (add_videos, remove_videos) = compare_trakt_plex_watchlist()
    for video in add_videos:
        print("+", video.title)
    for video in remove_videos:
        print("-", video.title)
