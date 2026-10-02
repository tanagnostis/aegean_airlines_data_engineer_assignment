CREATE OR REPLACE VIEW dwh.flights_availability AS
WITH flight_intervals AS (
    SELECT
        f.date_key,
        d.full_date AS flight_date,
        a.airline_code,
        f.tail_number,
        f.actual_departure_ts,
        f.actual_arrival_ts
    FROM dwh.fact_flights f
    JOIN dwh.dim_date d
        ON d.date_key = f.date_key
    JOIN dwh.dim_airline a
        ON a.airline_key = f.airline_key
    WHERE
        f.cancelled = 0
        AND f.diverted = 0
        AND f.actual_departure_ts IS NOT NULL
        AND f.actual_arrival_ts IS NOT NULL
),
flight_days AS (
    SELECT DISTINCT
        date_key,
        flight_date,
        airline_code
    FROM flight_intervals
),
aircraft_days AS (
    SELECT DISTINCT
        fd.date_key,
        fd.flight_date,
        fi.airline_code,
        fi.tail_number
    FROM flight_days fd
    JOIN flight_intervals fi
        ON fi.airline_code = fd.airline_code
),
aircraft_day_windows AS (
    SELECT
        ad.date_key,
        ad.flight_date,
        ad.airline_code,
        ad.tail_number,
        ad.flight_date::timestamp AS day_start,
        (ad.flight_date + INTERVAL '1 day')::timestamp AS day_end,
        (ad.flight_date + TIME '23:00')::timestamp AS night_start,
        (ad.flight_date + INTERVAL '1 day' + TIME '07:00')::timestamp AS night_end
    FROM aircraft_days ad
),
flying_time AS (
    SELECT
        w.date_key,
        w.flight_date,
        w.airline_code,
        w.tail_number,
        COALESCE(SUM(EXTRACT(EPOCH FROM (LEAST(fi.actual_arrival_ts, w.day_end)-GREATEST(fi.actual_departure_ts,w.day_start))) / 60),0) AS flying_minutes,
        COALESCE(SUM(EXTRACT( EPOCH FROM (LEAST(fi.actual_arrival_ts,w.night_end)-GREATEST(fi.actual_departure_ts,w.night_start))) / 60),0) AS night_flying_minutes
    FROM aircraft_day_windows w
    LEFT JOIN flight_intervals fi
        ON fi.airline_code = w.airline_code
        AND fi.tail_number = w.tail_number
        -- Flight overlaps the flight day
        AND fi.actual_departure_ts < w.day_end
        AND fi.actual_arrival_ts > w.day_start
    GROUP BY
        w.date_key,
        w.flight_date,
        w.airline_code,
        w.tail_number
),
aircraft_availability AS (
    SELECT
        date_key,
        flight_date,
        airline_code,
        tail_number,
        1440 - flying_minutes AS ground_time_availability_minutes,
        480 - night_flying_minutes AS night_time_availability_minutes
    FROM flying_time
)
SELECT
    date_key,
    flight_date,
    airline_code,
    COUNT(*) AS aircraft_count,
    SUM(ground_time_availability_minutes) AS availability_minutes,
    ROUND(SUM(ground_time_availability_minutes) / 60.0, 2) AS availability_hours,
    SUM(night_time_availability_minutes) AS night_availability_minutes,
    ROUND(SUM(night_time_availability_minutes) / 60.0,2) AS night_availability_hours
FROM aircraft_availability
GROUP BY
    date_key,
    flight_date,
    airline_code;