"""Expected coverage-gap score per tract from proxy estimates of the removed reference layers.

The score is the mean of the defined components (road, building, POI), each 1 - min(1, overture/reference).
Overture numerators are measured directly; each reference denominator is drawn from a proxy
distribution, and the prediction is the Monte Carlo mean of the resulting composite (the
RMSE-optimal point estimate under the model).

Usage: python model.py FEAT_DIR OUT_CSV [--alpha A] [--no-band] [--draws N]
"""
import argparse

import numpy as np
import pandas as pd

REGIONS = ["maricopa-az", "northern-ca", "eastern-ok", "south-central-tx", "eastern-wa"]

# Prior per-tract rates for the reference facility layers (USGS National Map structures),
# roughly national counts / 85k tracts.
FACILITY = {
    #          overture col, reference rate per tract, share of Overture places that match a reference record
    "fire":   ("poi_fire",   0.60, 0.85),
    "ems":    ("poi_ems",    0.15, 0.80),
    "school": ("poi_school", 1.40, 0.50),
}
CBP_PER_HU = 0.057        # ~8.3M CBP establishments / ~145M housing units
CBP_SIGMA = 0.5           # log-sd of the tract allocation of county CBP counts
MS_LOG_MU, MS_LOG_SIGMA = -0.10, 0.20   # log(Microsoft count / Overture count)
TIGER_LOG_SIGMA = 0.15    # log-sd of TIGER highway length around the Overture proxy
MIN_HWY_M = 50.0
SUBMISSION_COLUMNS = [
    "GEOID", "coverage_gap_score", "region",
    "transport_gap", "transport_defined", "building_gap", "building_defined", "poi_gap", "poi_defined",
    "poi_gap_fire", "poi_defined_fire", "poi_gap_ems", "poi_defined_ems",
    "poi_gap_schools", "poi_defined_schools", "poi_gap_cbp", "poi_defined_cbp",
]


def load(feat_dir):
    frames = []
    for r in REGIONS:
        f = pd.read_parquet(f"{feat_dir}/features-{r}.parquet")
        b = pd.read_parquet(f"{feat_dir}/band-{r}.parquet")
        frames.append(f.merge(b, on="GEOID", how="left"))
    d = pd.concat(frames, ignore_index=True)
    num = d.columns.difference(["region", "GEOID"])
    d[num] = d[num].fillna(0)
    return d


def gap(over, ref):
    with np.errstate(divide="ignore", invalid="ignore"):
        return 1 - np.minimum(1, np.where(ref > 0, over / ref, 1.0))


def simulate(d, draws, use_band, rng, use_fac=True, use_cbp=True):
    n = len(d)
    shape = (draws, n)

    # Road: TIGER S1100/S1200 length ~ Overture highway-route length (inside + edge band).
    tiger_est = d.hwy_len.to_numpy() + (d.hwy_band_len.to_numpy() if use_band else 0)
    tiger = tiger_est * np.exp(rng.normal(0, TIGER_LOG_SIGMA, shape))
    road_def = tiger > MIN_HWY_M
    road = gap(d.named_len.to_numpy(), tiger)

    # Building: Microsoft footprint count scattered around the Overture count.
    bn = d.bldg_n.to_numpy()
    ms = np.round(bn * np.exp(rng.normal(MS_LOG_MU, MS_LOG_SIGMA, shape)))
    bldg_def = ms > 0
    bldg = gap(bn, ms)

    # POI, facilities half: reference count = matched Overture places + missed facilities.
    # Missed-facility rate is spread over tracts by a size weight (bigger tracts hold more stations).
    w = np.sqrt(d.tract_area_m2.to_numpy() / 1e6) ** 0.7 * np.sqrt(np.maximum(d.housing_units.to_numpy(), 50) / 1500)
    w = w / w.mean()
    fac_sum = np.zeros(shape)
    fac_cnt = np.zeros(shape)
    per_type = {}
    for name, (col, rate, q) in FACILITY.items():
        o = d[col].to_numpy().astype(int)
        miss_rate = max(0.05, rate - q * o.mean())
        ref = rng.binomial(np.broadcast_to(o, shape), q) + rng.poisson(miss_rate * w, shape)
        defined = ref > 0
        g = gap(o, ref)
        per_type[name] = (g, defined)
        fac_sum += np.where(defined, g, 0)
        fac_cnt += defined
    fac_def = (fac_cnt > 0) & use_fac
    fac = np.where(fac_def, fac_sum / np.maximum(fac_cnt, 1), 0)

    # POI, establishments half: county CBP counts allocated by housing units.
    cbp = CBP_PER_HU * d.housing_units.to_numpy() * np.exp(rng.normal(-CBP_SIGMA**2 / 2, CBP_SIGMA, shape))
    cbp_def = (cbp >= 0.5) & use_cbp
    est = gap(d.poi_n.to_numpy(), cbp)

    poi_def = fac_def | cbp_def
    poi = (np.where(fac_def, fac, 0) + np.where(cbp_def, est, 0)) / np.maximum(fac_def.astype(int) + cbp_def, 1)

    num = np.where(road_def, road, 0) + np.where(bldg_def, bldg, 0) + np.where(poi_def, poi, 0)
    cnt = road_def.astype(int) + bldg_def + poi_def
    score = np.where(cnt > 0, num / np.maximum(cnt, 1), 0)

    def cond_mean(x, m):
        return np.where(m.sum(0) > 0, (x * m).sum(0) / np.maximum(m.sum(0), 1), 0)

    per_type["schools"] = per_type.pop("school")
    per_type["cbp"] = (est, cbp_def)
    out = {"GEOID": d.GEOID, "coverage_gap_score": score.mean(0), "region": d.region}
    for name, (g, m) in [("transport", (road, road_def)), ("building", (bldg, bldg_def)), ("poi", (poi, poi_def))]:
        out[f"{name}_defined"] = m.mean(0) >= 0.5
        out[f"{name}_gap"] = np.where(out[f"{name}_defined"], cond_mean(g, m), 0)
    for name, (g, m) in per_type.items():
        # Organiser convention: an undefined component is written as 0 with its flag false.
        out[f"poi_defined_{name}"] = m.mean(0) >= 0.5
        out[f"poi_gap_{name}"] = np.where(out[f"poi_defined_{name}"], cond_mean(g, m), 0)
    out["p_transport_defined"] = road_def.mean(0)
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("feat_dir")
    ap.add_argument("out_csv")
    ap.add_argument("--alpha", type=float, default=1.0, help="shrink toward the regional mean (1 = none)")
    ap.add_argument("--no-band", action="store_true")
    ap.add_argument("--no-fac", action="store_true", help="ablation: POI from establishments only")
    ap.add_argument("--no-cbp", action="store_true", help="ablation: POI from facilities only")
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    d = load(a.feat_dir)
    p = simulate(d, a.draws, not a.no_band, np.random.default_rng(a.seed), not a.no_fac, not a.no_cbp)
    s = p.coverage_gap_score
    p["coverage_gap_score"] = a.alpha * s + (1 - a.alpha) * s.groupby(p.region).transform("mean")

    print(p.groupby("region")[["coverage_gap_score", "transport_gap", "building_gap", "poi_gap", "p_transport_defined"]].mean().round(3))
    print(p.coverage_gap_score.describe().round(3))
    p[SUBMISSION_COLUMNS].to_csv(a.out_csv, index=False)


if __name__ == "__main__":
    main()
