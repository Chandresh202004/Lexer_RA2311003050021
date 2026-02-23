import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Lexer_no_ai import Lexer  # reuse your lexer

app = FastAPI(title="Lexer Simulator (no AI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SourceRequest(BaseModel):
    source: str

def tokens_to_dict(tokens):
    return [
        {"type": t.type, "value": t.value, "line": t.line, "column": t.column}
        for t in tokens
    ]

@app.post("/api/tokenize")
def tokenize(req: SourceRequest):
    lexer = Lexer(req.source)
    tokens = lexer.tokenize()
    return {
        "tokens": tokens_to_dict(tokens),
        "errors": [],  # Lexer_no_ai currently doesn’t emit errors; extend if needed
    }
