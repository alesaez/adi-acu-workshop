# Lab 05 - Data Extraction with Azure Content Understanding

Source repo: https://github.com/Azure-Samples/data-extraction-using-azure-content-understanding

In this lab, you explore a complete intelligent document processing solution that uses Azure Content Understanding to extract structured data from documents and Azure OpenAI to query processed content using natural language.

This lab is based on the Azure Samples repository above. Unlike the earlier labs, which walk through smaller service-specific exercises, this lab uses a full solution accelerator-style sample with infrastructure, application code, configuration files, API endpoints, and sample document workflows.

## Estimated Time

Plan for **90-150 minutes**. The shorter path is an architecture and code review. A full deployment can take longer depending on Azure permissions, model availability, Terraform setup, and resource provisioning time.

## Learning Objectives

After completing this lab, you will be able to:

- Explain how Azure Content Understanding can support end-to-end document extraction.
- Describe how Azure Functions, Azure Storage, Azure Cosmos DB, Azure Key Vault, and Azure OpenAI work together in the sample.
- Review the Terraform-based infrastructure deployment model.
- Understand how document extraction schemas are configured with JSON.
- Run or review the document ingestion, configuration upload, health check, and query workflows.
- Identify what would need to change before adapting the sample for production use.

## What the Sample Covers

The source repository demonstrates an intelligent document processing application with these major capabilities:

- **Document ingestion**: Process uploaded documents with Azure Content Understanding.
- **Configurable extraction**: Define document types, fields, and extraction rules with JSON configuration.
- **Document classification**: Route documents based on type and extraction configuration.
- **Persistent storage**: Store extracted data and metadata in Azure Cosmos DB.
- **Conversational enquiry**: Ask natural-language questions about processed documents using Azure OpenAI.
- **Serverless processing**: Host APIs and workflows with Azure Functions.
- **Managed secrets**: Store service configuration and secrets with Azure Key Vault.
- **Infrastructure as Code**: Deploy required Azure resources with Terraform.

## Prerequisites

Before you start, make sure you have:

- An Azure subscription with permission to create resources.
- Access to Azure Content Understanding.
- Access to Azure OpenAI models required by the sample.
- Azure CLI installed and signed in.
- Terraform installed if you plan to deploy the infrastructure.
- Python 3.12 or later.
- Azure Functions Core Tools if you plan to run the Function App locally.
- Permission to create or use Azure Functions, Azure Storage, Azure Cosmos DB, Azure Key Vault, and related role assignments.

> The source repository is a demonstration sample. Review security, networking, monitoring, identity, cost, and data-handling requirements before using the pattern with real organizational data.

## 1. Review the Source Repository

Open the source repository:

https://github.com/Azure-Samples/data-extraction-using-azure-content-understanding

Review these areas first:

- `README.md` for the solution overview, prerequisites, quick start, and usage instructions.
- `docs/` for architecture documentation and diagrams.
- `iac/` for Terraform infrastructure definitions.
- `configs/` for sample extraction configuration files.
- `document_samples/` for sample input documents.
- `src/` for Azure Functions application code, routes, services, and sample HTTP requests.

## 2. Review the Architecture

The solution implements three main workflows:

1. **Configuration upload**: Upload document extraction schemas and rules.
2. **Document ingestion**: Process documents with Azure Content Understanding and store extracted data.
3. **Document enquiry**: Query processed documents using Azure OpenAI-powered natural language responses.

As you review the architecture, identify the role of each Azure service:

| Service | Role in the solution |
| --- | --- |
| Azure Content Understanding | Extracts structured content from documents. |
| Azure OpenAI | Supports natural-language querying over processed content. |
| Azure Functions | Hosts API endpoints and serverless processing workflows. |
| Azure Storage | Stores uploaded documents and related files. |
| Azure Cosmos DB | Persists extracted data and document metadata. |
| Azure Key Vault | Stores secrets and service configuration securely. |
| Terraform | Provisions the Azure resources required by the sample. |

## 3. Choose Your Lab Path

