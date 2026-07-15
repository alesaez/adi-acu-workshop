# Lab 04 - Build an Automated RAG Ingestion Pipeline

Source exercise: https://microsoftlearning.github.io/mslearn-ai-information-extraction/Instructions/Exercises/05-rag-pipeline.html

Source lab files: https://github.com/MicrosoftLearning/mslearn-ai-information-extraction/tree/main/Labfiles/05-rag-pipeline

In this lab, you build an automated retrieval-augmented generation (RAG) ingestion pipeline. The pipeline uses Azure Content Understanding to extract content from travel documents, Azure OpenAI embeddings to vectorize content chunks, Azure AI Search to index the chunks, and a simple RAG agent to answer questions grounded in the indexed content.

This workshop structure is slightly different from the source repo:

- The source `documents.zip` file is included in `workshop/lab-03-knowledge-mining/` and is reused for this lab.
- Extracted Lab 04 input documents should be placed in `workshop/lab-04-rag-pipeline/data/`.
- The RAG pipeline scripts are in `workshop/lab-04-rag-pipeline/`.
- The only Python requirements file is `workshop/requirements.txt`.
- The only environment file is `workshop/.env`.
- The `.env` file should be copied from `workshop/.env.sample` because `.env` is intentionally gitignored.

This lab is mainly a portal follow-along experience for creating and configuring Azure resources. After the resources are ready, you run the included Python scripts to create the analyzer, ingest documents, query the RAG index, and test continuous ingestion.

## Estimated Time

Plan for **90-120 minutes** to complete this lab. The estimate includes Azure resource setup, environment configuration, document preparation, analyzer creation, ingestion, RAG querying, watch-mode ingestion, reset testing, and cleanup review.

## Learning Objectives

After completing this lab, you will be able to:

- Create a Microsoft Foundry project for Content Understanding and Azure OpenAI.
- Configure Content Understanding Studio to auto-deploy the required models.
- Create an Azure AI Search resource for RAG retrieval.
- Configure a shared `.env` file for Foundry, Azure OpenAI, and Azure AI Search.
- Create a Content Understanding analyzer from Python.
- Run an automated ingestion pipeline that extracts, chunks, embeds, indexes, and tracks documents.
- Query the indexed content with a RAG agent.
- Run the pipeline in watch mode to ingest new or updated documents automatically.

## Prerequisites

Before you start, complete the workshop setup and make sure you have:

- An Azure subscription.
- Permission to create or use Microsoft Foundry, Azure OpenAI model deployments, Content Understanding, and Azure AI Search resources.
- Python 3.10 through 3.13. Python 3.14 is not recommended for this workshop yet because some Azure SDK dependencies may not provide prebuilt wheels for every platform.
- Visual Studio Code.
- The dependencies from `workshop/requirements.txt` installed.

Create and activate a Python virtual environment from the repository root. If you have multiple Python versions installed on Windows, use the Python Launcher to choose a supported version explicitly:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r workshop/requirements.txt
```

If Python 3.13 is not installed, replace `-3.13` with another installed supported version, such as `-3.12`, `-3.11`, or `-3.10`.

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

## 1. Prepare the Lab Folder

From the repository root, confirm the lab has this structure:

```text
workshop/
	.env.sample
	.env
	requirements.txt
	lab-03-knowledge-mining/
		documents.zip
	lab-04-rag-pipeline/
		README.md
		create-analyzer.py
		ingest-pipeline.py
		rag-agent.py
		data/
			README.md
```

The scripts in this lab load configuration from `workshop/.env`, so you do not need to create another `.env` file inside `lab-04-rag-pipeline`.

## 2. Create Azure Resources

You need a Microsoft Foundry resource and project for Content Understanding and Azure OpenAI, plus an Azure AI Search resource for retrieval.

### Create a Microsoft Foundry Resource and Project

1. Open the [Microsoft Foundry portal](https://ai.azure.com/) at `https://ai.azure.com` and sign in with your Azure account.
2. Close any tips or quick start panes that open the first time you sign in.
3. Make sure the **New Foundry** toggle is on.
4. Select the project name in the upper-left corner, then select **Create new project**.
5. Enter a project name.
6. Expand **Advanced options** and configure these settings:

