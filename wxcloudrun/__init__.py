# Original code tries to import pymysql but it's no longer in requirements
# Comment out or modify the pymysql import
# import pymysql  

# If we need database connectivity, we're now using mysqlclient instead
# If you need to maintain compatibility with code expecting PyMySQL, you can add:
try:
    import pymysql
except ImportError:
    # Using mysqlclient instead
    pass

pymysql.install_as_MySQLdb()
