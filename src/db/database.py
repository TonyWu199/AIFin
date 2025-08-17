import os
import logging
from typing import List, Dict, Optional, Any
import mysql.connector
from mysql.connector import Error
import csv

# 为database模块创建独立的日志配置
logger = logging.getLogger('db.database')
logger.setLevel(logging.INFO)

# 只在logger没有处理器时添加处理器
if not logger.handlers:
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)

class StockDatabase:
    """Class for handling stock data interaction with MySQL database"""
    
    def __init__(self, host: str = "localhost", database: str = "stock_db", 
                 user: str = "root", password: str = "", port: int = 3306):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password  # Note: Password should not be displayed in logs
        self.connection = None
    
    def connect(self) -> bool:
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                logger.info(f"Successfully connected to MySQL database {self.database} (MySQL version: {db_info})")
                return True
                
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL database connection closed")
    
    def create_table(self) -> bool:
        """Create stock data table"""
        try:
            cursor = self.connection.cursor()
            
            # SQL statement to create table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS stock_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                open_price DECIMAL(10, 4),
                high_price DECIMAL(10, 4),
                low_price DECIMAL(10, 4),
                close_price DECIMAL(10, 4),
                volume DECIMAL(15, 2),
                average DECIMAL(10, 4),
                bar_count INT,
                company VARCHAR(10) NOT NULL,
                UNIQUE KEY unique_date_company (date, company)
            )
            """
            
            cursor.execute(create_table_query)
            self.connection.commit()
            cursor.close()
            logger.info("Stock data table created successfully")
            return True
            
        except Error as e:
            logger.error(f"Error creating table: {e}")
            return False
    
    def insert_stock_data(self, csv_file_path: str, company: str) -> bool:
        """Insert stock data from CSV file into database"""
        try:
            cursor = self.connection.cursor()
            
            # Read CSV file and insert data
            with open(csv_file_path, 'r') as file:
                csv_reader = csv.DictReader(file)
                # Use ON DUPLICATE KEY UPDATE to handle duplicate data
                insert_query = """
                INSERT INTO stock_data 
                (date, open_price, high_price, low_price, close_price, volume, average, bar_count, company)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                open_price = VALUES(open_price),
                high_price = VALUES(high_price),
                low_price = VALUES(low_price),
                close_price = VALUES(close_price),
                volume = VALUES(volume),
                average = VALUES(average),
                bar_count = VALUES(bar_count)
                """
                
                records = []
                for row in csv_reader:
                    record = (
                        row['date'],
                        float(row['open']) if row['open'] else None,
                        float(row['high']) if row['high'] else None,
                        float(row['low']) if row['low'] else None,
                        float(row['close']) if row['close'] else None,
                        float(row['volume']) if row['volume'] else None,
                        float(row['average']) if row['average'] else None,
                        int(float(row['barCount'])) if row['barCount'] else None,
                        company
                    )
                    records.append(record)
                
                cursor.executemany(insert_query, records)
                self.connection.commit()
                logger.info(f"Successfully inserted or updated {cursor.rowcount} {company} stock data records")
            
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error inserting stock data: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            return False
    
    def get_stock_data(self, company: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get stock data from database"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if limit:
                select_query = """
                SELECT date, open_price, high_price, low_price, close_price, volume, average, bar_count, company
                FROM stock_data 
                WHERE company = %s 
                ORDER BY date DESC 
                LIMIT %s
                """
                cursor.execute(select_query, (company, limit))
            else:
                select_query = """
                SELECT date, open_price, high_price, low_price, close_price, volume, average, bar_count, company
                FROM stock_data 
                WHERE company = %s 
                ORDER BY date DESC
                """
                cursor.execute(select_query, (company,))
            
            records = cursor.fetchall()
            cursor.close()
            
            # Convert date format
            for record in records:
                if record['date']:
                    record['date'] = record['date'].strftime('%Y-%m-%d')
            
            return records
            
        except Error as e:
            logger.error(f"Error querying stock data: {e}")
            return []
    
    def get_latest_stock_data(self, company: str) -> Optional[Dict[str, Any]]:
        """Get the latest stock data"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            select_query = """
            SELECT date, open_price, high_price, low_price, close_price, volume, average, bar_count, company
            FROM stock_data 
            WHERE company = %s 
            ORDER BY date DESC 
            LIMIT 1
            """
            cursor.execute(select_query, (company,))
            
            record = cursor.fetchone()
            cursor.close()
            
            # Convert date format
            if record and record['date']:
                record['date'] = record['date'].strftime('%Y-%m-%d')
            
            return record
            
        except Error as e:
            logger.error(f"Error querying latest stock data: {e}")
            return None