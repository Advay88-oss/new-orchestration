"""Cleaning and chunking — by content type, never one strategy for all.

  docs, Notion pages   heading-aware, parent-child: small chunks are what
                       search matches, and each points at its whole section,
                       which is what the agent reads
  FAQs                 one question and its answer = one chunk; never split
  blogs, landing pages semantic paragraphs plus one summary chunk per page,
                       so a broad question ("what does the company do?")
                       still has something to match

Every chunk carries a contextual prefix — "From Vanna docs, Liquidation ›
Health factor" — embedded and indexed with it, which is what lets a short
chunk be found by a query that names its topic but not its words.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional

CHILD_MAX = 900
_HEAD = re.compile(r"^(#{1,4})\s+(.+?)\s*#*\s*$")
_NAV = re.compile(r"(?im)^\s*(skip to (main )?content|cookie|accept all|all rights reserved|"
                  r"privacy policy|terms of (use|service)|©\s*\d{4}|"
                  r">\s*#*\s*documentation index|>\s*fetch the complete documentation index|"
                  r">\s*use this file to discover all available pages).*$")
_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)


@dataclass
class Chunk:
    text: str
    title: str
    section: str
    content_type: str
    prefix: str
    parent_key: Optional[str] = None      # key of the parent section chunk
    key: str = ""
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.key:
            self.key = hashlib.sha1((self.title + "|" + self.section + "|" + self.text)
                                    .encode("utf-8")).hexdigest()[:16]


def digest(text: str) -> str:
    return hashlib.sha1(" ".join(text.split()).encode("utf-8")).hexdigest()[:16]


def clean(text: str) -> str:
    """Drop front matter, nav/footer/cookie lines, HTML comments and blank runs."""
    text = _FRONTMATTER.sub("", text.replace("\r\n", "\n"))
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = _NAV.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _sections(md: str) -> list[tuple[list[str], str]]:
    """(heading path, body) for every heading-delimited section."""
    path: list[str] = []
    out: list[tuple[list[str], str]] = []
    buf: list[str] = []
    for line in md.splitlines():
        m = _HEAD.match(line)
        if m:
            if "\n".join(buf).strip():
                out.append((list(path), "\n".join(buf).strip()))
            level = len(m.group(1))
            path = path[:level - 1] + [m.group(2).strip()]
            buf = []
        else:
            buf.append(line)
    if "\n".join(buf).strip():
        out.append((list(path), "\n".join(buf).strip()))
    return out


def _paragraph_groups(body: str, limit: int = CHILD_MAX) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out, cur = [], ""
    for p in paras:
        if len(p) > limit:                       # a long table or list: split by lines
            for line in p.splitlines():
                if len(cur) + len(line) > limit and cur:
                    out.append(cur.strip())
                    cur = ""
                cur += line + "\n"
            continue
        if len(cur) + len(p) > limit and cur:
            out.append(cur.strip())
            cur = ""
        cur += p + "\n\n"
    if cur.strip():
        out.append(cur.strip())
    return out


def _is_faq(heading: str, body: str) -> bool:
    return heading.rstrip().endswith("?") or bool(re.match(r"(?i)^\s*(q:|question:)", body))


_CODE_SECTIONS = ("source reference", "function signatures", "signatures", "contract addresses")


def is_code(section: str, body: str) -> bool:
    """Code listings, signatures and file paths. They are kept and searchable
    on request, but a question about the product should not be answered with
    a Rust signature or a list of source files."""
    if any(section.lower().endswith(s) or ("› " + s) in section.lower() for s in _CODE_SECTIONS):
        return True
    fenced = sum(len(m) for m in re.findall(r"```.*?```", body, flags=re.S))
    ticks = sum(len(m) for m in re.findall(r"`[^`\n]+`", body))
    return (fenced + ticks) > 0.5 * max(1, len(body))


def chunk_markdown(md: str, *, title: str, company: str, source_label: str,
                   content_type: str = "doc") -> list[Chunk]:
    """Heading-aware parent-child chunks, with FAQ entries kept whole."""
    md = clean(md)
    chunks: list[Chunk] = []
    base_type = content_type
    for path, body in _sections(md):
        content_type = "code" if is_code(" › ".join(path), body) else base_type
        section = " › ".join(path) or title
        prefix = ("From " + company + " " + source_label + ": " + title
                  + (" › " + section if section != title else "") + ".")
        heading = path[-1] if path else ""
        if _is_faq(heading, body):
            chunks.append(Chunk(text=(heading + "\n" + body).strip(), title=title,
                                section=section, content_type="faq", prefix=prefix))
            continue
        groups = _paragraph_groups(body)
        if len(groups) <= 1:
            chunks.append(Chunk(text=body, title=title, section=section,
                                content_type=content_type, prefix=prefix))
            continue
        parent = Chunk(text=body[:6000], title=title, section=section,
                       content_type="section", prefix=prefix)
        chunks.append(parent)
        for g in groups:
            chunks.append(Chunk(text=g, title=title, section=section,
                                content_type=content_type, prefix=prefix,
                                parent_key=parent.key))
    return chunks


def chunk_page(text: str, *, title: str, company: str, source_label: str,
               summary: Optional[str] = None) -> list[Chunk]:
    """Blogs and landing pages: paragraphs, plus one summary chunk."""
    text = clean(text)
    prefix = "From " + company + " " + source_label + ": " + title + "."
    out = [Chunk(text=g, title=title, section=title, content_type="blog", prefix=prefix)
           for g in _paragraph_groups(text)]
    if summary:
        out.insert(0, Chunk(text=summary, title=title, section="summary",
                            content_type="summary", prefix=prefix))
    return out
