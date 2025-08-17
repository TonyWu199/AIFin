#!/usr/bin/env python3
"""
AIFin Project Main Entry Point
"""

import os
import sys
import argparse
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 确保log目录存在 (修改为与src同级目录)
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

from db.api import main as api_main
from db.init_db import main as init_db_main
from ib.ib_connect import main as ib_connect_main

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def main():
    """Main function"""
    setup_logging()
    
    parser = argparse.ArgumentParser(description='AIFin Stock Data Analysis System')
    parser.add_argument(
        'command', 
        choices=['api', 'init-db', 'ib-connect'],
        help='Command to execute: api(start API service), init-db(initialize database), ib-connect(connect to IB to get data)'
    )
    
    # Parse known args to get the command first
    args, remaining_argv = parser.parse_known_args()
    
    if args.command == 'api':
        api_main()
    elif args.command == 'init-db':
        init_db_main()
    elif args.command == 'ib-connect':
        # For ib-connect, we need to parse the remaining arguments
        ib_parser = argparse.ArgumentParser(description='IB Connect - Get historical stock data from Interactive Brokers')
        ib_parser.add_argument('--duration', type=str, default="4",
                            help='Duration value (default: 4) month')
        ib_parser.add_argument('--bar-size', type=str, default="1",
                            help='Bar size value (default: 1) day')
        
        # Parse only the remaining arguments
        ib_args = ib_parser.parse_args(remaining_argv)
        ib_connect_main(ib_args)

if __name__ == '__main__':
    main()