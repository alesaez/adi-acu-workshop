# Lab 01 - Extract Data with Azure AI Document Intelligence

Source lab files: https://github.com/MicrosoftLearning/mslearn-ai-information-extraction/tree/main/Labfiles/03-document-intelligence

In this lab, you use Azure AI Document Intelligence to extract structured data from documents. The flow is based on the Microsoft Learn exercise, but this workshop uses a shared setup folder:

- The only Python requirements file is `workshop/requirements.txt`.
- The only environment file is `workshop/.env`.
- The `.env` file should be copied from `workshop/.env.sample` because `.env` is intentionally gitignored.
- The prebuilt invoice script and step-by-step notebook are in `workshop/lab-01-document-intelligence/prebuilt/`.
- The custom model script, notebook, and storage setup helper are in `workshop/lab-01-document-intelligence/custom/`.
- Training documents for the custom model are in `workshop/lab-01-document-intelligence/custom/sample-forms/`.
- A sample invoice is available in `workshop/lab-01-document-intelligence/prebuilt/sample-invoice/sample-invoice.pdf`.

You will first call the prebuilt invoice model, then create and test a custom extraction model.

## Estimated Time

Plan for **75-90 minutes** to complete this lab. The estimate includes resource setup, environment configuration, prebuilt invoice analysis, custom project creation, model training, and custom model testing. If your Azure resources and local Python environment are already ready, the lab may take closer to 60 minutes.

## Learning Objectives

After completing this lab, you will be able to:

- Create or reuse an Azure AI Document Intelligence resource.
- Use the Python SDK to call a prebuilt Document Intelligence model from a script or notebook.
- Train a custom extraction model in Document Intelligence Studio.
- Test the custom model from a Python script with Microsoft Entra authentication.

## Prerequisites

Before you start, complete the workshop setup and make sure you have:

- An Azure subscription.
- Python 3.10 through 3.13. Python 3.14 is not recommended for this workshop yet because some Azure SDK dependencies may not provide prebuilt wheels for every platform.
- Azure CLI installed and signed in.
- Visual Studio Code with the [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) if you want to run the notebook version.
- The dependencies from `workshop/requirements.txt` installed.
- Permission to create or use an Azure AI Document Intelligence resource.

Create and activate a Python virtual environment from the repository root. If you have multiple Python versions installed on Windows, use the Python Launcher to choose a supported version explicitly:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If Python 3.13 is not installed, replace `-3.13` with another installed supported version, such as `-3.12`, `-3.11`, or `-3.10`.

If you are using Bash, use these equivalent commands:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the shared workshop dependencies in the activated environment:

```powershell
python -m pip install -r workshop/requirements.txt
```

Create your local environment file from the sample:

```powershell
Copy-Item workshop/.env.sample workshop/.env
```

If you are using Bash, use this equivalent command:

```bash
cp workshop/.env.sample workshop/.env
```

Sign in to Azure. The prebuilt script and notebook can use this current user credential when `DOC_INTELLIGENCE_KEY` is empty, and the custom model test uses it later in the lab:

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
	lab-01-document-intelligence/
		prebuilt/
			01-document-analysis-prebuild-model.py
			01-document-analysis-prebuild-model.ipynb
			sample-invoice/
				sample-invoice.pdf
		custom/
			02-document-analysis-custom-model.py
			02-document-analysis-custom-model.ipynb
			storage-setup.py
			storage-setup.ipynb
			test1.jpg
			sample-forms/
				fields.json
				Form_1.jpg
				Form_1.jpg.labels.json
				Form_1.jpg.ocr.json
				...
