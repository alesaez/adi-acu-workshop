# Lab 04 Data Folder

This folder is the target location for the Lab 04 RAG pipeline sample documents.

The PDF files are not authored directly in this folder. When you reach the data preparation step in the Lab 04 README, run this command from the repository root to extract the Lab 03 `documents.zip` package into this folder:

```powershell
$sourceZip = "workshop/lab-03-knowledge-mining/documents.zip"
$dataPath = "workshop/lab-04-rag-pipeline/data"

New-Item -ItemType Directory -Force -Path $dataPath | Out-Null
Expand-Archive -Path $sourceZip -DestinationPath $dataPath -Force
```

After extraction, this folder should contain the travel brochure PDF files used by the Lab 04 ingestion pipeline.
