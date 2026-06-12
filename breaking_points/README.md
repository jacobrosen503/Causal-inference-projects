# Breaking Points: Do Topic Choices Reveal Editorial Incentives?
## A Within-Day Fixed Effects Analysis of Political Media Viewership

**Channel:** Breaking Points with Krystal and Saagar (YouTube)  
**Sample:** 171 video segments, 33 days (~7 weeks)  
**Methods:** Day fixed effects, OLS, permutation test, variance decomposition  
**Data:** YouTube metadata via `yt-dlp` + Claude Haiku topic labels (~$0.10)

---

## The question

Political commentary channels face a structural tension: editorial commitment to covering what *matters* vs. the financial incentive to cover what *gets clicks*. If some topics systematically outperform others in viewership — controlling for everything else — the channel faces quantifiable pressure to tilt its editorial mix toward those topics.

This project measures that incentive. **What topics drive views on Breaking Points, and how large is the effect after controlling for which day the content aired?**

## The identification strategy

Breaking Points publishes 5–8 short segments per day, each covering a different topic, with the same host pair doing all segments. This creates a natural within-day control group: **all segments on a given day share the same hosts, the same news-cycle conditions, and the same algorithmic promotion state.** Within-day variation in views is driven by the segment itself — primarily its topic.

$$\log(\text{views}_{id}) = \alpha_d + \beta \cdot \text{topic}_i + \gamma \cdot \text{position}_i + \delta \cdot \log(\text{duration}_i) + \varepsilon_{id}$$

The day fixed effect $\alpha_d$ absorbs host identity, news-cycle magnitude, day-of-week patterns, and algorithmic variation. $\beta$ is identified from within-day topic contrasts.

**Pre-flight check:** A variance decomposition confirms 47.9% of log-view variance is within-day — enough signal remains after absorbing the FE.

## Key findings

**Foreign Policy / War is the dominant topic.** Every other category underperforms it within the same day:

| Topic | β | Views effect | Permutation p |
|-------|---|-------------|---------------|
| Foreign Policy / War | 0.000 | baseline | — |
| Economy / Finance | −0.234 | −20.8% | 0.066 |
| Media / Tech | −0.270 | −23.7% | 0.060 |
| Culture / Society | −0.376 | −31.3% | 0.019 ★ |
| Domestic Politics | −0.395 | −32.6% | < 0.001 ★ |
| Legal / Courts | −0.416 | −34.0% | 0.076 |

The view-effect and like-effect rankings have a rank correlation of **r = 0.931 (p = 0.007)** — the pattern reflects genuine engagement, not just click-through.

**An unexpected structural finding:** Foreign policy segments are consistently posted *last* in the day's lineup (mean position 4.47 vs. overall mean 3.63). Combined with a positive position effect (later = more views), this means the topic coefficient is *conservative* — the true FP/War premium may be larger than estimated. The no-position model puts it at −0.47 for Domestic Politics vs. −0.40 with position controlled.

**What this means for editorial incentives:** If views drive revenue, Breaking Points faces a measurable financial incentive to cover more foreign policy and less domestic politics — regardless of what's editorially important that day. The effect is within-day (same hosts, same news cycle), so it's not a proxy for global news-cycle differences.

## Why not host effects?

We ran the feasibility check before designing the study. The channel follows a near-rigid weekly rotation: Krystal & Saagar on Mon/Tue/Thu, Ryan & Emily on Wed. Day-of-week alone predicts the host pair at **79.5% accuracy**. Conditioning on day fixed effects — necessary to control for the news cycle — absorbs almost all host variation. Only 2 of 33 days have within-day host variation. This is a documented methodological constraint, not a post-hoc rationalization.

**Extension:** Pull the full archive (~3,000 videos, 2+ years). Schedule disruptions (illness, travel, guest hosts) accumulate over time and provide the rotation variation needed to identify host effects. The FWL residualization from `returns_to_schooling` applies directly.

## Notebooks

