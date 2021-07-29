import os

from plexapi.myplex import MyPlexAccount

plex = None


def connect_once():
    global plex
    if plex:
        return plex

    account = MyPlexAccount(
        username=os.environ["PLEX_USERNAME"],
        password=os.environ["PLEX_PASSWORD"],
        token=os.environ["PLEX_TOKEN"],
    )
    resource = account.resource(os.environ["PLEX_SERVER"])
    plex = resource.connect()

    return plex


def totalSize():
    plex = connect_once()

    size = 0
    size += plex.library.section("Movies").totalSize
    for show in plex.library.section("TV Shows").all():
        size += show.leafCount
    return size


def videos():
    plex = connect_once()

    for movie in plex.library.section("Movies").all():
        guids = set([guid.id for guid in movie.guids])
        yield (guids, movie)

    for show in plex.library.section("TV Shows").all():
        for episode in show.episodes():
            guids = set(
                ["{}/{}".format(guid.id, episode.seasonEpisode) for guid in show.guids]
            )
            yield (guids, episode)


if __name__ == "__main__":
    from tqdm import tqdm

    for (guids, video) in tqdm(videos(), total=totalSize()):
        print(guids)
