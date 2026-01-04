import os
import app.api
print(f"File: {app.api.__file__}")
print(f"DB_URL: {os.getenv('DATABASE_URL')}")
