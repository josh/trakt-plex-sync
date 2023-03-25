import os

import polars as pl
import requests
from plexapi.myplex import MyPlexAccount


def _load_plex_index():
    index = {
        "tmdb_movie": {},
        "tmdb_show": {},
    }
    df = (
        pl.scan_parquet(
            "s3://wikidatabots/plex.parquet",
            storage_options={"anon": True},
        )
        .filter(pl.col("tmdb_id").is_not_null())
        .with_columns(pl.col("key").bin.encode("hex").alias("hexkey"))
        .select("type", "hexkey", "tmdb_id")
        .collect()
    )
    for _, key, tmdb_id in df.filter(pl.col("type") == "movie").iter_rows():
        index["tmdb_movie"][tmdb_id] = key
    for _, key, tmdb_id in df.filter(pl.col("type") == "show").iter_rows():
        index["tmdb_show"][tmdb_id] = key
    return index


def _trakt_watchlist():
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


def _find_by_plex_guid(account, ratingkey):
    return account.fetchItem(
        f"https://metadata.provider.plex.tv/library/metadata/{ratingkey}"
    )


def compare_trakt_plex_watchlist():
    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )

    plex_index = _load_plex_index()

    plex_keys = set(
        [item.key.replace("/library/metadata/", "") for item in account.watchlist()]
    )

    trakt_keys = set()
    for trakt_item in _trakt_watchlist():
        item_type = trakt_item["type"]
        assert item_type == "movie" or item_type == "show"
        tmdb_id = trakt_item[item_type]["ids"]["tmdb"]
        plex_key = plex_index[f"tmdb_{item_type}"].get(tmdb_id)
        if plex_key:
            trakt_keys.add(plex_key)

    add = [_find_by_plex_guid(account, key) for key in trakt_keys - plex_keys]
    remove = [_find_by_plex_guid(account, key) for key in plex_keys - trakt_keys]
    return list(add), list(remove)


if __name__ == "__main__":
    (add, remove) = compare_trakt_plex_watchlist()
    for item in add:
        print("+", item.title)
    for item in remove:
        print("-", item.title)
