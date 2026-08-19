#!/usr/bin/env python3
from __future__ import annotations
"""Build the portable, single-file edition of Talking with Teens.

What this does
--------------
Reads the site source files (index.html, library.html, module-N.html, style.css)
and the chapter excerpts under excerpts/module-N/, then assembles them into one
self-contained HTML file at portable/talking-with-teens.html.

Writes two local files under portable/ (both gitignored — they embed
copyrighted chapter excerpts and must not go on the public site):

  portable/talking-with-teens.html            local-use; native players when media/ exists
  portable/talking-with-teens-shareable.html  iframe embeds only; still excerpted; noindex

The resulting file:
  - Inlines all CSS, no external stylesheet needed
  - Embeds chapter excerpts INLINE inside each step (visible by default)
  - Embeds YouTube and Apple Podcasts players where the URL is known
  - Uses SPA-style navigation (one section visible at a time, hash routing)
  - Works offline for the reading; media embeds need internet to play

Usage
-----
From the project root:

    python3 scripts/build-portable.py

One-time setup (install the markdown dependency):

    pip3 install markdown

Adding a new module
-------------------
1. Build module-N.html in the project root, following module-1's skeleton.
2. Drop the relevant chapter excerpts into excerpts/module-N/ as markdown.
3. Add the module to PAGES and TITLES below.
4. Add per-step excerpts to EXCERPTS_BY_STEP, keyed by (module-id, step-number).
5. If new step-source URLs are embeddable (YouTube, Apple Podcasts), add them
   to EMBED_REGISTRY.
6. Rerun this script.
"""

import re
import sys
from pathlib import Path

try:
    import markdown as md
except ImportError:
    sys.exit(
        "Missing dependency. Install it with:\n"
        "    pip3 install markdown\n"
    )

# ---- Project paths (resolved relative to this script's location) ----
ROOT = Path(__file__).resolve().parent.parent
EXCERPTS = ROOT / "excerpts"
OUT = ROOT / "portable" / "talking-with-teens.html"

# ---- Which site pages to include, in display order ----
PAGES = {
    "home":      "index.html",
    "scenarios": "scenarios.html",
    "library":   "library.html",
    "module-1":  "module-1.html",
    "module-2":  "module-2.html",
    "module-3":  "module-3.html",
    "module-4":  "module-4.html",
    "module-5":  "module-5.html",
    "module-6":  "module-6.html",
}

# ---- Page <title> strings for the document title swap ----
TITLES = {
    "home":      "Talking with Teens",
    "scenarios": "Scenarios - Talking with Teens",
    "library":   "The Library - Talking with Teens",
    "module-1":  "Module I: The Adolescent Brain - Talking with Teens",
    "module-2":  "Module II: Listening Before Talking - Talking with Teens",
    "module-3":  "Module III: Silence, Shutdown, and Boys - Talking with Teens",
    "module-4":  "Module IV: Friendship and Belonging - Talking with Teens",
    "module-5":  "Module V: Conflict, Limits, and Repair - Talking with Teens",
    "module-6":  "Module VI: What Students Actually Want from Us - Talking with Teens",
}

