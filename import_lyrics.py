import asyncio
import aiohttp
import json
import re
import html
import unicodedata
import string
import shutil
import chardet
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import quote
from unidecode import unidecode

class LyricsAPI:
    def __init__(self, name):
        self.name = name

    async def fetch_lyrics(self, session, title, options=None):
        raise NotImplementedError

class LyricsOvhAPI(LyricsAPI):
    def __init__(self):
        super().__init__("lyrics.ovh")

    async def fetch_lyrics(self, session, title, options=None):
        # First attempt with "The Beatles"
        url = f"https://api.lyrics.ovh/v1/The Beatles/{quote(title)}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return {'status': 'success', 'lyrics': json_response['lyrics']}
                else:
                    # If first attempt fails, try with "Beatles"
                    url = f"https://api.lyrics.ovh/v1/Beatles/{quote(title)}"
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                json_response = await response.json()
                                return {'status': 'success', 'lyrics': json_response['lyrics']}
                            else:
                                return {'status': 'error', 'error': f"HTTP {response.status} (both URLs failed)"}
                    except Exception as e:
                        return {'status': 'error', 'error': f"Second attempt failed: {str(e)}"}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

class ChartLyricsAPI(LyricsAPI):
    def __init__(self):
        super().__init__("chartlyrics.com")

    async def fetch_lyrics(self, session, title, options=None):
        # First, search for the song
        search_url = f"http://api.chartlyrics.com/apiv1.asmx/SearchLyric?artist=beatles&song={quote(title)}"
        try:
            async with session.get(search_url) as response:
                if response.status != 200:
                    return {'status': 'error', 'error': f"HTTP {response.status} on search"}
                
                text = await response.text()
                if not text:
                    return {'status': 'error', 'error': 'Empty response from search'}

                # Find all song entries
                songs = re.finditer(r'<SearchLyricResult>.*?</SearchLyricResult>', text, re.DOTALL)
                
                # Look for matching song
                for song_match in songs:
                    song_xml = song_match.group(0)
                    
                    # Extract song title
                    song_title_match = re.search(r'<Song>([^<]+)</Song>', song_xml)
                    if not song_title_match:
                        continue
                    
                    song_title = song_title_match.group(1)
                    
                    # Check if this is the song we're looking for
                    if slugify(song_title) == slugify(title):
                        # Extract LyricId and LyricChecksum
                        lyric_id_match = re.search(r'<LyricId>(\d+)</LyricId>', song_xml)
                        checksum_match = re.search(r'<LyricChecksum>([^<]+)</LyricChecksum>', song_xml)
                        
                        if lyric_id_match and checksum_match:
                            lyric_id = lyric_id_match.group(1)
                            checksum = checksum_match.group(1)
                            
                            # If we found a match with valid ID and checksum, fetch the lyrics
                            lyrics_url = f"http://api.chartlyrics.com/apiv1.asmx/GetLyric?lyricId={lyric_id}&lyricCheckSum={checksum}"
                            
                            async with session.get(lyrics_url) as lyrics_response:
                                if lyrics_response.status != 200:
                                    return {'status': 'error', 'error': f"HTTP {lyrics_response.status} on lyrics fetch"}
                                
                                lyrics_text = await lyrics_response.text()
                                lyrics_match = re.search(r'<Lyric>([^<]+)</Lyric>', lyrics_text)
                                
                                if lyrics_match:
                                    return {'status': 'success', 'lyrics': lyrics_match.group(1)}
                                else:
                                    return {'status': 'error', 'error': 'No lyrics found in response'}
                
                return {'status': 'error', 'error': 'No matching song found'}

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

