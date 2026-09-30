"""Live FastAPI tests against localhost. Reports factual checks, never secrets."""
import json
import re
from pathlib import Path
import httpx

def run():
    base = 'http://127.0.0.1:8000'
    cases = [
        ('price', {'message':'What is the exact demo price and warranty of P001? Answer briefly.'}, 'sales_agent', '129,999'),
        ('ticket', {'message':'What is the status of SR-1001? Answer in one sentence.'}, 'resq_agent', 'progress'),
        ('order', {'message':'Track ORD-9001. Answer in one sentence.', 'provider':'claude'}, 'sales_agent', 'delivered'),
        ('rag', {'message':'According to the knowledge base, what is the demo warranty of Daikin AC P002? Answer briefly.'}, 'rag_agent', '60'),
    ]
    report = {'health': httpx.get(base+'/health', timeout=10).json(), 'cases': []}
    for name, payload, agent, fact in cases:
        with httpx.Client(timeout=200) as client:
            response = client.post(base+'/chat/stream', json=payload)
        events = []
        for frame in response.text.split('\n\n'):
            lines = frame.splitlines()
            event = next((l[7:] for l in lines if l.startswith('event: ')), '')
            data = next((l[6:] for l in lines if l.startswith('data: ')), '')
            if data:
                events.append((event, json.loads(data)))
        text = ''.join(d['text'] for e,d in events if e == 'token')
        done = next((d for e,d in events if e == 'done'), {})
        meta = [d for e,d in events if e == 'meta']
        passed = bool(done.get('ok')) and done.get('agent') == agent and fact in text.lower() and not re.search(r'[A-Za-z]:[\\/]|reliance-data|\[\d+\]', text)
        report['cases'].append({'name':name,'passed':passed,'provider':done.get('provider'),'agent':done.get('agent'),'retrieval_mode':next((m.get('retrieval_mode') for m in meta if m.get('retrieval_mode')),None),'answer':text})
        print(f'{name}: {"PASS" if passed else "FAIL"}, provider={done.get("provider")}', flush=True)
    Path('smoke-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return all(c['passed'] for c in report['cases'])

if __name__ == '__main__':
    raise SystemExit(0 if run() else 1)
