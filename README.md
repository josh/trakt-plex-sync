# trakt-plex-sync

While [Trakt VIP](https://trakt.tv/vip) and [Plex Pass](https://trakt.tv/a/plex-pass) have [a cool feature to record Plex watches to Trakt](https://blog.trakt.tv/plex-scrobbler-52db9b016ead), there isn't an easy way to sync other watch history back to Plex. This little script does just that. It also syncs your Trakt watchlist to Plex as well.

## Setup

Design to run via GitHub Actions. To get started, Fork this repository.

Then set a bunch of Repository secrets for the following:

* `TRAKT_CLIENT_ID`: Trakt OAuth Client ID
* `TRAKT_CLIENT_SECRET`: Trakt OAuth Client Secret
* `TRAKT_ACCESS_TOKEN`: Initial Trakt API access token
* `TRAKT_REFRESH_TOKEN`: Initial Trakt API refresh token
* `GH_TOKEN`: Needs permission to update "Repository secrets" to keep `TRAKT_ACCESS_TOKEN`: refreshed
* `PLEX_USERNAME`: Plex email or username
* `PLEX_PASSWORD`: Plex password
* `PLEX_SERVER`: Plex server name
* `PLEX_TOKEN`: Plex server token
