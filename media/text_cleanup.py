"""Shared text cleanup heuristics for the media pipeline.

These helpers intentionally avoid external NLP dependencies. They focus on
reducing transcript filler/noise before higher-level pipeline stages convert
the evidence into recaps, memory, meeting minutes, and subject lines.
"""

from __future__ import annotations

import re
from collections import Counter

FILLER_WORDS = {
    "a", "ah", "alright", "anyway", "ass", "basically", "cause", "cool", "correct",
    "definitely", "gotcha", "hey", "hmm", "just", "kind", "kinda", "like",
    "literally", "mm", "mhm", "nope", "okay", "right", "really", "so", "sorry",
    "sure", "uh", "uhh", "um", "umm", "well", "yeah", "yep", "yo",
}

TOPIC_STOP_WORDS = FILLER_WORDS | {
    "all", "an", "and", "another", "any", "anything", "are", "as", "at", "be", "by",
    "but", "can", "client", "clients", "could", "does", "doing",
    "context", "everything", "file", "files", "for", "from", "good", "got", "had", "has", "have", "here",
    "how", "if", "in", "into", "it", "it's", "its", "just", "know", "means", "more", "need", "new", "no", "not", "of", "old", "on", "or", "our", "out", "question",
    "questions", "reason", "reasons", "said", "same", "something", "stuff",
    "so", "than", "that", "the", "their", "them", "there", "these", "they", "thing", "things",
    "those", "to", "too", "updates", "up", "value", "values", "was", "we", "we're", "were", "what", "when", "where",
    "which", "who", "why", "with", "would", "you", "your",
}

TOPIC_DISCOURSE_WORDS = {
    "about", "across", "after", "again", "ahead", "already", "around", "away",
    "back", "before", "between", "both", "by", "came", "come", "comes", "coming",
    "click", "clicked", "clicking", "connect", "connected", "connecting", "copy",
    "different", "done", "down", "drag", "end", "even", "feature", "features",
    "first", "follow", "followup",
    "gave", "give", "gives", "given", "go", "goes", "going", "gone", "hear",
    "heard", "hello", "hey", "however", "i", "i'd", "i'll", "i'm", "i've", "include",
    "includes", "including", "into", "it", "it's", "its", "let", "little", "look",
    "looking", "looks", "made", "make", "makes", "making", "mean", "maybe",
    "much", "my", "myself", "now", "off", "onto", "open", "opens", "out", "output",
    "over", "part", "parts",
    "perspective", "point", "points", "put", "puts", "putting", "say", "says",
    "seeing", "seen", "share", "shared", "sharing", "show", "shows", "showing",
    "side", "since", "some", "spot", "stop", "stopped", "stopping",
    "start", "started", "starting", "starts", "state", "still", "take", "takes",
    "taking", "talk", "talked", "talking", "talks", "tell", "telling", "terminal",
    "think",
    "thinking", "thinks", "through", "time", "times", "too", "toward", "trying",
    "use", "used", "uses", "using", "very", "via", "want", "wanted", "wants", "way",
    "ways", "we", "we'd", "we'll", "we're", "we've", "went", "work", "worked",
    "working", "works",
}

GENERIC_TOPIC_TOKENS = TOPIC_STOP_WORDS | {
    "activity", "capture", "captures", "center", "centers", "current", "discussion",
    "emphasis", "focused", "focuses", "focusing", "main", "media", "overview",
    "participant", "participants", "primarily", "recording", "segment", "state",
    "summary", "topic", "topics", "walkthrough", "window", "work", "workstream",
}

TOPIC_ACRONYMS = {
    "ai", "api", "asic", "cnn", "cnns", "cpu", "fpga", "gpu", "id", "ip", "llm",
    "ocr", "rtl", "sram", "ui", "ux", "voi", "voa",
}

TOPIC_SINGLETON_STOP_WORDS = {
    "background", "bio", "chance", "conversation", "conversations", "couple",
    "early", "example", "examples", "hello", "hey", "hi", "lot", "lots",
    "morning", "afternoon", "evening", "one", "ones", "people", "person",
    "point", "points", "potential", "thing", "things", "version", "versions",
}

GENERIC_TOPIC_PHRASES = {
    "context overview",
    "current activity",
    "current workstream",
    "discussion focused",
    "follow up work",
    "key topics",
    "main activity",
    "open questions",
}

