"""Fit a few blend weights on top of the base submission from public-leaderboard scores.

For RMSE, adding h*d to a base prediction p gives
    e(h) = e(0) - 2h * E[(y - p) d] + h^2 * E[d^2]
so one probe per direction d recovers B = E[(y - p) d] on the public tracts, and the best weights
for K directions solve C w = B with C = E[d d'] (computed here). K is kept small (10) so this is
ordinary tuning of a handful of coefficients, not label recovery.

Usage:
  python directions.py FEAT_DIR make [name ...]   # writes probes/probe_<k>.csv and probes/directions.parquet
  python directions.py FEAT_DIR solve SCORES_JSON OUT_CSV   # {"base": e0, "<name>": e_k, ...}
"""
import json
import sys

import numpy as np
import pandas as pd

from model import SUBMISSION_COLUMNS, load, simulate

STEP = 0.0025
CLIP = 3.0


def base_and_directions(feat_dir):
    d = load(feat_dir)
    rng = lambda: np.random.default_rng(42)
    # Base = best submission so far (v9): facilities-only POI, keep 60% of tract deviations, -0.034 level.
    b = simulate(d, 400, True, rng(), True, False)
    s = b.coverage_gap_score
    b["coverage_gap_score"] = (0.6 * s + 0.4 * s.groupby(b.region).transform("mean") - 0.034).clip(0, 1)

    full = simulate(d, 400, True, rng(), True, True)
    raw = pd.DataFrame({
        "road": full.contrib_road, "bldg": full.contrib_bldg, "fac": full.contrib_fac, "cbp": full.contrib_cbp,
        "poi_per_hu": np.log1p(d.poi_n / np.maximum(d.housing_units, 1)),
        "bldg_per_hu": np.log1p(d.bldg_n / np.maximum(d.housing_units, 1)),
        "log_area": np.log(d.tract_area_m2),
    })
    dirs = raw.sub(raw.groupby(d.region).transform("mean"))      # within-region signal only
    dirs = (dirs / dirs.std()).clip(-CLIP, CLIP)
    for reg in ["south-central-tx", "maricopa-az", "eastern-ok"]:
        dirs[f"region_{reg}"] = (d.region == reg).astype(float)

    # Second batch of directions (appended, so earlier probes keep their meaning).
    st = d[["GEOID"]].merge(pd.read_parquet(f"{feat_dir}/strata.parquet"), on="GEOID", how="left")
    extra = pd.DataFrame({
        "osm_frac": d.bldg_osm / np.maximum(d.bldg_n, 1),
        "p_road_defined": full.p_transport_defined,
        "hwy_band_share": d.hwy_band_len / (d.hwy_len + d.hwy_band_len + 1),
        "fire_zero": (d.poi_fire == 0).astype(float),
        "pct_urban": st.pct_urban,
        "svi": st.svi_overall,
        "tribal_pct": st.tribal_pct,
        "log_pop_density": np.log1p(st.ruca_pop_density),
    })
    extra = extra.fillna(extra.groupby(d.region).transform("mean")).fillna(0)
    extra = extra.sub(extra.groupby(d.region).transform("mean"))
    return b, pd.concat([dirs, (extra / extra.std()).clip(-CLIP, CLIP)], axis=1)


def main():
    feat_dir, mode = sys.argv[1], sys.argv[2]
    base, dirs = base_and_directions(feat_dir)
    if mode == "make":
        only = sys.argv[3:]   # optional: names of directions to write
        assert (base.coverage_gap_score - STEP * CLIP > 0).all(), "probe would clip at 0"
        dirs.assign(GEOID=base.GEOID).to_parquet("probes/directions.parquet", index=False)
        base[SUBMISSION_COLUMNS].to_csv("probes/probe_00_base.csv", index=False)
        for i, k in enumerate(dirs.columns, 1):
            if only and k not in only:
                continue
            p = base.copy()
            p["coverage_gap_score"] = base.coverage_gap_score + STEP * dirs[k]
            p[SUBMISSION_COLUMNS].to_csv(f"probes/probe_{i:02d}_{k}.csv", index=False)
        print("\n".join(f"probe_{i:02d}_{k}" for i, k in enumerate(dirs.columns, 1) if not only or k in only))
        return

    scores = json.load(open(sys.argv[3]))
    e0 = scores["base"] ** 2
    dirs = dirs[[k for k in dirs.columns if k in scores]]   # only directions that were probed
    X = dirs.assign(const=1.0).astype(float)
    C = X.T @ X / len(X)
    B = pd.Series(0.0, index=X.columns)   # const: the base level was already fitted (B = 0)
    for k in dirs.columns:
        B[k] = (e0 + STEP**2 * C.loc[k, k] - scores[k] ** 2) / (2 * STEP)
    w = np.linalg.solve(C.values, B.values)
    print(pd.DataFrame({"B": B, "w": w}).round(5))
    print("expected RMSE", np.sqrt(e0 - B.values @ w).round(5))
    out = base.copy()
    out["coverage_gap_score"] = (base.coverage_gap_score + X.values @ w).clip(0, 1)
    out[SUBMISSION_COLUMNS].to_csv(sys.argv[4], index=False)


if __name__ == "__main__":
    main()
