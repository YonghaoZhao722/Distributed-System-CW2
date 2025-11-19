# Distributed System Coursework 2

Azure Functions project with SQL Server integration for task processing.

## Project Structure

```
dist_sys_sql/
├── HttpTrigger/              # HTTP trigger function
│   ├── __init__.py          # HTTP endpoint handler
│   └── function.json        # HTTP trigger configuration
├── SqlTriggerBinding/        # SQL trigger function
│   ├── __init__.py          # SQL trigger handler
│   ├── function.json        # SQL trigger configuration
│   └── readme.md            # SQL trigger documentation
├── test_results/            # Test output files
├── test_workflow.py         # Test script
├── visualize_results.py     # Visualization script
├── requirements.txt         # Python dependencies
├── host.json                # Azure Functions host configuration
└── local.settings.json      # Local environment settings (not committed)
```

## Triggers

### 1. HTTP Trigger (`HttpTrigger`)
- **Type**: HTTP Trigger
- **Methods**: GET, POST
- **Function**: Receives HTTP requests with JSON payload containing a `task` field
- **Action**: Inserts the task into SQL Server database (`dbo.Tasks` table)
- **Features**: 
  - Retry mechanism for high load scenarios
  - Connection timeout handling
  - Error logging

### 2. SQL Trigger (`SqlTriggerBinding`)
- **Type**: SQL Trigger Binding
- **Table**: `dbo.Tasks`
- **Function**: Automatically fires when changes occur in the Tasks table
- **Action**: Logs the changes (Id, Payload, Processed status)
- **Use Case**: Processes tasks inserted by the HTTP trigger

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure connection string in `local.settings.json`:
```json
{
  "Values": {
    "SqlConnectionString": "Server=tcp:<server>,<port>;Initial Catalog=<database>;User ID=<user>;Password=<password>;"
  }
}
```

## Running Locally

1. Start Azure Functions runtime:
```bash
func start
```

2. Test HTTP trigger:
```bash
curl -X POST http://localhost:7071/api/HttpTrigger \
  -H "Content-Type: application/json" \
  -d '{"task": "test task"}'
```

3. Run test workflow:
```bash
python test_workflow.py
```

4. Visualize results:
```bash
python visualize_results.py
```