Due to the usage of ollama key 

Run these in cmd prompt 

# 1. Download & install Ollama from https://ollama.com/download

# 2. Start Ollama (it runs in the background)
ollama serve

# 3. Pull a model (do this once - it downloads ~4GB)
ollama pull llama3

then run your program



If you need faster model there are other options also 

# Smaller & faster (needs ~2GB RAM):
OLLAMA_MODEL = "gemma2:2b"

# Good balance (needs ~4GB RAM):
OLLAMA_MODEL = "llama3"

# Best for code analysis (needs ~4GB RAM):
OLLAMA_MODEL = "codellama"
