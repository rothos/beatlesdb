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

# Merge the data
merged_data = []
for title in songs_by_title.keys():
    merged_obj = {**songs_by_title[title], **lyrics_by_title[title]}
    merged_data.append(merged_obj)


def analyze_sentiment(text):
    # Initialize the NLTK sentiment analyzer
    sia = SentimentIntensityAnalyzer()
    
    # Get sentiment scores
    scores = sia.polarity_scores(text)
    
    return scores

# Create a new dictionary for our processed data
derived_data = []

# Process the data
for song in merged_data:
    title = song['title']
    data = {
        'title': title,
        'title_sentiment': analyze_sentiment(title)['compound']
    }

    lyrics_apis = ["lyrics.ovh", "chartlyrics.com", "beatleslyrics.org"]
    for api in lyrics_apis:
        sentiment = None
        if song[api]:
            sentiment = analyze_sentiment(song[api])['compound']
        data["lyrics_sentiment_"+api] = sentiment

    derived_data += [data]

# Save the results to a new file
with open('derived_data.json', 'w') as file:
    json.dump(sorted(derived_data, key=lambda x: x['title']), 
                file, indent=4, sort_keys=True, ensure_ascii=False)


end_time = time.perf_counter()
execution_time = end_time - start_time
print(f"\nExecution time: {execution_time:.2f} seconds")


