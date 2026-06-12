# Breaking Points: What Topics Drive Views?
## A Within-Day Fixed Effects Analysis

**Channel:** Breaking Points with Krystal and Saagar (YouTube)  
**Sample:** ~200 video segments, ~7 weeks  
**Methods:** Day fixed effects, OLS, variance decomposition  
**Data:** YouTube metadata via `yt-dlp` + Claude Haiku topic labels

---

## The question

Breaking Points publishes 5–8 short segments per day, each covering a different topic. Do some topics systematically outperform others — and can we identify that effect causally, or is it just confounded by which days topics happen to be covered?

## The identification strategy

The channel's format creates a natural within-day control group: all segments on a given day share the same host pair, the same news-cycle conditions, and the same day-level algorithmic promotion state. **Day fixed effects absorb all of this.** The remaining within-day variation in views is driven primarily by the segment's topic — that's what we identify.

$$\log(\text{views}_{id}) = \alpha_d + \beta \cdot \text{topic}_i + \gamma \cdot \text{position}_i + \delta \cdot \log(\text{duration}_i) + \varepsilon_{id}$$

A variance decomposition confirms the design is viable: **47.9% of log(view) variance is within-day**, ensuring the day FE doesn't swamp the signal.

## Why not host effects?

We checked. The channel follows a near-rigid weekly rotation (Krystal & Saagar on Mon/Tue/Thu, Ryan & Emily on Wed), making host assignment ~80% predictable from day-of-week alone. Conditioning on day fixed effects — necessary to control for the news cycle — absorbs almost all the host variation. This is a stated limitation, not a post-hoc rationalization: we ran the feasibility check before committing to the design. The host analysis is a stated extension requiring the full 3-year archive.

## Notebooks

| Notebook | Topic |
|---------|-------|
| [`01_identification_and_topic_effects`](notebooks/01_identification_and_topic_effects.ipynb) | Design check, variance decomposition, day FE estimates, naive vs. FE comparison |

## Data pipeline

```
yt-dlp (metadata only)  →  raw_metadata.json
                         →  label_topics.py (Claude Haiku, ~$0.10 for 200 videos)
                         →  labeled.json
                         →  build_dataset.py
                         →  analysis_dataset_clean.csv
```

Host labels are parsed from video descriptions (`"Ryan and Emily discuss..."`). No audio or video download required.

## Quick start

```bash
pip install -r requirements.txt

cd data/
export ANTHROPIC_API_KEY=sk-ant-...
python3 label_topics.py    # labels topics with Claude Haiku
python3 build_dataset.py   # merges host parsing + features

jupyter lab  # open notebooks/
```

To refresh the raw metadata (pull latest videos):
```bash
python3 data/fetch_metadata.py  # re-runs yt-dlp
```

## Talking about this in interviews

**"What's your identification strategy?"** → Day fixed effects. Every day the show publishes 5–8 segments on different topics with the same hosts and the same news cycle. Comparing views across those segments holds everything else constant. The residual within-day variation in views is what topic effects are identified from.

**"Why not host effects?"** → We ran a feasibility check first. Host assignment follows a rigid weekly rotation — day-of-week alone predicts the host pair with 80% accuracy. Conditioning on day FE to control for the news cycle eats almost all the host variation. We were honest about that rather than running an unidentified regression. The fix is the full historical archive, which has enough rotation disruptions to recover the host effect — that's a stated extension.

**"How did you get the topic labels?"** → Claude Haiku via the Anthropic API. Batches of 20 titles per call, fixed taxonomy of 10 categories, ~$0.10 total for 200 videos. The label quality check is in the data pipeline notebook.

## Connection to other projects

The day fixed effects estimator is the same FWL-applied-to-categorical-controls that `returns_to_schooling` notebook 04 derives from first principles. The "host effects require rotation disruptions" argument is the same positivity-and-overlap reasoning that motivates Callaway-Sant'Anna in `cannabis_legalization`.
