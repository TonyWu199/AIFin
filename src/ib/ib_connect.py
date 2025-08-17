from ast import arg
import os
import sys
import argparse  # Add argparse import
from ib_insync import *
import pandas as pd
import logging
from typing import Optional, List  # Add List for type hinting

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_companies, find_file

# 确保log目录存在 (修改为与src同级目录)
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 为ib_connect模块创建独立的日志配置
logger = logging.getLogger('ib.ib_connect')

# 只有在logger没有处理器时才添加处理器，避免重复
if not logger.handlers:
    logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(os.path.join(log_dir, 'ib_connect.log'), encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)


class IBServer:
    """IB connection and data acquisition management class"""
    
    def __init__(self, host='127.0.0.1', port=4001, client_id=741):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.connected = False
        self.save_dir = os.path.join(os.getcwd(), "data")
        
    def connect(self) -> bool:
        """Connect to IB Gateway/TWS"""
        try:
            logger.info(f"Connecting to IB Gateway/TWS {self.host}:{self.port}...")
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            logger.info("Connecting IB successfully!")
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Fail to connect to IB: {e}")
            logger.info("Using offline mode")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IB"""
        if not self.connected:
            return
            
        try:
            self.ib.disconnect()
            self.connected = False
        except Exception as e:
            logger.error(f"Fail to disconnect to IB: {e}")
    
    def get_data(
        self, 
        company: str,
        duration: str = '4 M', 
        bar_size: str = '1 day', 
        what_to_show: str = 'TRADES',
        use_rth: bool = True,
        is_save: bool = True
    ) -> Optional[pd.DataFrame]:
        """Get historical data"""
        if not self.connected:
            logger.warning("IB is offline, cannot get historical data.")
            return None
            
        try:
            logger.info(f"Requesting {company} historical data...")
            contract = Stock(company, 'SMART', 'USD')
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth,
                formatDate=1
            )
            
            if bars:
                df = util.df(bars)
                logger.info(f"Successfully retrieved {company} data with {len(df)} records")
                
                if is_save:
                    self.save_data(df, company, duration, bar_size)
                return df
            else:
                logger.warning(f"Failed to retrieve historical data for {company}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data for {company}: {e}")
            return None
    
    def save_data(
        self,
        df: pd.DataFrame,
        company: str,
        duration: str = '4M', 
        bar_size: str = '1day'
    ) -> str:
        """Save data to CSV file"""
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)

        try:
            filepath = f"{self.save_dir}/{company}_{duration.replace(' ','')}_{bar_size.replace(' ','')}.csv"
            df.to_csv(filepath, index=False)
            logger.info(f"Saving stock data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving stock data: {e}")
            return ""

def main(args=None):
    """Main function example"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='IB Connect - Get historical stock data from Interactive Brokers')
    parser.add_argument('--duration', type=str, default="4",
                        help='Duration value (default: 4) month')
    parser.add_argument('--bar-size', type=str, default="1",
                        help='Bar size value (default: 1) day')
    
    # If args is not provided, parse from sys.argv
    if args is None:
        args = parser.parse_args()
    
    # Format duration and bar size for IB
    duration = f"{args.duration} M"
    bar_size = f"{args.bar_size} day"
    
    # Load companies from companies.json
    companies = load_companies()
    logger.info(f"Companies to fetch data for: {companies}")
    
    # 初始化IB服务器
    ib_server = IBServer()
    
    # 尝试连接IB
    try:
        ib_connected = ib_server.connect()
        if ib_connected:
            logger.info("IB connection successful, real-time data available")
        else:
            logger.warning("IB connection failed, using offline mode")
    except Exception as e:
        logger.error(f"Error connecting to IB: {e}")
        logger.info("Will use offline mode")
    
    try:
        # 获取股票数据
        # 如果IB连接成功，尝试获取实时数据
        csv_file = None
        if ib_server.connected:
            logger.info("Attempting to get real-time data from IB...")
            for company in companies:
                ib_server.get_data(company=company, duration=duration, bar_size=bar_size)
        else:
            # IB未连接，直接尝试从现有文件获取
            logger.info("IB not connected, attempting to get data from existing CSV files...")
            for company in companies:
                csv_file = find_file(duration=duration, bar_size=bar_size)
                logger.info(f"Data file for {company}: {csv_file}")
        
    finally:
        # 断开连接
        ib_server.disconnect()


if __name__ == "__main__":
    main()