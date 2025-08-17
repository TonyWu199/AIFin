import os
import sys
import logging
import glob

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import StockDatabase
from utils import COMPANY, load_companies

# 确保log目录存在 (修改为与src同级目录)
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 为init_db模块创建独立的日志配置
logger = logging.getLogger('db.init_db')

# 只有在logger没有处理器时才添加处理器，避免重复
if not logger.handlers:
    logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(os.path.join(log_dir, 'init_db.log'), encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)

def find_csv_files(data_path, company):
    """Find all CSV files containing the specified company code"""
    # Find matching CSV files in project directory and subdirectories
    pattern = f"{data_path}/*{company}*.csv"
    csv_files = glob.glob(pattern, recursive=True)
    
    # Filter out files not in data directory (if needed)
    # csv_files = [f for f in csv_files if 'data' in f]
    
    return csv_files

def main():
    """Initialize database and import CSV data"""
    # Database configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': os.getenv('DB_NAME', 'stock_db'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '')  # Get password from environment variable
    }
    
    logger.info("Connecting to database...")
    logger.info(f"Database configuration: {DB_CONFIG}")
    
    # Create database connection
    db = StockDatabase(**DB_CONFIG)
    
    try:
        # Connect to database
        if not db.connect():
            logger.error("Failed to connect to database")
            logger.info("Please ensure:")
            logger.info("1. MySQL server is running")
            logger.info("2. Database configuration is correct (host, port, username, password)")
            logger.info("3. You can set environment variables as follows:")
            logger.info("   export DB_HOST=localhost")
            logger.info("   export DB_PORT=3306")
            logger.info("   export DB_NAME=stock_db")
            logger.info("   export DB_USER=root")
            logger.info("   export DB_PASSWORD=your_password")
            sys.exit(1)
        
        # Create table
        logger.info("Creating data table...")
        if not db.create_table():
            logger.error("Failed to create data table")
            sys.exit(1)

        # Get all company codes
        companies = load_companies()
        logger.info(f"Loaded company list: {companies}")
        
        data_path="/root/Code/AIFin/data"

        # Import data for each company
        for company in companies:
            logger.info(f"Processing company: {company}")
            
            # Find all matching CSV files
            csv_files = find_csv_files(data_path, company)
            
            if not csv_files:
                logger.warning(f"No CSV files found containing {company}")
                # Try using default path
                default_csv_path = f"{data_path}/{company}_4M_1day.csv"
                if os.path.exists(default_csv_path):
                    csv_files = [default_csv_path]
                    logger.info(f"Using default CSV file: {default_csv_path}")
                else:
                    logger.warning(f"Default CSV file also does not exist: {default_csv_path}")
            
            # Import all found CSV files
            for csv_file_path in csv_files:
                if os.path.exists(csv_file_path):
                    logger.info(f"Found CSV file: {csv_file_path}")
                    logger.info(f"Importing {company} stock data into database...")
                    if db.insert_stock_data(csv_file_path, company):
                        logger.info(f"Successfully imported {company} stock data from {csv_file_path} into database")
                    else:
                        logger.error(f"Failed to import {company} stock data from {csv_file_path}")
                else:
                    logger.warning(f"CSV file does not exist: {csv_file_path}")
            
            # Test query
            logger.info(f"Testing query for latest {company} data...")
            latest_data = db.get_latest_stock_data(company)
            if latest_data:
                logger.info(f"{company} latest data: {latest_data}")
            else:
                logger.warning(f"Could not get latest data for {company}")
            
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        sys.exit(1)
    
    finally:
        # Close database connection
        db.disconnect()

if __name__ == '__main__':
    main()