class BeatlesLyricsOrgAPI(LyricsAPI):
    def __init__(self):
        super().__init__("beatleslyrics.org")
        self.base_url = "https://www.beatleslyrics.org/index_files/"
        self.main_content = None

    async def fetch_lyrics(self, session, title, options=None):
        try:
            if not self.main_content:
                self.main_content = await self._fetch_page(session, self.base_url + "Page13763.htm")
                if not self.main_content:
                    return {'status': 'error', 'error': 'Failed to fetch main page'}

            links = self._extract_links(self.main_content)
            song_link = self._find_matching_link(links, title)
            
            if not song_link:
                return {'status': 'error', 'error': 'Song page not found'}

            url = self.base_url + song_link['href']
            page_content = await self._fetch_page(session, url)
            
            if not page_content:
                return {'status': 'error', 'error': 'Failed to fetch song page'}

            return self._process_lyrics_page(page_content, title, options=options)

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def _fetch_page(self, session, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                content = await response.read()
                detected = chardet.detect(content)
                try:
                    return content.decode(detected['encoding'] or 'utf-8')
                except UnicodeDecodeError:
                    return content.decode('utf-8', errors='ignore')
            return None

    def _extract_links(self, content):
        soup = BeautifulSoup('\n'.join(content.splitlines()[1000:]), 'html.parser')
        links = []
        pattern = re.compile(r'Page\d+\.htm$')
        
        for anchor in soup.find_all('a'):
            href = anchor.get('href', '')
            if pattern.search(href):
                links.append({
                    'href': href,
                    'text': anchor.get_text(strip=True)
                })
        
        return links

    def _find_matching_link(self, links, title):
        slug_title = slugify(title)
        for link in links:
            if slugify(link['text']) == slug_title:
                return link
        return None

    def _process_lyrics_page(self, content, title, options=None):
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        
        if not tables:
            return {'status': 'error', 'error': 'No tables found in page'}
        
        last_table = tables[-1]
        
        # Dumb hack for inconsistently formatted website
        if title == "Wild Honey Pie":
            last_table = tables[-2]

        if title == "Komm Gib Mir Deine Hand":
            last_table = tables[-3]

        spans = last_table.find_all('span')
        
        if len(spans) < 2:
            return {'status': 'error', 'error': 'Less than 2 spans found in table'}
        
        spandex = 0 # span index
        page_title = spans[0].get_text(strip=True)

        # Some pages are inconsistently formatted and have an empty span before the title
        if len(page_title) == 0 and len(spans) > 1:
            page_title = spans[1].get_text(strip=True)
            spandex = 1

        if slugify(page_title) not in [slugify(t) for t in [title]+options.get('other_titles', [])]:
            return {'status': 'error', 'error': f"Page title does not match expected title: ({slugify(page_title)}) vs ({slugify(title)})"}
        
        writer_credit = spans[spandex+1].get_text(strip=True)
        if not (writer_credit.startswith('(') and writer_credit.endswith(')')) \
            and "lennon" not in writer_credit.lower() and "mccartney" not in writer_credit.lower():
                return {'status': 'error', 'error': 'Writer credit not properly formatted'}
        
        lyrics_content = str(last_table)
        for span in spans[:spandex+2]:
            lyrics_content = lyrics_content.replace(str(span), '')
        
        lyrics = BeautifulSoup(lyrics_content, 'html.parser').get_text()
        lyrics = re.sub(r'<br\s*/?\s*>', '\n', lyrics, flags=re.IGNORECASE)
        lyrics = re.sub(r'<[^>]+>', '', lyrics)
        lyrics = normalize_lyrics(re.sub(r'\n\s*\n', '\n', lyrics).strip())
        
        return {'status': 'success', 'lyrics': lyrics}

def slugify(text):
    """Convert text to a normalized form for comparison"""
    text = unidecode(str(text).lower())
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def normalize_lyrics(text):
    """Sanitizes text by removing or replacing unwanted characters and normalizing whitespace."""
    if not text:
        return ""

    text = str(text) # Convert to string if not already
    text = html.unescape(text) # Decode HTML entities

    # Normalize multiple newlines to maximum of two
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Split into lines
    lines = text.split('\n')

    cleaned_lines = []
    for line in lines:
        # Strip whitespace
        new_line = line.strip()

        # Replace smart quotes with regular quotes
        new_line = new_line.replace('“', '"').replace('”', '"')
        new_line = new_line.replace('‘', "'").replace('’', "'")
        
        new_line = unicodedata.normalize('NFKD', new_line) # Normalize unicode characters

        # Remove control characters except newline
        new_line = ''.join(ch for ch in new_line if unicodedata.category(ch)[0] != "C")

        # Replace multiple whitespace with single space
        new_line = re.sub(r'[ \t]+', ' ', new_line)
        
        # Remove non-ASCII characters but keep basic punctuation
        new_line = re.sub(r'[^\x20-\x7E\u2018\u2019\u201C\u201D]', '', new_line)

        cleaned_lines += [new_line]

    return "\n".join(cleaned_lines)

def backup_lyrics_file():
    """Backup lyrics.json if it exists and is not empty"""
    try:
        with open('lyrics.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if data:  # Only backup if file has content
                    shutil.copy2('lyrics.json', 'lyrics.json.bak')
                    print("Created backup: lyrics.json.bak")
            except json.JSONDecodeError:
                # File exists but is empty or invalid
                print("Existing lyrics.json is empty or invalid - creating new file")
                with open('lyrics.json', 'w', encoding='utf-8') as f:
                    json.dump([], f)
    except FileNotFoundError:
        # Create an empty lyrics.json file
        with open('lyrics.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        print("Created new lyrics.json file")

def compare_stripped_strings(str1, str2):
    """Compare two strings after removing punctuation, whitespace, and case"""
    def clean_string(s):
        s = str(s) if s is not None else ""
        return ''.join(char.lower() for char in s if char not in string.punctuation).strip()
    return clean_string(str1) == clean_string(str2)

def remove_author_credits(text):
    """Remove author credits from the beginning of lyrics"""
    if not text:
        return ""
    
    pattern1 = r'^$$(?:harrison|lennon|mccartney|starkey)$$\s*'
    pattern2 = r'^\s*$$[^)]+$$\s*'
    
    text = re.sub(pattern1, '', text, flags=re.IGNORECASE)
    text = re.sub(pattern2, '', text, flags=re.IGNORECASE)
    
    return text.strip()

async def fetch_from_api(session, api, song_data):
    """Wrapper for API calls to handle errors consistently"""
    try:
        # First try with the main title
        result = await api.fetch_lyrics(session, song_data['title'], options=song_data)
        
        # If the main title fails and there are alternate names, try those
        if result['status'] == 'error' and 'other_titles' in song_data:
            for alt_name in song_data['other_titles']:
                alt_result = await api.fetch_lyrics(session, alt_name, options=song_data)
                if alt_result['status'] == 'success':
                    # Add indication that this was found using an alternate name
                    alt_result['alternate_name_used'] = alt_name
                    return alt_result
                await asyncio.sleep(0.1)  # Small delay between attempts
        
        return result
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

async def main(apis: Optional[list] = None,
               limit: Optional[int] = None,
               refetch: Optional[bool] = True,
               start_at: Optional[str] = ""):
    # Backup existing lyrics file before starting
    backup_lyrics_file()

    # Initialize APIs
    if not apis:
        apis = [
            LyricsOvhAPI(),
            ChartLyricsAPI(),
            BeatlesLyricsOrgAPI()
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
    processed_count = 0  # Track actual API calls made

    # Sort the items before processing
    for title, data in sorted(existing_lyrics.items(), key=lambda x: x[0]):
        needs_processing = False
        for api in apis:
            if api.name not in data or (not isinstance(data[api.name], str) and refetch):
                needs_processing = True
                break
        if needs_processing:
            songs_needing_processing.append(title)

    # Determine how many songs to process
    songs_to_process = songs_needing_processing[:limit] if limit else songs_needing_processing
    
    print(f"Songs needing processing: {len(songs_needing_processing)}")
    print(f"Songs that will be processed: {len(songs_to_process)}")

    # Create a mapping of titles to full song data
    song_data_map = {song['title']: song for song in song_titles}

    async with aiohttp.ClientSession() as session:
        for index, title in enumerate(songs_to_process):

            # Skip all songs alphabetically prior to the "start_at" parameter
            if start_at > title:
                continue

            current_entry = existing_lyrics[title]
            fetching_yet = False
            api_call_made = False

            for api in apis:
                if api.name in current_entry and (isinstance(current_entry[api.name], str) or refetch == False):
                    continue

                if not fetching_yet:
                    print(f"Fetching \"{title}\"")
                    fetching_yet = True

                print(f"    from {api.name}... ", end="")
                
                song_data = song_data_map.get(title, {'title': title})
                result = await fetch_from_api(session, api, song_data)

                api_call_made = True
                stats[api.name]['attempts'] += 1

                if result['status'] == 'success':
                    lyrics = result['lyrics'].strip()
                    lyrics = remove_author_credits(lyrics)
                    lyrics = normalize_lyrics(lyrics)

                    if len(lyrics) < 20 and compare_stripped_strings(lyrics, "instrumental"):
                        lyrics = ""

                    existing_lyrics[title][api.name] = lyrics
                    stats[api.name]['successes'] += 1

                    # Modified success message to include alternate name info
                    if 'alternate_name_used' in result:
                        print(f" success (alternate name: \"{result['alternate_name_used']}\")")
                    else:
                        print(" success")
                else:
                    print("error: " + result['error'])
                    existing_lyrics[title][api.name] = None

                await asyncio.sleep(0.2)

            if api_call_made:
                processed_count += 1
                
                # Save every N songs
                N = 1
                if processed_count % N == 0:
                    updated_lyrics_array = list(existing_lyrics.values())
                    with open('lyrics.json', 'w', encoding='utf-8') as file:
                        json.dump(sorted(updated_lyrics_array, key=lambda x: x['title']), 
                                file, indent=4, sort_keys=True, ensure_ascii=False)
                    # print(f"Progress saved after {processed_count} processed songs")

    # Save final results
    updated_lyrics_array = list(existing_lyrics.values())
    with open('lyrics.json', 'w', encoding='utf-8') as file:
        json.dump(sorted(updated_lyrics_array, key=lambda x: x['title']), 
                 file, indent=4, sort_keys=True, ensure_ascii=False)

    # Print statistics
    if any(stat['attempts'] for _, stat in stats.items()):
        print("\nFinal Statistics:")
        for api_name, stat in stats.items():
            attempts = stat['attempts']
            successes = stat['successes']
            if attempts > 0:
                success_rate = (successes / attempts) * 100
                print(f"    {api_name}: {successes}/{attempts} successes ({success_rate:.1f}%)")

if __name__ == "__main__":
    APIs = [
        LyricsOvhAPI(),
        ChartLyricsAPI(),
        BeatlesLyricsOrgAPI()
    ]

    LIMIT = None
    REFETCH_PREVIOUS_404s = False
    START_AT = "" # Will skip all song titles alphebetically prior

    asyncio.run(main(APIs, LIMIT, REFETCH_PREVIOUS_404s, START_AT))
