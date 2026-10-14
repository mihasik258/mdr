"""Coordinate-aware table extractor for the MDR1206FI specification.

Plain-text extraction flattens tables: cell boundaries are lost and
multi-column values collapse onto one line. This module recovers tables by
clustering the words on a page into rows (by y) and then into columns
(by x-occupancy gaps).

Usage:
    python tablex.py <pdf> <page> [<page> ...]
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Iterable

import pymupdf


@dataclass
class Word:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0


@dataclass
class Row:
    y0: float
    y1: float
    words: list[Word] = field(default_factory=list)

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0


def page_words(doc, pno: int) -> list[Word]:
    """All words on a page (0-based page number)."""
    out = []
    for w in doc[pno].get_text("words"):
        if w[4].strip():
            out.append(Word(w[0], w[1], w[2], w[3], w[4]))
    return out


def cluster_rows(words: Iterable[Word], tol: float | None = None) -> list[Row]:
    """Group words into rows by vertical-centre proximity."""
    ws = sorted(words, key=lambda w: (w.cy, w.x0))
    if not ws:
        return []
    if tol is None:
        tol = max(2.0, statistics.median([w.y1 - w.y0 for w in ws]) * 0.6)

    rows: list[Row] = []
    for w in ws:
        for r in rows:
            if abs(r.cy - w.cy) <= tol:
                r.words.append(w)
                r.y0 = min(r.y0, w.y0)
                r.y1 = max(r.y1, w.y1)
                break
        else:
            rows.append(Row(w.y0, w.y1, [w]))
    rows.sort(key=lambda r: r.cy)
    for r in rows:
        r.words.sort(key=lambda w: w.x0)
    return rows


def column_edges(rows: list[Row], min_gap: float = 8.0) -> list[tuple[float, float]]:
    """Recover column bands from the aggregate x-occupancy profile."""
    spans = [(w.x0, w.x1) for r in rows for w in r.words]
    if not spans:
        return []
    spans.sort()
    bands = [[spans[0][0], spans[0][1]]]
    for x0, x1 in spans[1:]:
        if x0 - bands[-1][1] > min_gap:
            bands.append([x0, x1])
        else:
            bands[-1][1] = max(bands[-1][1], x1)
    return [(a, b) for a, b in bands]


def to_grid(rows: list[Row], bands: list[tuple[float, float]]) -> list[list[str]]:
    """Assign every word to its nearest column band, then join cell text."""
    grid = []
    for r in rows:
        cells: list[list[str]] = [[] for _ in bands]
        for w in r.words:
            best, best_d = 0, None
            for i, (a, b) in enumerate(bands):
                d = 0.0 if a <= w.cx <= b else min(abs(w.cx - a), abs(w.cx - b))
                if best_d is None or d < best_d:
                    best, best_d = i, d
            cells[best].append(w.text)
        grid.append([" ".join(c).strip() for c in cells])
    return grid


def dump_pages(pdf_path: str, pages: list[int], min_gap: float = 8.0) -> str:
    doc = pymupdf.open(pdf_path)
    chunks = []
    for p in pages:
        rows = cluster_rows(page_words(doc, p - 1))
        bands = column_edges(rows, min_gap=min_gap)
        head = f"\n{'#' * 28} PAGE {p}  ({len(bands)} bands, {len(rows)} rows) {'#' * 28}\n"
        body = "\n".join(" | ".join(r) for r in to_grid(rows, bands)) if bands else "(empty)"
        chunks.append(head + body)
    doc.close()
    return "\n".join(chunks)


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pages = [int(a) for a in sys.argv[2:]] or [1]
    print(dump_pages(sys.argv[1], pages))