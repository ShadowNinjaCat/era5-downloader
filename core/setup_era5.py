import os
from pathlib import Path
from dotenv import load_dotenv
from utils.logger import Logger

def setup_cds_credentials() -> bool:
    load_dotenv()
    cdsapirc_path = Path.home() / ".cdsapirc"
    api_key = os.getenv("CDS_API_KEY")
    cds_url = os.getenv("CDS_API_URL")

    if not api_key:
        Logger.error("CDS_API_KEY not found")
        return False

    cdsapirc_content = f"url: {cds_url}\nkey: {api_key}\n"

    try:
        with open(cdsapirc_path, 'w') as f:
            f.write(cdsapirc_content)
        Logger.info(f"Credentials configured correctly!")
        return True
    except PermissionError as e:
        Logger.error(f"Error: Permission denied. Unable to write to file: {cdsapirc_path}.")
        return False

if __name__ == "__main__":
    setup_cds_credentials()
