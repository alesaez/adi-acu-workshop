# Lab 03 - Create a Knowledge Mining Solution

Source exercise: https://microsoftlearning.github.io/mslearn-ai-information-extraction/Instructions/Exercises/04-knowledge-mining.html

Source lab files: https://github.com/MicrosoftLearning/mslearn-ai-information-extraction/tree/main/Labfiles/knowledge

In this lab, you use Azure AI Search to create a knowledge mining solution for travel brochure documents. The indexing process uses AI enrichments to extract key phrases, people, locations, and image text, and then you query the generated search index from the Azure portal and from a Python client application.

This workshop structure is slightly different from the source repo:

- The source `documents.zip` file is included in `workshop/lab-03-knowledge-mining/`.
- The extracted documents are placed in `workshop/lab-03-knowledge-mining/documents/` for local upload to Azure Storage.
- The optional storage setup script and notebook are in `workshop/lab-03-knowledge-mining/`.
- The Python search client is in `workshop/lab-03-knowledge-mining/search-app.py`.
- The only Python requirements file is `workshop/requirements.txt`.
- The only environment file is `workshop/.env`.
- The `.env` file should be copied from `workshop/.env.sample` because `.env` is intentionally gitignored.

This lab is mainly a portal follow-along experience. You will create Azure AI Search and Azure Storage resources, upload the included brochure documents, use the **Import data** wizard to create an indexer with AI enrichments, test the index in Search explorer, and then run the optional local Python search app. You can create the storage account and upload documents manually in the Azure portal, or use the optional Python helper for that storage setup step.

## Estimated Time

Plan for **75-90 minutes** to complete this lab. The estimate includes resource creation, document extraction and upload, indexer configuration, portal query testing, and the optional Python search client. If you skip the optional Python sections, plan for about **60-75 minutes**.

## Learning Objectives

After completing this lab, you will be able to:

- Create an Azure AI Search resource for a knowledge mining solution.
- Create an Azure Storage account and upload PDF documents to a private blob container manually or with the optional Python helper.
- Use the Azure AI Search **Import data** wizard to create a data source, index, skillset, and indexer.
- Apply AI enrichments for key phrases, entities, and image text.
- Query enriched content in Search explorer.
- Configure and run a Python client application that searches the generated index.

## Prerequisites

Before you start, complete the workshop setup and make sure you have:

- An Azure subscription.
- Azure CLI installed and signed in.
- Permission to create or use Azure AI Search and Azure Storage resources.
- Python 3.10 through 3.13 if you plan to run the optional Python sections.
- The dependencies from `workshop/requirements.txt` installed if you plan to run the optional Python sections.

Create and activate a Python virtual environment from the repository root only if you plan to run the optional Python sections:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r workshop/requirements.txt
```

If you are using Bash, use these equivalent commands:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r workshop/requirements.txt
```

Create your local environment file from the sample if you have not already done so:

```powershell
Copy-Item workshop/.env.sample workshop/.env
```

If you are using Bash, use this equivalent command:

```bash
cp workshop/.env.sample workshop/.env
```

Sign in to Azure:

```powershell
az login
```

## 1. Prepare the Lab Folder

From the repository root, confirm the lab has this structure:

```text
workshop/
	lab-00-setup/
		README.md
	.env.sample
	.env
	requirements.txt
	lab-03-knowledge-mining/
		README.md
		documents.zip
		storage-setup.ipynb
		storage-setup.py
		search-app.py
```

The `documents.zip` file is included in this repo for Lab 03. You do not need to download it from the source exercise.

## 2. Extract the Included Documents

The source exercise uses travel brochure PDFs. In this workshop, those files are already packaged in `workshop/lab-03-knowledge-mining/documents.zip`.

From the repository root, extract the zip file locally:

```powershell
$labPath = "workshop/lab-03-knowledge-mining"
$zipPath = "$labPath/documents.zip"
$documentsPath = "$labPath/documents"

Expand-Archive -Path $zipPath -DestinationPath $documentsPath -Force
```

If you are using Bash, use these equivalent commands:

```bash
lab_path="workshop/lab-03-knowledge-mining"
rm -rf "$lab_path/documents"
unzip "$lab_path/documents.zip" -d "$lab_path/documents"
```

