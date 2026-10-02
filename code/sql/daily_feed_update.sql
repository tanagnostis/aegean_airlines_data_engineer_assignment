WITH feed_dates AS ( 
    SELECT 
        MIN(flight_date) AS feed_min_date, 
        MAX(flight_date) AS feed_max_date 
    FROM staging.daily_feed 
), correction_window AS ( 
    SELECT 
        GREATEST( feed_min_date, feed_max_date - INTERVAL '6 days' )::DATE AS correction_start, 
        feed_max_date::DATE AS correction_end 
    FROM feed_dates 
)  

------------------------------------------------------------ -- Delete affected facts -- ------------------------------------------------------------ 

DELETE FROM dwh.fact_flights f 
USING correction_window w 
WHERE f.date_key BETWEEN TO_CHAR(w.correction_start, 'YYYYMMDD')::INTEGER AND TO_CHAR(w.correction_end, 'YYYYMMDD')::INTEGER; 

------------------------------------------------------------ -- Refresh DATE dimension -- ------------------------------------------------------------ 
INSERT INTO dwh.dim_date ( date_key, full_date, year, month, day, day_of_week ) 
    SELECT DISTINCT 
        TO_CHAR(flight_date, 'YYYYMMDD')::INTEGER, 
        flight_date::DATE, 
        EXTRACT(YEAR FROM flight_date)::INTEGER, 
        EXTRACT(MONTH FROM flight_date)::INTEGER, 
        EXTRACT(DAY FROM flight_date)::INTEGER, 
        EXTRACT(ISODOW FROM flight_date)::INTEGER
    FROM staging.daily_feed 
    WHERE flight_date IS NOT NULL 
    ON CONFLICT (date_key) DO NOTHING; 

------------------------------------------------------------ -- Refresh AIRLINE dimension -- ------------------------------------------------------------ 

INSERT INTO dwh.dim_airline ( airline_code ) 
    SELECT DISTINCT 
        airline 
    FROM staging.daily_feed 
    WHERE airline IS NOT NULL 
    ON CONFLICT (airline_code) DO NOTHING;

------------------------------------------------------------ -- Refresh AIRPORT dimension -- ------------------------------------------------------------ 
INSERT INTO dwh.dim_airport ( airport_code ) 
    SELECT 
        origin_airport 
    FROM staging.daily_feed 
    WHERE origin_airport IS NOT NULL 
    UNION 
    SELECT 
        destination_airport 
    FROM staging.daily_feed 
    WHERE destination_airport IS NOT NULL 
    ON CONFLICT (airport_code) DO NOTHING;

------------------------------------------------------------ -- Reinsert affected facts -- ------------------------------------------------------------ 
INSERT INTO dwh.fact_flights (
    date_key,
    airline_key,
    origin_airport_key,
    destination_airport_key,
    flight_number,
    tail_number,

    scheduled_departure_ts,
    actual_departure_ts,
    wheels_off_ts,
    wheels_on_ts,
    scheduled_arrival_ts,
    actual_arrival_ts,

    scheduled_time_minutes,
    elapsed_time_minutes,
    air_time_minutes,
    distance,

    departure_delay_minutes,
    arrival_delay_minutes,

    taxi_out_minutes,
    taxi_in_minutes,

    diverted,
    cancelled,
    cancellation_reason,

    air_system_delay_minutes,
    security_delay_minutes,
    airline_delay_minutes,
    late_aircraft_delay_minutes,
    weather_delay_minutes
)
SELECT
    d.date_key,
    a.airline_key,
    ao.airport_key,
    ad.airport_key,

    f.flight_number,
    f.tail_number,

    f.scheduled_departure_ts,
    f.actual_departure_ts,
    f.wheels_off_ts,
    f.wheels_on_ts,
    f.scheduled_arrival_ts,
    f.actual_arrival_ts,

    f.scheduled_time_minutes,
    f.elapsed_time_minutes,
    f.air_time_minutes,
    f.distance,

    f.departure_delay_minutes,
    f.arrival_delay_minutes,

    f.taxi_out_minutes,
    f.taxi_in_minutes,

    f.diverted,
    f.cancelled,
    f.cancellation_reason,

    f.air_system_delay_minutes,
    f.security_delay_minutes,
    f.airline_delay_minutes,
    f.late_aircraft_delay_minutes,
    f.weather_delay_minutes

FROM staging.daily_feed f
JOIN dwh.dim_date d
    ON d.full_date = f.flight_date
JOIN dwh.dim_airline a
    ON a.airline_code = f.airline
JOIN dwh.dim_airport ao
    ON ao.airport_code = f.origin_airport
JOIN dwh.dim_airport ad
    ON ad.airport_code = f.destination_airport
WHERE f.flight_date IS NOT NULL;