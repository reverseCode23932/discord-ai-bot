# Install NVIDIA CUDA libraries for faster-whisper (RTX 4060 etc.) on Windows.
# Run from project root with your bot venv activated:
#   .\.venv\Scripts\activate
#   .\scripts\install-gpu-stt.ps1

$ErrorActionPreference = "Stop"

Write-Host "Installing GPU STT dependencies (nvidia-cublas-cu12, nvidia-cudnn-cu12)..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

Write-Host "Verifying CUDA..." -ForegroundColor Cyan
python -c @"
from pathlib import Path
import os, site, wave, struct, tempfile

for sp in site.getsitepackages():
    nvidia = Path(sp) / 'nvidia'
    if nvidia.is_dir():
        for sub in nvidia.iterdir():
            b = sub / 'bin'
            if b.is_dir():
                os.add_dll_directory(str(b))
        break

os.environ['PATH'] = ';'.join(
    str(p / 'bin') for p in nvidia.iterdir() if (p / 'bin').is_dir()
) + ';' + os.environ.get('PATH', '')

import ctranslate2
print('ctranslate2', ctranslate2.__version__, 'CUDA devices:', ctranslate2.get_cuda_device_count())

from faster_whisper import WhisperModel
path = os.path.join(tempfile.gettempdir(), 'whisper_cuda_test.wav')
with wave.open(path, 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(struct.pack('<h', 0) * 16000)

m = WhisperModel('tiny', device='cuda', compute_type='float16')
list(m.transcribe(path))
print('CUDA Whisper OK')
"@

Write-Host ""
Write-Host "Add to .env:" -ForegroundColor Green
Write-Host "  WHISPER_DEVICE=cuda"
Write-Host "  WHISPER_COMPUTE_TYPE=float16"
Write-Host "  WHISPER_LOCAL_MODEL=small"
