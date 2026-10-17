"""Serve OpenJev (https://huggingface.co/openjev/openjev) on Modal exactly as its
authors specify (serve/SERVE.md): vLLM 0.29.0 on one H100 with online FP8 and
the documented flags, plus their helper shim (vendored unmodified, sha256
verified at startup) with the documented readout settings. The class answers
batches of Jev-format request bodies {state, model, questions} via the shim's
/v1/systemone endpoint, all inside the container.

Pre-registration: research/methodology/openjev_crossmodel_preregistration.md (Amendment 1)

  .venv/bin/modal run research/src/openjev/modal_openjev.py::download   # once, weights to a volume
  .venv/bin/modal deploy research/src/openjev/modal_openjev.py
"""
import hashlib
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import modal

SHIM_SHA = "81a22f1b1b8912a465059207ef9f60b7c6c16b4de6372305d867efbe38a1987a"
REPO = os.environ.get("OPENJEV_REPO", "openjev/openjev")
WEIGHTS = "/weights/" + REPO.split("/")[-1]

app = modal.App("openjev-serve")
weights = modal.Volume.from_name("openjev-weights", create_if_missing=True)
image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("vllm==0.29.0", "transformers==5.17.0", "openai==3.16.2", "httpx==0.28.1", "huggingface_hub")
         .add_local_file(Path(__file__).parent / "vendor" / "openjev_shim.py", "/opt/shim.py"))


@app.function(image=image, volumes={"/weights": weights}, timeout=7200)
def download(repo: str = REPO):
    from huggingface_hub import snapshot_download
    snapshot_download(repo, local_dir="/weights/" + repo.split("/")[-1])
    weights.commit()
    return sorted(os.listdir("/weights/" + repo.split("/")[-1]))


def _wait(url, timeout_s):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            urllib.request.urlopen(url, timeout=5)
            return
        except Exception:
            time.sleep(3)
    raise RuntimeError(f"timed out waiting for {url}")


@app.cls(image=image, gpu="H100", volumes={"/weights": weights}, timeout=7200, scaledown_window=600)
class OpenJevServer:
    @modal.enter()
    def start(self):
        if hashlib.sha256(Path("/opt/shim.py").read_bytes()).hexdigest() != SHIM_SHA:
            raise RuntimeError("shim hash mismatch; refusing to serve")
        # vLLM, documented flags (SERVE.md step 2), loopback only
        self.vllm = subprocess.Popen(
            ["vllm", "serve", WEIGHTS, "--host", "127.0.0.1", "--served-model-name", "qwen", "--port", "8000",
             "--enable-prefix-caching", "--max-model-len", "16384", "--gpu-memory-utilization", "0.90",
             "--limit-mm-per-prompt", '{"image":1}', "--trust-remote-code", "--max-num-seqs", "256",
             "--max-logprobs", "64", "--gdn-prefill-backend", "triton", "--quantization", "fp8"])
        _wait("http://127.0.0.1:8000/health", 1800)
        # helper, documented settings (SERVE.md step 3), loopback only
        env = {**os.environ, "VLLM": "http://localhost:8000/v1", "TOKENIZER": WEIGHTS, "READOUT_T": "0.85",
               "READOUT_NOUL_T": "1.829074", "READOUT_NOUL_BIAS": "0", "READOUT_TARGETED": "1",
               "READOUT_INSTR_STYLE": "pyrepr", "SHIM_STAGGER": "1"}
        self.shim = subprocess.Popen(["python", "/opt/shim.py", "--host", "127.0.0.1", "--port", "3000"], env=env)
        _wait("http://127.0.0.1:3000/v1/version", 300)

    @modal.method()
    def ask_many(self, bodies: list) -> list:
        from concurrent.futures import ThreadPoolExecutor

        def one(body):
            req = urllib.request.Request("http://127.0.0.1:3000/v1/systemone", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    return {"http_status": r.status, "json": json.loads(r.read()), "latency_ms": (time.time() - t0) * 1000}
            except urllib.error.HTTPError as e:
                return {"http_status": e.code, "json": None, "error": e.read().decode()[:500]}
            except Exception as e:  # noqa: BLE001
                return {"http_status": None, "json": None, "error": repr(e)[:500]}
        with ThreadPoolExecutor(max_workers=16) as pool:
            return list(pool.map(one, bodies))

    @modal.method()
    def version(self) -> dict:
        with urllib.request.urlopen("http://127.0.0.1:3000/v1/version", timeout=30) as r:
            return json.loads(r.read())