```

The scripts in this lab load configuration from `workshop/.env`, so you do not need to create another `.env` file inside `lab-01-document-intelligence`.

## 2. Create a Document Intelligence Resource

1. Open the Azure portal.
2. Create a new **Document Intelligence** resource, or reuse an existing one.
3. After deployment, open the resource.
4. Go to **Keys and Endpoint**.
5. Copy the endpoint. Copy one key only if you want to use key-based authentication for the prebuilt invoice example.

You need the endpoint for both the prebuilt and custom model examples. The prebuilt script and notebook use `DOC_INTELLIGENCE_KEY` when it is set; if the key is empty, they use your current Azure user credentials through `DefaultAzureCredential`.

## 3. Configure the Shared Environment File

Open `workshop/.env` and update these values:

```env
DOC_INTELLIGENCE_ENDPOINT=<your-document-intelligence-endpoint>
DOC_INTELLIGENCE_KEY=<your-document-intelligence-key-or-leave-empty-for-current-user-credentials>
DOC_INTELLIGENCE_MODEL_ID=<your-document-intelligence-model-id>
DOC_INTELLIGENCE_RESOURCE_NAME=
DOC_INTELLIGENCE_RESOURCE_GROUP=
STORAGE_SUBSCRIPTION_ID=
STORAGE_RESOURCE_GROUP=<your-resource-group-name>
STORAGE_LOCATION=eastus2
STORAGE_ACCOUNT_NAME=
```

For now, leave `DOC_INTELLIGENCE_MODEL_ID` as the placeholder value. You will return to it after training the custom model. The storage values are used by the custom model setup helper. Leave `STORAGE_SUBSCRIPTION_ID` empty to use the current default Azure CLI subscription, or set it explicitly to override the CLI context. Leave `STORAGE_ACCOUNT_NAME` empty to let the helper generate a valid storage account name and save it back to `workshop/.env`; set it yourself to reuse a specific storage account across runs. Leave `DOC_INTELLIGENCE_RESOURCE_NAME` empty to infer the resource name from `DOC_INTELLIGENCE_ENDPOINT`. Leave `DOC_INTELLIGENCE_RESOURCE_GROUP` empty when the Document Intelligence resource is in `STORAGE_RESOURCE_GROUP`; otherwise set it to the resource group that contains the Document Intelligence resource.

If you leave `DOC_INTELLIGENCE_KEY` empty, run `az login` first and make sure your Azure user has permission to call the Document Intelligence resource.

<details>
<summary>Checkpoint: shared environment file format</summary>

Your `workshop/.env` should look like this after you add the Document Intelligence endpoint. The key can be a real key or left empty when you use current user credentials:

```env
# Lab 01 - Document Intelligence
DOC_INTELLIGENCE_ENDPOINT=https://<resource-name>.cognitiveservices.azure.com/
DOC_INTELLIGENCE_KEY=<your-document-intelligence-key-or-empty>
DOC_INTELLIGENCE_MODEL_ID=<your-document-intelligence-model-id>
DOC_INTELLIGENCE_RESOURCE_NAME=
DOC_INTELLIGENCE_RESOURCE_GROUP=

STORAGE_SUBSCRIPTION_ID=
STORAGE_RESOURCE_GROUP=<your-resource-group-name>
STORAGE_LOCATION=eastus2
STORAGE_ACCOUNT_NAME=

SEARCH_ENDPOINT=your_search_endpoint
QUERY_KEY=your_query_key
INDEX_NAME=your_index_name
```

</details>

## 4. Configure the Prebuilt Invoice Script

Open `workshop/lab-01-document-intelligence/prebuilt/01-document-analysis-prebuild-model.py`. The script should:

1. Load `workshop/.env`.
2. Read `DOC_INTELLIGENCE_ENDPOINT` and `DOC_INTELLIGENCE_KEY`.
3. Create a `DocumentIntelligenceClient` with `AzureKeyCredential` when `DOC_INTELLIGENCE_KEY` is set, or `DefaultAzureCredential` when the key is empty.
4. Analyze an invoice with the `prebuilt-invoice` model.
5. Print selected invoice fields, including vendor, customer, and total.

The script uses the Microsoft Learn sample invoice URL so Document Intelligence can retrieve the file directly. The same sample is also included locally at `prebuilt/sample-invoice/sample-invoice.pdf` for inspection.

<details>
<summary>Solution: completed prebuilt invoice script</summary>

```python
from dotenv import load_dotenv
import os
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest


