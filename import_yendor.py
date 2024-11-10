
# Import data from https://www.yendor.com/Beatles/

import urllib.request
import json
import db

URL = "https://www.yendor.com/Beatles/Beatles.json"

# Keys we don't care about.
BAD_KEYS = {'group', '_id', 'name', 'Other.releases'}

def main():
    songs = db.load()

    yendor_songs = json.load(urllib.request.urlopen(URL))
    nodes = yendor_songs["nodes"]
    all_keys = set()
    for node in nodes:
        if "Title" in node:
            title = node["Title"]
            song = db.get_song_by_title(songs, title)
            if song is None:
                song = {"title": title}
                songs.append(song)

            yendor = {}
            for key in node.keys():
                if key not in BAD_KEYS:
                    yendor[key.lower()] = node[key]
            song["yendor"] = yendor

    db.save(songs)

main()
