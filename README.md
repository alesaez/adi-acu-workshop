# Azure Document Intelligence and Content Understanding Workshop

This workshop introduces document extraction, multimodal content analysis, knowledge mining, and retrieval-augmented generation (RAG) patterns with Azure AI services.

The labs focus on two closely related service areas:

- **Azure AI Document Intelligence** for extracting structured data from forms and documents with prebuilt and custom document models.
- **Azure AI Content Understanding** for extracting information from documents, images, audio, and video, and for building configurable analyzer-based workflows.

Later labs show how extracted content can be indexed, queried, and integrated into larger solutions with Azure AI Search, Azure OpenAI, Azure Functions, Azure Cosmos DB, Azure Storage, and solution accelerators.

## Workshop Goals

After completing the workshop, you should be able to:

- Choose between Document Intelligence and Content Understanding for common extraction scenarios.
- Use prebuilt models and custom analyzers to extract structured information.
- Prepare local Python scripts and notebooks that call Azure AI services.
- Build a knowledge mining solution with Azure AI Search enrichments.
- Build an automated RAG ingestion pipeline over extracted content.
- Review larger solution accelerator patterns for production-style document processing.

## Lab Overview

| Lab | Topic | Estimated time | What you build or explore |
| --- | --- | --- | --- |
| [Lab 01 - Document Intelligence](lab-01-document-intelligence/README.md) | Azure AI Document Intelligence | 75-90 minutes | Analyze invoices with a prebuilt model, train a custom extraction model, and test it from Python. |
| [Lab 02 - Content Understanding](lab-02-content-understanding/README.md) | Azure AI Content Understanding | 2.5-3 hours | Explore prebuilt analyzers and create custom analyzers for documents, images, audio, video, and business cards. |
| [Lab 03 - Knowledge Mining](lab-03-knowledge-mining/README.md) | Azure AI Search | 75-90 minutes | Upload documents, run an enriched indexer, query extracted knowledge, and optionally use a Python search client. |
| [Lab 04 - RAG Pipeline](lab-04-rag-pipeline/README.md) | Automated ingestion and RAG | 90-120 minutes | Extract, chunk, embed, index, and query documents with Content Understanding, Azure OpenAI, and Azure AI Search. |
| [Lab 05 - Data Extraction with ACU](lab-05-data-extraction-using-acu/README.md) | End-to-end document extraction sample | 90-150 minutes | Review or deploy a full Azure Samples solution using Content Understanding, Azure Functions, Cosmos DB, Key Vault, and Terraform. |
| [Lab 06 - Solution Accelerators](lab-06-solution-accellerator/README.md) | Advanced optional exploration | 60-120 minutes | Compare Microsoft solution accelerators for content processing, knowledge mining, and chat over data. |

## Repository Structure

```text
workshop/
	.env.sample
	requirements.txt
	lab-01-document-intelligence/
	lab-02-content-understanding/
	lab-03-knowledge-mining/
	lab-04-rag-pipeline/
	lab-05-data-extraction-using-acu/
	lab-06-solution-accellerator/
```

The labs share one Python requirements file and one environment file:

- `requirements.txt` contains the Python packages used across the workshop.
- `.env.sample` contains the configuration keys used by the labs.
- `.env` should be created locally from `.env.sample` and should not be committed.

## Prerequisites

You need:

- An Azure subscription.
- Permission to create or use Azure AI services, Azure Storage, Azure AI Search, Azure OpenAI, and related resources used in the labs.
- Azure CLI installed and signed in.
- Python 3.10 through 3.13 for the core labs. Lab 05's source accelerator expects Python 3.12 or later.
- Visual Studio Code.
- The VS Code Jupyter extension if you plan to run notebook versions.
- Terraform and Azure Functions Core Tools if you plan to fully deploy and run the Lab 05 source sample.

## Setup

From the repository root, create and activate a virtual environment.

PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create your local environment file:

PowerShell:

```powershell
Copy-Item .env.sample .env
```

Bash:

```bash
cp .env.sample .env
```

Sign in to Azure:

```bash
az login
```

Fill in `.env` as each lab asks for resource endpoints, keys, model IDs, analyzer names, or search settings. Prefer Microsoft Entra authentication where the lab supports it, and only use keys when the exercise explicitly requires them.

## Key Concepts

### Azure AI Document Intelligence

Azure AI Document Intelligence extracts text, layout, tables, key-value pairs, and structured fields from documents. It is especially strong for document-centric scenarios such as invoices, receipts, IDs, tax forms, contracts, and custom business forms.

Common model types include:

- **Prebuilt models** for common document types such as invoices, receipts, identity documents, tax forms, and business cards.
- **Layout and read models** for extracting text, tables, selection marks, and structure.
- **Custom extraction models** for documents where you define and train the fields you need.
- **Composed models** for routing multiple document types through a combined model.

Use Document Intelligence when the primary input is a document and the desired output is structured extraction from pages, forms, tables, and repeated document layouts.

### Azure AI Content Understanding

Azure AI Content Understanding extracts structured information from multiple content types, including documents, images, audio, and video. It uses analyzers and schemas to define what information should be extracted from each content type.

Content Understanding is valuable when:

- You need one extraction approach across mixed content types.
- You want schema-driven extraction from documents, images, audio, or video.
- You need to build reusable analyzers and test them against new inputs.
- Your solution needs multimodal understanding rather than document-only extraction.

Use Content Understanding when the input is broader than traditional documents, or when your workflow needs configurable analyzers across multimodal content.

