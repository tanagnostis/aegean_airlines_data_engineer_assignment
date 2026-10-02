DROP TABLE IF EXISTS dwh.fact_flights;
DROP TABLE IF EXISTS dwh.dim_airport;
DROP TABLE IF EXISTS dwh.dim_airline;
DROP TABLE IF EXISTS dwh.dim_date;

DROP SCHEMA IF EXISTS dwh;
CREATE SCHEMA IF NOT EXISTS dwh;


CREATE TABLE IF NOT EXISTS dwh.dim_airline (
    airline_key BIGSERIAL PRIMARY KEY,
    airline_code VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_airport (
    airport_key BIGSERIAL PRIMARY KEY,
    airport_code VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dwh.fact_flights (
    flight_key BIGSERIAL PRIMARY KEY,

    date_key INTEGER NOT NULL
        REFERENCES dwh.dim_date(date_key),

    airline_key BIGINT NOT NULL
        REFERENCES dwh.dim_airline(airline_key),

    origin_airport_key BIGINT
        REFERENCES dwh.dim_airport(airport_key),

    destination_airport_key BIGINT
        REFERENCES dwh.dim_airport(airport_key),

    -- Natural/source identifiers
    flight_number INTEGER,
    tail_number VARCHAR(20),

    -- Actual timestamps
    scheduled_departure_ts TIMESTAMP,
    actual_departure_ts TIMESTAMP,
    wheels_off_ts TIMESTAMP,
    wheels_on_ts TIMESTAMP,
    scheduled_arrival_ts TIMESTAMP,
    actual_arrival_ts TIMESTAMP,

    -- Duration / measures
    scheduled_time_minutes INTEGER,
    elapsed_time_minutes INTEGER,
    air_time_minutes INTEGER,
    distance NUMERIC,

    departure_delay_minutes NUMERIC,
    arrival_delay_minutes NUMERIC,

    taxi_out_minutes NUMERIC,
    taxi_in_minutes NUMERIC,

    -- Flight status
    diverted SMALLINT,
    cancelled SMALLINT,
    cancellation_reason VARCHAR(10),

    -- Delay breakdown
    air_system_delay_minutes NUMERIC,
    security_delay_minutes NUMERIC,
    airline_delay_minutes NUMERIC,
    late_aircraft_delay_minutes NUMERIC,
    weather_delay_minutes NUMERIC
);