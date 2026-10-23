import re, json

def sentence_spans(text: str) -> list[tuple[int, int, str]]:
    """Dependency-free sentence spans preserving offsets for gold overlap."""
    boundaries = [0]
    for match in re.finditer(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])|\n+", text):
        boundaries.append(match.end())
    boundaries.append(len(text))
    output = []
    for left, right in zip(boundaries, boundaries[1:]):
        while left < right and text[left].isspace():
            left += 1
        while right > left and text[right - 1].isspace():
            right -= 1
        value = text[left:right]
        if len(re.findall(r"[A-Za-z0-9]+", value)) >= 3:
            output.append((left, right, value))
    return output

def source_text(item: dict) -> str:
    info = item.get("source_info")
    if isinstance(info, str):
        return info.strip()
    if isinstance(info, dict):
        if item.get("task_type") == "QA" and info.get("passages"):
            return str(info["passages"]).strip()
        return json.dumps(info, ensure_ascii=False, sort_keys=True)
    return str(info or "").strip()

def chunk_text(text: str, max_words: int = 350) -> list[str]:
    """Paragraph/sentence-aware chunks with a hard word fallback."""
    units = [x.strip() for x in re.split(r"\n\s*\n+", text) if x.strip()]
    if len(units) == 1:
        units = [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text) if x.strip()]
    chunks, current, count = [], [], 0
    for unit in units or [text]:
        words = unit.split()
        if len(words) > max_words:
            if current:
                chunks.append("\n".join(current)); current, count = [], 0
            chunks.extend(" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words))
        elif current and count + len(words) > max_words:
            chunks.append("\n".join(current)); current, count = [unit], len(words)
        else:
            current.append(unit); count += len(words)
    if current:
        chunks.append("\n".join(current))
    return [x for x in chunks if x.strip()] or [text.strip()]
