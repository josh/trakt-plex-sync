import plexapi

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
    return cache.get(guid)