NOISE_PHRASES = {
    "what's up",
    "whats up",
    "gotcha",
    "okay",
    "okay cool",
    "all right",
    "alright",
    "sounds good",
    "thank you",
    "thanks",
    "thank you yep",
    "thanks for listening",
    "thanks for watching",
    "thank you for listening",
    "thank you for watching",
    "talk to you later",
    "will do",
}

TRANSCRIPT_OUTRO_RE = re.compile(
    r"^(?:thanks|thank\s+you)(?:\s+for\s+(?:watching|listening))?$",
    re.IGNORECASE,
)

QUESTION_LEAD_NOISE = re.compile(
    r"^(?:"
    r"(?:um|uh|yeah|yep|okay|ok|cool|alright|all right|sorry|gotcha|right|well|so|hmm)[\s,.;:!?-]+"
    r")+",
    re.IGNORECASE,
)

QUESTION_WORD_RE = re.compile(r"^(who|what|when|where|why|how|is|are|do|does|did|can|could|would|should|will)\b", re.IGNORECASE)


def normalize_whitespace(text: str) -> str:
    return " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split()).strip()


def split_sentences(text: str) -> list[str]:
    clean = normalize_whitespace(text)
    if not clean:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\s+(?=[A-Z][a-z]+:)", clean)
    return [part.strip(" -") for part in parts if part.strip(" -")]


def strip_leading_filler(text: str) -> str:
    clean = normalize_whitespace(text)
    previous = None
    while clean and clean != previous:
        previous = clean
        clean = QUESTION_LEAD_NOISE.sub("", clean).strip(" ,.;:-")
    return clean


def lexical_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9']*", normalize_whitespace(text).lower())


def _topic_token_root(token: str) -> str:
    clean = str(token or "").strip().lower()
    if not clean:
        return ""
    if clean.endswith("n't"):
        return "not"
    if clean in TOPIC_ACRONYMS:
        return clean
    return re.sub(r"(?:'re|'ve|'ll|'d|'m|'s)$", "", clean)


