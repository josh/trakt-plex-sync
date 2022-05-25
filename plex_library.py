import os

from plexapi.myplex import MyPlexAccount

import cache


def video_guids(video):
    guids = cache.get(video.guid)
    if guids:
        return set(guids)

    guids = list([guid.id for guid in video.guids])
    cache.set(video.guid, guids)

    return set(guids)


def videos():
    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )
    resource = account.resource(os.environ["PLEX_SERVER"])
    plex = resource.connect()

    for movie in plex.library.section("Movies").all():
        yield (video_guids(movie), movie)

    for show in plex.library.section("TV Shows").all():
        show_guids = video_guids(show)
        for episode in show.episodes():
            guids = set(
                ["{}/{}".format(guid, episode.seasonEpisode)
                 for guid in show_guids]
            )
            yield (guids, episode)


if __name__ == "__main__":
    for (guids, video) in videos():
        print(guids)
