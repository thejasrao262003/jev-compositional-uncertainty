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

    def _plan(self, text: str, labels: list) -> tuple:
        """Context ids and one distinguishing token per label. Each label is
        tokenized after the prompt; any prefix ALL labels share (e.g. a
        SentencePiece word-start piece) is appended to the context, and the
        label's probability is read at the first token where labels differ."""
        base = self.tok(text, add_special_tokens=False)["input_ids"]
        seqs, ctx0 = {}, None
        for lab in labels:
            full = self.tok(text + lab, add_special_tokens=False)["input_ids"]
            k = 0
            while k < min(len(base), len(full)) and base[k] == full[k]:
                k += 1
            if ctx0 is None:
                ctx0 = full[:k]
            elif full[:k] != ctx0:
                raise ValueError("labels re-tokenize the prompt differently")
            seqs[lab] = full[k:]
        c = 0
        while all(len(v) > c for v in seqs.values()) and len({v[c] for v in seqs.values()}) == 1:
            c += 1
        shared = next(iter(seqs.values()))[:c]
        dist = {lab: v[c] for lab, v in seqs.items()}
        if len(set(dist.values())) != len(dist):
            raise ValueError(f"labels share a distinguishing token: {dist}")
        return ctx0 + shared, dist, len(shared)

    @modal.method()
    def distributions(self, requests: list, batch_size: int = 4) -> list:
        torch = self.torch
        out = []
        pad = self.tok.pad_token_id
        for s in range(0, len(requests), batch_size):
            chunk = requests[s:s + batch_size]
            texts = [self.tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True)
                     for r in chunk]
            plans = [self._plan(t, r["labels"]) for t, r in zip(texts, chunk)]
            L = max(len(p[0]) for p in plans)
            ids = torch.tensor([[pad] * (L - len(p[0])) + p[0] for p in plans], device="cuda")
            att = torch.tensor([[0] * (L - len(p[0])) + [1] * len(p[0]) for p in plans], device="cuda")
            with torch.no_grad():
                # Output layer on the final position only (memory); same values as logits[:, -1].
                hidden = self.model.model(input_ids=ids, attention_mask=att).last_hidden_state[:, -1, :]
                probs = torch.softmax(self.model.lm_head(hidden).float(), dim=-1)
            for (ctx, dist, n_shared), p in zip(plans, probs):
                mass = {lab: float(p[t]) for lab, t in dist.items()}
                tot = sum(mass.values())
                out.append({"probs": {k: v / tot for k, v in mass.items()} if tot > 0 else
                            {k: 1 / len(mass) for k in mass},
                            "label_mass": tot, "shared_prefix_tokens": n_shared})
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

    def _plan(self, text: str, labels: list) -> tuple:
        """Context ids and one distinguishing token per label. Each label is
        tokenized after the prompt; any prefix ALL labels share (e.g. a
        SentencePiece word-start piece) is appended to the context, and the
        label's probability is read at the first token where labels differ."""
        base = self.tok(text, add_special_tokens=False)["input_ids"]
        seqs, ctx0 = {}, None
        for lab in labels:
            full = self.tok(text + lab, add_special_tokens=False)["input_ids"]
            k = 0
            while k < min(len(base), len(full)) and base[k] == full[k]:
                k += 1
            if ctx0 is None:
                ctx0 = full[:k]
            elif full[:k] != ctx0:
                raise ValueError("labels re-tokenize the prompt differently")
            seqs[lab] = full[k:]
        c = 0
        while all(len(v) > c for v in seqs.values()) and len({v[c] for v in seqs.values()}) == 1:
            c += 1
        shared = next(iter(seqs.values()))[:c]
        dist = {lab: v[c] for lab, v in seqs.items()}
        if len(set(dist.values())) != len(dist):
            raise ValueError(f"labels share a distinguishing token: {dist}")
        return ctx0 + shared, dist, len(shared)

    @modal.method()
    def distributions(self, requests: list, batch_size: int = 4) -> list:
        torch = self.torch
        out = []
        pad = self.tok.pad_token_id
        for s in range(0, len(requests), batch_size):
            chunk = requests[s:s + batch_size]
            texts = [self.tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True)
                     for r in chunk]
            plans = [self._plan(t, r["labels"]) for t, r in zip(texts, chunk)]
            L = max(len(p[0]) for p in plans)
            ids = torch.tensor([[pad] * (L - len(p[0])) + p[0] for p in plans], device="cuda")
            att = torch.tensor([[0] * (L - len(p[0])) + [1] * len(p[0]) for p in plans], device="cuda")
            with torch.no_grad():
                # Output layer on the final position only (memory); same values as logits[:, -1].
                hidden = self.model.model(input_ids=ids, attention_mask=att).last_hidden_state[:, -1, :]
                probs = torch.softmax(self.model.lm_head(hidden).float(), dim=-1)
            for (ctx, dist, n_shared), p in zip(plans, probs):
                mass = {lab: float(p[t]) for lab, t in dist.items()}
                tot = sum(mass.values())
                out.append({"probs": {k: v / tot for k, v in mass.items()} if tot > 0 else
                            {k: 1 / len(mass) for k in mass},
                            "label_mass": tot, "shared_prefix_tokens": n_shared})
        return out
