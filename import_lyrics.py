# Known bugs/issues:
#   - Many song lyrics have attribution at the beginning and there is not a
#     reliable way to get ride of those attributions, as far as I can tell.
#     e.g. the lyrics.ovh result for "Oh Bonnie" begins with "
#     (Traditional, arranged by Tony Sheridan)". Most attributions are in
#     parentheses but we can't use parens as a hard rule for what to strip,
#     because some songs start with backing vocals that are sometimes put in
#     parens in lyrics (see "Magical Mystery Tour", e.g.")
#   - Some of the songs that are instrumentals correctly have an empty string
#     for the lyrics, while others say something like "Instrumental arranged
#     by George Martin" or something.
#   - "Songs that will be processed" output at the beginning of script run
#      does not take into account the recently added REFETCH_PREVIOUS_404S
#      flag. If REFETCH_PREVIOUS_404S = False then the output gives a number
#      which may be spuriously high (e.g. it might say 20 instead of 0).
#   - ChartLyrics gives a (non-404) error for only these songs:
#         - "All I've Got to Do"
#         - "Because"
#         - "Come and Get It"
#         - "From Me to You"
#         - "How Do You Do It?"
#         - "I Will"
#         - "I'll Be on My Way"
#         - "I'll Get You"
#         - "It's All Too Much"
#         - "You Can't Do That"
#         - "You Like Me Too Much"
#         - "You Won't See Me"
#     I have submitted an issue on GitHub about it:
#         https://github.com/matheusfillipe/chartlyrics/issues/1

import json
import requests
import time
import string
import unicodedata
import asyncio
import aiohttp
import re
from typing import Dict, List, Optional
from chartlyrics import ChartLyricsClient

class LyricsAPI:
    """Base class for lyrics APIs"""
    def __init__(self, name):
        self.name = name

    async def fetch_lyrics(self, session, title):
        raise NotImplementedError

class LyricsOvhAPI(LyricsAPI):
    def __init__(self):
        super().__init__("lyrics.ovh")

    async def fetch_lyrics(self, session, title):
        ascii_title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode()
        url = f"https://api.lyrics.ovh/v1/beatles/{ascii_title}"
        alternate_url = f"https://api.lyrics.ovh/v1/the%20beatles/{ascii_title}"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {'status': 'success', 'lyrics': data.get('lyrics', '')}
                elif response.status == 404:
                    async with session.get(alternate_url) as alternate_response:
                        if alternate_response.status == 200:
                            data = await alternate_response.json()
                            return {'status': 'success', 'lyrics': data.get('lyrics', '')}
                        else:
                            return {'status': 'error', 'error': f"404 on primary, {alternate_response.status} on alternate"}
                else:
                    return {'status': 'error', 'error': response.status}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

