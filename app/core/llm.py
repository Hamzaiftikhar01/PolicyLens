import requests
import json
import time
import re
from typing import Dict, Any, List
import config

# Version-controlled prompt system
PROMPT_VERSION = "1.0.0"
SYSTEM_INSTRUCTION = """You are PolicyLens, an authoritative AI legal assistant representing the Pakistani Legal & Policy database.
You must answer the user's question using ONLY the provided document sources.

Strictly adhere to the following rules:
1. Answer the question using ONLY the retrieved passages provided in the context.
2. If the context does not contain relevant information to answer, state: "I couldn't find sufficient evidence in the available documents to answer this question."
3. Every factual statement or legal provision in your response must be cited. Cite the source by placing the bracketed source index (e.g. [Source 1], [Source 2]) at the end of the sentence or clause it supports. Do not use generic citations.
4. Do not invent article numbers, section numbers, or legal provisions. Only mention what is explicitly written in the sources.
5. If the sources contain conflicting provisions (e.g. differing penalties or procedures), clearly present both sides and cite the respective sources. Do not silently select one.
6. Clearly distinguish between direct facts in the source and your legal interpretation.
7. Keep your answer concise, direct, and authoritative.
8. NEVER claim that your response constitutes legal advice. Always add a small note that PolicyLens is an AI research tool.
"""

class BaseLLM:
    def generate(self, prompt: str, context_str: str) -> Dict[str, Any]:
        raise NotImplementedError


class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Gemini API key is required.")

    def generate(self, prompt: str, context_str: str) -> Dict[str, Any]:
        model_name = config.LLM_MODELS.get("gemini", "gemini-3.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        full_prompt = f"CONTEXT INFORMATION:\n{context_str}\n\nUSER QUESTION:\n{prompt}\n\nRemember to answer only from context and cite using [Source X] format."
        
        data = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {"parts": [{"text": full_prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 1024
            }
        }
        
        for attempt in range(3):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                res_json = response.json()
                
                candidate = res_json["candidates"][0]
                text = candidate["content"]["parts"][0]["text"]
                usage = res_json.get("usageMetadata", {})
                
                prompt_tokens = usage.get("promptTokenCount", 0)
                completion_tokens = usage.get("candidatesTokenCount", 0)
                
                # Estimate cost
                cost = (prompt_tokens / 1_000_000 * config.PRICING.get(model_name, {"input": 0.075})["input"]) + \
                       (completion_tokens / 1_000_000 * config.PRICING.get(model_name, {"output": 0.30})["output"])
                       
                return {
                    "text": text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost": cost,
                    "provider": "gemini",
                    "model": model_name
                }
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f"Gemini LLM API call failed: {e}")
                time.sleep(2 ** attempt)


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required.")

    def generate(self, prompt: str, context_str: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        full_prompt = f"CONTEXT INFORMATION:\n{context_str}\n\nUSER QUESTION:\n{prompt}\n\nRemember to answer only from context and cite using [Source X] format."
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 1024
        }
        
        for attempt in range(3):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                res_json = response.json()
                
                text = res_json["choices"][0]["message"]["content"]
                usage = res_json.get("usage", {})
                
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                
                # Estimate cost
                cost = (prompt_tokens / 1_000_000 * config.PRICING["gpt-4o-mini"]["input"]) + \
                       (completion_tokens / 1_000_000 * config.PRICING["gpt-4o-mini"]["output"])
                       
                return {
                    "text": text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost": cost,
                    "provider": "openai",
                    "model": "gpt-4o-mini"
                }
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f"OpenAI LLM API call failed: {e}")
                time.sleep(2 ** attempt)


class LocalFallbackLLM(BaseLLM):
    """
    A smart local fallback generator. Uses keyword matching to synthesize
    a grounded answer from retrieved context when no API key is set.
    """
    def generate(self, prompt: str, context_str: str) -> Dict[str, Any]:
        # Context is passed as a string but we can analyze the lines
        lines = context_str.split("\n")
        sources = []
        current_source = None
        
        for line in lines:
            if line.startswith("[Source "):
                current_source = line.strip()
                sources.append({"id": current_source, "text": []})
            elif current_source and line.strip() and not line.startswith("Document:") and not line.startswith("Section:") and not line.startswith("Page:"):
                sources[-1]["text"].append(line.strip())
                
        # Clean text
        for s in sources:
            s["content"] = " ".join(s["text"])
            
        # Match keywords from prompt
        keywords = [w.lower() for w in prompt.split() if len(w) > 4]
        matched_sentences = []
        cited_sources = set()
        
        for s in sources:
            content = s["content"]
            sentences = re.split(r'(?<=[.!?])\s+', content)
            for sentence in sentences:
                if any(kw in sentence.lower() for kw in keywords):
                    # Find which source index
                    s_idx = s["id"]
                    matched_sentences.append(f"{sentence} {s_idx}")
                    cited_sources.add(s_idx)
                    
        if matched_sentences:
            text = "[LOCAL FALLBACK - NO API KEY] " + " ".join(matched_sentences)
        else:
            text = "[LOCAL FALLBACK - NO API KEY] I couldn't find sufficient evidence in the available documents to answer this question."
            
        # Estimate mock tokens
        prompt_words = len(prompt.split()) + len(context_str.split())
        completion_words = len(text.split())
        
        prompt_tokens = int(prompt_words * 1.3)
        completion_tokens = int(completion_words * 1.3)
        
        return {
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": 0.0,
            "provider": "local",
            "model": "fallback-keyword"
        }


def get_llm(provider: str = None, api_key: str = None) -> BaseLLM:
    """
    Factory function to get an LLM client.
    """
    if not provider:
        provider = config.DEFAULT_LLM_PROVIDER
        
    provider = provider.lower()
    
    if provider == "gemini":
        key = api_key or config.GEMINI_API_KEY
        if key:
            return GeminiLLM(key)
    elif provider == "openai":
        key = api_key or config.OPENAI_API_KEY
        if key:
            return OpenAILLM(key)
            
    # Fallback to local offline generator
    return LocalFallbackLLM()