# ---- Per-step excerpt mapping ----
# Keyed by (module-id, step-number). Value is a list of
# (path-relative-to-excerpts/, display-label) tuples.
# Excerpts render inline inside the step, visible by default.
EXCERPTS_BY_STEP = {
    ("module-1", 2): [
        ("module-1/siegel-part1-essence.md",
         "Siegel, <em>Brainstorm</em> &middot; Part I: The Essence of Adolescence"),
    ],
    ("module-1", 3): [
        ("module-1/damour-ch1-emotion-101.md",
         "Damour, <em>Emotional Lives of Teenagers</em> &middot; Chapter 1: Adolescent Emotion 101"),
    ],
    ("module-2", 2): [
        ("module-2/faber-ch1-dealing-with-feelings.md",
         "Faber &amp; Mazlish, <em>How to Talk So Teens Will Listen</em> &middot; Chapter 1: Dealing with Feelings"),
        ("module-2/faber-ch2-making-sure.md",
         "Faber &amp; Mazlish, <em>How to Talk So Teens Will Listen</em> &middot; Chapter 2: We&rsquo;re Still &ldquo;Making Sure&rdquo;"),
    ],
    ("module-2", 3): [
        ("module-2/damour-ch4-expressing-feelings.md",
         "Damour, <em>Emotional Lives of Teenagers</em> &middot; Chapter 4: Helping Teens Express Their Feelings"),
    ],
    ("module-3", 2): [
        ("module-3/natterson-ch1-how-to-talk-to-boys.md",
         "Natterson, <em>Decoding Boys</em> &middot; Chapter 1: How to Talk to Boys"),
        ("module-3/natterson-ch3-puberty-timing.md",
         "Natterson, <em>Decoding Boys</em> &middot; Chapter 3: Yes, Your Nine-Year-Old Might Be in Puberty"),
    ],
    ("module-3", 3): [
        ("module-3/damour-ch5-regaining-control.md",
         "Damour, <em>Emotional Lives of Teenagers</em> &middot; Chapter 5: Helping Teens Regain Emotional Control"),
    ],
    ("module-4", 2): [
        ("module-4/neufeld-ch1-why-parents-matter.md",
         "Neufeld &amp; Mat&eacute;, <em>Hold On to Your Kids</em> &middot; Chapter 1: Why Parents Matter More Than Ever"),
        ("module-4/neufeld-ch2-skewed-attachments.md",
         "Neufeld &amp; Mat&eacute;, <em>Hold On to Your Kids</em> &middot; Chapter 2: Skewed Attachments, Subverted Instincts"),
    ],
    ("module-4", 3): [
        ("module-4/fagell-ch6-shifting-friendships.md",
         "Fagell, <em>Middle School Matters</em> &middot; Chapter 6: Managing Shifting Friendships"),
    ],
    ("module-5", 2): [
        ("module-5/faber-ch3-punish-or-not.md",
         "Faber &amp; Mazlish, <em>How to Talk So Teens Will Listen</em> &middot; Chapter 3: To Punish or Not to Punish"),
        ("module-5/faber-ch4-working-it-out.md",
         "Faber &amp; Mazlish, <em>How to Talk So Teens Will Listen</em> &middot; Chapter 4: Working It Out Together"),
    ],
    ("module-5", 3): [
        ("module-5/siegel-part4-staying-present.md",
         "Siegel, <em>Brainstorm</em> &middot; Part IV: Staying Present Through Changes and Challenges"),
    ],
    ("module-6", 2): [
        ("module-6/cushman-ch2-teacher-on-our-side.md",
         "Cushman &amp; Rogers, <em>Fires in the Middle School Bathroom</em> &middot; Chapter 2: A Teacher on Our Side"),
        ("module-6/cushman-ch4-confident-learners.md",
         "Cushman &amp; Rogers, <em>Fires in the Middle School Bathroom</em> &middot; Chapter 4: Helping Us Grow into Confident Learners"),
    ],
    ("module-6", 3): [
        ("module-6/fagell-ch13-intervening-when-struggling.md",
         "Fagell, <em>Middle School Matters</em> &middot; Chapter 13: Intervening When School Is a Struggle"),
    ],
}

# ---- Embed registry: URL substring -> embed config ----
# When a step-source URL contains one of these substrings, an embed is
# injected after the step-source line. Each value is a dict with:
#   "local_basename" - filename stem to look for in media/; if found, build
#                      uses a native <audio>/<video> element instead of iframe
#   "iframe"         - HTML used when no local file is present (online embed)
EMBED_REGISTRY = {
    # Module I, Step 4 - Siegel Talks at Google (YouTube)
    "youtube.com/watch?v=kHZzhKyBW-I": {
        "local_basename": "m1-s4-siegel-talks-at-google",
        "iframe": (
            '<iframe class="step-embed-frame yt" '
            'src="https://www.youtube.com/embed/kHZzhKyBW-I" '
            'title="Brainstorm - Daniel Siegel at Talks at Google" '
            'frameborder="0" '
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            'allowfullscreen></iframe>'
        ),
    },
    # Module II, Step 1 - Adele Faber on The Psych Files Ep 135 (Apple Podcasts)
    "thepsychfiles.com/2010/11/episode-135": {
        "local_basename": "m2-s1-faber-psych-files-135",
        "iframe": (
            '<iframe class="step-embed-frame apple" '
            'allow="autoplay *; encrypted-media *; clipboard-write" '
            'frameborder="0" '
            'sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation" '
            'src="https://embed.podcasts.apple.com/us/podcast/adele-faber-interview-on-parenting-part-1/id215516451?i=1000581549886"></iframe>'
        ),
    },
    # Module II, Step 4 - Damour on Kate Bowler (Apple Podcasts)
    "katebowler.com/podcasts/how-to-talk-to-teenagers": {
        "local_basename": "m2-s4-damour-kate-bowler",
        "iframe": (
            '<iframe class="step-embed-frame apple" '
            'allow="autoplay *; encrypted-media *; clipboard-write" '
            'frameborder="0" '
            'sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation" '
            'src="https://embed.podcasts.apple.com/us/podcast/lisa-damour-how-to-talk-to-teenagers/id1341076079?i=1000706490055"></iframe>'
        ),
    },
    # Module IV, Step 1 - What Fresh Hell with Maté and Neufeld (Apple Podcasts)
    "whatfreshhellpodcast.com/fresh-take-dr-gabor-mate-and-dr-gordon-neufeld": {
        "local_basename": "m4-s1-mate-neufeld-what-fresh-hell",
        "iframe": (
            '<iframe class="step-embed-frame apple" '
            'allow="autoplay *; encrypted-media *; clipboard-write" '
            'frameborder="0" '
            'sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation" '
            'src="https://embed.podcasts.apple.com/us/podcast/fresh-take-dr-gabor-mat%C3%A9-and-dr-gordon-neufeld-on/id1170073178?i=1000650822534"></iframe>'
        ),
    },
    # Module V, Step 4 - Ask Lisa Ep 170 (Apple Podcasts)
    "drlisadamour.com/resource/how-should-i-deal-with-my-angry-disrespectful-son": {
        "local_basename": "m5-s4-damour-ask-lisa-170",
        "iframe": (
            '<iframe class="step-embed-frame apple" '
            'allow="autoplay *; encrypted-media *; clipboard-write" '
            'frameborder="0" '
            'sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation" '
            'src="https://embed.podcasts.apple.com/us/podcast/170-how-should-i-deal-with-my-angry-disrespectful-son/id1525689066?i=1000655521203"></iframe>'
        ),
    },
}