def is_noise_phrase(text: str) -> bool:
    clean = strip_leading_filler(text).strip(" ?!.,;:-").lower()
    if not clean:
        return True
    if clean in NOISE_PHRASES:
        return True
    tokens = lexical_tokens(clean)
    if not tokens:
        return True
    unique = set(tokens)
    if len(tokens) % 2 == 0 and tokens[: len(tokens) // 2] == tokens[len(tokens) // 2 :] and len(set(tokens[: len(tokens) // 2])) <= 2:
        return True
    if len(tokens) <= 4 and len(unique) <= 2 and (len(unique) == 1 or all(token in FILLER_WORDS for token in unique)):
        return True
    if all(token in FILLER_WORDS for token in unique):
        return True
    return False


def _coerce_transcript_word(word: object) -> dict | None:
    if word is None:
        return None
    if isinstance(word, dict):
        token = str(word.get("word") or "").strip()
        if not token:
            return None
        payload = {"word": token}
        if word.get("start") is not None:
            payload["start"] = float(word.get("start") or 0.0)
        if word.get("end") is not None:
            payload["end"] = float(word.get("end") or 0.0)
        if word.get("probability") is not None:
            payload["probability"] = float(word.get("probability") or 0.0)
        return payload

    token = str(getattr(word, "word", "") or "").strip()
    if not token:
        return None
    payload = {"word": token}
    start = getattr(word, "start", None)
    end = getattr(word, "end", None)
    probability = getattr(word, "probability", None)
    if start is not None:
        payload["start"] = float(start)
    if end is not None:
        payload["end"] = float(end)
    if probability is not None:
        payload["probability"] = float(probability)
    return payload


def _coerce_transcript_segment(segment: object) -> dict | None:
    if segment is None:
        return None
    if isinstance(segment, dict):
        text = normalize_whitespace(segment.get("text") or "")
        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", start) or start)
        no_speech_prob = float(segment.get("no_speech_prob", 0.0) or 0.0)
        raw_words = segment.get("words") or []
    else:
        text = normalize_whitespace(getattr(segment, "text", "") or "")
        start = float(getattr(segment, "start", 0.0) or 0.0)
        end = float(getattr(segment, "end", start) or start)
        no_speech_prob = float(getattr(segment, "no_speech_prob", 0.0) or 0.0)
        raw_words = getattr(segment, "words", None) or []

    if not text or end <= start:
        return None

    words = [payload for payload in (_coerce_transcript_word(word) for word in raw_words) if payload]
    return {
        "start": start,
        "end": end,
        "text": text,
        "no_speech_prob": no_speech_prob,
        "words": words,
    }


def _transcript_segment_key(text: str) -> str:
    clean = strip_leading_filler(text).strip(" ?!.,;:-").lower()
    return " ".join(clean.split())


def is_transcript_noise_phrase(text: str, repeat_count: int = 1) -> bool:
    clean = _transcript_segment_key(text)
    if not clean:
        return True
    if TRANSCRIPT_OUTRO_RE.fullmatch(clean):
        return True
    if is_noise_phrase(clean):
        return True

    tokens = lexical_tokens(clean)
    if not tokens:
        return True

    if repeat_count >= 5 and len(tokens) <= 4:
        informative = [token for token in tokens if _is_informative_topic_token(token)]
        if len(informative) <= 1:
            return True
        if len(set(tokens)) <= 2:
            return True

    return False


def clean_transcript_segments(segments: list[object] | None) -> tuple[list[dict], dict[str, int | bool]]:
    normalized_segments = [
        payload
        for payload in (_coerce_transcript_segment(segment) for segment in (segments or []))
        if payload
    ]
    phrase_counts = Counter(_transcript_segment_key(segment["text"]) for segment in normalized_segments)

    cleaned_segments: list[dict] = []
    removed_segments = 0
    for segment in normalized_segments:
        repeat_count = phrase_counts.get(_transcript_segment_key(segment["text"]), 1)
        if is_transcript_noise_phrase(segment["text"], repeat_count=repeat_count):
            removed_segments += 1
            continue
        cleaned_segments.append(segment)

    return cleaned_segments, {
        "transcript_cleanup_applied": True,
        "raw_segment_count": len(normalized_segments),
        "clean_segment_count": len(cleaned_segments),
        "removed_segment_count": removed_segments,
    }


def build_readable_transcript_text(segments: list[object] | None, paragraph_gap_s: float = 45.0) -> str:
    clean_segments = [
        payload
        for payload in (_coerce_transcript_segment(segment) for segment in (segments or []))
        if payload
    ]
    if not clean_segments:
        return ""

    paragraphs: list[str] = []
    current_parts: list[str] = []
    previous_end: float | None = None

    for segment in clean_segments:
        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", start) or start)
        text = normalize_whitespace(segment.get("text") or "")
        if not text:
            continue
        if previous_end is not None and current_parts and (start - previous_end) >= paragraph_gap_s:
            paragraphs.append(" ".join(current_parts).strip())
            current_parts = []
        current_parts.append(text)
        previous_end = max(previous_end or end, end)

    if current_parts:
        paragraphs.append(" ".join(current_parts).strip())

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph).strip()


def clean_question(text: str) -> str:
    for sentence in split_sentences(text):
        candidate = strip_leading_filler(sentence)
        if not candidate:
            continue
        if "?" in candidate or QUESTION_WORD_RE.match(candidate):
            candidate = candidate.strip(" .")
            if is_noise_phrase(candidate):
                continue
            if not candidate.endswith("?"):
                candidate = f"{candidate}?"
            return candidate
    fallback = strip_leading_filler(text)
    if fallback and not is_noise_phrase(fallback):
        return fallback if fallback.endswith("?") else f"{fallback}?"
    return ""


def distill_statement(text: str, limit: int = 220) -> str:
    sentences = split_sentences(text)
    cleaned_sentences: list[str] = []
    for sentence in sentences:
        candidate = strip_leading_filler(sentence)
        if not candidate:
            continue
        if is_noise_phrase(candidate):
            continue
        cleaned_sentences.append(candidate)
    distilled = " ".join(cleaned_sentences) if cleaned_sentences else strip_leading_filler(text)
    distilled = normalize_whitespace(distilled)
    if len(distilled) <= limit:
        return distilled
    clipped = distilled[:limit].rsplit(" ", 1)[0].strip(" ,.;:-")
    return f"{clipped}..."


