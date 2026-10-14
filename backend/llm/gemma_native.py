"""Google-hosted Gemma transport: exclude thoughts from answers, retain usage."""
import re

import httpx


def request_body(messages, max_tokens=1800, json_output=False):
    contents, instructions = [], []
    for message in messages:
        if isinstance(message, dict):
            role, content = message.get('role'), message.get('content', '')
        else:
            role, content = message.type, message.content
        if not isinstance(content, str):
            raise ValueError('Gemma text transport expects text messages.')
        if role in ('system', 'developer'):
            instructions.append(content)
        elif role in ('human', 'user', 'ai', 'assistant'):
            contents.append({'role': 'model' if role in ('ai', 'assistant') else 'user', 'parts':[{'text':content}]})
        else:
            raise ValueError('Unsupported message role for Gemma text transport.')
    body={'contents':contents,'generationConfig':{'temperature':0,'maxOutputTokens':max_tokens,'thinkingConfig':{'thinkingLevel':'minimal'}}}
    if instructions:
        body['systemInstruction']={'parts':[{'text':'\n\n'.join(instructions)}]}
    if json_output:
        body['generationConfig']['responseMimeType']='application/json'
    return body


def adapt_response(data, model):
    candidates=data.get('candidates') or []
    if not candidates:
        raise ValueError('Gemma returned no answer candidate.')
    candidate=candidates[0]
    text=''.join(p.get('text','') for p in candidate.get('content',{}).get('parts',[]) if not p.get('thought'))
    finish={'STOP':'stop','MAX_TOKENS':'length'}.get(candidate.get('finishReason'),'content_filter')
    return {'model':model,'choices':[{'finish_reason':finish,'message':{'role':'assistant','content':text}}], 'usageMetadata':data.get('usageMetadata',{})}


async def completion(model, messages, key, timeout=60, max_tokens=1800, json_output=False):
    model=model.removeprefix('models/')
    if not re.fullmatch(r'gemma-[a-z0-9-]+', model):
        raise ValueError('Invalid Gemma model ID.')
    url='https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent'
    async with httpx.AsyncClient(timeout=timeout,trust_env=False) as client:
        response=await client.post(url,headers={'x-goog-api-key':key},json=request_body(messages,max_tokens,json_output))
        response.raise_for_status()
    return adapt_response(response.json(),model)


class GemmaNative:
    def __init__(self, model, key, timeout):
        self.model, self.key, self.timeout = model, key, timeout

    async def ainvoke(self, messages):
        from types import SimpleNamespace
        data = await completion(self.model, messages, self.key, self.timeout)
        choice = data['choices'][0]
        if choice['finish_reason'] != 'stop' or not choice['message']['content'].strip():
            raise ValueError('Gemma did not return a complete answer.')
        usage = data.get('usageMetadata', {})
        return SimpleNamespace(content=choice['message']['content'], response_metadata={'token_usage': {'prompt_tokens':usage.get('promptTokenCount'), 'completion_tokens':usage.get('candidatesTokenCount',0), 'total_tokens':usage.get('totalTokenCount')}})