### Azure AI Search and Knowledge Mining

Azure AI Search indexes content so users and applications can query it. In the knowledge mining lab, Azure AI Search enrichments extract key phrases, people, locations, image text, and metadata from documents.

Use Azure AI Search when extracted content needs to become searchable, filterable, rankable, or available to retrieval pipelines.

### Retrieval-Augmented Generation

RAG combines search and generative AI. The pipeline in Lab 04 extracts content, chunks it, creates embeddings, stores vectors in Azure AI Search, and uses Azure OpenAI to answer questions grounded in retrieved content.

Use RAG when users need natural-language answers over private or specialized content and the answer should be grounded in retrieved source material.

## Document Intelligence vs Content Understanding

Use the Microsoft Learn guidance [Choose the right Azure AI tool for document processing - Foundry Tools](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/choosing-right-ai-tool) as the primary reference when deciding which service to use. The table below summarizes the decision points used throughout this workshop.

| Scenario | Better starting point | Why |
| --- | --- | --- |
| Extract fields from invoices, receipts, IDs, tax forms, or business forms | Document Intelligence | Prebuilt and custom document models are optimized for page-based document extraction. |
| Extract tables, layout, text, and key-value pairs from PDFs | Document Intelligence | Layout and document models provide strong page structure extraction. |
| Train a custom model for a consistent document type | Document Intelligence | Custom extraction models work well when training examples share a predictable document structure. |
| Extract structured data from documents, images, audio, and video in one lab or app | Content Understanding | Analyzer workflows span multiple modalities. |
| Build a reusable schema-driven analyzer for mixed business content | Content Understanding | You define schemas and test analyzers against new content. |
| Analyze meetings, voicemails, recordings, or visual slides | Content Understanding | These are multimodal scenarios outside traditional document-only extraction. |
| Build a production-style content processing application | Content Understanding plus other Azure services | Use analyzers with Functions, Storage, Cosmos DB, Search, and OpenAI for an end-to-end workflow. |
| Make extracted content searchable | Azure AI Search | Search indexes and enrichments make extracted content discoverable. |
| Chat with extracted or indexed private content | Azure AI Search plus Azure OpenAI | RAG grounds generated answers in retrieved content. |

## Tips and Tricks

- Start with a prebuilt model or analyzer before building a custom one. It helps you understand what the service already extracts.
- Use Document Intelligence for document-first work unless you know you need images, audio, video, or broader multimodal workflows.
- Use Content Understanding when the extraction schema matters more than the original file format.
- Keep sample inputs small while developing. Move to larger batches only after extraction quality and configuration are stable.
- Name custom models, analyzers, indexes, and deployments clearly. The labs reuse values across `.env`, portal steps, and scripts.
- Treat `.env`, `local.settings.json`, Terraform variable files, keys, and connection strings as local-only secrets.
- Prefer Microsoft Entra authentication when supported. Use API keys only when the lab or SDK path requires them.
- For custom extraction, test with documents that differ from the training examples. This reveals whether the model learned the field or memorized a layout.
- For RAG, inspect retrieved chunks before judging answer quality. Bad answers often come from retrieval, chunking, or missing source content rather than the chat model alone.
- Clean up lab resources when finished, especially Azure OpenAI, Azure AI Search, Storage, Cosmos DB, and deployed accelerator resources.

## Useful Documentation

- [Choose the right Azure AI tool for document processing - Foundry Tools](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/choosing-right-ai-tool)
- [Azure AI Document Intelligence documentation](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- [Document Intelligence model overview](https://learn.microsoft.com/azure/ai-services/document-intelligence/concept-model-overview)
- [Document Intelligence Studio](https://documentintelligence.ai.azure.com/studio)
- [Azure AI Content Understanding documentation](https://learn.microsoft.com/azure/ai-services/content-understanding/)
- [Content Understanding overview](https://learn.microsoft.com/azure/ai-services/content-understanding/overview)
- [Content Understanding Studio](https://contentunderstanding.ai.azure.com/)
- [Azure AI Search documentation](https://learn.microsoft.com/azure/search/)
- [Azure OpenAI documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure AI Foundry documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Azure Functions Python developer guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Key Vault documentation](https://learn.microsoft.com/azure/key-vault/)

## Source Content and Samples

These labs adapt or reference content from Microsoft Learn and Azure Samples:

- [Microsoft Learn information extraction lab files](https://github.com/MicrosoftLearning/mslearn-ai-information-extraction)
- [Data Extraction using Azure Content Understanding](https://github.com/Azure-Samples/data-extraction-using-azure-content-understanding)
- [Content Processing Solution Accelerator](https://github.com/microsoft/content-processing-solution-accelerator)
- [Conversation Knowledge Mining Solution Accelerator](https://github.com/microsoft/Conversation-Knowledge-Mining-Solution-Accelerator)
- [Document Knowledge Mining Solution Accelerator](https://github.com/microsoft/Document-Knowledge-Mining-Solution-Accelerator)
- [Chat with Your Data Solution Accelerator](https://github.com/Azure-Samples/chat-with-your-data-solution-accelerator)

## Suggested Learning Path

Complete Labs 01 and 02 first. They establish the difference between document-specific extraction and multimodal analyzer-based extraction.

Then complete Lab 03 to see how extracted and enriched content becomes searchable. Continue to Lab 04 to connect extraction, embeddings, search, and chat into a RAG pipeline.

Use Labs 05 and 06 as advanced optional labs when you are ready to review larger application architectures and solution accelerator patterns.