class ChartLyricsAPI(LyricsAPI):
    def __init__(self):
        super().__init__("chartlyrics")
        self.client = ChartLyricsClient()

    async def fetch_lyrics(self, session, title):
        try:
            lyrics = []
            for result in self.client.search_artist_and_song("the beatles", title):
                # Check to see if the title matches (more than one might, so we
                # add to an array)
                if slugify(result.song) == slugify(title):
                    lyrics += [result.lyrics]
                
                if len(lyrics) > 1:
                    print(f"    Found {len(lyrics)} results for {title}!")

                if len(lyrics) >= 1:
                    return {'status': 'success', 'lyrics': lyrics[0]}
                
            return {'status': 'error', 'error': 'No matching song found'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def slugify(s):
    return "".join([c for c in s if c not in string.punctuation and c not in string.whitespace]).lower()

def compare_stripped_strings(str1, str2):
    def clean_string(s):
        return ''.join(char.lower() for char in s if char not in string.punctuation).strip()
    return clean_string(str1) == clean_string(str2)

def remove_author_credits(text):
    pattern = r'^$$(?:harrison|lennon|mccartney|starkey)$$\s*'
    return re.sub(pattern, '', text, flags=re.IGNORECASE)

async def fetch_from_api(session, api, song_data):
    # First try with the canonical title
    result = await api.fetch_lyrics(session, song_data['title'])
    if result['status'] == 'success':
        result['title'] = song_data['title']
        return result

    # If that fails and there are other titles, try those
    if 'other_titles' in song_data:
        for alt_title in song_data['other_titles']:
            alt_result = await api.fetch_lyrics(session, alt_title)
            if alt_result['status'] == 'success':
                # Use the canonical title even though we found it with an alternative
                alt_result['title'] = song_data['title']
                return alt_result

    # If everything failed, return the original failed result
    result['title'] = song_data['title']
    return result

async def main(limit: Optional[int] = None, refetch: Optional[bool] = True):
    # Initialize APIs
    apis = [
        LyricsOvhAPI(),
        ChartLyricsAPI()
    ]

    # Add statistics tracking
    stats = {api.name: {'attempts': 0, 'successes': 0} for api in apis}

    # Load existing lyrics
    try:
        with open('lyrics.json', 'r', encoding='utf-8') as file:
            lyrics_array = json.load(file)
    except FileNotFoundError:
        lyrics_array = []

    # Load song titles
    with open('beatles_songs.json', 'r', encoding='utf-8') as file:
        song_titles = json.load(file)

    # Create a complete lyrics array with all songs
    existing_lyrics = {song['title']: song for song in lyrics_array}

    # Add any new songs from song_titles that aren't in existing_lyrics
    for song in song_titles:
        if song['title'] not in existing_lyrics:
            existing_lyrics[song['title']] = {'title': song['title']}

    # Find songs that need processing
    songs_needing_processing = []

    # Sort the items before figuring out which ones to process
    for title, data in sorted(existing_lyrics.items(), key=lambda x: x[0]):
        needs_processing = False
        for api in apis:
            if api.name not in data or not isinstance(data[api.name], str):
                needs_processing = True
                break
        if needs_processing:
            songs_needing_processing.append(title)

    # Determine how many songs to process
    songs_to_process = songs_needing_processing[:limit] if limit else songs_needing_processing
    
    print(f"Songs needing processing: {len(songs_needing_processing)}")

    # TODO/BUG: This doesn't take into account the recently added "REFETCH_PREVIOUS_404S" flag.
    print(f"Songs that will be processed: {len(songs_to_process)}")

    # Create a mapping of titles to full song data
    song_data_map = {song['title']: song for song in song_titles}

    async with aiohttp.ClientSession() as session:
        for index, title in enumerate(songs_to_process):
            current_entry = existing_lyrics[title]
            
            # Save to our json file every 5 songs
            if index % 5 == 0:
                updated_lyrics_array = list(existing_lyrics.values())
                with open('lyrics.json', 'w', encoding='utf-8') as file:
                    json.dump(sorted(updated_lyrics_array, key=lambda x: x['title']), 
                             file, indent=4, sort_keys=True, ensure_ascii=False)

            fetching_yet = False

            for api in apis:
                # Skip if we already have lyrics for this API
                if api.name in current_entry and (isinstance(current_entry[api.name], str) or refetch == False):
                    continue

                if not fetching_yet:
                    print(f"Fetching \"{title}\"")
                    fetching_yet = True

                print(f"    from {api.name}... ", end="")
                
                # Pass the full song data
                song_data = song_data_map.get(title, {'title': title})
                result = await fetch_from_api(session, api, song_data)

                stats[api.name]['attempts'] += 1

                if result['status'] == 'success':
                    lyrics = result['lyrics'].strip()
                    lyrics = remove_author_credits(lyrics)

                    if len(lyrics) < 20 and compare_stripped_strings(lyrics, "instrumental"):
                        lyrics = ""

                    existing_lyrics[title][api.name] = lyrics
                    stats[api.name]['successes'] += 1

                    print(" success")
                else:
                    print("error: " + result['error'])
                    existing_lyrics[title][api.name] = None

                await asyncio.sleep(0.2)  # Be nice to the API

    # Convert dictionary back to list and save
    updated_lyrics_array = list(existing_lyrics.values())
    with open('lyrics.json', 'w', encoding='utf-8') as file:
        json.dump(sorted(updated_lyrics_array, key=lambda x: x['title']), 
                 file, indent=4, sort_keys=True, ensure_ascii=False)

    # Print statistics
    print("\nFinal Statistics:")
    for api_name, stat in stats.items():
        attempts = stat['attempts']
        successes = stat['successes']
        if attempts > 0:
            print(f"    {api_name}: {successes}/{attempts} successes")


if __name__ == "__main__":

    # Limit on how many songs to try to fetch this round.
    LIMIT = None
    
    # Want to try to refetch songs that were 404 not found before?
    # Or just skip them and import any new songs we haven't tried to find yet?
    REFETCH_PREVIOUS_404S = True

    asyncio.run(main(LIMIT, REFETCH_PREVIOUS_404S))
