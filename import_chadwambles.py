
import csv
import db

FILENAME = "TheBeatlesCleaned.csv"

def main():
    songs = db.load()

    with open(FILENAME) as f:
        for row in csv.DictReader(f):
            # Keys are: id,year,album,song,danceability,energy,speechiness,acousticness,liveness,valence,duration_ms
            title = row["song"]
            song = db.get_song_by_title(songs, title)
            if song is None:
                print(f"Can't find song \"{title}\"")
            else:
                song["chadwambles"] = {
                    "year": int(row["year"]),
                    "album": row["album"],
                    "song": row["song"],
                    "danceability": float(row["danceability"]),
                    "energy": float(row["energy"]),
                    "speechiness": float(row["speechiness"]),
                    "acousticness": float(row["acousticness"]),
                    "liveness": float(row["liveness"]),
                    "valence": float(row["valence"]),
                    "duration_ms": int(row["duration_ms"]),
                }

    db.save(songs)

main()
