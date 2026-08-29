#!/usr/bin/env python3
"""check-paper-mirror.py - repo/papers/{figs,*.pdf} must match the outer paper/ tree.

Follows AUDIT-HY4-PAPER §2.3: repo/papers/figs/ publishes .py scripts as
"reproducibility SOURCE" mirrored by hand from the private paper/ repo one
directory up. The mirror had drifted silently (fG_expand_v1.py was missing
a 34-line function) because nothing compared the two trees. This gate does,
with line-ending normalization so CRLF-vs-LF noise (see .gitattributes) never
masks real content drift: .py files are compared as text (line endings
stripped before hashing), .pdf files are compared as raw bytes.

The mirror is a curated SUBSET, not a 1:1 directory copy: only 18 of paper/'s
figure scripts are published (the rest are internal-only), 4 of the mirrored
scripts live in paper/h/calc7/ rather than paper/figs/ upstream, and every
published PDF is renamed from its paper/ source filename (mth-paper.pdf ->
macro-transcension-hypothesis.pdf, etc). So this gate is driven from the
mirror side: for each file actually present in repo/papers/, look up its
known outer counterpart and diff; it does NOT require every outer file to
have a mirror counterpart (that would be an "add a mirror" gate, not a
"detect drift" gate, and the curation is intentional).

Local-only by design: the outer paper/ tree lives in the private
PostOakLabs/ocs-internal repo, one directory above this checkout, and is
not available to GitHub Actions runners checking out only PostOakLabs/OCS.
If the outer tree isn't found (e.g. in CI, or a bare checkout of repo/),
this gate reports and exits 0 rather than failing on an absent sibling.

Run: python3 scripts/check-paper-mirror.py
Exit 0 clean (or outer tree absent), 1 on any content mismatch, missing
outer source, or unmapped mirror file (so a newly-added mirror file must
be added to PDF_MAP / CALC7_SCRIPTS here, not silently skipped).
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MIRROR_DIR = os.path.join(REPO, "papers")
MIRROR_FIGS = os.path.join(MIRROR_DIR, "figs")
OUTER_PAPER = os.path.abspath(os.path.join(REPO, "..", "paper"))
OUTER_FIGS = os.path.join(OUTER_PAPER, "figs")

# Published PDF basename -> outer paper/ source path (relative to OUTER_PAPER).
PDF_MAP = {
    "engineered-imbh-systems.pdf": "engineered-imbh-paper.pdf",
    "inward-migration-economics.pdf": "economics-paper.pdf",
    "inward-migration-fermi-paradox-review.pdf": "inward-review.pdf",
    "macro-transcension-hypothesis.pdf": "mth-paper.pdf",
    "omega-centauri-accretion-limit.pdf": "accretion-limit-paper.pdf",
    "omega-centauri-axi-note.pdf": os.path.join("axi", "axi-note.pdf"),
    "omega-centauri-mass-tension.pdf": "mass-tension-paper.pdf",
    "omega-centauri-technosignature-campaign.pdf": "campaign-paper.pdf",
    "omega-centauri-xray-census.pdf": os.path.join("g", "census-paper.pdf"),
}

# Mirrored .py scripts that live in paper/h/calc7/ upstream, not paper/figs/.
CALC7_SCRIPTS = {
    "fH_calc7_amass0.py",
    "fH_calc7_cuspfam.py",
    "fH_calc7_records.py",
    "fH_calc7_tail_families.py",
}


def text_hash(path):
    with open(path, "rb") as fh:
        data = fh.read()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.md5(normalized).hexdigest()


def binary_hash(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def main():
    if not os.path.isdir(OUTER_PAPER):
        print(f"  outer paper/ tree not found at {OUTER_PAPER} — skipping "
              f"(expected in CI; this gate is local-only, see pre-push).")
        return 0

    problems = []
    py_checked = 0
    pdf_checked = 0

    mirror_py = sorted(
        name for name in os.listdir(MIRROR_FIGS)
        if name.endswith(".py") and os.path.isfile(os.path.join(MIRROR_FIGS, name))
    )
    for name in mirror_py:
        mirror_path = os.path.join(MIRROR_FIGS, name)
        if name in CALC7_SCRIPTS:
            outer_path = os.path.join(OUTER_PAPER, "h", "calc7", name)
        else:
            outer_path = os.path.join(OUTER_FIGS, name)
        if not os.path.isfile(outer_path):
            problems.append(f"repo/papers/figs/{name}: no outer source at "
                             f"{os.path.relpath(outer_path, OUTER_PAPER)}")
            continue
        py_checked += 1
        if text_hash(mirror_path) != text_hash(outer_path):
            problems.append(f"repo/papers/figs/{name}: content differs from "
                             f"paper/{os.path.relpath(outer_path, OUTER_PAPER)} "
                             f"(post line-ending-normalization)")

    mirror_pdf = sorted(
        name for name in os.listdir(MIRROR_DIR)
        if name.endswith(".pdf") and os.path.isfile(os.path.join(MIRROR_DIR, name))
    )
    for name in mirror_pdf:
        mirror_path = os.path.join(MIRROR_DIR, name)
        rel_outer = PDF_MAP.get(name)
        if rel_outer is None:
            problems.append(f"repo/papers/{name}: not in PDF_MAP — add its "
                             f"outer paper/ source path to check-paper-mirror.py")
            continue
        outer_path = os.path.join(OUTER_PAPER, rel_outer)
        if not os.path.isfile(outer_path):
            problems.append(f"repo/papers/{name}: mapped outer source "
                             f"paper/{rel_outer} does not exist")
            continue
        pdf_checked += 1
        if binary_hash(mirror_path) != binary_hash(outer_path):
            problems.append(f"repo/papers/{name}: byte content differs from "
                             f"paper/{rel_outer}")

    if problems:
        print(f"::error::{len(problems)} paper-mirror mismatch(es):")
        for p in problems:
            print(f"  {p}")
        return 1

    print(f"  {py_checked} figure script(s) + {pdf_checked} PDF(s) match "
          f"their paper/ source (line-ending-normalized for .py, raw for .pdf).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
