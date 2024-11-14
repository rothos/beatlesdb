# Beatles Database

Beatles songs database by [Hrothgar](https://gar.lol/) and [Lawrence](https://www.teamten.com/lawrence/).
[Some graphs](https://gar.lol/beatlesdb/).

# Resources

- [The Beatles API](https://github.com/vrandall66/the-beatles-api)
    - Seems to have dozens of Beatles songs as an API.
    - [Actual song data](https://github.com/vrandall66/the-beatles-api/blob/master/songsData.js)
- [All songs, on official website](https://www.thebeatles.com/songs)
- [List of all Beatles songs from BeatlesBible.com (maybe more comprehensive than other lists)](https://www.beatlesbible.com/songs/)
- [Website with Beatles songs, includes personnel/song credits](https://beatlestube.net/the-beatles-songs/)
- [Lyrics to Beatles songs (this site seems more scrape-able than most)](https://www.beatleslyrics.org/index_files/Page13763.htm)
- [Alan Pollack's "Notes on..." series](https://www.icce.rug.nl/~soundscapes/DATABASES/AWP/awp-notes_on.shtml)

# Schema of `beatles_songs.json`

- `title`: Title of the song.
- `other_titles`: List of synonyms.
- `yendor`: Data we pulled from the [yendor database](https://www.yendor.com/Beatles/).
- `pannell`: Data we pulled from David J. Pannell (2023). _Quantitative Analysis of the Evolution of The Beatles’ Releases for EMI, 1962 – 1970_, Journal of Beatles Studies volume 2.
- `chadwambles`: Data we pull from [Chad Wambles's dataset](https://www.kaggle.com/datasets/chadwambles/allbeatlesspotifysongdata2009remaster) (`TheBeatlesCleaned.csv`).
- `wikipedia`: Links to Wikipedia entries for the song, scraped from [this index page](https://en.wikipedia.org/wiki/List_of_songs_recorded_by_the_Beatles).
- `isophonics`: Data from the [isophonics.net database](http://isophonics.net/files/annotations/The%20Beatles%20Annotations.tar.gz).
    - `keylab`: Timestamps and the key that part of the song is in.
    - `seglab`: Timestamps and the type of segment (verse, etc.).
    - `chordlab`: Timestamps and chord being played.