def main():
	os.system('cls' if os.name == 'nt' else 'clear')

	try:
		env_path = Path(__file__).resolve().parents[2] / ".env"
		load_dotenv(env_path)
		endpoint = os.getenv('DOC_INTELLIGENCE_ENDPOINT')
		key = (os.getenv('DOC_INTELLIGENCE_KEY') or '').strip()

		fileUri = "https://github.com/MicrosoftLearning/mslearn-ai-information-extraction/blob/main/Labfiles/03-document-intelligence/prebuilt/sample-invoice/sample-invoice.pdf?raw=true"
		fileLocale = "en-US"

		print(f"\nConnecting to Forms Recognizer at: {endpoint}")
		print(f"Analyzing invoice at: {fileUri}")

		credential = AzureKeyCredential(key) if key else DefaultAzureCredential()
		document_analysis_client = DocumentIntelligenceClient(
			endpoint=endpoint,
			credential=credential
		)

		poller = document_analysis_client.begin_analyze_document(
			"prebuilt-invoice",
			AnalyzeDocumentRequest(url_source=fileUri),
			locale=fileLocale
		)

		result = poller.result()

		for document in result.documents:
			vendor_name = document.fields.get("VendorName")
			if vendor_name:
				print(f"\nVendor Name: {vendor_name.get('valueString')}, with confidence {vendor_name.get('confidence')}.")

			customer_name = document.fields.get("CustomerName")
			if customer_name:
				print(f"Customer Name: {customer_name.get('valueString')}, with confidence {customer_name.get('confidence')}.")

			invoice_total = document.fields.get("InvoiceTotal")
			if invoice_total:
				amount = invoice_total.get("valueCurrency", {})
				print(f"Invoice Total: {amount.get('currencySymbol', '$')}{amount.get('amount')}, with confidence {invoice_total.get('confidence')}.")

	except Exception as ex:
		print(ex)

	print("\nAnalysis complete.\n")


if __name__ == "__main__":
	main()
```

</details>

## 5. Run Prebuilt Invoice Analysis

You can run the prebuilt invoice example as a Python script or as a Jupyter notebook.

### Option A: Run the Python Script

From the repository root, run:

```powershell
python workshop/lab-01-document-intelligence/prebuilt/01-document-analysis-prebuild-model.py
```

Review the extracted fields and confidence scores. The exact values can vary by service version, but you should see output for fields such as vendor name, customer name, and invoice total.

### Option B: Run the Jupyter Notebook

Use this option if you want to run the same flow one step at a time.

1. Install the VS Code [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) if it is not already installed.
2. Open `workshop/lab-01-document-intelligence/prebuilt/01-document-analysis-prebuild-model.ipynb`.
3. Select the Python interpreter from your activated `.venv` when prompted.
4. Run the notebook cells from top to bottom.

The notebook loads `workshop/.env`, creates the Document Intelligence client, analyzes the sample invoice, and prints the extracted fields in separate runnable steps.

<details>
<summary>Checkpoint: what successful output looks like</summary>

```text
Connecting to Forms Recognizer at: https://<resource-name>.cognitiveservices.azure.com/
Analyzing invoice at: https://github.com/MicrosoftLearning/...

Vendor Name: CONTOSO LTD., with confidence 0.9...
Customer Name: MICROSOFT CORPORATION, with confidence 0.9...
Invoice Total: $110, with confidence 0.9...

