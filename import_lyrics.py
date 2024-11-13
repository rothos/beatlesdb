import json
import requests
import time
import string
import unicodedata
import asyncio
import aiohttp
import re
from typing import Dict, List, Optional

async def fetch_lyrics(session: aiohttp.ClientSession, title: str) -> Dict:
    """
    Fetch lyrics for a song title using lyrics.ovh API
    """
    # Normalize the title to ASCII
    ascii_title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode()
    
    url = f"https://api.lyrics.ovh/v1/beatles/{ascii_title}"
    alternate_url = f"https://api.lyrics.ovh/v1/the%20beatles/{ascii_title}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"{title}: success")
                return {
                    'title': title,
                    'status': 'success',
                    'lyrics': data.get('lyrics', '')
                }
            elif response.status == 404:
                # Try alternate URL
                async with session.get(alternate_url) as alternate_response:
                    if alternate_response.status == 200:
                        data = await alternate_response.json()
                        print(f"{title}: success")
                        return {
                            'title': title,
                            'status': 'success',
                            'lyrics': data.get('lyrics', '')
                        }
                    else:
                        print(f"{title}: error {alternate_response.status} (both URLs)")
                        return {
                            'title': title,
                            'status': 'error',
                            'error': f"404 on primary, {alternate_response.status} on alternate"
                        }
            else:
                print(f"{title}: error {response.status}")
                return {
                    'title': title,
                    'status': 'error',
                    'error': response.status
                }
    except Exception as e:
        print(f"{title}: error {str(e)}")
        return {
            'title': title,
            'status': 'error',
            'error': str(e)
        }

def compare_stripped_strings(str1, str2):
    # Remove whitespace and punctuation, convert to lowercase
    def clean_string(s):
        return ''.join(char.lower() for char in s if char not in string.punctuation).strip()
    
    return clean_string(str1) == clean_string(str2)

def remove_author_credits(text):
    pattern = r'^\((?:harrison|lennon|mccartney|starkey)\)\s*'
    return re.sub(pattern, '', text, flags=re.IGNORECASE)

async def main(limit: Optional[int] = None):
    """
    Main function to fetch and store lyrics
    Args:
        limit: Optional integer to limit the number of songs to process
    """
    # Load existing lyrics if available
    try:
        with open('lyrics.json', 'r', encoding='utf-8') as file:
            lyrics_array = json.load(file)
            existing_titles = {song['title'] for song in lyrics_array}
    except FileNotFoundError:
        lyrics_array = []
        existing_titles = set()

    # Load song titles from beatles_songs.json
    with open('beatles_songs.json', 'r', encoding='utf-8') as file:
        songs = json.load(file)

    # Create list of songs that need lyrics
    songs_to_fetch = [
        song['title'] for song in songs 
        if song['title'] not in existing_titles
    ]

    # Apply limit if specified
    if limit is not None:
        songs_to_fetch = songs_to_fetch[:limit]
        print(f"Processing first {limit} songs that need lyrics")
    
    print(f"Total songs to process: {len(songs_to_fetch)}")

    # Fetch lyrics asynchronously
    async with aiohttp.ClientSession() as session:
        # Create tasks for all songs that need lyrics
        tasks = [
            fetch_lyrics(session, title) 
            for title in songs_to_fetch
        ]
        
        # Process in batches to be respectful to the API
        successful_fetches = 0
        failed_fetches = 0
        
        for i in range(0, len(tasks), 5):
            batch = tasks[i:i+5]
            results = await asyncio.gather(*batch)
            
            # Process results
            for result in results:
                if result['status'] == 'success':
                    lyrics = result['lyrics'].strip()
                    lyrics = remove_author_credits(lyrics)

                    # Instrumental songs sometimes have lyrics that say "instrumental"
                    if len(lyrics) < 20 and compare_stripped_strings(lyrics, "instrumental"):
                        lyrics = ""

                    # Add to lyrics array
                    lyrics_array.append({
                        'title': result['title'],
                        'lyrics.ovh': lyrics
                    })
                    successful_fetches += 1
                else:
                    # Add to lyrics array with None for failed fetches
                    lyrics_array.append({
                        'title': result['title'],
                        'lyrics.ovh': None
                    })
                    failed_fetches += 1
            
            # Wait between batches to be nice to the API
            if i + 5 < len(tasks):
                await asyncio.sleep(1)

    # Print summary
    print(f"\nSummary:")
    print(f"    Successfully fetched: {successful_fetches}")
    print(f"    Failed to fetch: {failed_fetches}")

    # Save updated lyrics
    with open('lyrics.json', 'w', encoding='utf-8') as file:
        json.dump(sorted(lyrics_array, key=lambda a: a["title"]), file, indent=4, sort_keys=True, ensure_ascii=False)

if __name__ == "__main__":
    # You can modify this number to test with fewer songs
    LIMIT = None  # Set to None to process all songs
    asyncio.run(main(LIMIT))
