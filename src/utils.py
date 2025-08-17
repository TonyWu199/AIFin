import os
import logging
import csv
import json
from typing import List, Dict, Optional, Any

# Read all company codes from configuration file
def load_companies():
    """Load all company codes from configuration file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'companies.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('companies', [])
    except Exception as e:
        logging.warning(f"Failed to read company configuration file: {e}, using default company code")
        return [os.getenv("COMPANY", "BABA")]

COMPANY = os.getenv("COMPANY", "BABA")

logger = logging.getLogger(__name__)

def _parse_value(value):
    """Parse data values"""
    if value is None:
        return None
    s = value.strip()
    if s == "":
        return None
    try:
        # Prefer float, then check if it's an integer
        num = float(s)
        if num.is_integer():
            return int(num)
        return num
    except Exception:
        return s


def find_file(
    directory: str = "./Data", 
    duration: str = "4M", 
    bar_size :str = "1day"
    ) -> Optional[str]:
    """Find CSV file for the specified stock"""
    try:
        possible_csv_files = [
            f"{COMPANY}_{duration}_{bar_size}.csv",
        ]
        
        for csv_filename in possible_csv_files:
            csv_path = os.path.join(directory, csv_filename)
            if os.path.exists(csv_path):
                logger.info(f"Found existing data file: {csv_path}")
                return csv_path
        
        logger.warning(f"Cannot find existing file for {COMPANY}.")
        return None
    except Exception as e:
        logger.error(f"Error finding existing file: {e}")
        return None

def load_csv_data(csv_path: str) -> str:
    """Read data from the specified CSV file and return as JSON string"""
    try:
        records = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            drop_first = False
            if headers and (headers[0].strip() == "" or headers[0].lower().startswith("unnamed")):
                drop_first = True
                headers = headers[1:]
            for row in reader:
                if drop_first and len(row) > 0:
                    row = row[1:]
                item = {}
                for i in range(min(len(headers), len(row))):
                    key = headers[i]
                    item[key] = _parse_value(row[i])
                records.append(item)
        
        logger.info(f"Successfully loaded CSV data, {len(records)} records in total")
        #TODO: Display date
        return json.dumps(records, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error loading CSV data: {e}")
        return ""

def read_markdown_file(md_path: str) -> Optional[str]:
    """Read the specified markdown file and return content string"""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"Successfully read markdown file: {md_path}")
        return content
    except FileNotFoundError:
        logger.warning(f"File not found: {md_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return None

def count_tokens(text: str, encoding) -> int:
    """Count tokens in text using tiktoken"""
    return len(encoding.encode(text))