
# Import links to Wikipedia pages about each song.

import urllib.request
import db
import re

URL = "https://en.wikipedia.org/w/index.php?title=List_of_songs_recorded_by_the_Beatles&action=raw"
URL_PREFIX = "https://en.wikipedia.org/wiki/"

LINKS_RE = re.compile(r"\[\[.*?\]\]")

def main():
    songs = db.load()

    main_page = urllib.request.urlopen(URL).read().decode("utf-8")
    #main_page = open("x").read()

    sections = main_page.split("\n\n")
    sections = [section for section in sections if section.startswith("{|")]

    # Currently only import the first table.
    table = sections[0]
    table = table.rstrip("|}")
    rows = table.split("\n|-\n")
    found = False
    for row in rows:
        cols = row.strip().split("\n")
        if cols and "anchor|A" in cols[0]:
            found = True
        if found:
            if len(cols) != 6:
                print("Found unusual row", cols)
                return
            # Just focus on song title.
            cell = cols[0]
            links = LINKS_RE.findall(cell)
            if len(links) == 0:
                print("Found no links", cell)
                return
            parts = links[0][2:-2].split("|")
            link = parts[0]
            title = parts[0] if len(parts) == 1 else parts[1]
            url = URL_PREFIX + link
            song = db.get_song_by_title(songs, title)
            if song:
                song["wikipedia"] = {
                    "url": url,
                }
            else:
                print(f"Didn't find song \"{title}\"")

    db.save(songs)

main()