# Sources that aren't embeddable online (no clean iframe available) but DO
# have a designated local-file basename. When the user runs download-media.py
# and the file ends up in media/, the build will inject a native player for
# these even though they have no iframe fallback. Online: stays as text link.
LOCAL_ONLY_EMBEDS = {
    "npr.org/2016/04/15/474348291": {"local_basename": "m1-s1-npr-fresh-air-jensen"},
    "on-boys-podcast.com/decoding-boys-with-dr-cara-natterson": {"local_basename": "m3-s1-natterson-on-boys"},
    "mindfulmamamentor.com/decoding-boys-dr-cara-natterson-570": {"local_basename": "m3-s4-natterson-mindful-mama-570"},
    "mindfulmamamentor.com/hold-on-to-your-kids-dr-gabor-mate-481": {"local_basename": "m4-s4-mate-mindful-mama-481"},
    "drrobynsilverman.com/how-to-talk-when-kids-wont-listen": {"local_basename": "m5-s1-faber-king-silverman"},
    "offtheclockpsych.com/middle-school-matters": {"local_basename": "m6-s1-fagell-off-the-clock-272"},
}

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov"}


# ============================================================
# Glossary tooltips
# ============================================================
# Each entry: { definition: ..., excerpt_module: ..., excerpt_anchor: ..., aliases: [...] }
# The wrap_glossary_terms function wraps the first occurrence of each term
# (or its aliases) per module page in a <span class="glossary-term"> that
# shows a tooltip on hover/focus.
GLOSSARY = {
    "ESSENCE": {
        "definition": "Siegel's acronym for four developmental traits of adolescence: <strong>E</strong>motional spark, <strong>S</strong>ocial engagement, <strong>N</strong>ovelty-seeking, <strong>C</strong>reative exploration. Each is a feature of healthy development, not a defect.",
        "excerpt_module": "module-1",
        "excerpt_anchor": "excerpt-m1-siegel-part1-essence",
        "aliases": ["ESSENCE framework", "ESSENCE traits"],
    },
    "hyperrational": {
        "definition": "Siegel's term for how teens weigh decisions. They don't underweight consequences; they overweight reward. The risk-taking math is real, just tilted.",
        "excerpt_module": "module-1",
        "excerpt_anchor": "excerpt-m1-siegel-part1-essence",
        "aliases": ["hyperrationality", "hyperrational risk-taking"],
    },
    "acknowledgment moves": {
        "definition": "Faber and Mazlish's four practical steps for handling a teen's feelings: full attention, a sound like &ldquo;oh&rdquo; or &ldquo;mmm,&rdquo; naming the feeling, and giving in fantasy what you can't give in reality.",
        "excerpt_module": "module-2",
        "excerpt_anchor": "excerpt-m2-faber-ch1-dealing-with-feelings",
        "aliases": ["acknowledgement moves", "four moves"],
    },
    "ordinary suffering": {
        "definition": "Damour's distinction. Normal teenage distress (a bad day, a friend conflict, a missed opportunity) that doesn't require clinical intervention. The opposite of <em>trouble,</em> which does.",
        "excerpt_module": "module-1",
        "excerpt_anchor": "excerpt-m1-damour-ch1-emotion-101",
        "aliases": ["ordinary distress"],
    },
    "emotional regulation": {
        "definition": "Damour's umbrella term for two skills teens need: expressing emotions in healthy ways, and reining them in when appropriate. Distraction can be a healthy regulation tool; permanent avoidance is not.",
        "excerpt_module": "module-3",
        "excerpt_anchor": "excerpt-m3-damour-ch5-regaining-control",
        "aliases": ["emotion regulation", "regulating emotions"],
    },
    "swing to silence": {
        "definition": "Natterson's term for the cultural and biological pull boys feel toward withdrawal at puberty. Not a personality change; a predictable developmental shift the adult job is to stay close to.",
        "excerpt_module": "module-3",
        "excerpt_anchor": "excerpt-m3-natterson-ch1-how-to-talk-to-boys",
        "aliases": [],
    },
    "peer-orientation": {
        "definition": "Neufeld and Maté's central thesis. When kids orient primarily toward peers rather than adults for their attachment needs. Distinct from <em>peer attachment,</em> which is normal and healthy.",
        "excerpt_module": "module-4",
        "excerpt_anchor": "excerpt-m4-neufeld-ch1-why-parents-matter",
        "aliases": ["peer orientation", "peer-oriented"],
    },
    "collecting your kid": {
        "definition": "Neufeld and Maté's term for re-establishing connection before correction. Notice them, make eye contact, share a small moment, before issuing any direction or instruction.",
        "excerpt_module": "module-4",
        "excerpt_anchor": "excerpt-m4-neufeld-ch2-skewed-attachments",
        "aliases": ["collecting our kids", "collecting"],
    },
}


