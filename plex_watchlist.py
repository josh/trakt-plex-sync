import os

import requests
from plexapi.myplex import MyPlexAccount

import cache

plex_guid_item = {}


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


def compare_media_items(trakt_item, plex_item):
    if trakt_item["type"] != plex_item.TYPE:
        return False

    plex_guids = cache.get(plex_item.guid)

    if trakt_item["type"] == "movie":
        tmdb_guid = "tmdb://{}".format(trakt_item["movie"]["ids"]["tmdb"])
        imdb_guid = "imdb://{}".format(trakt_item["movie"]["ids"]["imdb"])

        if plex_guids:
            if tmdb_guid in plex_guids or imdb_guid in plex_guids:
                return True

        if (
            plex_item.title == trakt_item["movie"]["title"]
            and plex_item.year == trakt_item["movie"]["year"]
        ):
            return True

    elif trakt_item["type"] == "show":
        if (
            plex_item.title == trakt_item["show"]["title"]
            and plex_item.year == trakt_item["show"]["year"]
        ):
            return True

    return False


def detect_plex_guid_from_trakt_media(account, trakt_item):
    if trakt_item["type"] == "movie":
        title = trakt_item["movie"]["title"]
    elif trakt_item["type"] == "show":
        title = trakt_item["show"]["title"]
    else:
        return None

    for plex_item in account.searchDiscover(title):
        plex_guid_item[plex_item.guid] = plex_item
        if compare_media_items(trakt_item=trakt_item, plex_item=plex_item):
            return plex_item.guid

    return None


def compare_trakt_plex_watchlist():
    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )

    plex_guids = set()
    trakt_guids = set()

    # BUG: Watchlist only returns 20 items
    for plex_item in account.watchlist():
        plex_guid_item[plex_item.guid] = plex_item
        plex_guids.add(plex_item.guid)

    for trakt_item in trakt_watchlist():
        plex_guid = detect_plex_guid_from_trakt_media(account, trakt_item)
        if plex_guid:
            trakt_guids.add(plex_guid)

    add = [plex_guid_item[guid] for guid in trakt_guids - plex_guids]
    remove = [plex_guid_item[guid] for guid in plex_guids - trakt_guids]
    return list(add), list(remove)


if __name__ == "__main__":
    (add, remove) = compare_trakt_plex_watchlist()
    for item in add:
        print("+", item.title)
    for item in remove:
        print("-", item.title)
