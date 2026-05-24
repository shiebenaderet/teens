#!/usr/bin/env python3
from __future__ import annotations
"""Extract chapter excerpts from EPUB and PDF source files into excerpts/.

What this does
--------------
For each excerpt configured below, this script opens the source book (EPUB or
PDF) and writes a clean markdown file to excerpts/module-N/. It runs in three
stages:

  1. Pre-process the raw XHTML/HTML (for EPUB sources) to convert publisher-
     specific styling into semantic structure html2text can preserve:
       - Faber's <span class="big9"> spans, used as visual section headings
         throughout the book, get promoted to <h3>.
       - <br/> inside <h1> chapter titles gets stripped to prevent multi-line
         markdown links forming when the title is wrapped in an anchor.
       - Anchor wrappers around chapter title text get flattened, so the
         heading comes through without a broken markdown link.
  2. Run html2text to produce markdown.
  3. Post-process the markdown to drop chapter-title anchors that survived
     pre-processing, drop empty headings, and remove the "Excerpt from..."
     preamble (we'll re-add a fresh one from the script's config).

PDF sources go through a custom text cleanup that strips page footers,
rejoins hard-wrapped paragraphs, promotes ALL-CAPS section lines to ###
headings, and formats indented student quotes as blockquotes with the
attribution name.

Usage
-----
    pip3 install html2text markdown        # one-time
    python3 scripts/extract-excerpts.py    # writes everything

Each run is idempotent and overwrites existing excerpt files. Add new
sources to EPUB_SOURCES or PDF_SOURCES below as new excerpts are needed.
"""

import re
import shutil
import subprocess
import sys
import zipfile
import tempfile
from pathlib import Path

try:
    import html2text
except ImportError:
    sys.exit("Missing dependency. Install it with:\n    pip3 install html2text\n")

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books"
EXCERPTS = ROOT / "excerpts"


# ============================================================
# EPUB extraction
# ============================================================

