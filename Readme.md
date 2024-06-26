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

### Dump the csv data in Data folder 
* store_timezone.csv
* store_hours.csv
* store_status.csv

Start the Application
```bash
uvicorn app.main:app --reload
```
## How It Works
# Data Ingestion
* The system periodically reads from the specified CSV files.
* A custom logic ensures that only new data entries since the last poll are imported, avoiding duplicates. This is tracked using a file that records the last read line of each CSV (dataread.txt).

## Data Processing

### Efficient Data Ingestion

The system is designed to handle large volumes of data by periodically ingesting updates from CSV files. Here's how it ensures efficiency and accuracy:

- **Read Last Processed Line**: To avoid reprocessing data, the system reads a JSON file (`data_upload_check.txt`) that records the last processed line for each data type (store status, business hours, and time zone). This mechanism ensures that each hourly data ingestion starts right where the last one ended.

- **Batch Processing**: Data is ingested in chunks, allowing the system to manage memory effectively and improve performance. Each batch of new entries is appended to the respective tables in the PostgreSQL database.

- **Update Last Processed Line**: After processing each chunk, the system updates the JSON file with the latest line number that was processed. This step is crucial for maintaining data integrity and ensuring that subsequent data reads are accurate.

### Time-Sensitive Scheduling
- **Scheduled Jobs**: Using APScheduler, the system schedules data ingestion tasks to run hourly. Each job is specifically tailored to update its designated CSV file and database table, ensuring the latest data is always available.
- **Immediate Execution on Startup**: The jobs are configured to start processing immediately upon system startup, guaranteeing that data feeds are always current and reflect the most recent updates

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
## Handling Edge Cases

### Start and End Time Calculations

The system computes the duration from the first observed status in each period until the last. It's crucial to accurately record the time spent in each state when a status changes. This computation involves the following considerations:

- **Initial Status in a Period**: At the start of each time period, if the first status data point is delayed (e.g., the first data comes in after 10 minutes from the period start), the system assumes the status has not changed since the period began. The duration calculation starts from the period's start time until the first data point is recorded.

- **Final Status in a Period**: The duration for the last observed status continues until the end of the period unless a new status is recorded. This method ensures that the system does not underreport activity or downtime.

### Gaps in Data

For periods without any data points:

- **Extrapolation Based on Available Data**: If there are gaps in data collection or no operational data for certain periods (e.g., early morning hours), the system extrapolates using the current known status. If a store was last observed as active and no subsequent data contradicts this status, it is assumed to remain active for the duration of the gap.

This approach helps in minimizing the effects of data collection gaps on the overall accuracy of status reporting, ensuring that store operations are appropriately logged and reported.

### Implementation Details

The processing functions are designed to handle these scenarios gracefully, ensuring that data integrity and accuracy are maintained across all reports. The system's design allows for future adjustments and improvements in data extrapolation and gap handling methodologies.

### Data Output Requirement

The output for the application includes detailed uptime and downtime metrics for each store, calculated as follows:

- **Uptime and Downtime within Business Hours**:
  - The system dynamically calculates the uptime and downtime only during the designated business hours. This ensures the accuracy of operational reporting and relevance to actual store performance.

- **Interpolation of Data**:
  - To address gaps in data, where polls might not cover every minute within business hours, the system uses interpolation based on available data points to estimate uptime and downtime.

## Image of the time calculation:
![Blank diagram (5)](https://github.com/shivamsouravjha/loop/assets/60891544/af063fab-403a-4d61-b293-2b9f7a03d6e1)


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
* Ping
  * URL: /basic/ping 
  * Method: GET
  * Success Response:
  * Code: 200
  * Content: Pong
* Post Report
  * URL: /reporting/trigger_report/
  * Method: POST
  * Success Response:
  * Code: 200
  * Content: report_id (random string) will be used for polling the status of report completion

* Note: Since the data is of year 2023, the current generate report is hardcoded to a random date in 2023, you can update it to current date by commenting line 13-14 and uncommenting line 16 in generateReport.py

### Video of the above snippet

https://github.com/shivamsouravjha/loop/assets/60891544/2412e2c0-73bc-473b-bd92-a863ac900523


