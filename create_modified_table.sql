--This is the table I used to train my logistic regression model
--I added calculated fields to improve model performance

CREATE OR REPLACE TABLE `flight_delay_ML.flight_features_v16` AS

WITH base AS (
  SELECT *
  FROM `flight_delay_ML.flight-delay-all-rows`
  WHERE cancelled = 0
    AND dep_del15 IS NOT NULL
),
airport_stats AS (
  SELECT
    origin,
    AVG(dep_del15) AS origin_delay_rate
  FROM base
  GROUP BY origin
),
airline_stats AS (
  SELECT
    op_unique_carrier,
    AVG(dep_del15) AS airline_delay_rate
  FROM base
  GROUP BY op_unique_carrier
),
airport_hour_stats AS (
  SELECT
    origin,
    FLOOR(crs_dep_time / 100) AS dep_hour,
    AVG(dep_del15) AS origin_hour_delay_rate
  FROM base
  GROUP BY origin, FLOOR(crs_dep_time / 100)
),
route_stats AS (
  SELECT
    origin,
    dest,
    COUNT(*) AS route_cnt,
    AVG(dep_del15) AS route_delay_rate
  FROM base
  GROUP BY origin, dest
),
route_stats_smoothed AS (
  SELECT
    origin,
    dest,
    CASE
      WHEN route_cnt >= 300 THEN LOG(1 + route_delay_rate)
      ELSE NULL
    END AS route_signal_soft
  FROM route_stats
)

SELECT
  b.dep_del15,

  b.year,
  b.quarter,
  b.month,
  b.day_of_week,
  b.day_of_month,
  FLOOR(b.crs_dep_time / 100) AS dep_hour,
  b.dep_time_blk,
  b.op_unique_carrier,
  b.origin,
  b.dest,
  b.distance_group,
  SAFE_DIVIDE(b.crs_elapsed_time, NULLIF(b.distance, 0)) AS speed_proxy,
  a.origin_delay_rate,
  al.airline_delay_rate,
  ah.origin_hour_delay_rate,
  COALESCE(rss.route_signal_soft, a.origin_delay_rate) AS route_fallback_signal,
  b.weather_delay,
  b.late_aircraft_delay

FROM base b

LEFT JOIN airport_stats a
  ON b.origin = a.origin
LEFT JOIN airline_stats al
  ON b.op_unique_carrier = al.op_unique_carrier
LEFT JOIN airport_hour_stats ah
  ON b.origin = ah.origin
 AND FLOOR(b.crs_dep_time / 100) = ah.dep_hour
LEFT JOIN route_stats_smoothed rss
  ON b.origin = rss.origin
 AND b.dest = rss.dest;