def strip_summary_boilerplate(text: str) -> str:
    clean = normalize_whitespace(text)
    if not clean:
        return ""

    patterns = [
        r"^(?:window\s+summary:\s*)+",
        r"^(?:this\s+(?:media|recording|video|audio)\s+(?:is\s+primarily\s+about|focuses\s+on|covers?|captures?)\s+)+",
        r"^(?:the\s+recording\s+(?:centers|focuses)\s+on\s+)+",
        r"^(?:the\s+segment\s+(?:covers?|captures?)\s+)+",
        r"^(?:the\s+segment\s+(?:centers|focuses)\s+on\s+)+",
        r"^(?:discussion|conversation|segment|window)\s+(?:focused|focuses|centers)\s+on\s+",
    ]
    previous = None
    while clean and clean != previous:
        previous = clean
        for pattern in patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE).strip(" ,.;:-")

    emphasis_match = re.search(r"\bwith emphasis on\s+(.+)$", clean, flags=re.IGNORECASE)
    if emphasis_match:
        tail = emphasis_match.group(1).strip(" .")
        tail_tokens = lexical_tokens(tail)
        if tail_tokens and all(token in GENERIC_TOPIC_TOKENS for token in tail_tokens):
            clean = clean[:emphasis_match.start()].strip(" ,.;:-")

    return clean.strip()


def is_generic_topic_phrase(text: str) -> bool:
    clean = strip_summary_boilerplate(text).strip(" ?!.,;:-").lower()
    if not clean:
        return True
    if clean in GENERIC_TOPIC_PHRASES:
        return True
    tokens = lexical_tokens(clean)
    if not tokens:
        return True
    return all(token in GENERIC_TOPIC_TOKENS for token in tokens)


def _is_informative_topic_token(token: str) -> bool:
    clean = _topic_token_root(token)
    if not clean:
        return False
    if clean in TOPIC_STOP_WORDS or clean in TOPIC_DISCOURSE_WORDS or clean in GENERIC_TOPIC_TOKENS:
        return False
    if clean in TOPIC_SINGLETON_STOP_WORDS:
        return False
    if clean.isdigit():
        return False
    if len(clean) <= 1:
        return False
    if len(clean) == 2 and clean not in TOPIC_ACRONYMS:
        return False
    return True


def _format_topic_term(term: str) -> str:
    parts: list[str] = []
    for raw_part in str(term or "").split():
        part = raw_part.strip()
        lower = _topic_token_root(part)
        if lower in TOPIC_ACRONYMS:
            parts.append("CNNs" if lower == "cnns" else lower.upper())
            continue
        if re.fullmatch(r"[a-z][a-z0-9']*", lower):
            parts.append(lower.title())
            continue
        parts.append(part)
    return " ".join(parts).strip()


def is_weak_topic_phrase(text: str) -> bool:
    clean = strip_summary_boilerplate(text).strip(" ?!.,;:-")
    if not clean:
        return True
    tokens = [_topic_token_root(token) for token in lexical_tokens(clean)]
    tokens = [token for token in tokens if token]
    if not tokens:
        return True
    if len(tokens) == 1 and tokens[0] in TOPIC_ACRONYMS:
        return False
    if is_noise_phrase(clean) or is_generic_topic_phrase(clean):
        return True
    if len(tokens) == 1 and tokens[0] in TOPIC_SINGLETON_STOP_WORDS:
        return True
    if tokens[0] in TOPIC_STOP_WORDS or tokens[0] in TOPIC_DISCOURSE_WORDS or tokens[0] in TOPIC_SINGLETON_STOP_WORDS:
        return True
    if all(token in TOPIC_STOP_WORDS or token in TOPIC_DISCOURSE_WORDS or token in TOPIC_SINGLETON_STOP_WORDS for token in tokens):
        return True
    return False


