# Bias Bounty: Mapping Equity Challenge (Zindi)

Per-tract Overture coverage-gap estimates for the four scored regions (9,379 tracts).

No labels are provided and the reference layers (TIGER, Microsoft buildings, HIFLD/USGS
facilities, CBP) were removed, so the model rebuilds the published scoring formula: Overture
numerators are measured directly, each reference denominator is drawn from a proxy distribution,
and the prediction is the Monte Carlo mean of the composite (mean of defined components).

| Component | Reference proxy |
|---|---|
| Road | Length of Overture segments carrying Interstate / US / state routes, inside the tract plus a 30 m band outside it (TIGER roads coincide with tract boundaries) |
| Building | Overture count with log-normal noise (Overture already conflates Microsoft ML footprints) |
| POI facilities | Matched Overture places (binomial) + Poisson missed facilities weighted by tract size |
| POI establishments | 0.057 CBP establishments per ACS housing unit, log-normal allocation noise |

Check: the share of tracts with a road reference matches the organisers' published undefined
rates (Maricopa 46% vs ≤45%, N. California 62% vs ≤63%, E. Oklahoma 78% vs ≤79%, S.-C. Texas 68% vs ≤72%).

## Reproduce

```bash
aws s3 sync s3://us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/reference/ DATA/reference/ --no-sign-request --exclude '*roads-unfiltered*' --exclude 'eastern-wa/*'
aws s3 sync s3://us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/strata/ DATA/strata/ --no-sign-request --exclude '*.csv' --exclude 'national/*'
python features.py DATA FEAT
python band_features.py DATA FEAT
python model.py FEAT submissions/v1_full.csv                  # full model
python model.py FEAT submissions/v2_shrunk.csv --alpha 0.7    # 30% shrink toward regional means
python model.py FEAT submissions/v3_noband.csv --no-band      # ablation: no boundary band
```

Requires `duckdb` (with the `spatial` extension), `pandas`, `numpy`, `pyarrow`. Seeded (`--seed 42`).
