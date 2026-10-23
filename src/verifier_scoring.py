from __future__ import annotations
import torch
MAX_LENGTH=2048
NO_ID, YES_ID=3,209
DOC_CHAR_BUDGET=(MAX_LENGTH-256)*4
def minicheck_evidence_texts(row):
    out = []
    for item in row["evidence"]:
        out.append(str(item.get("text", "")) if isinstance(item, dict) else str(item))
    return out

def minicheck_pack_evidence(evidence):
    chunks, current, size = [], [], 0
    for raw in evidence:
        text = str(raw).strip()
        if not text:
            continue
        length = len(text)
        if length > DOC_CHAR_BUDGET:
            if current:
                chunks.append("\n\n".join(current))
                current, size = [], 0
            chunks.extend(text[i : i + DOC_CHAR_BUDGET] for i in range(0, length, DOC_CHAR_BUDGET))
        elif current and size + length > DOC_CHAR_BUDGET:
            chunks.append("\n\n".join(current))
            current, size = [text], length
        else:
            current.append(text)
            size += length
    if current:
        chunks.append("\n\n".join(current))
    return chunks or [""]

def minicheck_score_rows(rows, tokenizer, model, batch_size):
    pairs = []
    for row in rows:
        for document in minicheck_pack_evidence(minicheck_evidence_texts(row)):
            pairs.append((row["id"], document, str(row["claim"])))

    by_id = {}
    label_ids = torch.tensor([NO_ID, YES_ID], device="cuda")
    eos = tokenizer.eos_token
    for start in range(0, len(pairs), batch_size):
        minibatch = pairs[start : start + batch_size]
        texts = ["predict: " + eos.join([document, claim]) for _, document, claim in minibatch]
        encoded = tokenizer(
            texts,
            max_length=MAX_LENGTH,
            truncation=True,
            padding=True,
            return_tensors="pt",
        ).to("cuda")
        decoder_input_ids = torch.zeros(
            (encoded["input_ids"].size(0), 1), dtype=torch.long, device="cuda"
        )
        with torch.inference_mode():
            logits = model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
                decoder_input_ids=decoder_input_ids,
            ).logits.squeeze(1)
            support = torch.softmax(logits[:, label_ids], dim=-1)[:, 1].float().cpu().tolist()
        for (row_id, _, _), value in zip(minibatch, support):
            by_id.setdefault(row_id, []).append(float(value))
    return by_id

def hhem_evidence_texts(row):
    return [str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in row["evidence"]]

def hhem_score_rows(rows, model, batch_size):
    pairs, owners = [], []
    for row in rows:
        for evidence in hhem_evidence_texts(row):
            pairs.append((evidence, str(row["claim"])))
            owners.append(str(row["id"]))
    # HHEM pads every minibatch to its longest sequence.  Length sorting keeps
    # long documents from forcing excessive padding for unrelated short ones.
    order = sorted(range(len(pairs)), key=lambda index: len(pairs[index][0]) + len(pairs[index][1]))
    pairs = [pairs[index] for index in order]
    owners = [owners[index] for index in order]
    scores = {}
    for start in range(0, len(pairs), batch_size):
        with torch.inference_mode():
            values = model.predict(pairs[start : start + batch_size]).float().cpu().tolist()
        for owner, value in zip(owners[start : start + batch_size], values):
            scores.setdefault(owner, []).append(float(value))
    return scores
