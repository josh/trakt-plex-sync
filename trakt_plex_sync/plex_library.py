import os
from collections.abc import Iterator

import lru_cache
from plexapi.myplex import MyPlexAccount  # type: ignore
from plexapi.video import Video  # type: ignore


def videos() -> Iterator[tuple[set[str], Video]]:
    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )
    resource = account.resource(os.environ["PLEX_SERVER"])
    plex = resource.connect()

    cache = lru_cache.open(
        os.environ.get("CACHE_PATH", "/tmp/cache.pickle"),
        max_bytesize=5 * 1024 * 1024,  # 5 MB
    )

    with cache:
        for movie in plex.library.section("Movies").all():
            guids = cache.get_or_load(
                movie.guid, lambda: set(guid.id for guid in movie.guids)
            )
            yield (guids, movie)

        for show in plex.library.section("TV Shows").all():
            show_guids = cache.get_or_load(
                show.guid, lambda: set(guid.id for guid in show.guids)
            )
            for episode in show.episodes():
                guids = set([f"{guid}/{episode.seasonEpisode}" for guid in show_guids])
                yield (guids, episode)


if __name__ == "__main__":
    for guids, video in videos():
        print(guids)
