
import os
import pathlib
import db

URL_NAME = "The%20Beatles%20Annotations.tar.gz"
URL = "http://isophonics.net/files/annotations/" + URL_NAME
DIR = "The_Beatles_Annotations"

# Convert a pathname to a song title.
def pathname_to_title(pathname):
    title = pathlib.Path(pathname).stem
    title = title.split("_-_")[-1].replace("_", " ")
    return title

# Get all pathnames starting at root_dir with the given extension.
def get_pathnames(root_dir, extension):
    files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        files.extend(os.path.join(dirpath, filename)
                     for filename in filenames
                     if filename.endswith(extension))

    return files

# Array of (song, lines) tuples.
def get_song_lines(songs, subdir):
    song_lines = []

    pathnames = get_pathnames(DIR + "/" + subdir, ".lab")
    for pathname in pathnames:
        title = pathname_to_title(pathname)
        song = db.get_song_by_title(songs, title)
        if song is None:
            print(f"Can't find song \"{title}\" ({pathname})")
        else:
            with open(pathname) as f:
                lines = f.read().strip().split("\n")
                song_lines.append( (song, lines) )

    return song_lines

def main():
    if not os.path.isdir(DIR):
        print()
        print("Download the following file:")
        print()
        print("    " + URL)
        print()
        print("and untar it into a directory called \"" + DIR + "\" in the current directory.")
        print()
        print("    % curl -O " + URL)
        print("    % mkdir " + DIR)
        print("    % tar xvzf \"" + URL_NAME + "\" --directory " + DIR)
        print()
        print("Then run this script again.")
        print()
        return

    songs = db.load()

    # Get the key songs are in.
    for song, lines in get_song_lines(songs, "keylab"):
        infos = []
        for line in lines:
            fields = line.split("\t")
            info = {
                    "beginTime": float(fields[0]),
                    "endTime": float(fields[1]),
                    "sectionType": fields[2],
            }
            if fields[2] == "Key":
                info["key"] = fields[3]
            infos.append(info)
        if "isophonics" not in song:
            song["isophonics"] = {}
        song["isophonics"]["keylab"] = infos

    # Get the segments of the songs.
    for song, lines in get_song_lines(songs, "seglab"):
        infos = []
        for line in lines:
            fields = line.split("\t", 3)
            if len(fields) != 4:
                print("seg doesn't have 4 fields", song["title"], fields)
            info = {
                    "beginTime": float(fields[0]),
                    "endTime": float(fields[1]),
                    "segment": fields[3],
            }
            infos.append(info)
        if "isophonics" not in song:
            song["isophonics"] = {}
        song["isophonics"]["seglab"] = infos

    # Get the song chords.
    for song, lines in get_song_lines(songs, "chordlab"):
        infos = []
        for line in lines:
            fields = line.split(" ")
            if len(fields) != 3:
                print("chord doesn't have 3 fields", fields)
            info = {
                    "beginTime": float(fields[0]),
                    "endTime": float(fields[1]),
                    "chord": fields[2],
            }
            infos.append(info)
        if "isophonics" not in song:
            song["isophonics"] = {}
        song["isophonics"]["chordlab"] = infos

    db.save(songs)

main()
