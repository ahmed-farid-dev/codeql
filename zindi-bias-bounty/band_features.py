"""Highway length in a thin band just outside each tract.

TIGER roads are topologically integrated with tract boundaries, so a reference highway running
along a tract edge intersects both neighbouring tracts, while the Overture/OSM line for the same
road usually falls a few metres inside only one of them. Highway length in a band outside the
tract approximates that reference length the tract "sees" without Overture having it inside.

Usage: python band_features.py DATA_DIR OUT_DIR [region ...]
"""
import sys
import duckdb

DATA, OUT = sys.argv[1], sys.argv[2]
REGIONS = ["maricopa-az", "northern-ca", "eastern-ok", "south-central-tx"]
PROJ = "ST_Transform(geometry, 'EPSG:4326', 'EPSG:5070', always_xy := true)"
BAND_M = 30

con = duckdb.connect()
con.sql("LOAD spatial; SET threads=4; SET memory_limit='12GB'; SET preserve_insertion_order=false;")

for region in (sys.argv[3:] or REGIONS):
    ref = f"{DATA}/reference/{region}/{region}"
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE t AS
        SELECT c.GEOID, {PROJ} AS g
        FROM '{DATA}/strata/{region}/{region}-census-tracts.parquet' c
        JOIN read_csv('{ref}-sample-submission.csv', types={{'GEOID':'VARCHAR'}}) s USING (GEOID)
    """)
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE band AS
        SELECT GEOID, ST_Difference(ST_Buffer(g, {BAND_M}), g) AS g FROM t
    """)
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE r AS
        SELECT class IN ('motorway','trunk','primary','secondary') AS named,
               coalesce(list_bool_or([x.network IN ('US:I','US:US') OR regexp_matches(x.network, '^US:[A-Z]{{2}}$')
                                      OR regexp_matches(x.network, '^US:(I|US|[A-Z]{{2}}):(Business|Spur|Loop|Bypass|Alternate|Truck)$')
                                      FOR x IN routes]), false) AS hwy,
               coalesce(list_bool_or([x.network = 'US:TX:FM' FOR x IN routes]), false) AS fm,
               {PROJ} AS g
        FROM '{ref}-overture-roads.parquet'
        WHERE class IN ('motorway','trunk','primary','secondary','tertiary')
    """)
    df = con.sql("""
        SELECT band.GEOID,
               sum(L) FILTER (WHERE hwy) AS hwy_band_len,
               sum(L) FILTER (WHERE named) AS named_band_len,
               sum(L) FILTER (WHERE fm) AS fm_band_len
        FROM (SELECT band.GEOID, r.hwy, r.named, r.fm, ST_Length(ST_Intersection(r.g, band.g)) AS L
              FROM r JOIN band ON ST_Intersects(r.g, band.g)) x
        JOIN band USING (GEOID)
        GROUP BY band.GEOID
    """).df()
    fm_in = con.sql("""
        SELECT t.GEOID, sum(ST_Length(ST_Intersection(r.g, t.g))) AS fm_len
        FROM r JOIN t ON ST_Intersects(r.g, t.g) WHERE r.fm GROUP BY t.GEOID
    """).df()
    df = df.merge(fm_in, on="GEOID", how="outer")
    df.to_parquet(f"{OUT}/band-{region}.parquet", index=False)
    print(region, df.shape, flush=True)