Analysis complete.
```

</details>

## 6. Create a Custom Extraction Project

Next, train a custom model that extracts fields from the purchase order-style forms in `custom/sample-forms/`.

Run the storage setup helper to create a storage account and upload the sample forms by using your current Azure credential context:

```powershell
python workshop/lab-01-document-intelligence/custom/storage-setup.py
```

If you prefer to run the setup step by step, open `workshop/lab-01-document-intelligence/custom/storage-setup.ipynb` in VS Code and run the cells from top to bottom.

The helper uses `DefaultAzureCredential`, so it runs with your current Azure credential context, such as VS Code Azure sign-in or the account from `az login`. If `STORAGE_SUBSCRIPTION_ID` is blank, it uses the current default subscription from `az account show`; otherwise it uses the subscription ID from `workshop/.env`. If `STORAGE_ACCOUNT_NAME` is blank, the helper generates a valid storage account name and writes it back to `workshop/.env` so future runs reuse the same account. The helper creates or reuses the storage account, enables the system-assigned managed identity on the Document Intelligence resource when needed, assigns both your signed-in user and the Document Intelligence managed identity **Storage Blob Data Contributor** on that account by using the Azure SDK, waits for RBAC propagation, and uploads the sample forms. Your account must have permission to create storage accounts, update the Document Intelligence resource identity, and assign roles, such as **Owner** or **User Access Administrator** at the resource group or subscription scope.

Copy the printed `Container URL`; you will use it when the studio asks for the training data location. Sign in to Document Intelligence Studio with the same Azure account so the studio can access the container with your user credentials.

1. Open [Document Intelligence Studio](https://documentintelligence.ai.azure.com/studio).
2. Sign in with the same Azure account you used for the Document Intelligence resource.
3. Select **Custom extraction model**.
4. Create a new project.
5. Select your Document Intelligence resource.
6. Connect the storage container by using the container URL printed by `storage-setup.py` and your signed-in Azure account.
7. Confirm the sample form files from `workshop/lab-01-document-intelligence/custom/sample-forms/` are available in the connected container.

Upload the JPG files and their matching label/OCR JSON files together. The included `fields.json` defines the custom fields used by the labeled forms.

The custom fields include:

- `Merchant`
- `PhoneNumber`
- `Website`
- `Email`
- `PurchaseOrderNumber`
- `DatedAs`
- `VendorName`
- `CompanyName`
- `CompanyAddress`
- `CompanyPhoneNumber`
- `Subtotal`
- `Tax`
- `Total`
- `Signature`
- `Quantity`

## 7. Train the Custom Model

In Document Intelligence Studio:

1. Confirm the uploaded forms show their labels.
2. Select **Train**.
3. Choose a descriptive model name, such as `purchase-order-extractor`.
4. Start training.
5. When training completes, open the model details.
6. Copy the **Model ID**.

Update `workshop/.env` with the trained model ID:

```env
DOC_INTELLIGENCE_MODEL_ID=<your-trained-model-id>
```

<details>
<summary>Checkpoint: custom model details to capture</summary>

Record these values in `workshop/.env`:

```text
DOC_INTELLIGENCE_ENDPOINT=<your-document-intelligence-endpoint>
DOC_INTELLIGENCE_KEY=<your-document-intelligence-key-or-empty>
DOC_INTELLIGENCE_MODEL_ID=<your-trained-model-id>
```

The custom test script uses `DefaultAzureCredential`, so it does not pass the key to the SDK. The key can remain empty if you are using current user credentials for the prebuilt example too.

</details>

## 8. Configure the Custom Model Test Script

Open `workshop/lab-01-document-intelligence/custom/02-document-analysis-custom-model.py`. The script and notebook should:

1. Load `workshop/.env`.
2. Read `DOC_INTELLIGENCE_ENDPOINT` and `DOC_INTELLIGENCE_MODEL_ID`.
3. Create a `DocumentIntelligenceClient` with `DefaultAzureCredential`.
4. Analyze a test form with your custom model.
5. Print each extracted field value and confidence score.

<details>
<summary>Solution: completed custom model test script</summary>

```python
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv
import os
from pathlib import Path


