"""Small live connectivity checks; never print credentials or raw provider exceptions."""
import asyncio
import json
from config import key_present
from llm.factory import get_chat_model, text_content
from rag.multimodal import GeminiMultimodal
from langchain_core.messages import HumanMessage

async def main():
    report = {}
    for provider, key in [('claude','ANTHROPIC_API_KEY'),('chatgpt','OPENAI_API_KEY'),('ollama',None)]:
        if key and not key_present(key):
            report[provider] = {'status':'missing_key'}
            continue
        try:
            result = await asyncio.wait_for(get_chat_model(provider).ainvoke([HumanMessage(content='Reply only OK.')]), timeout=95)
            report[provider] = {'status':'ok' if text_content(result.content).strip() else 'empty'}
        except Exception as exc:
            report[provider] = {'status':'failed','error_type':type(exc).__name__}
    if key_present('GOOGLE_API_KEY'):
        try:
            vector = await asyncio.to_thread(GeminiMultimodal().embed_text, 'Connectivity test')
            report['google_embeddings'] = {'status':'ok','dimensions':len(vector)}
        except Exception as exc:
            report['google_embeddings'] = {'status':'failed','error_type':type(exc).__name__, 'code':getattr(exc,'code',None)}
    else:
        report['google_embeddings'] = {'status':'missing_key'}
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
