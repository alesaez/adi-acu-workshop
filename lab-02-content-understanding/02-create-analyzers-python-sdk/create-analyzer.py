from pathlib import Path
import json
import os

from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


def optional_setting(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    return "" if not value or value.startswith("<") else value


def require_setting(name: str) -> str:
    value = optional_setting(name)
    if not value:
        raise ValueError(f"Set {name} in workshop/.env")
    return value


def get_credential():
    key = optional_setting("CONTENT_UNDERSTANDING_KEY")
    return AzureKeyCredential(key) if key else DefaultAzureCredential()


def main():

    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')

    try:
        script_dir = Path(__file__).resolve().parent
        env_path = script_dir.parents[1] / ".env"
        schema_path = script_dir / "biz-card.json"

        # Get the business card schema
        with schema_path.open("r", encoding="utf-8") as file:
            schema_json = json.load(file)

        # Get config settings
        load_dotenv(env_path)
        ai_svc_endpoint = require_setting('CONTENT_UNDERSTANDING_ENDPOINT')
        analyzer = require_setting('ANALYZER_NAME')

        # Create the analyzer
        create_analyzer(schema_json, analyzer, ai_svc_endpoint)

        print("\n")

    except Exception as ex:
        print(ex)



def create_analyzer(schema, analyzer, endpoint):
    
    # Create a Content Understanding analyzer
    print(f"Creating {analyzer}")

    # Create the Content Understanding client
    client = ContentUnderstandingClient(
        endpoint=endpoint,
        credential=get_credential()
    )

    # Create the analyzer using the SDK (long-running operation)
    poller = client.begin_create_analyzer(
        analyzer_id=analyzer,
        resource=schema,
        allow_replace=True
    )

    # Wait for the operation to complete
    result = poller.result()
    print(f"Analyzer '{analyzer}' created successfully.")
    print(f"Status: {result['status'] if isinstance(result, dict) else 'Succeeded'}")



if __name__ == "__main__":
    main()        
