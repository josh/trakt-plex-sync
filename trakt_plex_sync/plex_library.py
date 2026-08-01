import os
from collections.abc import Iterator
from functools import partial

import lru_cache
from plexapi.myplex import MyPlexAccount
from plexapi.video import Video


def _video_guids(video: Video) -> set[str]:
    return {guid.id for guid in video.guids}


def videos() -> Iterator[tuple[set[str], Video]]:
    account = MyPlexAccount(  # type: ignore[no-untyped-call]
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )
    resource = account.resource(os.environ["PLEX_SERVER"])  # type: ignore[no-untyped-call]
    plex = resource.connect()

    cache = lru_cache.open(
        os.environ.get("CACHE_PATH", "/tmp/cache.pickle"),
        max_bytesize=5 * 1024 * 1024,  # 5 MB
    )

    with cache:
        for movie in plex.library.section("Movies").all():
            guids = cache.get_or_load(movie.guid, partial(_video_guids, movie))
            yield (guids, movie)

        for show in plex.library.section("TV Shows").all():
            show_guids = cache.get_or_load(show.guid, partial(_video_guids, show))
            for episode in show.episodes():
                guids = {f"{guid}/{episode.seasonEpisode}" for guid in show_guids}
                yield (guids, episode)


if __name__ == "__main__":
    for guids, video in videos():
        print(guids)
