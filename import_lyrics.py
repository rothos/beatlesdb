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
                    print(f"Found {len(lyrics)} results for {title}!")

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

async def fetch_from_api(session, api, title):
    result = await api.fetch_lyrics(session, title)
    result['title'] = title
    return result

async def main(limit: Optional[int] = None):
    # Initialize APIs
    apis = [
        LyricsOvhAPI(),
        ChartLyricsAPI()
    ]

    # Load existing lyrics
    try:
        with open('lyrics.json', 'r', encoding='utf-8') as file:
            lyrics_array = json.load(file)
    except FileNotFoundError:
        lyrics_array = []

    # Create dictionary of existing lyrics
    existing_lyrics = {song['title']: song for song in lyrics_array}

    # Load song titles
    with open('beatles_songs.json', 'r', encoding='utf-8') as file:
        song_titles = json.load(file)

    # Create list of songs to process
    songs_to_process = song_titles[:limit] if limit else song_titles
    
    print(f"Total songs to process: {len(songs_to_process)}")

    async with aiohttp.ClientSession() as session:
        for song in songs_to_process:
            title = song['title']
            current_entry = existing_lyrics.get(title, {})
            
            for api in apis:
                # Skip if we already have lyrics for this API
                if api.name in current_entry:
                    continue

                print(f"Fetching {title} from {api.name}")
                result = await fetch_from_api(session, api, title)

                if result['status'] == 'success':
                    lyrics = result['lyrics'].strip()
                    lyrics = remove_author_credits(lyrics)

                    if len(lyrics) < 20 and compare_stripped_strings(lyrics, "instrumental"):
                        lyrics = ""

                    if title not in existing_lyrics:
                        existing_lyrics[title] = {'title': title}
                    existing_lyrics[title][api.name] = lyrics
                else:
                    if title not in existing_lyrics:
                        existing_lyrics[title] = {'title': title}

                    print("    " + result['error'])
                    existing_lyrics[title][api.name] = None

                await asyncio.sleep(1)  # Be nice to the API

    # Convert dictionary back to list and save
    updated_lyrics_array = list(existing_lyrics.values())
    with open('lyrics.json', 'w', encoding='utf-8') as file:
        json.dump(sorted(updated_lyrics_array, key=lambda x: x['title']), 
                 file, indent=4, sort_keys=True, ensure_ascii=False)

if __name__ == "__main__":
    LIMIT = 2
    asyncio.run(main(LIMIT))
