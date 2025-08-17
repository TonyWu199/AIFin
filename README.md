# AIFin - 股票数据分析项目

本项目用于获取、分析和存储股票数据，并提供API接口供外部访问。

## 功能特性

1. 从Interactive Brokers获取实时股票数据
2. 将股票数据存储到MySQL数据库
3. 提供RESTful API接口访问股票数据
4. 使用AI分析股票数据并生成交易策略

## 项目结构

```
AIFin/
├── data/                  # 股票数据文件
|-- log/                   # 日志文件
├── src/                   # 源代码
│   ├── __init__.py        # 项目根模块
│   ├── main.py            # 项目主入口点
│   ├── utils.py           # 工具函数
│   ├── db/                # 数据库相关模块
│   │   ├── __init__.py    # 数据库模块包
│   │   ├── database.py    # 数据库操作类
│   │   ├── api.py         # API服务模块
│   │   └── init_db.py     # 数据库初始化脚本
│   ├── ib/                # IB连接相关模块
│   │   ├── __init__.py    # IB连接模块包
│   │   └── ib_connect.py  # IB连接模块
│   └── log/               # 日志文件
│       ├── api.log        # API服务日志
│       └── ib_connect.log # IB连接日志
├── requirements.txt       # 项目依赖
└── README.md             # 项目说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 安装和配置MySQL

### 在Ubuntu/Debian上安装MySQL

```bash
# 更新包索引
sudo apt update

# 安装MySQL服务器
sudo apt install mysql-server

# 启动MySQL服务
sudo systemctl start mysql

# 设置开机自启
sudo systemctl enable mysql

# 安全配置（可选但推荐）
sudo mysql_secure_installation
```

### 在CentOS/RHEL上安装MySQL

```bash
# 下载MySQL仓库包
sudo wget https://dev.mysql.com/get/mysql80-community-release-el8-1.noarch.rpm

# 安装仓库包
sudo rpm -ivh mysql80-community-release-el8-1.noarch.rpm

# 安装MySQL服务器
sudo yum install mysql-server

# 启动MySQL服务
sudo systemctl start mysqld

# 设置开机自启
sudo systemctl enable mysqld
```

### 配置MySQL

1. 获取临时root密码（CentOS/RHEL）：
```bash
sudo grep 'temporary password' /var/log/mysqld.log
```

2. 登录MySQL并修改密码：
```bash
mysql -u root -p
```

```sql
-- 修改root密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_new_password';

-- 创建数据库
CREATE DATABASE stock_db;

-- 创建专用用户（可选但推荐）
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'stock_password';

-- 授权用户访问stock_db数据库
GRANT ALL PRIVILEGES ON stock_db.* TO 'stock_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

## 数据库配置

项目使用MySQL数据库存储股票数据。需要设置以下环境变量：

- `DB_HOST`: 数据库主机地址 (默认: localhost)
- `DB_PORT`: 数据库端口 (默认: 3306)
- `DB_NAME`: 数据库名称 (默认: stock_db)
- `DB_USER`: 数据库用户名 (默认: root)
- `DB_PASSWORD`: 数据库密码 (默认: 空)

示例配置：
```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=stock_db
export DB_USER=stock_user
export DB_PASSWORD=stock_password
```

## 初始化数据库

运行以下命令初始化数据库并导入CSV数据：

```bash
cd src
python main.py init-db
```

或者直接运行：
```bash
cd src/db
python init_db.py
```

## 启动API服务

```bash
cd src
python main.py api
```

或者直接运行：
```bash
cd src/db
python api.py
```

API服务默认在 `http://0.0.0.0:5000` 上运行。

## 从IB获取实时数据

```bash
cd src
python main.py ib-connect
```

或者直接运行：
```bash
cd src/ib
python ib_connect.py
```

## API接口说明

### 获取股票数据

```
GET /api/stock/<company>
```

参数:
- `company`: 股票代码 (如: BABA)
- `limit` (可选): 限制返回记录数量

示例:
```
GET /api/stock/BABA
GET /api/stock/BABA?limit=10
```

### 获取最新股票数据

```
GET /api/stock/<company>/latest
```

示例:
```
GET /api/stock/BABA/latest
```

### 健康检查

```
GET /api/health
```

## 环境变量

可以设置以下环境变量来配置API服务：

- `API_HOST`: API服务主机地址 (默认: 0.0.0.0)
- `API_PORT`: API服务端口 (默认: 5000)
- `API_DEBUG`: 是否启用调试模式 (默认: False)
- `COMPANY`: 股票代码 (默认: BABA)

## 通过URL访问API服务

API服务运行在5000端口，所以您应该使用以下URL访问：

1. 获取股票数据：
   ```
   http://<server-ip>:5000/api/stock/BABA
   ```

2. 获取最新的10条股票数据：
   ```
   http://<server-ip>:5000/api/stock/BABA?limit=10
   ```

3. 获取最新的股票数据：
   ```
   http://<server-ip>:5000/api/stock/BABA/latest
   ```

4. 健康检查：
   ```
   http://<server-ip>:5000/api/health
   ```

注意：3306是MySQL数据库端口，5000是API服务端口，不要混淆。