def wrap_glossary_terms(html: str, module_id: str) -> str:
    """Wrap the first occurrence of each glossary term in the body with a
    glossary-term span. Skips matches inside HTML tags, headings, source-citation
    lines, and step-excerpt blocks (excerpts are where terms are defined, so
    we don't link them to themselves)."""
    if module_id not in PAGES:
        return html

    # Split the html into "safe zones" (where we can wrap) and "skip zones"
    # (tags, headings, step-source, step-excerpt). We use a state-machine
    # approach with regex to find candidates only in prose <p> tags that
    # aren't step-source.
    used_terms = set()
    out_parts = []
    last_end = 0

    # Find each <p> that is plain prose (not step-source)
    # We iterate paragraphs; for each, scan for glossary terms.
    para_re = re.compile(r'<p(\s+[^>]*)?>(.*?)</p>', re.S)

    def replace_terms_in_paragraph(text):
        # Returns the paragraph text with first-unused terms wrapped
        for canonical, entry in GLOSSARY.items():
            if canonical in used_terms:
                continue
            patterns = [canonical] + entry.get("aliases", [])
            # Sort by length descending so longer aliases match first
            patterns.sort(key=len, reverse=True)
            for pat in patterns:
                # Word-boundary match, case-insensitive on first letter
                pat_re = re.compile(
                    r'(?<![A-Za-z])(' + re.escape(pat) + r')(?![A-Za-z])',
                    re.IGNORECASE,
                )
                m = pat_re.search(text)
                if m:
                    matched_text = m.group(1)
                    anchor_data = (
                        f' data-page="{entry["excerpt_module"]}" '
                        f'data-scroll="{entry["excerpt_anchor"]}"'
                    )
                    span = (
                        f'<span class="glossary-term" tabindex="0">'
                        f'{matched_text}'
                        f'<span class="glossary-tooltip" role="tooltip">'
                        f'<span class="glossary-tooltip-def">{entry["definition"]}</span>'
                        f'<a class="glossary-tooltip-link" '
                        f'href="#{entry["excerpt_module"]}"{anchor_data}>'
                        f'Read in context &rarr;'
                        f'</a>'
                        f'</span>'
                        f'</span>'
                    )
                    text = text[:m.start()] + span + text[m.end():]
                    used_terms.add(canonical)
                    break
        return text

    for m in para_re.finditer(html):
        attrs = m.group(1) or ""
        body = m.group(2)
        # Skip step-source, hero-lede, colophon, and similar non-prose paragraphs
        skip_classes = ("step-source", "hero-lede", "module-sub", "colophon",
                        "book-author", "book-why", "pair-note", "pair-alt",
                        "pair-none", "stop-card", "essential-q", "flip-hint")
        if any(f'class="{cls}"' in attrs or f"class='{cls}'" in attrs
               or f"class=\"{cls}" in attrs for cls in skip_classes):
            continue
        # Skip paragraphs inside step-excerpt-body (we know that's where terms are defined)
        # Simple heuristic: find the closest enclosing block.
        # For now: skip nothing extra; the per-page used_terms set prevents over-wrapping.

        new_body = replace_terms_in_paragraph(body)
        if new_body != body:
            # Replace the paragraph in html
            old_para = m.group(0)
            new_para = f'<p{attrs}>{new_body}</p>'
            # Substitute the FIRST occurrence (this exact paragraph)
            html = html.replace(old_para, new_para, 1)

    return html


