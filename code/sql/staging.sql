CREATE SCHEMA IF NOT EXISTS staging;

DROP TABLE IF EXISTS staging.flights_stg;

CREATE TABLE IF NOT EXISTS staging.flights_stg (
    flight_date DATE NOT NULL,

    airline VARCHAR(10),
    flight_number INTEGER,
    tail_number VARCHAR(20),

    origin_airport VARCHAR(10),
    destination_airport VARCHAR(10),

    scheduled_departure_ts TIMESTAMP,
    actual_departure_ts TIMESTAMP,
    wheels_off_ts TIMESTAMP,

    scheduled_arrival_ts TIMESTAMP,
    actual_arrival_ts TIMESTAMP,
    wheels_on_ts TIMESTAMP,

    scheduled_time_minutes INTEGER,
    elapsed_time_minutes INTEGER,
    air_time_minutes INTEGER,

    distance NUMERIC,

    departure_delay_minutes NUMERIC,
    arrival_delay_minutes NUMERIC,

    taxi_out_minutes NUMERIC,
    taxi_in_minutes NUMERIC,

    diverted SMALLINT,
    cancelled SMALLINT,
    cancellation_reason VARCHAR(10),

    air_system_delay_minutes NUMERIC,
    security_delay_minutes NUMERIC,
    airline_delay_minutes NUMERIC,
    late_aircraft_delay_minutes NUMERIC,
    weather_delay_minutes NUMERIC
);