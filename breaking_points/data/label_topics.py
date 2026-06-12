"""
label_topics.py
---------------
Labels each Breaking Points video with a topic category using Claude.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 label_topics.py

Writes: labeled.json  (raw_metadata.json + topic fields)
"""

import json, os, time, re
import anthropic

TOPIC_TAXONOMY = [
    "Domestic Politics",    # elections, Congress, parties, White House
    "Foreign Policy / War", # Ukraine, Middle East, Iran, China, NATO
    "Economy / Finance",    # inflation, jobs, markets, tariffs, Fed
    "Legal / Courts",       # indictments, trials, SCOTUS, DOJ
    "Immigration",          # border, deportations, asylum
    "Media / Tech",         # media criticism, Big Tech, social media
    "Healthcare / Pharma",  # drugs, insurance, public health
    "Culture / Society",    # social issues, education, culture war
    "Environment / Energy", # climate, oil, green energy
    "Other",                # anything that doesn't fit cleanly
]

SYSTEM_PROMPT = f"""You are a news topic classifier for the political commentary channel Breaking Points.

Classify each video title into exactly one of these categories:
{chr(10).join(f'  - {t}' for t in TOPIC_TAXONOMY)}

Respond with valid JSON only — no markdown, no explanation:
{{
  "topic": "<category from list above>",
  "confidence": <0.0-1.0>,
  "rationale": "<one sentence>"
}}"""


def label_batch(client, titles: list[str]) -> list[dict]:
    """Label a batch of titles in a single API call."""
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    prompt = f"""Classify each of these {len(titles)} video titles:

{numbered}

Respond with a JSON array of {len(titles)} objects, one per title, in order:
[{{"topic": "...", "confidence": 0.9, "rationale": "..."}}, ...]"""

    resp = client.messages.create(
        model="claude-haiku-4-5",   # cheapest, fast, more than enough for classification
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY first: export ANTHROPIC_API_KEY=sk-ant-...")

    client = anthropic.Anthropic(api_key=api_key)

    with open("raw_metadata.json") as f:
        records = json.load(f)

    good = [r for r in records if "title" in r and not r.get("error")]
    print(f"Labeling {len(good)} videos in batches of 20...")

    BATCH_SIZE = 20
    labeled = []
    for i in range(0, len(good), BATCH_SIZE):
        batch = good[i : i + BATCH_SIZE]
        titles = [r["title"] for r in batch]
        try:
            labels = label_batch(client, titles)
            for rec, lbl in zip(batch, labels):
                labeled.append({**rec, **lbl})
            print(f"  {min(i+BATCH_SIZE, len(good))}/{len(good)} done")
        except anthropic.BadRequestError as e:
            # Credit exhaustion comes back as a 400 — stop immediately, save what we have
            if "credit" in str(e).lower() or "billing" in str(e).lower():
                print(f"\n⚠️  Out of credits — stopping. Saving {len(labeled)} labeled so far.")
                break
            print(f"  Bad request on batch {i//BATCH_SIZE}: {e}")
            for rec in batch:
                labeled.append({**rec, "topic": "ERROR", "confidence": 0.0, "rationale": str(e)})
        except anthropic.APIStatusError as e:
            # Catch any other billing/quota status errors and stop
            if e.status_code in (402, 429) or "credit" in str(e).lower() or "billing" in str(e).lower():
                print(f"\n⚠️  API limit/billing error (status {e.status_code}) — stopping. Saving {len(labeled)} labeled so far.")
                break
            print(f"  API error on batch {i//BATCH_SIZE} (status {e.status_code}): {e}")
            for rec in batch:
                labeled.append({**rec, "topic": "ERROR", "confidence": 0.0, "rationale": str(e)})
        except Exception as e:
            print(f"  Error on batch {i//BATCH_SIZE}: {e}")
            for rec in batch:
                labeled.append({**rec, "topic": "ERROR", "confidence": 0.0, "rationale": str(e)})
        time.sleep(0.5)

    with open("labeled.json", "w") as f:
        json.dump(labeled, f, indent=2)

    # Quick summary
    from collections import Counter
    topics = Counter(r["topic"] for r in labeled)
    print("\n=== Topic distribution ===")
    for topic, count in topics.most_common():
        print(f"  {count:3d}  {topic}")
    print(f"\nSaved labeled.json ({len(labeled)} records)")


if __name__ == "__main__":
    main()
