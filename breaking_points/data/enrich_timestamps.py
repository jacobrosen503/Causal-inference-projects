"""
One-time script: enrich raw_metadata.json with real publish timestamps.
Fetches each video individually to get the timestamp field (time-of-day precision).
Run time: ~7 min for 200 videos.
"""
import json, time, datetime, sys
import yt_dlp

def fetch_timestamp(vid_id):
    url = f"https://www.youtube.com/watch?v={vid_id}"
    opts = {'quiet': True, 'no_warnings': True, 'ignoreerrors': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info.get('timestamp') if info else None

with open('raw_metadata.json') as f:
    records = json.load(f)

print(f"Enriching {len(records)} records with publish timestamps...")
enriched = []
for i, rec in enumerate(records):
    ts = fetch_timestamp(rec['id'])
    enriched.append({**rec, 'timestamp': ts})
    if ts:
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        print(f"  [{i+1}/{len(records)}] {rec['upload_date']} {dt.strftime('%H:%M:%S')} UTC | {rec['title'][:45]}")
    else:
        print(f"  [{i+1}/{len(records)}] {rec['upload_date']} NO TIMESTAMP | {rec['title'][:45]}")
    time.sleep(0.3)

with open('raw_metadata.json', 'w') as f:
    json.dump(enriched, f, indent=2)

has_ts = sum(1 for r in enriched if r.get('timestamp'))
print(f"\nDone. {has_ts}/{len(enriched)} records have timestamps.")
