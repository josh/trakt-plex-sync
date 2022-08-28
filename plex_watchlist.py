import os

import requests
from plexapi.myplex import MyPlexAccount

PLEX_GUID_ITEM = {}


def trakt_watchlist():
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


def plex_watchlist_guids(account):
    return set([item.guid for item in account.watchlist()])


def pmdb_fetch_plex_id(path):
    r = requests.get("https://josh.github.io/pmdb/{}".format(path))
    if r.status_code != 200:
        return None

    data = r.json()
    if data.get("plex_type") and data.get("plex_id"):
        return "plex://{}/{}".format(data["plex_type"], data["plex_id"])

    return None


def detect_plex_guid_from_trakt_media(trakt_item):
    if trakt_item["type"] == "movie" and trakt_item["movie"]["ids"]["imdb"]:
        url = "imdb/{}.json".format(trakt_item["movie"]["ids"]["imdb"])
        plex_guid = pmdb_fetch_plex_id(url)
        if plex_guid:
            return plex_guid

    if trakt_item["type"] == "movie" and trakt_item["movie"]["ids"]["tmdb"]:
        url = "tmdb/movie/{}.json".format(trakt_item["movie"]["ids"]["tmdb"])
        plex_guid = pmdb_fetch_plex_id(url)
        if plex_guid:
            return plex_guid

    if trakt_item["type"] == "show" and trakt_item["show"]["ids"]["imdb"]:
        url = "imdb/{}.json".format(trakt_item["show"]["ids"]["imdb"])
        plex_guid = pmdb_fetch_plex_id(url)
        if plex_guid:
            return plex_guid

    if trakt_item["type"] == "show" and trakt_item["show"]["ids"]["tmdb"]:
        url = "tmdb/tv/{}.json".format(trakt_item["show"]["ids"]["tmdb"])
        plex_guid = pmdb_fetch_plex_id(url)
        if plex_guid:
            return plex_guid

    return None


def find_by_plex_guid(account, guid):
    assert isinstance(guid, str)
    assert guid.startswith("plex://")

    if guid in PLEX_GUID_ITEM:
        return PLEX_GUID_ITEM[guid]

    ekey = "https://metadata.provider.plex.tv/library/metadata/{}".format(
        guid.split("/", 4)[3]
    )
    return account.fetchItem(ekey)


def compare_trakt_plex_watchlist():
    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )

    plex_guids = plex_watchlist_guids(account)

    trakt_guids = set()
    for trakt_item in trakt_watchlist():
        plex_guid = detect_plex_guid_from_trakt_media(trakt_item)
        if plex_guid:
            trakt_guids.add(plex_guid)

    add = [find_by_plex_guid(account, guid) for guid in trakt_guids - plex_guids]
    remove = [find_by_plex_guid(account, guid) for guid in plex_guids - trakt_guids]
    return list(add), list(remove)


if __name__ == "__main__":
    (add, remove) = compare_trakt_plex_watchlist()
    for item in add:
        print("+", item.title)
    for item in remove:
        print("-", item.title)
