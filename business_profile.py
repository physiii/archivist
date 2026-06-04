from __future__ import annotations

import os
import re


DEFAULT_BUSINESS_TERMS = ("versant", "gigantor", "vivonics")


def _normalize_term(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def business_terms() -> tuple[str, ...]:
    raw_extra = os.getenv("ARCHIVIST_BUSINESS_TERMS", "")
    terms: list[str] = []
    seen: set[str] = set()
    for raw in [*DEFAULT_BUSINESS_TERMS, *raw_extra.split(",")]:
        term = _normalize_term(raw)
        if not term or term in seen:
            continue
        seen.add(term)
        terms.append(term)
    return tuple(terms)


def business_terms_label() -> str:
    return ", ".join(term.title() for term in business_terms())


def _term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)


def business_matches_text(*values: object) -> bool:
    text = " ".join(str(value or "") for value in values).strip()
    if not text:
        return False
    return any(_term_pattern(term).search(text) for term in business_terms())


def business_term_matches(*values: object) -> list[str]:
    text = " ".join(str(value or "") for value in values).strip()
    if not text:
        return []
    matches: list[str] = []
    for term in business_terms():
        if _term_pattern(term).search(text):
            matches.append(term)
    return matches


def business_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", _normalize_term(value)).strip("-") or "business"


def business_tags_for_text(*values: object) -> list[str]:
    matches = business_term_matches(*values)
    if not matches:
        return []
    return ["category:business", *[f"business:{business_slug(term)}" for term in matches]]