def assign_excerpt_anchors(html: str, module_id: str) -> str:
    """Add id attributes to each step-excerpt block in a module's body so
    glossary tooltip 'Read in context' links can scroll to them. The id is
    derived deterministically from the excerpts in EXCERPTS_BY_STEP."""
    # Mapping: module_id -> list of basenames in display order
    excerpts_for_module = []
    for (mod, step), entries in EXCERPTS_BY_STEP.items():
        if mod == module_id:
            for path, _label in entries:
                basename = Path(path).stem  # e.g., "siegel-part1-essence"
                excerpts_for_module.append((module_id, basename))

    if not excerpts_for_module:
        return html

    # Find each step-excerpt block in order, assign ids
    def make_anchor(module_id, basename):
        mod_prefix = module_id.replace("module-", "m")
        return f"excerpt-{mod_prefix}-{basename}"

    excerpt_re = re.compile(r'(<div class="step-excerpt">)', re.S)
    matches = list(excerpt_re.finditer(html))
    if not matches:
        return html

    # Replace from last to first to preserve string positions
    for i in range(len(matches) - 1, -1, -1):
        if i >= len(excerpts_for_module):
            continue
        mod, basename = excerpts_for_module[i]
        anchor = make_anchor(mod, basename)
        m = matches[i]
        new_open = f'<div class="step-excerpt" id="{anchor}">'
        html = html[:m.start()] + new_open + html[m.end():]

    return html


def find_local_media(basename):
    """Return the first non-empty file in media/ whose stem matches basename,
    or None. Empty files (partial downloads, accidental touches) are ignored
    so they don't produce broken players in the build. Returns None when the
    build is running in shareable mode (so all embeds stay as iframes)."""
    if _SUPPRESS_LOCAL_MEDIA:
        return None
    media_dir = ROOT / "media"
    if not media_dir.exists():
        return None
    matches = [m for m in sorted(media_dir.glob(f"{basename}.*")) if m.stat().st_size > 0]
    return matches[0] if matches else None


def build_local_player(media_file):
    """Build a native <audio> or <video> element pointing at a local file.
    Path is relative to portable/talking-with-teens.html, so we use ../media/."""
    rel = f"../media/{media_file.name}"
    if media_file.suffix.lower() in VIDEO_EXTENSIONS:
        return (
            f'<video class="step-embed-frame local-video" '
            f'src="{rel}" controls preload="metadata" playsinline></video>'
        )
    return (
        f'<audio class="step-embed-frame local-audio" '
        f'src="{rel}" controls preload="metadata"></audio>'
    )


def build_embed_html(entry):
    """Return the HTML to inject for an embed entry: native player if a
    local file exists, otherwise the iframe fallback (or empty string)."""
    basename = entry.get("local_basename")
    if basename:
        local = find_local_media(basename)
        if local:
            return build_local_player(local)
    return entry.get("iframe", "")


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def extract_body(html):
    """Strip the doctype/html/head/masthead/footer, return only the inner content."""
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S)
    body = m.group(1) if m else html
    body = re.sub(r"<header class=\"masthead\">.*?</header>\s*", "", body, count=1, flags=re.S)
    body = re.sub(r"<footer>.*?</footer>\s*", "", body, count=1, flags=re.S)
    body = re.sub(r'<script src="site\.js"></script>\s*', "", body)
    return body.strip()


