from pathlib import Path
import json
import os
import sys

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

        # Get the business card
        image_file = script_dir / 'biz-card-1.png'
        if len(sys.argv) > 1:
            image_file = Path(sys.argv[1])
            if not image_file.is_absolute():
                image_file = script_dir / image_file

        # Get config settings
        load_dotenv(env_path)
        ai_svc_endpoint = require_setting('CONTENT_UNDERSTANDING_ENDPOINT')
        analyzer = require_setting('ANALYZER_NAME')

        # Analyze the business card
        analyze_card(image_file, analyzer, ai_svc_endpoint)

        print("\n")

    except Exception as ex:
        print(ex)



def analyze_card(image_file, analyzer, endpoint):
    # Use Content Understanding to analyze the image
    print(f"Analyzing {image_file.name}")

    # Create the Content Understanding client
    client = ContentUnderstandingClient(
        endpoint=endpoint,
        credential=get_credential()
    )

    # Read the image data
    image_data = image_file.read_bytes()

    # Submit the image for analysis
    print("Submitting request...")
    poller = client.begin_analyze_binary(
        analyzer_id=analyzer,
        binary_input=image_data,
        content_type="image/png"
    )

    # Wait for the analysis to complete
    result = poller.result()
    print("Analysis succeeded:\n")

    # Save JSON results to a file
    output_file = image_file.parent / "results.json"
    with output_file.open("w", encoding="utf-8") as json_file:
        json.dump(dict(result), json_file, indent=4, default=str)
        print(f"Response saved in {output_file}\n")

    # Iterate through the contents and extract fields
    for content in result.contents:
        if hasattr(content, 'fields') and content.fields:
            for field_name, field_data in content.fields.items():
                value = field_data.value if hasattr(field_data, 'value') else None
                print(f"{field_name}: {value}")





if __name__ == "__main__":
    main()        
