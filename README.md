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

or run this in powershell

# --- STEP 1: Download Ollama ---
Write-Host "Downloading Ollama..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "$env:USERPROFILE\Downloads\OllamaSetup.exe"
Write-Host "Download complete!" -ForegroundColor Green

# --- STEP 2: Install Ollama ---
Write-Host "Installing Ollama..." -ForegroundColor Cyan
Start-Process "$env:USERPROFILE\Downloads\OllamaSetup.exe" -Wait
Write-Host "Installation complete!" -ForegroundColor Green

# --- STEP 3: Refresh PATH so 'ollama' is recognized ---
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# --- STEP 4: Verify ---
Write-Host "Verifying installation..." -ForegroundColor Cyan
ollama --version

# --- STEP 5: Pull model ---
Write-Host "Pulling llama3 model (this may take a few minutes)..." -ForegroundColor Cyan
ollama pull llama3
Write-Host "All done! You can now run: python ll.py" -ForegroundColor Green