# Each entry: output path (relative to excerpts/) -> config dict.
# Multiple xhtml_files entries are concatenated in order before extraction.
EPUB_SOURCES = {
    # ---- Module I ----
    "module-1/siegel-part1-essence.md": {
        "epub": "brainstorm-siegel.epub",
        "xhtml_files": ["OEBPS/9781101631522_EPUB-6.xhtml"],
        "title": "Part I: The Essence of Adolescence",
        "source_book": "Brainstorm: The Power and Purpose of the Teenage Brain by Daniel J. Siegel, M.D.",
        "blurb": "The ESSENCE chapters: Benefits and Challenges, Risk and Reward, Pushing Away, Timing of Puberty, and the central reframe of adolescent behavior as developmental rather than defective. Module I, Step 2 reading.",
    },
    "module-1/damour-ch1-emotion-101.md": {
        "epub": "emotional-lives-damour.epub",
        "xhtml_files": ["OEBPS/xhtml/Damo_9780593500026_epub3_c001_r1.xhtml"],
        "title": "Chapter 1: Adolescent Emotion 101 — Getting Past Three Big Myths",
        "source_book": "The Emotional Lives of Teenagers by Lisa Damour",
        "blurb": "The function-of-emotion chapter and the 'ordinary suffering vs. mental illness' framework. Module I, Step 3 reading.",
    },

    # ---- Module II ----
    "module-2/faber-ch1-dealing-with-feelings.md": {
        "epub": "how-to-talk-faber.epub",
        "xhtml_files": ["OEBPS/9780062046413_epub_c01_r1.htm"],
        "title": "Chapter 1: Dealing with Feelings",
        "source_book": "How to Talk So Teens Will Listen & Listen So Teens Will Talk by Adele Faber and Elaine Mazlish",
        "blurb": "The foundation chapter. Module II, Step 2 reading.",
    },
    "module-2/faber-ch2-making-sure.md": {
        "epub": "how-to-talk-faber.epub",
        "xhtml_files": ["OEBPS/9780062046413_epub_c02_r1.htm"],
        "title": "Chapter 2: We're Still \"Making Sure\"",
        "source_book": "How to Talk So Teens Will Listen & Listen So Teens Will Talk by Adele Faber and Elaine Mazlish",
        "blurb": "The cooperation chapter (the teens-edition rename of the classic 'Engaging Cooperation'). Module II, Step 2 reading.",
    },
    "module-2/damour-ch4-expressing-feelings.md": {
        "epub": "emotional-lives-damour.epub",
        "xhtml_files": ["OEBPS/xhtml/Damo_9780593500026_epub3_c004_r1.xhtml"],
        "title": "Chapter 4: Managing Emotions, Part One — Helping Teens Express Their Feelings",
        "source_book": "The Emotional Lives of Teenagers by Lisa Damour",
        "blurb": "Listening, empathy, getting teens to open up, and the 'what to say' sidebars. Module II, Step 3 reading.",
    },

    # ---- Module III ----
    "module-3/natterson-ch1-how-to-talk-to-boys.md": {
        "epub": "decoding-boys-natterson.epub",
        "xhtml_files": ["OEBPS/xhtml/Natt_9781984819048_epub3_c001_r1.xhtml"],
        "title": "Chapter 1: How to Talk to Boys",
        "source_book": "Decoding Boys: New Science Behind the Subtle Art of Raising Sons by Cara Natterson, M.D.",
        "blurb": "The silence chapter. Why boys go quiet, what the cultural pressures look like, and how adults can keep the door cracked. Module III, Step 2 reading.",
    },
    "module-3/natterson-ch3-puberty-timing.md": {
        "epub": "decoding-boys-natterson.epub",
        "xhtml_files": ["OEBPS/xhtml/Natt_9781984819048_epub3_c003_r1.xhtml"],
        "title": "Chapter 3: Yes, Your Nine-Year-Old Might Be in Puberty",
        "source_book": "Decoding Boys: New Science Behind the Subtle Art of Raising Sons by Cara Natterson, M.D.",
        "blurb": "The timing-of-puberty chapter. Why puberty arrives sooner than parents and teachers expect, and what that means for an 11- or 12-year-old who already looks like he's been at it for years. Module III, Step 2 reading.",
    },
    "module-3/damour-ch5-regaining-control.md": {
        "epub": "emotional-lives-damour.epub",
        "xhtml_files": ["OEBPS/xhtml/Damo_9780593500026_epub3_c005_r1.xhtml"],
        "title": "Chapter 5: Managing Emotions, Part Two — Helping Teens Regain Emotional Control",
        "source_book": "The Emotional Lives of Teenagers by Lisa Damour",
        "blurb": "When emotions need to be brought under control. Shutdown as regulation, healthy and unhealthy. Module III, Step 3 reading.",
    },

    # ---- Module V ----
    "module-5/faber-ch3-punish-or-not.md": {
        "epub": "how-to-talk-faber.epub",
        "xhtml_files": ["OEBPS/9780062046413_epub_c03_r1.htm"],
        "title": "Chapter 3: To Punish or Not to Punish",
        "source_book": "How to Talk So Teens Will Listen & Listen So Teens Will Talk by Adele Faber and Elaine Mazlish",
        "blurb": "Faber and Mazlish's chapter on alternatives to punishment. Five concrete moves to use instead. Module V, Step 2 reading.",
    },
    "module-5/faber-ch4-working-it-out.md": {
        "epub": "how-to-talk-faber.epub",
        "xhtml_files": ["OEBPS/9780062046413_epub_c04_r1.htm"],
        "title": "Chapter 4: Working It Out Together",
        "source_book": "How to Talk So Teens Will Listen & Listen So Teens Will Talk by Adele Faber and Elaine Mazlish",
        "blurb": "The problem-solving chapter. Five steps for working through conflicts with a teen as a partner rather than a defendant. Module V, Step 2 reading.",
    },
    "module-5/siegel-part4-staying-present.md": {
        "epub": "brainstorm-siegel.epub",
        "xhtml_files": ["OEBPS/9781101631522_EPUB-12.xhtml"],
        "title": "Part IV: Staying Present Through Changes and Challenges",
        "source_book": "Brainstorm: The Power and Purpose of the Teenage Brain by Daniel J. Siegel, M.D.",
        "blurb": "Siegel's chapters on presence, leaving home, and returning home: reflection, realignment, and repairing ruptures. The clinical case for repair as relationship-building. Module V, Step 3 reading.",
    },

    # ---- Module IV ----
    "module-4/neufeld-ch1-why-parents-matter.md": {
        "epub": "hold-on-to-your-kids-neufeld.epub",
        "xhtml_files": ["OEBPS/Neuf_9780307485960_epub_c01_r1.htm"],
        "title": "Chapter 1: Why Parents Matter More Than Ever",
        "source_book": "Hold On to Your Kids: Why Parents Need to Matter More Than Peers by Gordon Neufeld and Gabor Maté",
        "blurb": "The opening of the peer-orientation thesis. Twelve-year-old Jeremy on MSN Messenger as the through-line. Module IV, Step 2 reading.",
    },
    "module-4/neufeld-ch2-skewed-attachments.md": {
        "epub": "hold-on-to-your-kids-neufeld.epub",
        "xhtml_files": ["OEBPS/Neuf_9780307485960_epub_c02_r1.htm"],
        "title": "Chapter 2: Skewed Attachments, Subverted Instincts",
        "source_book": "Hold On to Your Kids: Why Parents Need to Matter More Than Peers by Gordon Neufeld and Gabor Maté",
        "blurb": "The mechanism behind peer-orientation: how attachment moves from adults to peers and what the cost is. Module IV, Step 2 reading.",
    },
    "module-4/fagell-ch6-shifting-friendships.md": {
        "epub": "middle-school-matters-fagell.epub",
        "xhtml_files": ["OEBPS/chapter006.xhtml"],
        "title": "Chapter 6: Managing Shifting Friendships",
        "source_book": "Middle School Matters: The 10 Key Skills Kids Need to Thrive in Middle School and Beyond by Phyllis L. Fagell",
        "blurb": "Fagell on the social shifts of middle school friendships, with the practical school-counselor moves for navigating them. Module IV, Step 3 reading.",
    },

    # ---- Module VI ----
    "module-6/fagell-ch13-intervening-when-struggling.md": {
        "epub": "middle-school-matters-fagell.epub",
        "xhtml_files": ["OEBPS/chapter013.xhtml"],
        "title": "Chapter 13: Intervening When School Is a Struggle",
        "source_book": "Middle School Matters: The 10 Key Skills Kids Need to Thrive in Middle School and Beyond by Phyllis L. Fagell",
        "blurb": "Fagell's chapter on supporting struggling students, including the self-advocacy skill that maps directly to 'asking for help.' Module VI, Step 3 reading.",
    },
}


