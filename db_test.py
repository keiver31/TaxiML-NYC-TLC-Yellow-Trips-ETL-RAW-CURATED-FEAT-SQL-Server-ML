import pyodbc

server = r"DESKTOP-5VDFT83\SQLEXPRESS"
database = "TaxiML"
username = "user_daemon"
password = "userdaemon"  # pon tu clave

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=yes;"
)

cur = conn.cursor()
cur.execute("SELECT 1;")
print(cur.fetchone())
conn.close()
