import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GenAI API", version="1.0.0")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


class GenerateRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("prompt must not be empty")
        if len(v) > 4096:
            raise ValueError("prompt must not exceed 4096 characters")
        return v


class GenerateResponse(BaseModel):
    response: str


def mock_llm(prompt: str) -> str:
    """Return a mock response for demonstration purposes."""
    return f"[Mock LLM] You asked: '{prompt}'. This is a placeholder response."


def real_llm(prompt: str) -> str:
    """Call OpenAI API if key is provided."""
    try:
        import openai  # type: ignore
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        return completion.choices[0].message.content or ""
    except Exception as exc:
        logger.error("OpenAI call failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM backend error") from exc


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    logger.info("Received /generate request")
    if OPENAI_API_KEY:
        text = real_llm(request.prompt)
    else:
        text = mock_llm(request.prompt)
    return GenerateResponse(response=text)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
