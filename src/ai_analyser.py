import csv
import json
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import tiktoken
from openai import OpenAI

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_csv_data, count_tokens
from utils import COMPANY

# Configure logging (修改为与src同级目录)
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 为ai_analyser模块创建独立的日志配置
logger = logging.getLogger('ai.analyser')
logger.setLevel(logging.INFO)

# 清除现有的处理器（如果有的话）
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 创建文件处理器
file_handler = logging.FileHandler(os.path.join(log_dir, 'ai_analyser.log'), encoding='utf-8')
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

class AISearch:
    """AI search and analysis management class"""
    
    def __init__(self, api_key: str, base_url: str, model_name: str = "qwen-plus"):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.logger = logging.getLogger('ai.analyser.AISearch')
        self.save_dir = "../report"

        self.set_encoding()
    
    def set_encoding(self):   
        # Initialize tiktoken encoder
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except:
            # If automatic mapping fails, use cl100k_base encoder
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.logger.info("Using cl100k_base encoder")
    
    def analyze_stock(
        self, 
        stock_data: str, 
        existing_analysis: str = "",
        max_tokens: int = 32768, 
        is_save: bool = True
    ) -> Dict[str, Any]:
        """Analyze stock data"""
        self.logger.info(f"Starting stock analysis: {COMPANY}")
        
        prompt = f"Here is the K-line chart for {COMPANY} stock over the past year. Please help me analyze it and suggest appropriate options strategies, both aggressive and conservative." + str(stock_data) + str(existing_analysis)
        # Build message
        messages = [{
            "role": "assistant", 
            "content": prompt
        }]
        
        # Count input tokens
        input_tokens = count_tokens(prompt, self.encoding)
        assert input_tokens < 32768, "Input token exceed normal length 32K"
        self.logger.info(f"Input token count: {input_tokens}")
        
        # Call API
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            max_tokens=max_tokens
        )
        
        # Collect output content
        output_content = ""
        for chunk in completion:
            if getattr(chunk, "choices", None) and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                print(content, end="")
                if content:
                    output_content += content
        
        # Count output tokens
        output_tokens = count_tokens(output_content, self.encoding)
        
        # Return result
        result = {
            "company": COMPANY,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_chars": sum(len(msg.get('content', '')) for msg in messages),
            "output_chars": len(output_content),
            "content": output_content,
            "token_ratio": input_tokens/output_tokens if output_tokens > 0 else 0
        }
        
        self.logger.info(f"Analysis completed - Input: {input_tokens}, Output: {output_tokens}, Total: {result['total_tokens']}")

        if is_save:
            self.save_analysis(result, output_path=f"{self.save_dir}/{COMPANY}_analysis.md")
        return result
    
    def save_analysis(self, analysis_result: Dict[str, Any], output_path: str):
        """Save analysis results to file"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {analysis_result['symbol']} Analysis\n\n")
            f.write(f"_Start time: {datetime.now().isoformat(timespec='seconds')}_\n\n")
            f.write(f"**Token statistics:**\n")
            f.write(f"- Input tokens: {analysis_result['input_tokens']}\n")
            f.write(f"- Output tokens: {analysis_result['output_tokens']}\n")
            f.write(f"- Total tokens: {analysis_result['total_tokens']}\n")
            f.write(f"- Input/output ratio: {analysis_result['token_ratio']:.2f}\n\n")
            f.write("---\n\n")
            f.write(analysis_result['content'])
        
        self.logger.info(f"Analysis results saved to: {output_path}")


def main():
    """Main function example"""
    # API configuration - Get from environment variables
    bl_api = os.getenv('DASHSCOPE_API_KEY', 'YOUR_DASHSCOPE_API_KEY')
    # dpsk_api = os.getenv('DEEPSEEK_API_KEY', 'YOUR_DEEPSEEK_API_KEY')

    # Initialize AI search
    ai_search = AISearch(
        api_key=bl_api,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name="qwen-plus"
        # api_key=dpsk_api,
        # base_url="https://api.deepseek.com/v1",
        # model_name="deepseek-reasoner"
    )

    stock_data = load_csv_data(f"../data/{COMPANY}_4M_1day.csv")
    # analysis_data = read_markdown_file(f"")
    ai_search.analyze_stock(stock_data=stock_data)

if __name__ == "__main__":
    main()