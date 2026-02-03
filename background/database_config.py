"""
数据库配置文件
请根据您的实际MySQL配置修改这里的参数
"""

# MySQL 数据库配置
DB_CONFIG = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'community_db',           # 您创建的数据库名
    'USER': 'root',                   # MySQL 用户名
    'PASSWORD': '123456', # 请修改为您的 MySQL 密码
    'HOST': 'localhost',              # 数据库主机地址
    'PORT': '3306',                   # MySQL 端口号
    'OPTIONS': {
        'charset': 'utf8mb4',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    },
}

# 如果您想使用不同的数据库用户，可以这样配置：
# DB_CONFIG = {
#     'ENGINE': 'django.db.backends.mysql',
#     'NAME': 'community_db',
#     'USER': 'your_db_user',          # 您的MySQL用户名
#     'PASSWORD': 'your_password',     # 您的MySQL密码
#     'HOST': 'localhost',
#     'PORT': '3306',
#     'OPTIONS': {
#         'charset': 'utf8mb4',
#         'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#     },
# }