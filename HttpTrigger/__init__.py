import logging
import azure.functions as func
import pymssql
import os
import re
import time


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger received a request.")

    try:
        req_body = req.get_json()
    except:
        return func.HttpResponse("Invalid JSON", status_code=400)

    # Expecting: { "task": "do something" }
    task_text = req_body.get("task")
    if not task_text:
        return func.HttpResponse("Missing 'task'", status_code=400)

    conn_str = os.environ["SqlConnectionString"]
    
    # Parse connection string for pymssql
    server_match = re.search(r'Server=tcp:([^,]+),(\d+)', conn_str)
    db_match = re.search(r'Initial Catalog=([^;]+)', conn_str)
    user_match = re.search(r'User ID=([^;]+)', conn_str)
    pwd_match = re.search(r'Password=([^;]+)', conn_str)
    
    if not (server_match and db_match and user_match and pwd_match):
        return func.HttpResponse("Invalid connection string format", status_code=500)
    
    server = server_match.group(1)
    port = int(server_match.group(2))
    database = db_match.group(1)
    user = user_match.group(1)
    password = pwd_match.group(1)
    
    # Connect using pymssql with retry mechanism for high load scenarios
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            conn = pymssql.connect(
                server=server, 
                port=port, 
                user=user, 
                password=password, 
                database=database,
                timeout=10,  # Connection timeout in seconds
                login_timeout=10  # Login timeout in seconds
            )
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dbo.Tasks (Payload) VALUES (%s)", task_text)
            conn.commit()
            conn.close()
            
            logging.info(f"Task inserted successfully (attempt {attempt + 1})")
            return func.HttpResponse(f"Task added: {task_text}")
            
        except Exception as e:
            logging.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                logging.error(f"All {max_retries} connection attempts failed")
                return func.HttpResponse(f"Database connection failed after {max_retries} attempts: {str(e)}", status_code=503)
