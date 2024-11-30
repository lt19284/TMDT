import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="tmdt"
)
if connection.is_connected():
    print("Nice! connecting...")
else:
    print("Error: ")
connection.close()