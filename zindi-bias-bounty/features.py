"""Per-tract features from the challenge data package (Overture extracts, ACS, strata).

Usage: python features.py DATA_DIR OUT_DIR
Only challenge-provided layers are read; no removed reference layer is used.
"""
import sys
import duckdb

DATA, OUT = sys.argv[1], sys.argv[2]
REGIONS = ["maricopa-az", "northern-ca", "eastern-ok", "south-central-tx"]
NAMED = "('motorway','trunk','primary','secondary')"
PROJ = "ST_Transform(geometry, 'EPSG:4326', 'EPSG:5070', always_xy := true)"

con = duckdb.connect()
con.sql("LOAD spatial; SET threads=4; SET memory_limit='12GB'; SET preserve_insertion_order=false;")


def run(region):
    ref = f"{DATA}/reference/{region}/{region}"
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE t AS
        SELECT c.GEOID, {PROJ} AS g
        FROM '{DATA}/strata/{region}/{region}-census-tracts.parquet' c
        JOIN read_csv('{ref}-sample-submission.csv', types={{'GEOID':'VARCHAR'}}) s USING (GEOID)
    """)

    # Roads: clip each segment to tracts, length in metres. A segment "carries a highway route"
    # if any of its routes is an Interstate, US or state route.
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE r AS
        SELECT class,
               coalesce(list_bool_or([x.network IN ('US:I','US:US') OR regexp_matches(x.network, '^US:[A-Z]{{2}}$')
                                      OR regexp_matches(x.network, '^US:(I|US|[A-Z]{{2}}):(Business|Spur|Loop|Bypass|Alternate|Truck)$')
                                      FOR x IN routes]), false) AS hwy,
               coalesce(list_bool_or([x.network = 'US:I' FOR x IN routes]), false) AS interstate,
               coalesce(list_bool_or([regexp_matches(x.network, '^US:[A-Z]{{2}}:[A-Za-z_ ]+$') AND NOT regexp_matches(x.network, ':(Business|Spur|Loop|Bypass|Alternate|Truck|Historic)$')
                                      FOR x IN routes]), false) AS county_route,
               names.primary IS NOT NULL AS has_name,
               {PROJ} AS g
        FROM '{ref}-overture-roads.parquet'
    """)
    con.sql("""
        CREATE OR REPLACE TEMP TABLE rf AS
        SELECT t.GEOID,
          sum(L) AS road_len,
          sum(L) FILTER (WHERE class IN ('motorway','trunk','primary','secondary')) AS named_len,
          sum(L) FILTER (WHERE class='motorway') AS motorway_len,
          sum(L) FILTER (WHERE class='trunk') AS trunk_len,
          sum(L) FILTER (WHERE class='primary') AS primary_len,
          sum(L) FILTER (WHERE class='secondary') AS secondary_len,
          sum(L) FILTER (WHERE class='tertiary') AS tertiary_len,
          sum(L) FILTER (WHERE class='residential') AS residential_len,
          sum(L) FILTER (WHERE class='unclassified') AS unclassified_len,
          sum(L) FILTER (WHERE hwy) AS hwy_len,
          sum(L) FILTER (WHERE hwy AND class IN ('motorway','trunk','primary','secondary')) AS hwy_named_len,
          sum(L) FILTER (WHERE hwy AND class NOT IN ('motorway','trunk','primary','secondary')) AS hwy_unnamed_len,
          sum(L) FILTER (WHERE interstate) AS interstate_len,
          sum(L) FILTER (WHERE county_route) AS county_route_len,
          sum(L) FILTER (WHERE has_name) AS named_street_len
        FROM (SELECT t.GEOID, r.class, r.hwy, r.interstate, r.county_route, r.has_name,
                     ST_Length(ST_Intersection(r.g, t.g)) AS L
              FROM r JOIN t ON ST_Intersects(r.g, t.g)) x
        JOIN t USING (GEOID)
        GROUP BY t.GEOID
    """)

    # Buildings: assign by centroid; break counts down by upstream source.
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE b AS
        SELECT ST_Centroid({PROJ}) AS p, ST_Area({PROJ}) AS area,
               sources[1].dataset AS ds
        FROM '{ref}-overture-buildings.parquet'
    """)
    con.sql("""
        CREATE OR REPLACE TEMP TABLE bf AS
        SELECT t.GEOID, count(*) AS bldg_n, sum(area) AS bldg_area,
          count(*) FILTER (WHERE ds='OpenStreetMap') AS bldg_osm,
          count(*) FILTER (WHERE ds ILIKE '%microsoft%') AS bldg_ms,
          count(*) FILTER (WHERE ds ILIKE '%google%') AS bldg_google,
          count(*) FILTER (WHERE ds ILIKE '%esri%') AS bldg_esri,
          count(*) FILTER (WHERE area < 40) AS bldg_small
        FROM b JOIN t ON ST_Within(b.p, t.g) GROUP BY t.GEOID
    """)

    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE pf AS
        SELECT t.GEOID, count(*) AS poi_n,
          count(*) FILTER (WHERE confidence >= 0.5) AS poi_conf50,
          count(*) FILTER (WHERE confidence >= 0.8) AS poi_conf80,
          count(*) FILTER (WHERE cat='fire_department') AS poi_fire,
          count(*) FILTER (WHERE cat='ambulance_and_ems_services') AS poi_ems,
          count(*) FILTER (WHERE cat IN ('elementary_school','middle_school','high_school','school','private_school','public_school')) AS poi_school,
          count(*) FILTER (WHERE list_contains(alt, 'fire_department') OR cat ILIKE '%fire%') AS poi_fire_any,
          count(*) FILTER (WHERE cat ILIKE '%school%' OR list_bool_or([a ILIKE '%school%' FOR a IN alt])) AS poi_school_any,
          count(*) FILTER (WHERE cat ILIKE '%hospital%') AS poi_hospital,
          count(*) FILTER (WHERE operating_status='open') AS poi_open,
          count(*) FILTER (WHERE nsrc > 1) AS poi_multisrc,
          count(*) FILTER (WHERE has_web) AS poi_web
        FROM (SELECT categories.primary AS cat, coalesce(categories.alternate, []) AS alt, confidence,
                     operating_status, len(sources) AS nsrc, len(websites) > 0 AS has_web,
                     ST_Transform(geometry, 'EPSG:4326', 'EPSG:5070', always_xy := true) AS p
              FROM '{ref}-overture-pois.parquet') q
        JOIN t ON ST_Within(q.p, t.g) GROUP BY t.GEOID
    """)

    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE xf AS
        SELECT t.GEOID, count(*) AS infra_n FROM
          (SELECT ST_Centroid({PROJ}) AS p FROM '{ref}-overture-infrastructure.parquet') q
        JOIN t ON ST_Within(q.p, t.g) GROUP BY t.GEOID
    """)
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rl AS
        SELECT t.GEOID, sum(ST_Length(ST_Intersection(q.g, t.g))) AS rail_len FROM
          (SELECT {PROJ} AS g FROM '{ref}-overture-rail.parquet') q
        JOIN t ON ST_Intersects(q.g, t.g) GROUP BY t.GEOID
    """)

    df = con.sql(f"""
        SELECT '{region}' AS region, t.GEOID, ST_Area(t.g) AS tract_area_m2,
               a.housing_units, rf.* EXCLUDE (GEOID), bf.* EXCLUDE (GEOID), pf.* EXCLUDE (GEOID),
               xf.infra_n, rl.rail_len
        FROM t
        LEFT JOIN '{ref}-census-acs-housing.parquet' a USING (GEOID)
        LEFT JOIN rf USING (GEOID) LEFT JOIN bf USING (GEOID) LEFT JOIN pf USING (GEOID)
        LEFT JOIN xf USING (GEOID) LEFT JOIN rl USING (GEOID)
    """).df()
    df.to_parquet(f"{OUT}/features-{region}.parquet", index=False)
    print(region, df.shape, flush=True)


for reg in (sys.argv[3:] or REGIONS):
    run(reg)