def extract_inline_topic_terms(text: str, limit: int = 6) -> list[str]:
    clean = strip_summary_boilerplate(text)
    if not clean:
        return []

    token_counts: Counter[str] = Counter()
    phrase_counts: Counter[str] = Counter()
    words = lexical_tokens(clean)
    normalized_words = [_topic_token_root(word) for word in words]

    for word in normalized_words:
        if not _is_informative_topic_token(word):
            continue
        token_counts[word] += 1

    for left, right in zip(normalized_words, normalized_words[1:]):
        if not _is_informative_topic_token(left) or not _is_informative_topic_token(right):
            continue
        if left in TOPIC_ACRONYMS or right in TOPIC_ACRONYMS:
            continue
        if left in TOPIC_SINGLETON_STOP_WORDS or right in TOPIC_SINGLETON_STOP_WORDS:
            continue
        if len(left) < 3 or len(right) < 3:
            continue
        phrase_counts[f"{left} {right}"] += 1

    ordered: list[str] = []
    for token, count in token_counts.most_common():
        if count < 1 and token in TOPIC_ACRONYMS:
            continue
        if token not in TOPIC_ACRONYMS and count < 2 and len(token) < 6:
            continue
        pretty = _format_topic_term(token)
        if not pretty or is_weak_topic_phrase(pretty):
            continue
        if pretty not in ordered:
            ordered.append(pretty)
        if len(ordered) >= limit:
            return ordered

    for phrase, count in phrase_counts.most_common():
        if count < 1:
            continue
        pretty = _format_topic_term(phrase)
        if not pretty or is_weak_topic_phrase(pretty):
            continue
        if pretty not in ordered:
            ordered.append(pretty)
        if len(ordered) >= limit:
            break

    return ordered[:limit]


def extract_topic_phrases(texts: list[str], limit: int = 6) -> list[str]:
    """Heuristic keyword extraction for themes/topics.

    Prefers repeated capitalized acronyms/terms and repeated two-word phrases.
    This is intentionally conservative; we only keep phrases that recur.
    """
    token_counter: Counter[str] = Counter()
    phrase_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()

    phrase_stop = TOPIC_STOP_WORDS | TOPIC_DISCOURSE_WORDS | {
        "manual", "review", "document", "documents", "report", "reports",
        "submission", "submissions", "score", "scores", "tool", "tools",
    }

    for text in texts:
        clean = strip_summary_boilerplate(text)
        if not clean:
            continue
        seen_terms: set[str] = set()
        seen_keywords: set[str] = set()
        seen_phrases: set[str] = set()

        acronyms = re.findall(r"\b[A-Z]{2,6}\b", clean)
        for acronym in acronyms:
            if acronym not in seen_terms:
                token_counter[acronym] += 1
                seen_terms.add(acronym)

        title_terms = re.findall(r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?\b", clean)
        for term in title_terms:
            tokens = [_topic_token_root(part) for part in term.split()]
            if not tokens:
                continue
            if len(tokens) == 1:
                # Single title-cased words are usually people or sentence starters.
                continue
            if any(token in phrase_stop for token in tokens):
                continue
            if is_noise_phrase(" ".join(tokens)) or is_weak_topic_phrase(term):
                continue
            if term not in seen_terms:
                token_counter[term] += 1
                seen_terms.add(term)

        words = lexical_tokens(clean)
        for word in words:
            root = _topic_token_root(word)
            if not _is_informative_topic_token(root):
                continue
            if is_weak_topic_phrase(root):
                continue
            if root not in seen_keywords:
                keyword_counter[root] += 1
                seen_keywords.add(root)

        for left, right in zip(words, words[1:]):
            left_root = _topic_token_root(left)
            right_root = _topic_token_root(right)
            if left_root in phrase_stop or right_root in phrase_stop:
                continue
            if not _is_informative_topic_token(left_root) or not _is_informative_topic_token(right_root):
                continue
            if len(left_root) < 3 or len(right_root) < 3:
                continue
            phrase = f"{left_root} {right_root}"
            if is_weak_topic_phrase(phrase):
                continue
            if phrase not in seen_phrases:
                phrase_counter[phrase] += 1
                seen_phrases.add(phrase)

    ordered: list[str] = []
    for term, count in token_counter.most_common():
        if count < 2:
            continue
        if is_weak_topic_phrase(term):
            continue
        if term not in ordered:
            ordered.append(term)
        if len(ordered) >= limit:
            return ordered

    for token, count in keyword_counter.most_common():
        if count < 2:
            continue
        pretty = _format_topic_term(token)
        if not pretty or is_weak_topic_phrase(pretty):
            continue
        if pretty not in ordered:
            ordered.append(pretty)
        if len(ordered) >= limit:
            return ordered

    for phrase, count in phrase_counter.most_common():
        if count < 2:
            continue
        pretty = _format_topic_term(phrase)
        if is_weak_topic_phrase(pretty):
            continue
        if pretty not in ordered:
            ordered.append(pretty)
        if len(ordered) >= limit:
            break

    return ordered[:limit]
