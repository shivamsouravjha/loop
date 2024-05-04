### Loop Project
The Loop project is designed to manage and analyze operational data from multiple stores. It leverages the FastAPI framework to serve data through a REST API, and uses PostgreSQL for data storage. This system dynamically processes and reports on store activity by comparing hourly polls of store activity to their respective business hours and time zones.

### Features
Dynamic Data Handling: Imports data hourly from CSVs into a PostgreSQL database, ensuring all data analyses are up-to-date.
Time Zone Awareness: Adjusts data from UTC to local time zones for accurate reporting during business hours.
Business Hour Calculation: Only includes uptime and downtime during defined business hours, with logic to handle missing data.

### Data Sources
Store Activity Polls: Hourly data about store activity (store_id, timestamp_utc, status). Download CSV
Business Hours: Weekly business hours for stores. Download CSV
Time Zones: Time zone information for each store. Download CSV

###System Requirements
```
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
# Install Dependencies
```bash
pip install -r requirements.txt
```
# Initialize the Database
```bash
docker-compose up -d
```

# Setup the database by running 
```bash
python3 app/database/createSchema.py
```

Start the Application
```bash
uvicorn app.main:app --reload
```
###H ow It Works
# Data Ingestion
* The system periodically reads from the specified CSV files.
* A custom logic ensures that only new data entries since the last poll are imported, avoiding duplicates. This is tracked using a file that records the last read line of each CSV (dataread.txt).

# Data Processing
* Timestamps from CSVs are converted from UTC to the respective local time zones of the stores to align the polls with business hours.
* During the specified business hours, the system calculates uptime and downtime based on the status changes observed in the polls.

# Database Choice
PostgreSQL was chosen for its robust handling of time-based data and excellent support for complex queries, which are essential for the time zone conversions and the dynamic querying needed by this application.

# Reporting
The API endpoint /report provides a detailed report based on the latest data, including extrapolated uptime and downtime within business hours using interpolation logic to estimate the states between actual polled data points.

# API Usage
* Get Report
* URL: /reporting/report_status/:reportId
* Method: GET
* Success Response:
* Code: 200
* Content: JSON array of reports with uptime and downtime calculations for the last hour, day, and week.

