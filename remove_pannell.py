
import db

def main():
    songs = db.load()

    for song in songs:
        if "pannell" in song:
            del song["pannell"]

    db.save(songs)

main()

