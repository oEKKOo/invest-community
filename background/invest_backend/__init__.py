# 使用 PyMySQL 替代 mysqlclient（纯 Python 实现，无需编译）
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
