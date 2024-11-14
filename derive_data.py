import time
import json
import shutil

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

start_time = time.perf_counter()

# Back up derived data file.
with open('derived_data.json', 'r') as f:
    try:
        data = json.load(f)
        if data:  # Only backup if file has content
            shutil.copy2('derived_data.json', 'derived_data.json.bak')
            print("Created backup: derived_data.json.bak")
    except json.JSONDecodeError:
        # File exists but is empty or invalid
        print("Existing derived_data.json is empty or invalid - creating new file")
        with open('derived_data.json', 'w') as f:
            json.dump([], f)

# Load the data from files
with open('beatles_songs.json', 'r') as f:
    songs_data = json.load(f)

with open('lyrics.json', 'r') as f:
    lyrics_data = json.load(f)

# Create dictionaries keyed by title for easier lookup
songs_by_title = {song['title']: song for song in songs_data}
lyrics_by_title = {lyric['title']: lyric for lyric in lyrics_data}

# Check for titles that aren't in both datasets
songs_titles = set(songs_by_title.keys())
lyrics_titles = set(lyrics_by_title.keys())

missing_from_lyrics = songs_titles - lyrics_titles
missing_from_songs = lyrics_titles - songs_titles

if missing_from_lyrics or missing_from_songs:
    raise ValueError(
        f"Titles missing from lyrics: {missing_from_lyrics}\n"
        f"Titles missing from songs: {missing_from_songs}"
    )

# Merge the data
merged_data = []
for title in songs_titles:
    song_obj = songs_by_title[title]
    lyrics_obj = lyrics_by_title[title]
    
    # Check for conflicting properties
    common_keys = set(song_obj.keys()) & set(lyrics_obj.keys())
    if len(common_keys) > 1:  # > 1 because 'title' is expected to be common
        raise ValueError(f"Unexpected common properties found: {common_keys}")
    
    # Merge the objects
    merged_obj = {**song_obj, **lyrics_obj}
    merged_data.append(merged_obj)


def analyze_sentiment(text):
    # Initialize the NLTK sentiment analyzer
    sia = SentimentIntensityAnalyzer()
    
    # Get sentiment scores
    scores = sia.polarity_scores(text)
    
    # Determine overall sentiment
    if scores['compound'] >= 0.05:
        sentiment = 'Positive'
    elif scores['compound'] <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    
    return {
        'text': text,
        'scores': scores,
        'sentiment': sentiment
    }

# Create a new dictionary for our processed data
derived_data = []

# Process the data
for song in songs_data[:10]:
    title = song['title']
    data = {
        'title': title,
        'title_sentiment': analyze_sentiment(title)['scores']['compound']
    }

    # lyrics_apis = ["lyrics.ovh", "chartlyrics.com", "beatleslyrics.org"]
    # for api in lyrics_apis:
    #     sentiment = None
    #     print(title, song.keys())
    #     if song[api]:
    #         sentiment = analyze_sentiment(song[api])['scores']['compound']
    #     data["lyrics_sentiment_"+api] = sentiment

    derived_data += [data]

# Save the results to a new file
with open('derived_data.json', 'w') as file:
    json.dump(sorted(merged_data, key=lambda x: x['title']), 
                file, indent=4, sort_keys=True, ensure_ascii=False)


end_time = time.perf_counter()
execution_time = end_time - start_time
print(f"\nExecution time: {execution_time:.2f} seconds")


