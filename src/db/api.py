import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import StockDatabase
from utils import load_companies

# 确保log目录存在 (修改为与src同级目录)
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 为api模块创建独立的日志配置
logger = logging.getLogger('db.api')
logger.setLevel(logging.INFO)

# 清除现有的处理器（如果有的话）
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 创建文件处理器
file_handler = logging.FileHandler(os.path.join(log_dir, 'api.log'), encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Database configuration - Use environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'stock_db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '')  # Get password from environment variable
}

# Initialize database connection
db = StockDatabase(**DB_CONFIG)

@app.route('/api/stock/<company>/latest', methods=['GET'])
def get_company_latest_stock_data(company):
    """Get the latest stock data for the specified company"""
    try:
        latest_data = db.get_latest_stock_data(company)
        if latest_data:
            return jsonify({
                'status': 'success',
                'data': latest_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Data not found for company {company}'
            }), 404
    except Exception as e:
        logger.error(f"Error getting latest stock data for {company}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/stock/<company>/history', methods=['GET'])
def get_company_history_stock_data(company):
    """Get historical stock data for the specified company"""
    try:
        limit = request.args.get('limit', 30, type=int)  # Default to 30 records
        history_data = db.get_stock_data(company, limit)
        return jsonify({
            'status': 'success',
            'data': history_data
        })
    except Exception as e:
        logger.error(f"Error getting historical stock data for {company}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def main():
    """Start the API service"""
    logger.info("Connecting to database...")
    logger.info(f"Database configuration: {DB_CONFIG}")
    
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
        
        host = os.getenv('API_HOST', '0.0.0.0')
        port = int(os.getenv('API_PORT', 5000))
        
        logger.info(f"Starting API service: http://{host}:{port}")
        app.run(host=host, port=port, debug=True, use_reloader=False)
        
    except Exception as e:
        logger.error(f"Error starting API service: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()