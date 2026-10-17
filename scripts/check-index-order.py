#!/usr/bin/env python3
"""Index-order gate: papers and proposals stay complete and in sequence.

paper.html
  - every <a class="paper-card"> points at a file that exists;
  - "Paper X" cards appear in strict letter order (A, B, C, ...), no gaps;
  - a companion card ("... companion to Paper X") sits after Paper X and
    before the next lettered paper;
  - every paper card is also listed in sitemap.xml.

proposals.html
  - every proposal_*.html on disk is linked from proposals.html exactly once;
  - every proposal_*.html linked from proposals.html exists on disk;
  - every proposal_*.html is listed in sitemap.xml.

Output is ASCII only (see CLAUDE.md "Gate scripts print ASCII only").
Exit 1 on any failure.
"""
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def text(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


def main():
    errors = []
    sitemap = read("sitemap.xml")

    # ---- papers ----
    paper = read("paper.html")
    cards = re.findall(r'<a class="paper-card" href="([^"]+)">([\s\S]*?)</a>', paper)
    if not cards:
        errors.append("paper.html: no paper-card links found (markup changed?)")
    seen = []        # lettered papers in page order
    last_letter = None
    for href, body in cards:
        rel = href.lstrip("/")
        if not os.path.isfile(os.path.join(REPO, rel)):
            errors.append("paper.html: card links to missing file %s" % href)
        if "/" + rel not in sitemap and rel not in sitemap:
            errors.append("paper.html: %s is not listed in sitemap.xml" % href)
        label = text(body)[:160]
        comp = re.search(r"companion to Paper ([A-Z])\b", label)
        lett = re.match(r"Paper ([A-Z])\b", label)
        if comp:
            parent = comp.group(1)
            if last_letter != parent:
                errors.append("paper.html: companion card %s must follow Paper %s directly "
                              "(it follows %s)" % (href, parent, last_letter or "nothing"))
        elif lett:
            L = lett.group(1)
            expected = "A" if last_letter is None else chr(ord(last_letter) + 1)
            if L != expected:
                errors.append("paper.html: Paper %s appears where Paper %s was expected "
                              "(cards must run A, B, C, ... with no gaps)" % (L, expected))
            last_letter = L
            seen.append(L)
        else:
            errors.append("paper.html: card %s has no 'Paper X' or 'companion to Paper X' label" % href)

    # ---- proposals ----
    prop = read("proposals.html")
    linked = re.findall(r'href="/?(proposal_[\w-]+\.html)"', prop)
    on_disk = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "proposal_*.html")))
    for f in on_disk:
        n = linked.count(f)
        if n == 0:
            errors.append("proposals.html: %s exists but is not linked from the hub" % f)
        elif n > 1:
            errors.append("proposals.html: %s is linked %d times (expected once)" % (f, n))
        if f not in sitemap:
            errors.append("sitemap.xml: %s is not listed" % f)
    for f in sorted(set(linked)):
        if f not in on_disk:
            errors.append("proposals.html: links to missing file %s" % f)

    if errors:
        print("Index-order gate: %d problem(s)" % len(errors))
        for e in errors:
            print("  - " + e)
        print("See CLAUDE.md 'Adding a paper or proposal'.")
        return 1
    print("[OK] Papers %s in order (%d cards incl. companions); %d proposals linked once and in sitemap."
          % ("-".join(seen), len(cards), len(on_disk)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