| Setting | Value |
| --- | --- |
| Subscription | Your Azure subscription |
| Resource group | Create or select a resource group |
| Location | A Content Understanding supported region, such as East US, East US 2, Sweden Central, UK South, West Europe, or another currently supported region |

7. Select **Create** and wait for the project to be created. This also creates the parent Foundry resource.
8. After the project opens, select the project name at the top of the page, then select **Project details**.
9. Follow the link to the parent resource and leave that browser tab open. You will return to it for the endpoint and keys.

> NOTE: Azure Content Understanding is available in selected regions. Check the region support documentation if the region you want is unavailable.

### Configure Content Understanding Models and Connection

1. In a new browser tab, open [Content Understanding Studio](https://contentunderstanding.ai.azure.com/home) at `https://contentunderstanding.ai.azure.com/home`.
2. Sign in with the same Azure account.
3. Select the settings gear icon in the top navigation bar.
4. Select **+ Add resource**.
5. Select the subscription and resource group that contain your Foundry resource.
6. Select your Foundry resource name from the dropdown. This is the parent resource for the project you created.
7. Make sure **Enable auto-deployment** is selected.
8. Select **Next**, then **Save**.
9. Wait while Content Understanding Studio deploys the required models.

### Create an Azure AI Search Resource

1. Open the [Azure portal](https://portal.azure.com/) at `https://portal.azure.com`.
2. Select **+ Create a resource**.
3. Search for `Azure AI Search` and create a new **Azure AI Search** resource with these settings:

| Setting | Value |
| --- | --- |
| Subscription | Your Azure subscription |
| Resource group | The same resource group as your Foundry resource |
| Service name | Enter a valid unique search service name |
| Location | The same location as your Foundry resource |
| Pricing tier | Free or Basic |

4. Select **Review + create**, then **Create**.
5. Wait for deployment to complete.

### Gather Credentials

You need these values for `workshop/.env`:

| Setting | Where to find it |
| --- | --- |
| `FOUNDRY_ENDPOINT` | Parent Foundry resource **Overview** page, **Endpoint** value |
| `FOUNDRY_KEY` | Parent Foundry resource **Resource Management** > **Keys and Endpoint** |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | Foundry project **Build** > **Deployments** |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` | Foundry project **Build** > **Deployments** |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search resource **Overview** page, **Url** value |
| `AZURE_SEARCH_KEY` | Azure AI Search resource **Settings** > **Keys**, use an admin key |

> NOTE: The Foundry endpoint and key are used for both Content Understanding and Azure OpenAI because both services are included in the same Foundry resource.

## 3. Configure the Shared Environment File

Open `workshop/.env` and update the Lab 04 values:

```env
FOUNDRY_ENDPOINT=<your-foundry-endpoint>
FOUNDRY_KEY=<your-foundry-key>
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=<your-chat-model-deployment-name>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=<your-embedding-model-deployment-name>
AZURE_SEARCH_ENDPOINT=<your-azure-search-endpoint>
AZURE_SEARCH_KEY=<your-azure-search-admin-key>
```

Use the deployment names exactly as they appear in Foundry. Content Understanding Studio may add a numeric suffix to auto-deployed model names, such as `gpt-4.1-######` or `text-embedding-3-large-######`.

<details>
<summary>Checkpoint: Lab 04 environment values</summary>

Your Lab 04 section in `workshop/.env` should look similar to this after you add your real values:

```env
########################
# Lab 4 - RAG Pipeline #
########################

FOUNDRY_ENDPOINT=https://<foundry-resource-name>.services.ai.azure.com/
FOUNDRY_KEY=<your-foundry-key>
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4.1-######
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-large-######
AZURE_SEARCH_ENDPOINT=https://<search-service-name>.search.windows.net
AZURE_SEARCH_KEY=<your-search-admin-key>
```

</details>

## 4. Prepare the Sample Documents

The source exercise uses the same travel brochure documents from Lab 03. In this workshop, `documents.zip` is already included at `workshop/lab-03-knowledge-mining/documents.zip`.

From the repository root, extract the documents into the Lab 04 `data/` folder.

PowerShell:

```powershell
$sourceZip = "workshop/lab-03-knowledge-mining/documents.zip"
$dataPath = "workshop/lab-04-rag-pipeline/data"

New-Item -ItemType Directory -Force -Path $dataPath | Out-Null
Expand-Archive -Path $sourceZip -DestinationPath $dataPath -Force
```

Bash:

```bash
data_path="workshop/lab-04-rag-pipeline/data"
mkdir -p "$data_path"
unzip -o "workshop/lab-03-knowledge-mining/documents.zip" -d "$data_path"
```

After extraction, confirm that `workshop/lab-04-rag-pipeline/data/` contains files such as `Dubai Brochure.pdf`, `Las Vegas Brochure.pdf`, `London Brochure.pdf`, `Margies Travel Company Info.pdf`, `New York Brochure.pdf`, and `San Francisco Brochure.pdf`.

<details>
<summary>Checkpoint: expected data folder</summary>

Your Lab 04 data folder should look similar to this:

```text
workshop/
	lab-04-rag-pipeline/
		data/
			Dubai Brochure.pdf
			Las Vegas Brochure.pdf
			London Brochure.pdf
			Margies Travel Company Info.pdf
			New York Brochure.pdf
			San Francisco Brochure.pdf
```

</details>

## 5. Create a Content Understanding Analyzer

The first pipeline step creates a Content Understanding analyzer that extracts structured content from documents.

1. Open `workshop/lab-04-rag-pipeline/create-analyzer.py`.
2. Review the code. It does the following:
   - Loads configuration from `workshop/.env`.
   - Creates a `ContentUnderstandingClient` with `FOUNDRY_ENDPOINT` and `FOUNDRY_KEY`.
   - Defines an analyzer named `rag_document_analyzer` based on `prebuilt-document`.
   - Adds generated fields for `Summary` and `KeyTopics`.
   - Creates or replaces the analyzer by calling `begin_create_analyzer`.
3. From the repository root, run:

```powershell
python workshop/lab-04-rag-pipeline/create-analyzer.py
```

4. Wait for the analyzer creation operation to finish.

<details>
<summary>Checkpoint: analyzer created</summary>

Expected output should include a message similar to:

```text
Creating analyzer 'rag_document_analyzer'...
Analyzer 'rag_document_analyzer' created successfully.
```

If analyzer creation fails because a model is missing, return to Content Understanding Studio, confirm the Foundry resource connection, and wait for model auto-deployment to complete.

</details>

## 6. Run the Automated Ingestion Pipeline

The ingestion pipeline extracts content, chunks the extracted text, generates vector embeddings, creates or updates the Azure AI Search index, uploads chunk documents, and tracks processed files in a manifest.

1. Open `workshop/lab-04-rag-pipeline/ingest-pipeline.py`.
2. Review the code. It does the following:
   - Uses `processed_files.json` to track file hashes.
   - Reads files from `workshop/lab-04-rag-pipeline/data/`.
   - Creates or updates the Azure AI Search index named `rag-content-index`.
   - Uses the Content Understanding analyzer to extract document content.
   - Splits content into chunks with a 2000-character limit.
   - Uses your Azure OpenAI embedding deployment to create 3072-dimension vectors.
   - Uploads chunks to Azure AI Search with deterministic IDs.
   - Supports `--watch` for continuous ingestion and `--reset` to reprocess all files.
3. From the repository root, run:

```powershell
python workshop/lab-04-rag-pipeline/ingest-pipeline.py
```

4. Watch the output as each document is processed.
5. After the run completes, confirm that `workshop/lab-04-rag-pipeline/processed_files.json` was created.
6. Run the pipeline again:

```powershell
python workshop/lab-04-rag-pipeline/ingest-pipeline.py
```

The second run should report that there are no new files to ingest.

<details>
<summary>Checkpoint: ingestion output</summary>

Your output should look similar to this:

```text
[14:23:01] Verifying search index...
[14:23:02] Search index 'rag-content-index' is ready.
[14:23:02] Detected 6 new/updated file(s).
[14:23:02]   Processing: Margies Travel Company Info.pdf
[14:23:08]     Embedding chunk 1/3...
[14:23:09]     Embedding chunk 2/3...
[14:23:10]     Indexed 3 chunk(s) from Margies Travel Company Info.pdf.
[14:23:40] Ingestion complete - 6 file(s), 18 chunk(s) indexed.
```

The exact number of chunks can vary depending on extracted content.

</details>

## 7. Query the Index with the RAG Agent

After the ingestion pipeline indexes the content, run the RAG agent to ask questions about the documents.

1. Open `workshop/lab-04-rag-pipeline/rag-agent.py`.
2. Review the code. It does the following:
   - Loads configuration from `workshop/.env`.
   - Creates an Azure AI Search client for `rag-content-index`.
   - Creates an Azure OpenAI client for chat and embeddings.
   - Uses hybrid retrieval with keyword search and vector search.
   - Builds a grounded prompt from retrieved chunks.
   - Runs a question-and-answer loop until you type `quit`.
3. From the repository root, run:

```powershell
python workshop/lab-04-rag-pipeline/rag-agent.py
```

4. Ask questions such as:

```text
What destinations are featured in the travel brochures?
```

```text
What activities are recommended in Dubai?
```

```text
Tell me about Margie's Travel company.
```

5. Review the answers. They should be grounded in the indexed travel documents and cite source document names when possible.
6. Type `quit` to exit.

<details>
<summary>Checkpoint: RAG agent behavior</summary>

The agent should start with a prompt like this:

```text
RAG Agent ready! Ask questions about your indexed documents.
Type 'quit' to exit.

You:
```

When you ask a travel question, the answer should use retrieved brochure content rather than general model knowledge.

</details>

## 8. Ingest New Documents Automatically

In this section, you start the pipeline in watch mode, add a new local document, and confirm that the pipeline ingests it automatically.

### Start the Pipeline in Watch Mode

1. Open a second terminal in VS Code.
2. Activate the virtual environment if needed:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. From the repository root, run:

```powershell
python workshop/lab-04-rag-pipeline/ingest-pipeline.py --watch
```

4. Leave this terminal running. The pipeline checks the `data/` folder every 30 seconds.

### Add a New Document

1. In VS Code Explorer, create a new file named `tokyo-guide.txt` in `workshop/lab-04-rag-pipeline/data/`.
2. Add travel-guide content about Tokyo.
3. Save the file.
4. Return to the watch-mode terminal. Within about 30 seconds, it should detect and process the new file.

<details>
<summary>Solution: sample Tokyo guide content</summary>

You can use this text for `workshop/lab-04-rag-pipeline/data/tokyo-guide.txt`:

```text
Tokyo Travel Guide

Tokyo, the capital of Japan, is one of the most dynamic cities in the world, blending centuries-old tradition with cutting-edge technology and innovation.

Top Attractions:
- Senso-ji Temple: Tokyo's oldest temple, located in Asakusa, is a must-visit. The approach through Nakamise-dori shopping street is iconic.
- Shibuya Crossing: The world's busiest pedestrian crossing is a symbol of Tokyo's energy and pace.
- Meiji Shrine: A serene Shinto shrine set in a lush forest in the heart of the city, dedicated to Emperor Meiji.
- Tokyo Skytree: At 634 meters, this broadcasting tower offers panoramic views of the entire metropolitan area.
- Tsukiji Outer Market: The outer market offers fresh seafood and street food.

Neighborhoods to Explore:
- Shinjuku: A vibrant district known for nightlife, shopping, and Shinjuku Gyoen National Garden.
- Akihabara: The hub of anime, manga, and electronics culture.
- Harajuku: Famous for youth fashion, Takeshita Street, and trendy cafes.
- Ginza: Tokyo's upscale shopping and dining district.

Getting Around:
Tokyo has one of the world's most efficient public transportation systems. The Tokyo Metro and JR lines connect every corner of the city. A Suica or Pasmo card makes travel seamless. For visitors, the Japan Rail Pass offers unlimited travel on JR lines.

Best Time to Visit:
Spring from March to May is popular for cherry blossoms, and autumn from October to November is popular for fall foliage. Summers can be hot and humid, while winters are mild compared to northern Japan.
```

</details>

### Query the Newly Ingested Content

1. Open another terminal, or return to your first terminal.
2. Run the RAG agent again:

```powershell
python workshop/lab-04-rag-pipeline/rag-agent.py
```

3. Ask questions such as:

```text
What can you tell me about Tokyo?
```

```text
What are the top attractions in Tokyo?
```

```text
How do I get around in Tokyo?
```

4. The agent should now answer using the new Tokyo guide content.
5. Type `quit` to exit the agent.
6. Return to the watch-mode terminal and press **Ctrl+C** to stop the pipeline.

<details>
<summary>Checkpoint: watch-mode ingestion</summary>

The watch-mode terminal should show output similar to this after you save `tokyo-guide.txt`:

```text
[14:31:00] Detected 1 new/updated file(s).
[14:31:00]   Processing: tokyo-guide.txt
[14:31:05]     Embedding chunk 1/1...
[14:31:06]     Indexed 1 chunk(s) from tokyo-guide.txt.
[14:31:06] Ingestion complete - 1 file(s), 1 chunk(s) indexed.
```

</details>

## 9. Reset and Reprocess Documents

Use `--reset` when you want to clear the manifest and reprocess every supported file in `data/`:

```powershell
python workshop/lab-04-rag-pipeline/ingest-pipeline.py --reset
```

This deletes `processed_files.json` and causes the next run to process all current files again.

## 10. Troubleshooting

### Analyzer Creation Fails

- Confirm `FOUNDRY_ENDPOINT` and `FOUNDRY_KEY` are copied from the parent Foundry resource, not only the project page.
- Confirm Content Understanding Studio is connected to the same Foundry resource.
- Confirm auto-deployment completed for the required Content Understanding models.

### Ingestion Finds No Files

- Confirm the PDFs were extracted into `workshop/lab-04-rag-pipeline/data/`.
- Confirm the files have supported extensions: `.pdf`, `.png`, `.jpg`, `.docx`, or `.txt`.
- Run with `--reset` if files were already processed and you want to process them again.

### Embedding or Chat Calls Fail

- Confirm `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` and `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` match the exact deployment names in Foundry.
- Confirm the Foundry resource is in a region that supports the selected models.
- Confirm your Foundry key has not been rotated since you copied it.

### Search Indexing or Retrieval Fails

- Confirm `AZURE_SEARCH_ENDPOINT` points to your Azure AI Search resource URL.
- Confirm `AZURE_SEARCH_KEY` is an admin key, not a query key. The ingestion pipeline creates or updates an index and uploads documents, so it needs admin permissions.
- Confirm the Azure AI Search service is Free or Basic and available in the same region as the Foundry resource.

## 11. Clean Up

If you are finished with the lab, delete the resource group that contains the Foundry and Azure AI Search resources to avoid unnecessary costs.

1. Open the [Azure portal](https://portal.azure.com/).
2. Go to **Resource groups**.
3. Select the resource group you used for this lab.
4. Select **Delete resource group**.
5. Follow the confirmation prompts.

You can also remove generated local files if you no longer need them:

```powershell
Remove-Item workshop/lab-04-rag-pipeline/processed_files.json -ErrorAction SilentlyContinue
Remove-Item workshop/lab-04-rag-pipeline/data/*.pdf -ErrorAction SilentlyContinue
Remove-Item workshop/lab-04-rag-pipeline/data/tokyo-guide.txt -ErrorAction SilentlyContinue
```

## More Information

- [Build an automated RAG ingestion pipeline with Content Understanding](https://microsoftlearning.github.io/mslearn-ai-information-extraction/Instructions/Exercises/05-rag-pipeline.html)
- [Tutorial: Build a RAG solution with Content Understanding](https://learn.microsoft.com/azure/ai-services/content-understanding/tutorial/build-rag-solution)
- [Retrieval-augmented generation in Azure AI Search](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)
- [Azure Content Understanding Python SDK](https://pypi.org/project/azure-ai-contentunderstanding/)
