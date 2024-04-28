from sqlalchemy import create_engine, Column, Integer, String, Time, Text,BigInteger, TIMESTAMP, ForeignKey, MetaData, Table
from sqlalchemy.sql.schema import ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID

# Database connection details
DATABASE_URL = "postgresql://storageData:storageData@localhost:5432/storageData"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define the tables
store_status = Table('store_status', metadata,
    Column('store_id', BigInteger, nullable=True),  # Allow store_id to be nullable
    Column('status', String(10)),
    Column('timestamp_utc', TIMESTAMP(timezone=True)),
)

store_hours = Table('store_hours', metadata,
    Column('store_id', BigInteger, nullable=True),  # Allow store_id to be nullable
    Column('day', Integer),
    Column('start_time_local', Time),
    Column('end_time_local', Time),
)

store_timezone = Table('store_timezone', metadata,
    Column('store_id', BigInteger, primary_key=True),
    Column('timezone_str', String(50), default='America/Chicago')
)

store_reports = Table('store_reports', metadata,
    Column('report_id', UUID, primary_key=True),  # Using UUID as the primary key
    Column('status', String(10), nullable=False),  # Status field, not nullable
    Column('data', Text),  # Text field for storing report data
    Column('created_at', TIMESTAMP, default='now()'),  # Timestamp with default value
)

# Create the tables in the database
metadata.create_all(engine)