| Notebook | Content |
|---------|---------|
| [`01_identification_and_topic_effects`](notebooks/01_identification_and_topic_effects.ipynb) | Identification check, variance decomposition, naive OLS, day FE estimates, naive-vs-FE shift, control effects, host limitation proof, editorial incentive interpretation |
| [`02_robustness_and_extensions`](notebooks/02_robustness_and_extensions.ipynb) | Permutation test (1,000 within-day shuffles), alternative outcome (log likes), full-sample sensitivity (N=200), position mechanism investigation |

## Data pipeline

```
yt-dlp (metadata only, no download)  →  raw_metadata.json  (200 videos)
                                      →  label_topics.py    (Claude Haiku, ~$0.10)
                                      →  labeled.json
                                      →  build_dataset.py   (host parsing + features)
                                      →  analysis_dataset_clean.csv  (171 clean-host rows)
```

Host labels are parsed from video descriptions (`"Ryan and Emily discuss..."`). No audio or video processing required.

## Quick start

```bash
pip install -r requirements.txt

cd data/
export ANTHROPIC_API_KEY=sk-ant-...
python3 label_topics.py    # labels 200 videos with Claude Haiku
python3 build_dataset.py   # merges host parsing + derived features

jupyter lab  # open notebooks/
```

To refresh raw metadata (pull latest videos):
```bash
python3 data/fetch_metadata.py
```

## Talking about this in interviews

**"What's the identification strategy?"**  
Day fixed effects. The channel posts 5–8 segments per day on different topics with the same hosts. Comparing views across those segments holds host identity, news-cycle magnitude, and algorithmic promotion constant. Within-day variation is what we identify topic effects from. A pre-registration step — variance decomposition confirming 47.9% of variance is within-day — established that the design was viable before running a single regression.

**"Why not estimate host effects?"**  
We ran a feasibility check first. Host assignment follows a rigid weekly rotation — day-of-week alone predicts the host pair at 79.5% accuracy. Conditioning on day FE (to control for the news cycle) eats almost all host variation. We were honest about the limitation rather than running an unidentified regression and presenting it as causal. The fix requires the full archive, which has enough rotation disruptions over 3 years to recover host effects.

**"How did you validate the permutation test?"**  
We shuffle topic labels within each day 1,000 times, preserving day structure and the marginal topic distribution. Under the null, reshuffling topic labels within a day should make the day FE estimates look like noise. The actual estimates for Domestic Politics and the Other category fall well outside the null distribution (perm-p < 0.001). This is a nonparametric validity check that makes no normality assumption.

**"What's the most interesting unexpected finding?"**  
The position effect. Later segments in a day's lineup get more views (β=+0.047, p=0.046), which is counterintuitive — you'd expect the lead segment to dominate. We tested whether this was driven by Foreign Policy being posted late (it is — mean position 4.47 vs. 3.63 overall) and found no significant topic×position interaction, meaning the position effect is uniform across topics. The mechanism is ambiguous between algorithmic timing and an editorial "closer" strategy, but the implication is that the FP/War premium in our main estimates is conservative.

## Blog post angles

1. **"The Algorithmic Pressure on Political Media"** — The 33% view gap between foreign policy and domestic politics as a measurable editorial incentive. Does audience demand shape coverage, or does coverage shape demand?

2. **"Why Within-Day Controls Matter: A YouTube Case Study"** — The naive OLS vs. day FE shift for Legal/Courts (+0.23 log points) as a concrete example of confounding from day-level variation.

3. **"How I Built a $0.10 Topic Classifier for Political Media"** — The yt-dlp + Claude Haiku pipeline, why a fixed taxonomy beats open-ended generation, and the feasibility-check-first methodology.

## Connection to other projects

The day fixed effects estimator is algebraically equivalent to the de-meaning FWL decomposition derived in `returns_to_schooling` notebook 04. The "host effects require rotation disruptions" argument mirrors the overlap/positivity logic in `cannabis_legalization` — you need enough treated and untreated units *within* the conditioning set to identify effects.
