# Data — cruise cabin causal demo

**All files in `processed/` are semi-synthetic.** They do not describe any real cruise operator, ship, or booking system.

## Files

| File | Grain | Rows (default config) |
|------|-------|------------------------|
| `ship_month_panel.parquet` | ship × month | 800 ships × 48 months = 38,400 |
| `category_change_events.parquet` | one row per refit event | ~144 events (18% of ships) |

## Regenerate

```bash
cd projects/cruise_cabin_causal
pip install -r requirements.txt
python scripts/generate_data.py
```

Parameters live in `config/sim_params.yaml`. Change `seed` only if you want a different draw from the same DGP.

## Column dictionary

See `DATA_DICTIONARY.md` in the project root.
