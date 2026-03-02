from celery import shared_task


@shared_task(name="contracts.ingest_placeholder")
def ingest_placeholder(contract_id: str) -> dict:
    """
    Placeholder for the ingestion pipeline:
    - fetch file from object storage
    - extract text (and OCR fallback)
    - chunk
    - embeddings
    - term extraction
    """
    return {"contract_id": contract_id, "status": "queued_placeholder"}