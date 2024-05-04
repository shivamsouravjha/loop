# Loop Project

The Loop project is designed to manage and analyze operational data from multiple stores. It leverages the FastAPI framework to serve data through a REST API and uses PostgreSQL for data storage. This system dynamically processes and reports on store activity by comparing hourly polls of store activity to their respective business hours and time zones.

## Features

- **Dynamic Data Handling**: Imports data hourly from CSVs into a PostgreSQL database, ensuring all data analyses are up-to-date.
- **Time Zone Awareness**: Adjusts data from UTC to local time zones for accurate reporting during business hours.
- **Business Hour Calculation**: Only includes uptime and downtime during defined business hours, with logic to handle missing data.

## Data Sources

- **Store Activity Polls**: Hourly data about store activity (`store_id, timestamp_utc, status`). [Download CSV](https://drive.google.com/file/d/1UIx1hVJ7qt_6oQoGZgb8B3P2vd1FD025/view?usp=sharing)
- **Business Hours**: Weekly business hours for stores. [Download CSV](https://drive.google.com/file/d/1va1X3ydSh-0Rt1hsy2QSnHRA4w57PcXg/view?usp=sharing)
- **Time Zones**: Time zone information for each store. [Download CSV](https://drive.google.com/file/d/101P9quxHoMZMZCVWQ5o-shonk2lgK1-o/view?usp=sharing)

## System Requirements

```plaintext
Python 3.8+
PostgreSQL
FastAPI
Uvicorn (for serving the API)
```
# Setup Instructions
Clone the Repository
```bash
git clone https://github.com/shivamsouravjha/loop
cd loop
```
### Install Dependencies
```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```
### Initialize the Database
```bash
docker-compose up -d
```

### Setup the database by running 
```bash
python3 app/database/createSchema.py
```

Start the Application
```bash
uvicorn app.main:app --reload
```
## How It Works
# Data Ingestion
* The system periodically reads from the specified CSV files.
* A custom logic ensures that only new data entries since the last poll are imported, avoiding duplicates. This is tracked using a file that records the last read line of each CSV (dataread.txt).

## Data Processing
* Timestamps from CSVs are converted from UTC to the respective local time zones of the stores to align the polls with business hours.
* During the specified business hours, the system calculates uptime and downtime based on the status changes observed in the polls.

## Database Choice
PostgreSQL was chosen for its robust handling of time-based data and excellent support for complex queries, which are essential for the time zone conversions and the dynamic querying needed by this application.

## Reporting
The API endpoint /report provides a detailed report based on the latest data, including extrapolated uptime and downtime within business hours using interpolation logic to estimate the states between actual polled data points.

# Technical Implementation Details

## Timing Calculations

This project addresses the challenge of calculating uptime and downtime across different time zones and business hours through a series of SQL queries and Python functions, incorporating asynchronous programming for efficiency.

### Data Handling and Timezone Considerations

1. **Timezone Awareness**: 
   - Each store's operational data is timestamped in UTC (Universal Coordinated Time) and must be converted to local times based on the store's timezone. This is critical for accurately determining if a store is within its business hours when evaluating its operational status.

2. **Business Hours Alignment**:
   - The application adjusts the store operational status data to align with the local business hours. Only data within these hours contributes to uptime and downtime calculations.
   - If business hours are missing, it defaults to 24/7 operation, and if the timezone data is missing, it defaults to America/Chicago.

### Query Design and Data Processing

- **Subqueries for Time Alignment**:
  - SQL subqueries are used to ensure that the operational status data falls within business hours. This involves converting the UTC timestamps to the local time zone and comparing these with the store's start and end times.

- **Batch Processing**:
  - Data is processed in batches where each batch corresponds to one hour, one day, or one week of data. This allows the application to manage memory efficiently and handle large datasets without performance degradation.

### Asynchronous Processing

- **Concurrent Data Processing**:
  - The application leverages Python's `asyncio` library to handle data processing for hours, days, and weeks concurrently. This is achieved using the `asyncio.gather()` function, which schedules the asynchronous execution of these tasks and waits for all of them to complete. This approach significantly speeds up the processing time as these operations can run in parallel rather than sequentially.

### Handling Edge Cases

- **Start and End Time Calculations**:
  - The initial and final statuses within each batch are crucial for accurate reporting. The system calculates the duration from the first observed status in a period until the last, and if the status changes, it records the time spent in each state.
  - For periods without any data points (e.g., no operational data for an early morning hour), the system extrapolates based on the last known status. This means if a store was last seen active and no data points contradict this, it remains 'active' until proven otherwise.

### Data Output Requirement

The output for the application includes detailed uptime and downtime metrics for each store, calculated as follows:

- **Uptime and Downtime within Business Hours**:
  - The system dynamically calculates the uptime and downtime only during the designated business hours. This ensures the accuracy of operational reporting and relevance to actual store performance.

- **Interpolation of Data**:
  - To address gaps in data, where polls might not cover every minute within business hours, the system uses interpolation based on available data points to estimate uptime and downtime.

### PostgreSQL Usage

- **Database Choice**:
  - PostgreSQL is used due to its robust support for complex queries, reliability in handling time-series data, and capabilities in managing large datasets efficiently. The use of SQL also simplifies the implementation of timezone conversions and time-range checks within queries.

### Last Read Optimization

- **Efficient Data Ingestion**:
  - The system tracks the last line read from each CSV file to ensure that only new data is processed. This prevents the duplication of records and ensures that the database is always up to date without reprocessing the same data.

# API Usage
* Get Report
  * URL: /reporting/report_status/:report_id
  * Method: GET
  * Success Response:
  * Code: 200
  * Content: JSON objects containing data of reports with uptime and downtime calculations for the last hour, day, and week.
* Post Report
  * URL: /reporting/trigger_report/
  * Method: POST
  * Success Response:
  * Code: 200
  * Content: report_id (random string) will be used for polling the status of report completion


