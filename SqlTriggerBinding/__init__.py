import logging
import json

def main(changes: str):
    logging.info("SQL Trigger fired.")
    
    try:
        changes_list = json.loads(changes)
        if changes_list:
            for item in changes_list:
                logging.info(f"SQL Trigger fired: Id={item.get('Id')}, Payload={item.get('Payload')}, Processed={item.get('Processed')}")
        else:
            logging.info("SQL Trigger fired but no changes detected.")
    except Exception as e:
        logging.error(f"Error parsing SQL trigger input: {e}")
        logging.error(f"Raw content: {changes}")