def md_to_html(text):
    """Convert excerpt markdown to HTML, scrubbing leftover EPUB-internal anchors."""
    # Convert chapter-header anchor links (broken EPUB internal links) to plain headings
    text = re.sub(
        r"^\s*#\s*\[([^\]]+)\]\([^)]*\.x?html?[^)]*\)\s*$",
        r"### \1",
        text,
        flags=re.M,
    )
    # Strip residual chapter-marker links that span lines
    text = re.sub(r"\[(_\w+_|\*\*\w+\*\*)[^\]]*\]\([^)]*\.x?html?[^)]*\)", "", text)
    text = re.sub(r"\(\s*\d+_epub[^)]*\)", "", text)

    html = md.markdown(text, extensions=["extra", "sane_lists"])
    # Drop empty heading tags left over where EPUB chapter graphics were stripped
    html = re.sub(r"<h[1-6]>\s*</h[1-6]>\s*", "", html)
    # Drop the "Excerpt from ..." preamble paragraph (and its trailing <hr>) that I added during extraction.
    # In the inline-reading view, the chapter title is shown by the surrounding step-excerpt-header.
    html = re.sub(r"<p><em>Excerpt from[^<]*</em></p>\s*<hr\s*/?>\s*", "", html, count=1)
    # Drop the leading <h1> that repeats the chapter title (we render that title in the wrapper header instead).
    html = re.sub(r"^\s*<h1>[^<]*</h1>\s*", "", html, count=1)
    return html


def build_inline_excerpt(rel_path, label):
    """Render an inline, open-by-default reading block for a single excerpt."""
    body_html = md_to_html(read_text(EXCERPTS / rel_path))
    return f"""
    <div class="step-excerpt">
      <div class="step-excerpt-header">{label}</div>
      <div class="step-excerpt-body">
{body_html}
      </div>
    </div>"""


# Regex: capture a whole step block. Each step is wrapped in a <div class="step">.
# The step block continues until its matching </div>. We rely on the source HTML's
# consistent two-space indentation to find the closing tag.
STEP_BLOCK_RE = re.compile(
    r'(?P<open><div class="step">)(?P<body>.*?)(?P<close>\n  </div>)',
    re.S,
)

STEP_NUM_RE = re.compile(r'<div class="step-num">(\d+)</div>')

STEP_SOURCE_RE = re.compile(r'<p class="step-source">.*?</p>', re.S)


def inject_into_step(step_html, module_id):
    """For one step block, inject the embed iframe (after the step-source line)
    and inline excerpts (before the step's closing div).
    """
    m = STEP_NUM_RE.search(step_html)
    if not m:
        return step_html
    step_num = int(m.group(1))

    # 1) Inject embed after the step-source paragraph. Check EMBED_REGISTRY
    # first (online iframe with optional local override), then LOCAL_ONLY_EMBEDS
    # (text-link sources that get a native player only when a local file exists).
    source_match = STEP_SOURCE_RE.search(step_html)
    if source_match:
        source_html = source_match.group(0)
        embed_html = ""
        for key, entry in EMBED_REGISTRY.items():
            if key in source_html:
                embed_html = build_embed_html(entry)
                break
        if not embed_html:
            for key, entry in LOCAL_ONLY_EMBEDS.items():
                if key in source_html:
                    local = find_local_media(entry["local_basename"])
                    if local:
                        embed_html = build_local_player(local)
                    break
        if embed_html:
            wrapped = f'{source_html}\n    <div class="step-embed">{embed_html}</div>'
            step_html = step_html.replace(source_html, wrapped, 1)

    # 2) Append inline excerpts (visible by default) at the end of the step
    excerpts = EXCERPTS_BY_STEP.get((module_id, step_num), [])
    for rel_path, label in excerpts:
        step_html = step_html + build_inline_excerpt(rel_path, label)

    return step_html


def transform_module(page_html, module_id):
    """Apply per-step transformations across a module page."""
    if not module_id.startswith("module-"):
        return page_html

    def replace_step(match):
        full_step = match.group(0)
        # The captured groups: open, body, close. Inject inside the body, then reassemble.
        body_with_injections = inject_into_step(
            match.group("open") + match.group("body"),
            module_id,
        )
        return body_with_injections + match.group("close")

    page_html = STEP_BLOCK_RE.sub(replace_step, page_html)

    # After steps and excerpts are injected, assign anchor IDs to excerpts
    # so glossary tooltips can scroll to them, then wrap glossary terms in
    # the page's prose.
    page_html = assign_excerpt_anchors(page_html, module_id)
    page_html = wrap_glossary_terms(page_html, module_id)

    return page_html


