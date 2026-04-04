# Usage

Once connected, Claude has access to four tools. A typical workflow looks like this:

```
# 1. Upload a ZIP of documents
upload("/Users/alice/tender_docs.zip")   → kb_id

# 2. Build the knowledge base (takes a few minutes)
analyse(kb_id)

# 3. Ask questions
chat(kb_id, "What is the submission deadline?")
```

## Tools

### `upload(file_path)` → `kb_id`

Uploads a ZIP archive from an absolute local path to Ailtir storage and returns a
`kb_id`.

### `analyse(kb_id)` → `status`

Triggers the ingestion pipeline — unzips the archive and builds an AWS Bedrock
knowledge base. Takes a few minutes.

### `list()` → `string`

Lists all knowledge bases in your account, showing name, `kb_id`, and status.

### `chat(kb_id, question)` → `answer`

Answers a natural-language question using the documents in the given knowledge base
(RAG via AWS Bedrock).
