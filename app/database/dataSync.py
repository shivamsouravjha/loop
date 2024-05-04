import pandas as pd
from app.dependencies import DATABASE_URL
from sqlalchemy import create_engine
import json
import os

sync_engine = create_engine(DATABASE_URL)  # Ensure this is your actual database URL

def read_last_processed_line(file_path, key):
    """Read the last processed line index from a JSON file for a specific key."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get(key, 0)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        # Initialize the file with an empty JSON object if not found or if error in decoding
        with open(file_path, 'w') as file:
            json.dump({}, file)
        return 0  # Return 0 to start from the beginning

def write_last_processed_line(file_path, key, line_number):
    """Write the last processed line index to a JSON file for a specific key."""
    try:
        data = {}
        # Ensure file exists or create an empty one with initial structure
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = {}
        data[key] = line_number
        with open(file_path, 'w') as file:
            json.dump(data, file)
    except IOError as e:
        print("Error updating the last processed line:", e)

def load_csv_to_db(csv_file_path, table_name, index_file_path):
    """Load a CSV file into a database, starting from the last processed line."""
    chunk_size = 10000  # Size of each chunk
    start_line = read_last_processed_line(index_file_path, table_name)
    for chunk in pd.read_csv(csv_file_path, skiprows=range(1, start_line + 1), chunksize=chunk_size):
        if not chunk.empty:
            chunk.to_sql(table_name, con=sync_engine, if_exists='append', index=False)
        # Update the last processed line
        start_line += len(chunk)
    write_last_processed_line(index_file_path, table_name, start_line)
