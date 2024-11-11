
import os
import json

FILENAME = "beatles_songs.json"

def load():
    with open(FILENAME) as f:
        return json.load(f)

def save(songs):
    # Keep a backup in case the save fails.
    os.rename(FILENAME, FILENAME + ".bak")

    # Write to make git diffs more readable: Sort by song title, and sort keys.
    with open(FILENAME, "w") as f:
        json.dump(sorted(songs, key=lambda song: song["title"]), f, sort_keys=True, indent=4)

def get_song_by_title(songs, title):
    title = title.lower()

    for song in songs:
        if title in [t.lower() for t in [song["title"]] + song.get("other_titles", [])]:
            return song

    return None

