# Things to change:
# - create lyrics.json if it doesn't exist (don't quit/error)
# - when script runs, backup lyrics.json to lyrics.json.bak before doing
#   anything else (do this only if lyrics.json is not empty)
# - skip songs whose lyrics we've already gotten from this site
# - output error details at the moment there is an error, not at the end
# - write a function to normalize song lyrics: split into lines, strip each line,
#   join with "\n" (eliminating all "\r"s and extra whitespace)

import json
import re
import requests
from bs4 import BeautifulSoup
import time

def slugify(s):
    return "".join([c for c in s if c not in string.punctuation and c not in string.whitespace]).lower()

def load_existing_lyrics():
    """Load existing lyrics from JSON file"""
    try:
        with open('lyrics.json', 'r', encoding='utf-8') as f:
            print("Loading existing lyrics data...")
            return json.load(f)
    except FileNotFoundError:
        print("Error: lyrics.json not found!")
        return []

def save_lyrics(lyrics_data):
    """Save lyrics data to JSON file"""
    with open('lyrics.json', 'w', encoding='utf-8') as file:
        json.dump(sorted(lyrics_data, key=lambda x: x['title']), 
                 file, indent=4, sort_keys=True, ensure_ascii=False)
        print("Lyrics data saved successfully")

def extract_song_titles(lyrics_data):
    """Extract all song titles from existing lyrics data"""
    return [song['title'] for song in lyrics_data]

def fetch_page_content(url):
    """Fetch content from a given URL with browser-like headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def extract_links(content):
    """Extract links matching the pattern Page*.htm"""
    soup = BeautifulSoup('\n'.join(content.splitlines()[1000:]), 'html.parser')  # Skip first 1000 lines
    # soup = BeautifulSoup(content[1000:], 'html.parser')  # Skip first 1000 lines
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

def process_lyrics_page(content, song_titles):
    """Process individual lyrics page content"""
    if not content:
        return None, ['Failed to fetch page content']
    
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        return None, ['No tables found in page']
    
    last_table = tables[-1]
    spans = last_table.find_all('span')
    
    if len(spans) < 2:
        return None, ['Less than 2 spans found in table']
    
    # Check title match
    title = spans[0].get_text(strip=True)
    if title not in song_titles:
        return None, [f'Song title not found: {title}']
    
    # Check second span for parentheses
    writer_credit = spans[1].get_text(strip=True)
    if not (writer_credit.startswith('(') and writer_credit.endswith(')')):
        return None, [f'Writer credit not properly formatted: {writer_credit}']
    
    # Extract lyrics
    lyrics_content = str(last_table)
    for span in spans[:2]:  # Remove first two spans
        lyrics_content = lyrics_content.replace(str(span), '')
    
    # Clean up lyrics
    lyrics = BeautifulSoup(lyrics_content, 'html.parser').get_text()
    lyrics = re.sub(r'<br\s*/?\s*>', '\n', lyrics, flags=re.IGNORECASE)
    lyrics = re.sub(r'<[^>]+>', '', lyrics)
    lyrics = re.sub(r'\n\s*\n', '\n', lyrics).strip()
    
    return title, lyrics

def main():
    # Load existing lyrics and extract titles
    existing_lyrics = load_existing_lyrics()
    song_titles = extract_song_titles(existing_lyrics)
    print(f"Found {len(song_titles)} existing song titles")
    
    # Fetch main page
    base_url = "https://www.beatleslyrics.org/index_files/"
    main_content = fetch_page_content(base_url + "Page13763.htm")
    if not main_content:
        print("Failed to fetch main page. Exiting.")
        return
    
    # Extract links
    links = extract_links(main_content)
    print(f"Found {len(links)} song pages to process")
    
    # Process statistics
    processed = 0
    successful = 0
    errors = []
    
    # Process each page
    for i, link in enumerate(links, 1):
        url = base_url + link['href']
        print(f"Fetching lyrics for {link['text']}...", end=' ')
        
        page_content = fetch_page_content(url)
        title, result = process_lyrics_page(page_content, song_titles)
        
        if title:
            # Update existing lyrics
            for item in existing_lyrics:
                if item['title'] == title:
                    item['beatleslyrics.org'] = result
                    successful += 1
                    print("success")
                    break
        else:
            errors.append({
                'url': url,
                'errors': result
            })
            print("error")
        
        processed += 1
        
        # Save every 5 pages
        if i % 5 == 0:
            print(f"Saving progress after {i} pages...")
            save_lyrics(existing_lyrics)
        
        # Add a small delay to be nice to the server
        time.sleep(1)
    
    # Final save
    save_lyrics(existing_lyrics)
    
    # Print summary
    print("\nProcessing Complete!")
    print(f"Total pages processed: {processed}")
    print(f"Successful updates: {successful}")
    print(f"Errors encountered: {len(errors)}")
    
    if errors:
        print("\nError Details:")
        for error in errors:
            print(f"\nURL: {error['url']}")
            for err in error['errors']:
                print(f"- {err}")

if __name__ == "__main__":
    main()