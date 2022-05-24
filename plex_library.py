import os

from plexapi.myplex import MyPlexAccount

import plex_cache


def videos():
    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )
    resource = account.resource(os.environ["PLEX_SERVER"])
    plex = resource.connect()

    for movie in plex.library.section("Movies").all():
        yield (plex_cache.video_guids(movie), movie)

    for show in plex.library.section("TV Shows").all():
        show_guids = plex_cache.video_guids(show)
        for episode in show.episodes():
            guids = set(
                ["{}/{}".format(guid, episode.seasonEpisode) for guid in show_guids]
            )
            yield (guids, episode)


if __name__ == "__main__":
    for (guids, video) in videos():
        print(guids)