After extraction, confirm that the folder contains files such as `Dubai Brochure.pdf`, `Las Vegas Brochure.pdf`, `London Brochure.pdf`, `Margies Travel Company Info.pdf`, `New York Brochure.pdf`, and `San Francisco Brochure.pdf`.

<details>
<summary>Checkpoint: extracted document location</summary>

Your lab folder should now include these local extracted files:

```text
workshop/
	lab-03-knowledge-mining/
		documents.zip
		documents/
			Dubai Brochure.pdf
			Las Vegas Brochure.pdf
			London Brochure.pdf
			Margies Travel Company Info.pdf
			New York Brochure.pdf
			San Francisco Brochure.pdf
```

The extracted `documents/` folder is a local working folder and should not be committed.

</details>

## 3. Create Azure Resources

The knowledge mining solution requires Azure AI Search and Azure Storage resources. Create both resources in the same resource group and region.

### Create an Azure AI Search Resource

1. Open the [Azure portal](https://portal.azure.com/) at `https://portal.azure.com` and sign in with your Azure account.
2. Select **+ Create a resource**, search for `Azure AI Search`, and create a new **Azure AI Search** resource with the following settings:

| Setting | Value |
| --- | --- |
| Subscription | Your Azure subscription |
| Resource group | Create or select a resource group |
| Service name | Enter a valid globally unique search service name |
| Location | Any available location |
| Pricing tier | Free |

3. Select **Review + create**, then **Create**.
4. Wait for deployment to complete, then open the deployed Azure AI Search resource.
5. Review the **Overview** page. You will return here to import data and test queries.

### Create a Storage Account

1. Return to the Azure portal home page.
2. Select **+ Create a resource**, search for `Storage account`, and create a new **Storage account** resource with the following settings:

| Setting | Value |
| --- | --- |
| Subscription | Your Azure subscription |
| Resource group | The same resource group as your Azure AI Search resource |
| Storage account name | Enter a globally unique storage account name |
| Region | The same region as your Azure AI Search resource |
| Primary service | Azure Blob Storage or Azure Data Lake Storage Gen2 |
| Performance | Standard |
| Redundancy | Locally-redundant storage (LRS) |

3. Select **Review + create**, then **Create**.
4. Wait for deployment to complete, then open the deployed storage account.

### Optional: Create Storage and Upload Documents with Python

If you prefer not to create the storage account and upload files manually in the portal, you can use the Lab 03 storage helper. It creates or reuses a storage account, creates a private `documents` container, grants your current Azure user `Storage Blob Data Contributor`, extracts `documents.zip` if needed, uploads the PDF files, and prints the storage account and container URL.

Open `workshop/.env` and update these storage settings:

```env
STORAGE_SUBSCRIPTION_ID=
STORAGE_RESOURCE_GROUP=<your-resource-group-name>
STORAGE_LOCATION=eastus2
STORAGE_ACCOUNT_NAME=
```

Leave `STORAGE_SUBSCRIPTION_ID` empty to infer the subscription from your current Azure credential when exactly one subscription is available. If your account can access multiple subscriptions, set `STORAGE_SUBSCRIPTION_ID` explicitly. Leave `STORAGE_ACCOUNT_NAME` empty to let the helper generate a valid storage account name and save it back to `workshop/.env`.

From the repository root, run:

```powershell
python workshop/lab-03-knowledge-mining/storage-setup.py
```

If you prefer to run the setup step by step, open `workshop/lab-03-knowledge-mining/storage-setup.ipynb` and run the cells from top to bottom.

After this optional path completes, skip the manual upload steps in the next section and use the printed storage account and `documents` container when you create the Azure AI Search indexer.

<details>
<summary>Solution: what the storage helper creates</summary>

The helper creates or reuses these resources and local files:

```text
Azure Storage account: STORAGE_ACCOUNT_NAME or generated aikm######## name
Blob container: documents
Uploaded blobs:
	Dubai Brochure.pdf
	Las Vegas Brochure.pdf
	London Brochure.pdf
	Margies Travel Company Info.pdf
	New York Brochure.pdf
	San Francisco Brochure.pdf
```

The helper uses your current Azure credentials through `DefaultAzureCredential`. Your Azure account must have permission to create storage accounts and assign `Storage Blob Data Contributor` on the storage account.

</details>

## 4. Upload Documents to Azure Storage

If you used `storage-setup.py` or `storage-setup.ipynb`, the documents are already uploaded to the `documents` container. Continue to the next section and select that storage account and container in the Azure AI Search **Import data** wizard.

If you are following the portal-only path, upload the documents manually:

1. In the Azure portal, open your storage account.
2. Select **Storage browser** in the navigation pane.
3. Select **Blob containers**.
4. Select **+ Container** and create a new container with these settings:

| Setting | Value |
| --- | --- |
| Name | `documents` |
| Anonymous access level | Private, no anonymous access |

5. Open the `documents` container.
6. Select **Upload**.
7. Upload the PDF files from `workshop/lab-03-knowledge-mining/documents/`.

<details>
<summary>Checkpoint: uploaded documents</summary>

Your Azure Storage container should contain the extracted travel brochure PDFs. These files are the input data for the Azure AI Search indexer.

</details>

## 5. Create and Run an Indexer

In this section, you use the Azure AI Search **Import data** wizard to create the search data source, index, skillset, and indexer.

1. In the Azure portal, open your Azure AI Search resource.
2. On the **Overview** page, select **Import data**.
3. On **Connect to your data**, select **Azure Blob Storage** as the data source.
4. Select **keyword search**.
5. Configure the data store details:

| Setting | Value |
| --- | --- |
| Storage account | Your Lab 03 storage account |
| Blob container | `documents` |

6. Leave the remaining options at their defaults, then select **Next**.
7. On **Apply AI enrichments**, select **Extract phrases**.
8. Select **Extract entities**, open the settings, choose only **Persons** and **Locations**, then save.
9. Select **Extract text from images**, open the settings, choose **Generate tags** and **Categorize content**, then save.
10. If prompted for an enrichment resource, choose the free Foundry Tools resource option, then select **Next**.

> NOTE: The free Azure AI Services enrichment option for Azure AI Search can index a maximum of 20 documents. That is enough for this workshop. In production, create and attach a dedicated Azure AI Services resource.

11. On **Preview mappings**, review the generated field mappings. The fields are already mapped based on the enrichment options you selected. Confirm the following fields are configured as shown below. To update a field, select it, then select **Configure field**. Keep all other fields at their default settings:

| Target index field name | Retrievable | Filterable | Sortable | Facetable | Searchable |
| --- | --- | --- | --- | --- | --- |
| `metadata_storage_size` | Yes | Yes | Yes |  |  |
| `metadata_storage_last_modified` | Yes | Yes | Yes |  |  |
| `title` | Yes | Yes | Yes |  | Yes |
| `locations` | Yes | Yes |  |  | Yes |
| `persons` | Yes | Yes |  |  | Yes |
| `keyPhrases` | Yes | Yes |  |  | Yes |

12. Select **Next**.
13. On **Advanced settings**, ensure **Enable semantic ranker** is selected if available.
14. Set **Schedule** to **Once** if it is not already selected.
15. Select **Next**.
16. On **Review and create**, set **Objects name prefix** to `margies-index`.
17. Select **Create**.
18. In the left navigation pane, under **Search management**, select **Indexers**.
19. Wait for `margies-index-indexer` to show **Success**. Select **Refresh** until the status updates.

<details>
<summary>Checkpoint: generated Azure AI Search objects</summary>

After the wizard completes, your Azure AI Search resource should include generated objects similar to these:

- Index: `margies-index`
- Indexer: `margies-index-indexer`
- Data source: generated from the `documents` blob container
- Skillset: generated from the selected AI enrichments

The exact generated names can vary, but the Python app later expects the index name to be `margies-index`.

</details>

## 6. Search the Index in the Azure Portal

1. Open your Azure AI Search resource.
2. On the **Overview** page, select **Search explorer**.
3. In the query box, enter `*` and select **Search**.
4. Review the JSON results. Notice document metadata and enriched fields such as `locations`, `persons`, and `keyPhrases`.
5. Switch to **JSON view** if needed.
6. Run this query to return all documents and count the results:

```json
{
	"search": "*",
	"count": true
}
```

7. Run this query to return only titles and extracted locations:

```json
{
	"search": "*",
	"count": true,
	"select": "title,locations"
}
```

8. Run this query to search for `New York` and return key phrases:

```json
{
	"search": "New York",
	"count": true,
	"select": "title,keyPhrases"
}
```

9. Run this query to filter the `New York` results by document size:

```json
{
	"search": "New York",
	"count": true,
	"select": "title,keyPhrases",
	"filter": "metadata_storage_size lt 380000"
}
```

<details>
<summary>Checkpoint: what to notice in Search explorer</summary>

The index should return brochure documents and enriched fields generated by the indexer. The `locations`, `persons`, and `keyPhrases` fields come from AI skills, not from manually entered document metadata.

</details>

## 7. Configure the Python Search Client

Now that the index is ready, configure the local Python app to query it with the Azure AI Search SDK.

### Get the Endpoint and Query Key

1. In the Azure portal, open your Azure AI Search resource.
2. On the **Overview** page, copy the **Url** value. It should look like `https://<your-search-service>.search.windows.net`.
3. In the navigation pane, expand **Settings** and select **Keys**.
4. Copy the default query key.

> NOTE: Azure AI Search creates one default query key. In the Azure portal, this default query key can appear with a blank name. That is expected.

### Update the Shared Environment File

Open `workshop/.env` and update these values:

```env
SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
QUERY_KEY=<your-query-key>
INDEX_NAME=margies-index
```

<details>
<summary>Solution: shared environment file format</summary>

Your `workshop/.env` should include the Lab 03 search settings below:

```env
SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
QUERY_KEY=<your-query-key>
INDEX_NAME=margies-index
```

Use the query key from your Azure AI Search resource. Do not use an admin key unless you are intentionally testing administrative operations.

</details>

## 8. Run the Python Search App

From the repository root, run:

```powershell
python workshop/lab-03-knowledge-mining/search-app.py
```

When prompted, enter a search query such as:

```text
London
```

Try another query:

```text
flights
```

When you are finished, enter:

```text
quit
```

The app searches the `margies-index` index and returns these fields:

- `title`
- `locations`
- `persons`
- `keyPhrases`

<details>
<summary>Solution: completed search client application</summary>

```python
from dotenv import load_dotenv
import os
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


def main():

		# Clear the console
		os.system('cls' if os.name=='nt' else 'clear')

		try:

				# Get config settings
				env_path = Path(__file__).resolve().parent.parent / ".env"
				load_dotenv(env_path)
				search_endpoint = os.getenv('SEARCH_ENDPOINT')
				query_key = os.getenv('QUERY_KEY')
				index = os.getenv('INDEX_NAME')

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
						os.system('cls' if os.name=='nt' else 'clear')
            
						# Search the index
						found_documents = search_client.search(
								search_text=query_text,
								select=["title", "locations", "persons", "keyPhrases"],
								include_total_count=True
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
```

</details>

<details>
<summary>Checkpoint: successful Python search output</summary>

The exact results depend on the index content, but successful output should look similar to this:

```text
Enter a query (or type 'quit' to exit): London

Search returned 1 documents:

Document: London Brochure.pdf
 - Locations:
	 - London
 - People:
 - Key phrases:
	 - ...
```

</details>

## Troubleshooting

If the indexer fails, open the `margies-index-indexer` details page and review the error messages. Common causes include an empty blob container, missing storage permissions, or selecting the wrong container during import.

If the **Import data** wizard cannot connect to storage, confirm that the storage account and Azure AI Search resource are in the same resource group and region for this lab, then retry.

If Search explorer returns no documents, wait for the indexer to complete successfully and refresh the indexer status.

If `ModuleNotFoundError: No module named 'azure.search'` appears in the optional SDK section, activate `.venv` and reinstall the shared requirements:

```powershell
python -m pip install -r workshop/requirements.txt
```

If the Python app returns authentication errors, confirm that `QUERY_KEY` in `workshop/.env` is a query key from your Azure AI Search resource.

If the Python app returns index-not-found errors, confirm that `INDEX_NAME=margies-index` matches the index created by the **Import data** wizard.

## Note About Knowledge Store

Knowledge store steps are excluded from this version of the source exercise. The current Azure portal **Import data** keyword search flow for this scenario creates a search index, indexer, data source, and skillset, but it does not create a knowledge store.

## Clean Up

When you are finished, remove any Azure resources you created only for this lab to avoid ongoing charges. If you used a shared workshop resource group, delete only the resources that are no longer needed.
