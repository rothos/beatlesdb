
# The "TheHoleGotFixed.tsv" file is from:
# https://www.beatlesbible.com/forum/recording-and-musicology/keys-that-the-beatles-used-now-that-youve-found-another-key/
# The name comes from the username of that post.

import db

def main():
    songs = db.load()

    with open("TheHoleGotFixed.tsv") as f:
        for line_number, line in enumerate(f.readlines()):
            if line_number == 0:
                # Skip header.
                pass
            else:
                line = line.rstrip()
                title, tempos, key = line.split("\t")
                title = title.replace("’", "'") \
                        .replace(" ‘", "'") \
                        .replace(" !", "!") \
                        .replace(" ?", "?") \
                        .replace("inPepperland", "in Pepperland")
                song = db.get_song_by_title(songs, title)
                if song is None:
                    print(f"Can't find song \"{title}\".")
                else:
                    tempos = [int(tempo) for tempo in tempos.split("/")]
                    if "TheHoleGotFixed" not in song:
                        song["TheHoleGotFixed"] = {}
                    song["TheHoleGotFixed"]["tempos"] = tempos
                    song["TheHoleGotFixed"]["key"] = key
                    if "tempo" in song["TheHoleGotFixed"]:
                        del song["TheHoleGotFixed"]["tempo"]

    db.save(songs)

main()