# ---- CSS additions specific to the single-file build ----
EXTRA_CSS = """
/* === Single-file build additions === */
.page { display: none; }
.page.active { display: block; animation: fade 0.15s ease; }
@keyframes fade { from { opacity: 0; } to { opacity: 1; } }

/* Inline reading blocks (chapter excerpts shown open by default inside steps) */
.step-excerpt {
  margin: 1.5rem 0 0.5rem -1rem;
  padding: 1.25rem 1.5rem 1.5rem 1.5rem;
  background: var(--cream-deep);
  border-radius: 3px;
  border-left: 4px solid var(--maroon);
  position: relative;
}
.step-excerpt-header {
  font-family: 'Playfair Display', serif;
  font-style: italic;
  color: var(--maroon-deep);
  font-size: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px dotted var(--rule);
  line-height: 1.35;
}
.step-excerpt-header::before {
  content: 'The chapter';
  display: inline-block;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 0.68rem;
  color: var(--gold);
  font-style: normal;
  font-weight: 800;
  margin-right: 0.6rem;
  padding: 0.18rem 0.45rem;
  background: var(--paper);
  border-radius: 2px;
  vertical-align: 0.1em;
}
.step-excerpt-body {
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--ink);
  max-height: 320px;
  overflow-y: auto;
  padding-right: 0.5rem;
  scrollbar-width: thin;
  scrollbar-color: var(--gold-soft) transparent;
}
.step-excerpt-body::-webkit-scrollbar { width: 8px; }
.step-excerpt-body::-webkit-scrollbar-track { background: transparent; }
.step-excerpt-body::-webkit-scrollbar-thumb { background: var(--gold-soft); border-radius: 4px; }
.step-excerpt-body p { margin-bottom: 0.7rem; }
.step-excerpt-body h1, .step-excerpt-body h2 {
  font-size: 1.1rem;
  font-style: italic;
  margin: 1rem 0 0.4rem;
  color: var(--maroon-deep);
}
.step-excerpt-body h3, .step-excerpt-body h4 {
  font-size: 1rem;
  font-style: italic;
  margin: 0.85rem 0 0.3rem;
  color: var(--maroon);
}
.step-excerpt-body em { color: var(--maroon); }
.step-excerpt-body hr { border: none; border-top: 1px dotted var(--rule); margin: 1.2rem 0; }
.step-excerpt-body blockquote {
  border-left: 3px solid var(--gold);
  padding-left: 0.85rem;
  margin: 0.8rem 0;
  font-style: italic;
  color: var(--ink-soft);
}

/* Media embed (YouTube / Apple Podcasts iframe inside a step) */
.step-embed {
  margin: 0.85rem 0 1.25rem;
  border-radius: 3px;
  overflow: hidden;
  box-shadow: 0 2px 14px var(--shadow);
}
.step-embed-frame.yt {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 0;
}
.step-embed-frame.apple {
  display: block;
  width: 100%;
  max-width: 660px;
  height: 175px;
  background: transparent;
  overflow: hidden;
}
.step-embed-frame.local-audio {
  display: block;
  width: 100%;
  max-width: 660px;
}
.step-embed-frame.local-video {
  display: block;
  width: 100%;
  max-height: 480px;
  background: #000;
}

/* Placeholder anchors (modules not yet built) render as inert chips */
.stop-card a[href="#"] {
  background: var(--cream-deep);
  color: var(--ink-soft);
  padding: 0.35rem 0.7rem;
  border-radius: 2px;
  cursor: default;
  pointer-events: none;
}
.stop-card a[href="#"]::after { content: ''; }
"""


_SUPPRESS_LOCAL_MEDIA = False


