import os
import pickle
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import closing
from functools import partial
from pathlib import Path

from plexapi.myplex import MyPlexAccount
from plexapi.video import Video


class _GuidCache:
    """Video guid to external guids, persisted as a pickle.

    Oldest entries are evicted on close until the pickle fits in max_bytesize.
    """

    _filename: Path
    _max_bytesize: int
    _data: OrderedDict[str, set[str]]

    def __init__(self, filename: Path | str, max_bytesize: int) -> None:
        self._filename = Path(filename)
        self._max_bytesize = max_bytesize
        self._data = OrderedDict()
        if self._filename.exists():
            self._data.update(pickle.loads(self._filename.read_bytes()))

    def get_or_load(self, key: str, load_value: Callable[[], set[str]]) -> set[str]:
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        self._data[key] = value = load_value()
        return value

    def close(self) -> None:
        data = pickle.dumps(self._data, pickle.HIGHEST_PROTOCOL)
        while len(data) > self._max_bytesize and self._data:
            self._data.popitem(last=False)
            data = pickle.dumps(self._data, pickle.HIGHEST_PROTOCOL)
        self._filename.parent.mkdir(parents=True, exist_ok=True)
        self._filename.write_bytes(data)


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

    cache = _GuidCache(
        os.environ.get("CACHE_PATH", "/tmp/cache.pickle"),
        max_bytesize=5 * 1024 * 1024,  # 5 MB
    )

    with closing(cache):
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
