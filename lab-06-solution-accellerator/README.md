# Lab 06 - Solution Accelerator Exploration

This is an **optional advanced lab**. Instead of a single guided build, you will choose one of several Microsoft solution accelerators to explore after completing the core workshop labs.

Each accelerator is a more complete reference implementation that shows how the individual services from the earlier labs can be combined into an end-to-end solution. Review the options below, choose the one that best matches your scenario, and follow the setup instructions in the original repository.

## Estimated Time

Plan for **60-120 minutes** to review and explore one accelerator. Deployment time varies by accelerator, Azure subscription permissions, model availability, and whether you only review the architecture or fully deploy the solution.

## Accelerator Options

### Content Processing Solution Accelerator

Original repo: https://github.com/microsoft/content-processing-solution-accelerator

This accelerator focuses on automating content extraction and processing workflows for enterprise documents. It is a good fit when you want to understand how to move beyond individual document analysis scripts into a reusable processing solution.

It covers:

- Ingestion and processing of content at scale.
- Document extraction workflows using Azure AI services.
- A reference architecture for organizing extracted content and metadata.
- Patterns for operationalizing document processing beyond a single lab sample.

Choose this option if you are most interested in automated content processing pipelines, document extraction, and production-style workflow patterns.

### Conversation Knowledge Mining Solution Accelerator

Original repo: https://github.com/microsoft/Conversation-Knowledge-Mining-Solution-Accelerator

This accelerator focuses on mining insights from conversational content such as transcripts, chats, calls, and meeting records. It is useful for scenarios where the source data is dialogue-oriented rather than document-oriented.

It covers:

- Processing conversation transcripts and related unstructured content.
- Extracting topics, entities, summaries, and useful metadata from conversations.
- Making conversational knowledge searchable and easier to analyze.
- Patterns for turning communication records into discoverable knowledge assets.

Choose this option if your scenario involves call center transcripts, meeting records, support conversations, or other dialogue-heavy data.

### Document Knowledge Mining Solution Accelerator

Original repo: https://github.com/microsoft/Document-Knowledge-Mining-Solution-Accelerator

This accelerator focuses on extracting, enriching, indexing, and searching knowledge from document collections. It aligns closely with the knowledge mining concepts introduced earlier in the workshop.

It covers:

- Document ingestion and enrichment.
- Knowledge extraction from unstructured or semi-structured files.
- Search indexing patterns for enriched document content.
- End-to-end architecture for document discovery and knowledge mining.

Choose this option if you want to go deeper on document search, enrichment, and enterprise knowledge mining scenarios.

### Chat With Your Data Solution Accelerator

Original repo: https://github.com/Azure-Samples/chat-with-your-data-solution-accelerator

This accelerator focuses on building a chat experience over private data using retrieval-augmented generation. It is the best follow-on option for learners who want to extend the RAG concepts from Lab 04 into a richer application pattern.

It covers:

- Ingesting and indexing private data for retrieval.
- Using Azure OpenAI with retrieval-augmented generation.
- Building a chat interface grounded in your own content.
- Reference patterns for enterprise chat, search, and answer generation.

Choose this option if you are most interested in RAG applications, chat experiences, and grounding generative AI responses in enterprise data.

## Suggested Lab Flow

1. Review all four accelerator options above.
2. Choose the accelerator that best matches your use case.
3. Open the original repository link for that accelerator.
4. Read the repository overview, architecture, prerequisites, and deployment instructions.
5. Decide whether to perform an architecture review only or deploy the solution in Azure.
6. Capture what services the accelerator uses and how it extends the concepts from the earlier labs.

## Discussion Prompts

- Which Azure AI services does the accelerator use?
- What problem does the accelerator solve beyond the smaller lab exercises?
- What data types does it handle: documents, conversations, mixed content, or private knowledge bases?
- What would need to change before using it with your own data?
- Which parts of the architecture would you keep, simplify, or replace for your organization?
