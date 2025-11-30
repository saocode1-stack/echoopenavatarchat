from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import time, json, uuid, asyncio

app = FastAPI()

def build_response(content: str):
    now = int(time.time())
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": now,
        "model": "echo-001",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    stream = body.get("stream", False)

    user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_text = m.get("content", "")
            break
    if not user_text:
        user_text = "..."

    if not stream:
        return JSONResponse(build_response(user_text))

    async def gen():
        now = int(time.time())
        cid = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        yield "data: " + json.dumps({
            "id": cid,
            "object": "chat.completion.chunk",
            "created": now,
            "model": "echo-001",
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }) + "\n\n"
        yield "data: " + json.dumps({
            "id": cid,
            "object": "chat.completion.chunk",
            "created": now,
            "model": "echo-001",
            "choices": [{"index": 0, "delta": {"content": user_text}, "finish_reason": None}]
        }) + "\n\n"
        yield "data: " + json.dumps({
            "id": cid,
            "object": "chat.completion.chunk",
            "created": now,
            "model": "echo-001",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }) + "\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
