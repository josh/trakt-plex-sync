import atexit
import json
import os

enabled = "CACHE_PATH" in os.environ
path = os.environ.get("CACHE_PATH")
cache = {}
queue_flush = False


def get(key):
    assert isinstance(key, str)
    return cache.get(key)


def set(key, value):
    global cache
    global queue_flush
    assert isinstance(key, str)
    cache[key] = value
    queue_flush = True


def flush():
    assert enabled, "caching not enabled"

    if not queue_flush:
        return

    with open(path, "w") as f:
        json.dump(cache, f)


def reload():
    global cache
    assert enabled, "caching not enabled"

    try:
        with open(path) as f:
            cache = json.load(f)
            assert isinstance(cache, dict)
    except FileNotFoundError:
        pass


if enabled:
    reload()
    atexit.register(flush)
