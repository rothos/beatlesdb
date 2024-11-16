# Beatles Database

Beatles songs database.

# Resources

- [MIR Python module](https://mirdata.readthedocs.io/en/0.3.5/_modules/mirdata/datasets/beatles.html)
    - Note [link to archive](http://isophonics.net/files/annotations/The%20Beatles%20Annotations.tar.gz).
- [Beatles song sorted by key](https://www.reddit.com/r/beatles/comments/134qk5r/beatles_songs_sorted_by_key/)
- [The Beatles API](https://github.com/vrandall66/the-beatles-api)
    - Seems to have dozens of Beatles songs as an API.
- [All songs, on official website](https://www.thebeatles.com/songs)
- [Visualizing songs by year](https://www.yendor.com/Beatles/)
    - [JSON data file](https://www.yendor.com/Beatles/Beatles.json)
- [All data from Spotify](https://www.kaggle.com/datasets/chadwambles/allbeatlesspotifysongdata2009remaster)
    - Provides various data in CSV format.
- [List of all Beatles songs from BeatlesBible.com (maybe more comprehensive than other lists)](https://www.beatlesbible.com/songs/)
- [Website with Beatles songs, includes personnel/song credits](https://beatlestube.net/the-beatles-songs/)
- [Lyrics to Beatles songs (this site seems more scrape-able than most)](https://www.beatleslyrics.org/index_files/Page13763.htm)
- [Wikipedia article "List of songs recorded by the Beatles"](https://en.wikipedia.org/wiki/List_of_songs_recorded_by_the_Beatles)
- [Alan Pollack's "Notes on..." series](https://www.icce.rug.nl/~soundscapes/DATABASES/AWP/awp-notes_on.shtml)

# Schema of `beatles_songs.json`

- `title`: Title of the song.
- `other_titles`: List of synonyms.
- `yendor`: Data we pulled from the [yendor database](https://www.yendor.com/Beatles/).
- `pannell`: Data we pulled from David J. Pannell (2023). _Quantitative Analysis of the Evolution of The Beatles’ Releases for EMI, 1962 – 1970_, Journal of Beatles Studies volume 2.
    - `album`: Data about the album version of the song (always present).
    - `single`: Data about the single version of the song (rarely present).
