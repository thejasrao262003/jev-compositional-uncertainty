"""open-Jev inference on Modal: next-token label probabilities from an
open-weight instruct model. Pre-registration:
research/methodology/openjev_crossmodel_preregistration.md

Each request is (chat messages, list of allowed labels). The function returns,
for each request, the model's next-token probability of each label at the
answer position (leading-space and case variants summed), renormalized over
the allowed labels. Deterministic; no sampling.

Deploy-free use from Python:  modal.Cls.from_name / app.run via client.py
"""

import modal

APP_NAME = "openjev"
app = modal.App(APP_NAME)
image = (modal.Image.debian_slim(python_version="3.11")
         .pip_install("torch==2.4.1", "transformers==4.46.3", "accelerate==1.1.1", "sentencepiece", "protobuf")
         .env({"HF_HOME": "/cache", "TOKENIZERS_PARALLELISM": "false"}))
cache = modal.Volume.from_name("openjev-hf-cache", create_if_missing=True)
# OLMo-2 needs transformers >= 4.47 (pre-registration deviation, disclosed in Amendment 2);
# all other models run on the image above, unchanged.
image_t447 = (modal.Image.debian_slim(python_version="3.11")
              .pip_install("torch==2.4.1", "transformers==4.47.1", "accelerate==1.1.1", "sentencepiece", "protobuf")
              .env({"HF_HOME": "/cache", "TOKENIZERS_PARALLELISM": "false"}))


@app.cls(image=image, gpu="A10G", volumes={"/cache": cache}, timeout=3600, scaledown_window=120)
class OpenJev:
    model_id: str = modal.parameter()

    @modal.enter()
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=False)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, torch_dtype=torch.bfloat16,
                                                          device_map="cuda", trust_remote_code=False)
        self.model.eval()
        cache.commit()

    def _label_ids(self, label: str) -> list:
        ids = set()
        variants = {label, " " + label}
        if len(label) > 1:  # case variants only for word labels (Yes/No); never for "A"/"B" (the article "a")
            variants |= {label.lower(), " " + label.lower(), label.upper(), " " + label.upper()}
        for v in variants:
            enc = self.tok.encode(v, add_special_tokens=False)
            if enc:
                ids.add(enc[0])
        return sorted(ids)

    @modal.method()
    def distributions(self, requests: list, batch_size: int = 4) -> list:
        torch = self.torch
        out = []
        for s in range(0, len(requests), batch_size):
            chunk = requests[s:s + batch_size]
            texts = [self.tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True)
                     for r in chunk]
            enc = self.tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
            with torch.no_grad():
                # Output layer on the final position only (full-sequence logits over a
                # ~150k vocabulary exhaust GPU memory). Same values as model(...).logits[:, -1].
                hidden = self.model.model(**enc).last_hidden_state[:, -1, :]
                logits = self.model.lm_head(hidden).float()
            probs = torch.softmax(logits, dim=-1)
            for r, p in zip(chunk, probs):
                mass = {lab: float(sum(p[i] for i in self._label_ids(lab))) for lab in r["labels"]}
                tot = sum(mass.values())
                out.append({"probs": {k: v / tot for k, v in mass.items()} if tot > 0 else
                            {k: 1 / len(mass) for k in mass},
                            "label_mass": tot})
        return out


@app.cls(image=image_t447, gpu="A10G", volumes={"/cache": cache}, timeout=3600, scaledown_window=120)
class OpenJevT447:
    model_id: str = modal.parameter()

    @modal.enter()
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=False)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, torch_dtype=torch.bfloat16,
                                                          device_map="cuda", trust_remote_code=False)
        self.model.eval()
        cache.commit()

    def _label_ids(self, label: str) -> list:
        ids = set()
        variants = {label, " " + label}
        if len(label) > 1:  # case variants only for word labels (Yes/No); never for "A"/"B" (the article "a")
            variants |= {label.lower(), " " + label.lower(), label.upper(), " " + label.upper()}
        for v in variants:
            enc = self.tok.encode(v, add_special_tokens=False)
            if enc:
                ids.add(enc[0])
        return sorted(ids)

    @modal.method()
    def distributions(self, requests: list, batch_size: int = 4) -> list:
        torch = self.torch
        out = []
        for s in range(0, len(requests), batch_size):
            chunk = requests[s:s + batch_size]
            texts = [self.tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True)
                     for r in chunk]
            enc = self.tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
            with torch.no_grad():
                # Output layer on the final position only (full-sequence logits over a
                # ~150k vocabulary exhaust GPU memory). Same values as model(...).logits[:, -1].
                hidden = self.model.model(**enc).last_hidden_state[:, -1, :]
                logits = self.model.lm_head(hidden).float()
            probs = torch.softmax(logits, dim=-1)
            for r, p in zip(chunk, probs):
                mass = {lab: float(sum(p[i] for i in self._label_ids(lab))) for lab in r["labels"]}
                tot = sum(mass.values())
                out.append({"probs": {k: v / tot for k, v in mass.items()} if tot > 0 else
                            {k: 1 / len(mass) for k in mass},
                            "label_mass": tot})
        return out
