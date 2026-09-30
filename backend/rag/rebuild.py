"""Build and verify a fresh collection, then atomically activate it. Never delete."""
import json
import os
import uuid
from config import CHROMA_PATH, DATA_ROOT
from rag.ingest import RAGIngestor

def rebuild():
    name = 'reliance_knowledge_' + uuid.uuid4().hex[:12]
    old = os.environ.get('REBUILD_COLLECTION')
    os.environ['REBUILD_COLLECTION'] = name
    try:
        ingestor = RAGIngestor()
        paths = [DATA_ROOT / name for name in ('product_manuals','warranty_policies','faqs','troubleshooting','service_guides','images')]
        totals = ingestor.ingest_paths(paths)
        expected = totals['text_chunks'] + totals['images']
        count = ingestor.collection.count()
        if count != expected or count == 0:
            raise RuntimeError('Index count verification failed')
        vector = ingestor.gemini.embed_text('P002 Daikin AC warranty')
        result = ingestor.collection.query(query_embeddings=[vector], n_results=min(count, 3))
        if not result['documents'][0]:
            raise RuntimeError('Index retrieval verification failed')
        temp = CHROMA_PATH / ('active_collection.' + uuid.uuid4().hex + '.tmp')
        temp.write_text(name, encoding='utf-8')
        temp.replace(CHROMA_PATH / 'active_collection.txt')
        report = {'collection': name, 'verified_count': count, **totals}
        (CHROMA_PATH / 'rebuild_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    finally:
        if old is None:
            os.environ.pop('REBUILD_COLLECTION', None)
        else:
            os.environ['REBUILD_COLLECTION'] = old

if __name__ == '__main__':
    try:
        rebuild()
    except Exception as exc:
        print(f'Rebuild failed ({type(exc).__name__}); active collection preserved. Check Google API credentials and quota.')
        raise SystemExit(1)
