# Doc QA Agent

An agent that answers natural language questions about a folder of documents by retrieving the most relevant passages and grounding its answer strictly in that retrieved content — no general-knowledge guessing.

This template demonstrates retrieval-augmented answering without any external infrastructure: chunking and relevance scoring are done with plain keyword overlap (no embeddings, no vector database), so the whole thing runs with zero extra setup.

## What it does

Given a folder of `.txt`/`.pdf` files and a question, the agent:

1. Calls `list_documents` to see what's available in the target folder.
2. Calls `retrieve_chunks` with a search query derived from the question to pull the most relevant passages.
3. Issues a follow-up `retrieve_chunks` call with a refined query if the first pass doesn't clearly cover the question.
4. Answers using only the retrieved chunks, citing the source document for each claim, or says explicitly that the documents don't contain an answer.

## Prerequisites

- Python 3.10 or later
- An Anthropic API key

## Setup

```bash
cd templates/doc-qa-agent
pip install -r ../../requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Run

```bash
python agent.py --docs examples/docs "What is the refund policy?"
```

Ask a different question against the same sample documents:

```bash
python agent.py --docs examples/docs "Do you offer annual billing?"
python agent.py --docs examples/docs --model claude-haiku-4-5 "What happens if a payment fails?"
```

The sample folder (`examples/docs/`) contains a billing FAQ and a terms-of-service document.

## Sample output

Question: `What is the refund policy?`

```
Tool: list_documents
Documents found: 2
Tool: retrieve_chunks (query: "refund policy")
Chunks retrieved: 4
```

Answer:

> Based on the retrieved documents, here is the refund policy:
>
> According to **terms-of-service.txt**:
>
> 1. **Annual plans**: May be refunded in full within **30 days** of purchase.
> 2. **Monthly plans**: May be refunded within **14 days** of purchase.
> 3. **How to request a refund**: Refund requests must be sent to **support@example.com** and are processed within **5 business days**.
> 4. **After the refund window**: Subscriptions are **non-refundable**, but can be cancelled to stop future billing.
> 5. **Cancellation note**: Cancellation takes effect at the end of the current billing period, and there is no partial-period refund outside the refund windows mentioned above.

Completed in 2 iterations — the agent listed the documents, retrieved chunks for "refund policy," found terms-of-service.txt clearly covered the question, and answered directly from that content without needing a follow-up query.

## Adapting to real data sources

To scale beyond keyword scoring, replace `retrieve_chunks` in `tools.py` with a real vector search (e.g., embeddings + a vector DB like Chroma, Pinecone, or pgvector). The agent logic in `agent.py` does not need to change — it only expects a list of `{source, text}` chunks back.

## Files

```
doc-qa-agent/
  agent.py                      main agent loop: list documents, retrieve, answer
  tools.py                      configure_docs, list_documents, retrieve_chunks (keyword-overlap scoring)
  examples/
    docs/
      billing-faq.txt           sample billing FAQ
      terms-of-service.txt      sample terms of service
  README.md
```
