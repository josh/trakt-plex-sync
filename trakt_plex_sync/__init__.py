import logging
import os
import sys

from . import plex_library, trakt_played

logger = logging.getLogger("trakt-plex-sync")


class GitHubActionsFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.levelno >= 40:
            levelname = "error"
        elif record.levelno >= 30:
            levelname = "warning"
        elif record.levelno >= 20:
            levelname = "notice"
        else:
            levelname = "debug"
        title = f"{record.module}.{record.funcName}"
        message = record.getMessage()
        return f"::{levelname} file={record.filename},line={record.lineno},title={title}::{message}"


if os.environ.get("GITHUB_ACTIONS") == "true":
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(GitHubActionsFormatter())
    logger.addHandler(handler)


def main() -> None:
    watched_guids = trakt_played.watched_guids()

    watched_count = 0
    unwatched_count = 0

    for guids, video in plex_library.videos():
        if not guids:
            continue

        isPlayed = watched_guids.intersection(guids)

        if video.isPlayed and not isPlayed:
            video.markUnwatched()  # type: ignore[no-untyped-call]
            unwatched_count += 1
        elif not video.isPlayed and isPlayed:
            video.markPlayed()  # type: ignore[no-untyped-call]
            watched_count += 1

    if watched_count:
        print(f"+{watched_count} watched", file=sys.stderr)

    if unwatched_count:
        print(f"-{unwatched_count} unwatched", file=sys.stderr)


if __name__ == "__main__":
    main()
