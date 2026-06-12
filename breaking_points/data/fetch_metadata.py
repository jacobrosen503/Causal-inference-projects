"""
fetch_metadata.py
-----------------
Fetch Breaking Points video metadata from YouTube via yt-dlp.

Each video is fetched individually (not flat-playlist) so that the
`timestamp` field — real publish time with second-level precision — is
available for computing accurate within-day segment ordering.

Usage:
    python3 fetch_metadata.py                  # last 60 days (default)
    python3 fetch_metadata.py --days 180       # last 6 months
    python3 fetch_metadata.py --dateafter 20260101  # from a specific date

Writes: raw_metadata.json
Runtime: ~2s per video. 60 days ≈ 200 videos ≈ 7 min.
"""

import json, time, argparse, datetime
import yt_dlp

CHANNEL = "https://www.youtube.com/@breakingpoints/videos"

FIELDS = [
    'id', 'title', 'upload_date', 'timestamp',
    'view_count', 'like_count', 'comment_count',
    'duration', 'description', 'tags', 'webpage_url',
]


def get_video_ids(dateafter: str) -> list[str]:
    """Fast flat-playlist pass to get video IDs in date range."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'dateafter': dateafter,
        'ignoreerrors': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(CHANNEL, download=False)
    entries = info.get('entries') or []
    ids = [e['id'] for e in entries if e and e.get('id')]
    print(f"Playlist pass found {len(ids)} videos (dateafter={dateafter})")
    return ids


def fetch_video(vid_id: str) -> dict | None:
    """Fetch full metadata for a single video (includes timestamp)."""
    url = f"https://www.youtube.com/watch?v={vid_id}"
    opts = {'quiet': True, 'no_warnings': True, 'ignoreerrors': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        return None
    rec = {f: info.get(f) for f in FIELDS}
    rec['url'] = info.get('webpage_url')
    if rec.get('description'):
        rec['description'] = rec['description'][:800]
    if rec.get('tags'):
        rec['tags'] = rec['tags'][:15]
    return rec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=60,
                        help='Fetch videos from last N days (default: 60)')
    parser.add_argument('--dateafter', type=str, default=None,
                        help='Override: fetch from this date (YYYYMMDD)')
    parser.add_argument('--out', type=str, default='raw_metadata.json')
    args = parser.parse_args()

    if args.dateafter:
        dateafter = args.dateafter
    else:
        dateafter = (datetime.date.today() - datetime.timedelta(days=args.days)).strftime('%Y%m%d')

    # Step 1: get IDs
    ids = get_video_ids(dateafter)
    if not ids:
        print("No videos found. Check channel URL or date range.")
        return

    # Step 2: fetch full metadata per video
    records = []
    for i, vid_id in enumerate(ids):
        rec = fetch_video(vid_id)
        if rec:
            ts = rec.get('timestamp')
            ts_str = ''
            if ts:
                dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
                ts_str = dt.strftime('%H:%M UTC')
            print(f"  [{i+1}/{len(ids)}] {rec.get('upload_date','?')} {ts_str:10} | {rec.get('title','')[:50]}")
            records.append(rec)
        else:
            print(f"  [{i+1}/{len(ids)}] FAILED: {vid_id}")
        time.sleep(0.4)

    with open(args.out, 'w') as f:
        json.dump(records, f, indent=2)

    has_ts = sum(1 for r in records if r.get('timestamp'))
    print(f"\nSaved {len(records)} records to {args.out}")
    print(f"  {has_ts}/{len(records)} have real timestamps (time-of-day precision)")
    print(f"  Run build_dataset.py next to generate analysis CSVs.")


if __name__ == '__main__':
    main()
