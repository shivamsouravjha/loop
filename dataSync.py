import pandas as pd
from sqlalchemy import create_engine

# Database connection details
DATABASE_URL = "postgresql://storageData:storageData@localhost:5432/storageData"

# Create a database engine
engine = create_engine(DATABASE_URL)


def read_last_processed_line(file_path):
    """ Read the last processed line index from a file. """
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return 0  # If no file or empty/corrupt file, start from the beginning

def write_last_processed_line(file_path, line_number):
    """ Write the last processed line index to a file. """
    try:
        with open(file_path, 'w') as file:
            file.write(str(line_number))
    except IOError:
        return

# Define a function to load a CSV file to a specified table
def load_csv_to_db(csv_file_path,table_name,index_file_path ):
    # Load CSV file into DataFrame
    chunk_size = 10000  # Size of each chunk
    start_line = read_last_processed_line(index_file_path)
    for chunk in pd.read_csv(csv_file_path, skiprows=range(1, start_line + 1), chunksize=chunk_size):
        chunk.to_sql(table_name, con=engine, if_exists='append', index=False)
        # Update the last processed line
        start_line += len(chunk)
        write_last_processed_line(index_file_path, start_line)

# Call the function for each CSV file and respective table name
