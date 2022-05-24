import plexapi
import requests

import cache


def video_guids(video):
    assert isinstance(video, plexapi.video.Video)

    guids = cache.get(video.guid)
    if guids:
        return set(guids)

    guids = list([guid.id for guid in video.guids])
    cache.set(video.guid, guids)
    for guid in guids:
        cache.set(guid, video.guid)

    return set(guids)


def video_guids2(account, video):
    assert account
    assert isinstance(video, plexapi.video.Video)

    guids = cache.get(video.guid)
    if guids:
        return set(guids)

    video = account.fetchItem("https://metadata.provider.plex.tv{}".format(video.key))
    guids = list([guid.id for guid in video.guids])
    cache.set(video.guid, guids)
    for guid in guids:
        cache.set(guid, video.guid)

    return set(guids)


def plex_guid(guid):
    assert isinstance(guid, str)

    external_guid = cache.get(guid)
    if external_guid:
        assert isinstance(external_guid, str)
        return external_guid

    if guid.startswith("tmdb://"):
        id = int(guid[7:])
        url = "https://josh.github.io/pmdb/tmdb/movie/{}.json".format(id)
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data.get("plex_type") and data.get("plex_id"):
            plex_guid = "plex://{}/{}".format(data["plex_type"], data["plex_id"])
            cache.set(guid, plex_guid)
            return plex_guid

    return None