def main():
	os.system('cls' if os.name == 'nt' else 'clear')

	try:
		env_path = Path(__file__).resolve().parents[2] / ".env"
		load_dotenv(env_path)
		endpoint = os.getenv("DOC_INTELLIGENCE_ENDPOINT")
		model_id = os.getenv("DOC_INTELLIGENCE_MODEL_ID")

		formUrl = "https://github.com/MicrosoftLearning/mslearn-ai-information-extraction/blob/main/Labfiles/03-document-intelligence/custom/test1.jpg?raw=true"

		document_analysis_client = DocumentIntelligenceClient(
			endpoint=endpoint,
			credential=DefaultAzureCredential()
		)

		poller = document_analysis_client.begin_analyze_document(
			model_id,
			AnalyzeDocumentRequest(url_source=formUrl)
		)
		result = poller.result()

		for idx, document in enumerate(result.documents):
			print("--------Analyzing document #{}--------".format(idx + 1))
			print("Document has type {}".format(document.doc_type))
			print("Document has confidence {}".format(document.confidence))
			print("Document was analyzed by model with ID {}".format(result.model_id))
			for name, field in document.fields.items():
				field_value = field.get("valueString") or field.get("content", "N/A")
				print("Found field '{}' with value '{}' and with confidence {}".format(name, field_value, field.get("confidence")))

		print("-----------------------------------")
	except Exception as ex:
		print(ex)

	print("\nAnalysis complete.\n")


if __name__ == "__main__":
	main()
```

</details>

## 9. Run the Custom Model Test

You can run the custom model test as a Python script or as a Jupyter notebook.

### Option A: Run the Python Script

From the repository root, run:

```powershell
python workshop/lab-01-document-intelligence/custom/02-document-analysis-custom-model.py
```

The script sends a test form to the model and prints every field returned by Document Intelligence.

### Option B: Run the Jupyter Notebook

Use this option if you want to run the custom model test one step at a time.

1. Install the VS Code [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) if it is not already installed.
2. Open `workshop/lab-01-document-intelligence/custom/02-document-analysis-custom-model.ipynb`.
3. Select the Python interpreter from your activated `.venv` when prompted.
4. Run the notebook cells from top to bottom.

The notebook loads `workshop/.env`, creates the Document Intelligence client with `DefaultAzureCredential`, analyzes the test form with your custom model, and displays the returned fields in a table with the field value and confidence score.

<details>
<summary>Checkpoint: what successful custom model output looks like</summary>

```text
--------Analyzing document #1--------
Document has type <your-model-id>
Document has confidence 0.9...
Document was analyzed by model with ID <your-model-id>
Found field 'Merchant' with value '...' and with confidence 0.9...
Found field 'PurchaseOrderNumber' with value '...' and with confidence 0.9...
Found field 'Total' with value '...' and with confidence 0.9...
-----------------------------------

Analysis complete.
```

In the notebook version, the same extracted fields are shown as a table with columns for document number, document type, document confidence, model ID, field name, value, and field confidence.

</details>

## Troubleshooting

If the prebuilt script or notebook fails with an authentication error, confirm that `workshop/.env` contains `DOC_INTELLIGENCE_ENDPOINT` and that the endpoint includes the full `https://...` URL. If `DOC_INTELLIGENCE_KEY` is empty, run `az login` again and make sure your account has access to the Document Intelligence resource.

If the custom script fails with an authentication error, run `az login` again and make sure your account has access to the Document Intelligence resource.

If the custom script returns no fields or a model-not-found error, confirm that `DOC_INTELLIGENCE_MODEL_ID` exactly matches the trained model ID from Document Intelligence Studio.

If training does not show labels in Document Intelligence Studio, upload each JPG with its matching `.labels.json` and `.ocr.json` file from `custom/sample-forms/`.

## Clean Up

When you are finished, remove any Azure resources you created only for this lab to avoid ongoing charges. If you used a shared workshop resource, leave it in place for the remaining labs.