Choose one of these paths based on your time and permissions.

### Option A: Architecture and Code Review

Use this option if you do not want to deploy Azure resources.

1. Review the repository README and architecture documentation.
2. Inspect the Terraform files under `iac/` to understand what resources would be deployed.
3. Review the sample extraction configuration under `configs/`.
4. Review the Function App routes and service code under `src/`.
5. Review the sample HTTP requests under `src/samples/`.
6. Map the sample back to the earlier workshop labs: extraction, ingestion, enrichment, storage, and querying.

### Option B: Deploy and Explore the Sample

Use this option if you have Azure permissions and want to deploy the full sample.

Follow the deployment instructions in the source repository. At a high level, the deployment flow is:

1. Clone the source repository:

	```bash
	git clone https://github.com/Azure-Samples/data-extraction-using-azure-content-understanding.git
	cd data-extraction-using-azure-content-understanding
	```

2. Sign in to Azure and confirm the target subscription:

	```bash
	az login
	az account list --output table
	az account set --subscription "<your-subscription-id>"
	az account show --output table
	```

3. Review the infrastructure configuration in `iac/`.
4. Copy and update the Terraform variables file as described in the source repo.
5. Run `terraform init`, `terraform plan`, and `terraform apply` from the `iac/` folder when you are ready to deploy.
6. Configure local application settings using the source repo's `src/local.settings.sample.json` guidance.
7. Review or update `src/resources/app_config.yaml` so it references the deployed service endpoints and Key Vault secret names.

Do not commit local settings files, Terraform variable files, keys, connection strings, or secrets.

## 4. Review the Extraction Configuration

The sample uses JSON configuration to define document extraction behavior. Review the files in the source repo's `configs/` folder.

Look for these concepts:

- Document type or collection definitions.
- Field schemas that describe what values should be extracted.
- Field names, data types, and descriptions.
- Analyzer IDs or routing information.
- Versioned configuration IDs.

The configuration-driven approach is important because it lets the application support new document types without rewriting the entire processing workflow.

## 5. Run or Review the Application

If you deploy the solution and configure local settings, use the source repo instructions to start the Azure Functions application:

```bash
func start --script-root ./src/
```

Then review the sample HTTP requests in `src/samples/`, including:

- Health check requests.
- Configuration upload requests.
- Document ingestion requests.
- Query requests.
- Classifier management requests.

If you are only reviewing the solution, inspect these sample requests and trace which route, controller, and service each request uses in the `src/` folder.

## 6. Process Documents and Query Results

For a deployed environment, follow the source repo instructions to:

1. Upload or reference sample documents.
2. Upload the extraction configuration.
3. Trigger document ingestion.
4. Monitor Azure Function logs for processing status.
5. Query processed documents with the sample query endpoint.
6. Review the extracted fields, citations, and response grounding behavior.

For a review-only path, inspect how the sample handles each of these steps in code and configuration.

## 7. Production Readiness Review

Before adapting this sample for real workloads, consider:

- Identity and access control for users, applications, Key Vault, Cosmos DB, and Storage.
- Private networking, firewall rules, and data exfiltration controls.
- Secret management and rotation.
- Prompt, completion, and document data handling policies.
- Monitoring, tracing, and alerting.
- Error handling, retries, and dead-letter workflows.
- Cost controls for Azure OpenAI, Content Understanding, Storage, Cosmos DB, and Functions.
- Data retention and deletion requirements.
- Test coverage for extraction schemas and API behavior.

## Clean Up

If you deployed Azure resources, clean them up when you finish the lab to avoid ongoing charges. Use the cleanup guidance from the source repository or remove the resource group you created for the sample if it contains only lab resources.

## Discussion Prompts

- How does this solution extend the smaller Content Understanding exercises from Lab 02?
- What parts of the architecture are required for a production document extraction system?
- Which parts could be simplified for a proof of concept?
- How would you add a new document type?
- What data should be stored in Cosmos DB versus Blob Storage?
- Where would you add human review, approval, or exception handling?
