from dotenv import load_dotenv
import os
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


def main():
    # Clear the console
    os.system("cls" if os.name == "nt" else "clear")

    try:
        # Get config settings
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_path)
        search_endpoint = os.getenv("SEARCH_ENDPOINT")
        query_key = os.getenv("QUERY_KEY")
        index = os.getenv("INDEX_NAME")

        # Get a search client
        search_client = SearchClient(search_endpoint, index, AzureKeyCredential(query_key))

        # Loop until the user types 'quit'
        while True:
            # Get query text
            query_text = input("Enter a query (or type 'quit' to exit): ")
            if query_text.lower() == "quit":
                break
            if len(query_text) == 0:
                print("Please enter a query.")
                continue

            # Clear the console
            os.system("cls" if os.name == "nt" else "clear")

            # Search the index
            found_documents = search_client.search(
                search_text=query_text,
                select=["title", "locations", "persons", "keyPhrases"],
                include_total_count=True,
            )

            # Parse the results
            print(f"\nSearch returned {found_documents.get_count()} documents:")
            for document in found_documents:
                print(f"\nDocument: {document.get('title', '<untitled>')}")
                print(" - Locations:")
                for location in document.get("locations", []) or []:
                    print(f"   - {location}")
                print(" - People:")
                for person in document.get("persons", []) or []:
                    print(f"   - {person}")
                print(" - Key phrases:")
                for phrase in document.get("keyPhrases", []) or []:
                    print(f"   - {phrase}")

    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    main()
