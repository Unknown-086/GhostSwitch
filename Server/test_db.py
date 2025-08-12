import mysql.connector

conn = mysql.connector.connect(
    host="your-rds-endpoint.rds.amazonaws.com",
    user="admin",
    password="your-password",
    database="ghostswitch"
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES;")
print(cursor.fetchall())

cursor.close()
conn.close()