def build(*, suppress_local_media=False, out_filename="talking-with-teens.html",
          noindex=False, log_loaded=True):
    """Build a single portable HTML file.

    suppress_local_media=False (default): native <audio>/<video> players are
        injected wherever a matching file exists in media/. This is the
        local-use build.
    suppress_local_media=True: all embeds stay as iframes regardless of what's
        in media/. Used for the shareable colleague build. Still embeds
        excerpted chapter text — generate locally, do not deploy.
    """
    global _SUPPRESS_LOCAL_MEDIA
    _SUPPRESS_LOCAL_MEDIA = suppress_local_media

    style_css = read_text(ROOT / "style.css")

    pages = {}
    for pid, filename in PAGES.items():
        src = ROOT / filename
        if not src.exists():
            if log_loaded:
                print(f"  skip: {filename} not found", file=sys.stderr)
            continue
        body = extract_body(read_text(src))
        body = transform_module(body, pid)
        pages[pid] = body
        if log_loaded:
            print(f"  loaded: {filename}")

    sections = []
    for pid in PAGES:
        if pid in pages:
            klass = "page active" if pid == "home" else "page"
            sections.append(f'<section id="{pid}" class="{klass}">\n{pages[pid]}\n</section>')
    sections_html = "\n\n".join(sections)

    titles_js = ",\n    ".join(f"'{k}': '{v}'" for k, v in TITLES.items())

    noindex_meta = (
        '<meta name="robots" content="noindex, nofollow">\n'
        if noindex else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Talking with Teens - a portable reader</title>
<meta name="description" content="A self-contained reader for teachers and parents of teens. Seven books, six modules, paired with verified author interviews and reproduced chapter excerpts. Built in the Chunk-Chew-Check format.">
{noindex_meta}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700;1,900&family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
{style_css}
{EXTRA_CSS}
</style>
</head>
<body>

<header class="masthead">
  <div class="masthead-inner">
    <a href="#home" data-page="home" class="brand">Talking with Teens</a>
    <nav>
      <a href="#home" data-page="home" class="current">The Path</a>
      <a href="#scenarios" data-page="scenarios">Scenarios</a>
      <a href="#library" data-page="library">Library</a>
      <a href="#home" data-page="home" data-scroll="about">About</a>
    </nav>
    <div class="role-toggle masthead-role" role="tablist" aria-label="Read as parent or teacher">
      <button type="button" class="role-pill active" data-role="parent" role="tab" aria-selected="true">Parents</button>
      <button type="button" class="role-pill" data-role="teacher" role="tab" aria-selected="false">Teachers</button>
    </div>
  </div>
</header>

<main>
{sections_html}
</main>

<footer>
  <p class="colophon">A reader assembled by Mr. B Social Studies</p>
  <p>Alderwood Middle School &middot; Edmonds School District &middot; Portable edition with embedded excerpts and media players</p>
  <p style="margin-top:1rem; font-size:0.78rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--gold);">Set in Playfair Display &amp; Nunito</p>
</footer>

<script>
(function() {{
  const TITLES = {{
    {titles_js}
  }};

  function show(pageId, scrollAnchor) {{
    if (!document.getElementById(pageId)) pageId = 'home';
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    document.title = TITLES[pageId] || 'Talking with Teens';
    document.querySelectorAll('.masthead nav a').forEach(a => {{
      a.classList.toggle('current', a.dataset.page === pageId);
    }});
    if (scrollAnchor) {{
      const el = document.getElementById(scrollAnchor);
      if (el) {{ el.scrollIntoView({{ behavior: 'smooth', block: 'start' }}); return; }}
    }}
    window.scrollTo({{ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' }});
  }}

  function hrefToPageId(href) {{
    if (!href) return null;
    if (href.startsWith('#')) {{
      const h = href.slice(1);
      return h || 'home';
    }}
    if (href.endsWith('.html')) {{
      let base = href.replace(/\\.html$/, '');
      if (base === 'index') base = 'home';
      return base;
    }}
    return null;
  }}

  document.body.addEventListener('click', function(e) {{
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href) return;
    if (href.startsWith('http') || href.startsWith('mailto:')) return;
    const scrollAnchor = a.dataset.scroll || null;
    const pageId = hrefToPageId(href);
    if (!pageId) return;
    if (document.getElementById(pageId)) {{
      e.preventDefault();
      history.pushState({{ page: pageId, scroll: scrollAnchor }}, '', '#' + pageId);
      show(pageId, scrollAnchor);
    }}
  }});

  window.addEventListener('popstate', function(e) {{
    const state = e.state || {{}};
    const pageId = state.page || (location.hash ? location.hash.slice(1) : 'home');
    show(pageId, state.scroll);
  }});

  const initial = location.hash ? location.hash.slice(1) : 'home';
  show(initial);
}})();
</script>

</body>
</html>
"""

    site_js = read_text(ROOT / "site.js")
    html = html.replace("</body>", f"<script>\n{site_js}\n</script>\n</body>", 1)

    out_path = OUT.parent / out_filename
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"  Wrote {out_path.relative_to(ROOT)} ({size_kb:.1f} KB)")


def main():
    print(f"Building portable files from {ROOT}/\n")
    print("Local build (uses media/ files when present):")
    build(
        suppress_local_media=False,
        out_filename="talking-with-teens.html",
        noindex=False,
    )
    print("\nShareable build (iframes only, excerpted, gitignored, noindex):")
    build(
        suppress_local_media=True,
        out_filename="talking-with-teens-shareable.html",
        noindex=True,
        log_loaded=False,
    )
    print("\nDone.")


if __name__ == "__main__":
    main()