# ============================================================
# PDF extraction (Cushman is a scanned-then-OCR'd PDF, not an EPUB)
# ============================================================

PDF_SOURCES = {
    "module-6/cushman-ch2-teacher-on-our-side.md": {
        "pdf": "fires-in-the-bathroom-cushman.pdf",
        "pages": (56, 82),
        "title": "Chapter 2: A Teacher on Our Side",
        "source_book": "Fires in the Middle School Bathroom: Advice for Teachers from Middle Schoolers by Kathleen Cushman and Laura Rogers",
        "blurb": "Middle schoolers in their own words on what they want from their teachers. Module VI, Step 2 reading.",
        "footers": ["fires in the middle school bathroom", "a teacher on our side"],
    },
    "module-6/cushman-ch4-confident-learners.md": {
        "pdf": "fires-in-the-bathroom-cushman.pdf",
        "pages": (120, 148),
        "title": "Chapter 4: Helping Us Grow into Confident Learners",
        "source_book": "Fires in the Middle School Bathroom: Advice for Teachers from Middle Schoolers by Kathleen Cushman and Laura Rogers",
        "blurb": "What kids say they need from teachers when classwork gets hard. Module VI, Step 2 reading.",
        "footers": ["fires in the middle school bathroom", "helping us grow into confident learners"],
    },
}


# ============================================================
# EPUB preprocessing — fix publisher-specific styling
# ============================================================

