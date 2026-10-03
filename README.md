# Aegean Airlines - Data Engineer Assignment

Technical challenge: Find ground time availability and night availability of flight airlines.

## Overview

This project implements an end-to-end data engineering pipeline that extracts US flight data from 2015, transforms them into analytical datasets, creates a dimensional star schema, and loads the data into PostgreSQL.

The final warehouse follows a Kimball-style dimensional model optimized for analytics and reporting.

---
# Instructions

Make sure to have Python, Docker and Docker Compose to be able to setup and run this ETL pipeline on your machine.
The following instructions will get you a copy of the project up and running on your local machine.
1) Clone the repo: `git@github.com:tanagnostis/aegean_airlines_data_engineer_assignment.git`
2) Download the CSV file (https://www.kaggle.com/usdot/flight-delays?select=flights.csv) and store it in data/historical_data folder/directory
3) To start all the containers and services run: `docker compose up -d`

# Folder structure and description
**code**: Contains a Jupyter Notebook with initial data exploration and Python modules to setup the ETL pipeline, the DWH and database connection.\
**data**: Contains the initial CSV file from https://www.kaggle.com/usdot/flight-delays?select=flights.csv. \ 
The data will be extracted from that file.\
There are 2 subfolders: 
- historical_data (Contains the original data file with the full data of year 2015).
- daily_feed (Contains the daily feed with the corrected/updated data of 7 days from 2015-01-01 to 2015-01-07).
  
**docker-compose.yaml**: designed to create and install the PostgreSQL database and run the ETL pipeline.


## Database PostgreSQL
1) To access the database through pgadmin.
- Go to: [pdadmin](http://localhost:8080)
- Access details:
  - username: flights@domain.com
  - password: flights26
- Server setup:
  - hostname/address: postgres
  - port: 5432
  -  database = flights_db
  -  user = flights_db_user
  -  password = flights_db_password

2) You can access the PostgreSQL database on any other RDBMS to see and query the populated tables.

- Login details:
- host = localhost
- port = 5434
- database = flights_db
- user = flights_db_user
- password = flights_db_password

## Tasks
### Task1: Create DWH and use a daily feed with the rolling last n flight days

The source can correct records from the most recent 7 flight days. \
I would therefore require a minimum rolling window of 7 days, but I would prefer a 14-day feed if the source supports it.  
The additional 7 days provide a recovery and validation buffer for pipeline failures, delayed processing, and late-arriving corrections. \
I would validate that the feed contains the expected date range and reprocess the authoritative correction window rather than blindly appending records.

### Task2: Create flights availability dataset

I created a view (dwh.flights_availability) to be able to see the flight availability and query this view each day after the daily feed has updated the DWH.

## Further ideas and Improvements
- Setup Airflow to orchestrate the ETL pipeline and future daily incremental loads
- Add more data quality and data validation checks