def preprocess_xhtml(html: str) -> str:
    """Convert publisher-specific visual styling into semantic structure
    that html2text can preserve. Applied before html2text conversion."""

    # Faber: <span class="big9">SECTION TITLE</span> is visually rendered as
    # a section heading throughout the book. Promote to <h3>.
    html = re.sub(
        r'<span[^>]*class="big9"[^>]*>(.*?)</span>',
        r'<h3>\1</h3>',
        html,
        flags=re.S,
    )

    # Strip <br/> inside chapter <h1> elements. Some books wrap the chapter
    # word + title in a single <h1> with a <br/> between them, which html2text
    # turns into a multi-line markdown link if there's an anchor wrapper.
    def fix_h1(m):
        attrs = m.group(1)
        inner = m.group(2)
        inner = re.sub(r'<br\s*/?>', ' ', inner)
        # Strip <a> wrappers that link back to the TOC so the heading text
        # comes through cleanly without the embedded markdown link.
        inner = re.sub(
            r'<a[^>]*href="[^"]*\.x?html?[^"]*"[^>]*>(.*?)</a>',
            r'\1',
            inner,
            flags=re.S,
        )
        # Also flatten self-closing <a> anchor tags (page markers) inside the heading.
        inner = re.sub(r'<a[^>]*/>', '', inner)
        return f'<h1{attrs}>{inner}</h1>'

    html = re.sub(r'<h1([^>]*)>(.*?)</h1>', fix_h1, html, flags=re.S)

    return html


# ============================================================
# Markdown postprocessing — final tidying
# ============================================================

def postprocess_markdown(md: str) -> str:
    """Final tidying of the html2text output."""

    # Drop chapter-title-anchor patterns that survived the pre-process.
    # Pattern: "# [text](file.htm#anchor)" possibly spanning multiple lines.
    md = re.sub(
        r'^\s*#+\s*\[([^\]]+)\]\([^)]*\.x?html?[^)]*\)\s*\n',
        '',
        md,
        flags=re.M | re.S,
    )

    # Drop "# [CHAPTER 13](...)" style standalone TOC-link headings entirely
    # (Fagell does this twice in a row at the top of every chapter)
    md = re.sub(
        r'^\s*#+\s*\[[^\]]+\]\([^)]+\)\s*\n',
        '',
        md,
        flags=re.M,
    )

    # Drop empty headings (chapter graphics stripped out leave these behind)
    md = re.sub(r'<h[1-6]>\s*</h[1-6]>\s*\n?', '', md)
    md = re.sub(r'^#+\s*\n', '', md, flags=re.M)

    # Drop leading top-level (#) H1 headings that just repeat the chapter
    # title. Our excerpt header writes the title above the body, so any H1
    # that comes through from the source is redundant. We iterate so books
    # like Fagell (which emit two H1s: "CHAPTER 13" and the chapter name) get
    # cleaned up. Stops at the first non-H1 line (paragraph, ##, list, etc.).
    lines = md.lstrip().split('\n')
    while lines and re.match(r'^#\s+', lines[0]):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    md = '\n'.join(lines)

    # After stripping the chapter-title H1, any remaining H1s in the body
    # are actually section heads (Fagell uses H1 for major section breaks
    # within a chapter, for example). Demote them to H2 so the heading
    # hierarchy is consistent across all excerpts: H1 = chapter title (lives
    # in the wrapper above the body), H2 = section, H3 = subsection.
    md = re.sub(r'^#\s+', '## ', md, flags=re.M)

    # Collapse 3+ blank lines into 2
    md = re.sub(r'\n{3,}', '\n\n', md)

    return md.strip() + '\n'


# ============================================================
# Pipeline driver
# ============================================================

def extract_epub_excerpt(spec: dict, out_path: Path):
    epub_path = BOOKS / spec["epub"]
    if not epub_path.exists():
        print(f"  skip: {epub_path.name} not found")
        return

    combined_html = ""
    with zipfile.ZipFile(epub_path) as z:
        for f in spec["xhtml_files"]:
            with z.open(f) as fh:
                combined_html += fh.read().decode("utf-8") + "\n"

    combined_html = preprocess_xhtml(combined_html)

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0
    md = h.handle(combined_html)
    md = postprocess_markdown(md)

    header = (
        f"# {spec['title']}\n\n"
        f"*Excerpt from {spec['source_book']}. {spec['blurb']}*\n\n---\n\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + md, encoding="utf-8")
    print(f"  wrote {out_path.relative_to(ROOT)} ({len(md):,} chars)")


def extract_pdf_excerpt(spec: dict, out_path: Path):
    pdf_path = BOOKS / spec["pdf"]
    if not pdf_path.exists():
        print(f"  skip: {pdf_path.name} not found")
        return
    if not shutil.which("pdftotext"):
        print(f"  skip: pdftotext not on PATH (install via 'brew install poppler')")
        return

    first, last = spec["pages"]
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["pdftotext", "-layout", "-f", str(first), "-l", str(last),
             str(pdf_path), tmp_path],
            check=True, capture_output=True,
        )
        text = Path(tmp_path).read_text(encoding="utf-8")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    md_body = cushman_text_to_markdown(text, spec.get("footers", []))
    header = (
        f"# {spec['title']}\n\n"
        f"*Excerpt from {spec['source_book']}. {spec['blurb']}*\n\n---\n\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + md_body, encoding="utf-8")
    print(f"  wrote {out_path.relative_to(ROOT)} ({len(md_body):,} chars)")


def cushman_text_to_markdown(text: str, footers: list[str]) -> str:
    """Convert pdftotext output into clean markdown, handling page footers,
    hard-wrapped paragraphs, section headers, and student-quote attributions."""

    # Strip recurring page footers (chapter title pages, etc.)
    for footer in footers:
        text = re.sub(
            rf"^\s*\d+\s+{re.escape(footer)}\s*$",
            "",
            text,
            flags=re.M | re.I,
        )
        text = re.sub(
            rf"^\s*{re.escape(footer)}\s+\d+\s*$",
            "",
            text,
            flags=re.M | re.I,
        )

    # Strip bare page numbers and chapter-opening title/epigraph
    text = re.sub(r"^\s*\d{1,3}\s*$", "", text, flags=re.M)
    text = re.sub(r"^\s*chapter \d+\s*\n+[^\n]+\n", "", text, count=1, flags=re.I)
    text = re.sub(r'^\s*[“"][^”"]+[”"]\s*\n', "", text, count=1)

    blocks = re.split(r"\n\s*\n+", text)
    out_blocks = []
    for raw_block in blocks:
        if not raw_block.strip():
            continue
        raw_lines = [ln.rstrip() for ln in raw_block.split("\n") if ln.strip()]
        if not raw_lines:
            continue
        is_indented = raw_lines[0].startswith("    ")
        joined = " ".join(ln.strip() for ln in raw_lines)
        joined = re.sub(r"\s+", " ", joined).strip()

        # Fix PDF dropcap split ("S tudents" -> "Students")
        joined = re.sub(r"^([A-Z]) ([a-z])", r"\1\2", joined)
        # Rejoin lowercase-hyphen-space-lowercase ("elemen- tary" -> "elementary")
        joined = re.sub(r"([a-z]{2,})- ([a-z]{2,})", r"\1\2", joined)

        letters = re.sub(r"[^A-Za-z]", "", joined)
        if (5 <= len(joined) <= 70 and letters
                and sum(1 for c in letters if c.isupper()) / max(len(letters), 1) > 0.85
                and not re.search(r"[.!?]$", joined)):
            out_blocks.append(f"### {joined.title()}")
            continue

        m = re.search(
            r"\s+([A-Z][A-Z’']{1,20}(?:\s+[A-Z][A-Z’']{1,20}){0,2})\s*$",
            joined,
        )
        if is_indented and m and len(m.group(1)) >= 3:
            attribution = m.group(1).strip()
            quote_text = joined[:m.start()].rstrip().rstrip(",")
            attr_display = " ".join(w.title() for w in attribution.split())
            out_blocks.append(f"> {quote_text}\n>\n> — **{attr_display}**")
            continue

        out_blocks.append(joined)

    body = "\n\n".join(out_blocks)
    body = re.sub(r" +", " ", body)
    return body + "\n"


def main():
    EXCERPTS.mkdir(exist_ok=True)
    print(f"Extracting excerpts to {EXCERPTS.relative_to(ROOT)}/\n")

    print("EPUB sources:")
    for rel_out, spec in EPUB_SOURCES.items():
        extract_epub_excerpt(spec, EXCERPTS / rel_out)

    print("\nPDF sources:")
    for rel_out, spec in PDF_SOURCES.items():
        extract_pdf_excerpt(spec, EXCERPTS / rel_out)

    print("\nDone. Next step: rerun the portable build to pick up the refreshed excerpts.")
    print("    python3 scripts/build-portable.py")


if __name__ == "__main__":
    main()
