# Talking with Teens — a reader for teachers

A curated mini-course on understanding and communicating with middle schoolers. Built around 7 books, each paired with a verified audio/video companion, organized into 6 thematic modules using the Chunk-Chew-Check format.

## Suggested deployment

Three options:

1. **Subdomain on your existing ecosystem**: `teens.mrbsocialstudies.org` — matches your `current.`, `scotus.`, `teaching.`, `ss8.` pattern. Probably the right home.
2. **As a subdirectory of `teaching.mrbsocialstudies.org`**: lives at `/talking-with-teens/`.
3. **Standalone repo**: cleanest if you might want to share publicly.

## File structure

```
/
├── README.md                 This file
├── library.html              Books paired with verified author interviews + cross-cutting reading
├── module-1.html             Module I: The Adolescent Brain (full Chunk-Chew-Check template)
├── module-2.html             Module II: Listening Before Talking
├── style.css                 Shared stylesheet
│                             (index.html still to be reconstructed)
│
├── books/                    Raw source files (EPUB and PDF). Local only, don't deploy.
│   ├── brainstorm-siegel.epub
│   ├── decoding-boys-natterson.epub
│   ├── emotional-lives-damour.epub
│   ├── fires-in-the-bathroom-cushman.pdf
│   ├── hold-on-to-your-kids-neufeld.epub
│   ├── how-to-talk-faber.epub
│   └── middle-school-matters-fagell.epub
│                             All seven library books accounted for.
│
├── scripts/                  Build tools.
│   └── build-portable.py     Regenerates portable/talking-with-teens.html
│
├── portable/                 Single-file portable build. Local only, don't deploy.
│   └── talking-with-teens.html
│
└── excerpts/                 Extracted chapters as markdown, organized per module.
    ├── module-1/             The Adolescent Brain
    │   ├── siegel-part1-essence.md
    │   └── damour-ch1-emotion-101.md
    ├── module-2/             Listening Before Talking
    │   ├── faber-ch1-dealing-with-feelings.md
    │   ├── faber-ch2-making-sure.md   (the cooperation chapter)
    │   └── damour-ch4-expressing-feelings.md
    ├── module-3/             Silence, Shutdown, and Boys
    │   ├── damour-ch5-regaining-control.md
    │   ├── natterson-ch1-how-to-talk-to-boys.md
    │   └── natterson-ch3-puberty-timing.md
    ├── module-5/             Conflict, Limits, and Repair
    │   ├── faber-ch3-punish-or-not.md
    │   ├── faber-ch4-working-it-out.md
    │   └── siegel-part4-staying-present.md
    └── module-6/             What Students Actually Want from Us
        ├── cushman-ch2-teacher-on-our-side.md
        ├── cushman-ch4-confident-learners.md
        └── fagell-ch13-intervening-when-struggling.md
```

The site itself is just what's at the root: HTML, CSS, README. The `books/` and `excerpts/` folders are working source materials and should stay out of any GitHub Pages deploy (a `.gitignore` line like `books/` and `excerpts/` does it).

## What's built so far

- **The Path** (`index.html`) — six modules laid out as a vertical journey, each with an essential question, source books, and time estimate. Modules I, II, and III link to built pages; IV, V, and VI are placeholders.
- **The Library** (`library.html`) — seven books, each paired with a real, currently-published audio or video companion. Plus a cross-cutting section pointing to authors' columns and resource sites.
- **Module I** (`module-1.html`) — Foundations. The Adolescent Brain. Built on Siegel and Damour.
- **Module II** (`module-2.html`) — Communication Base. Listening Before Talking. Built on Faber & Mazlish and Damour.
- **Module III** (`module-3.html`) — When the Door Closes. Silence, Shutdown, and Boys. Built on Natterson and Damour.
- **Module V** (`module-5.html`) — Friction. Conflict, Limits, and Repair. Built on Faber & Mazlish, Siegel, and Damour.
- **Module VI** (`module-6.html`) — Practice. What Students Actually Want from Us. Built on Cushman & Rogers, and Fagell.
- Module IV (Friendship and Belonging) is the remaining placeholder.

## Building the portable file

There's a single-file edition of the reader at `portable/talking-with-teens.html` that bundles the site, the brand styling, and the chapter excerpts into one HTML file. Double-click it, your browser opens it, no install or internet needed. It's for sharing with colleagues directly rather than for public deployment (since it embeds copyrighted chapter text).

To regenerate it after adding a new module or new excerpts:

```bash
# One-time setup
pip3 install markdown

# Rebuild
cd ~/Downloads/teenagers
python3 scripts/build-portable.py
```

The script picks up everything in the project automatically. When you add a Module IV, edit the `PAGES` and `EXCERPTS_BY_MODULE` dicts near the top of `scripts/build-portable.py` to include it.

### Downloading the podcasts and video for offline playback (optional)

The portable file uses online iframe embeds for media (YouTube + Apple Podcasts) by default. To make it truly offline-capable, you can download the audio for every step that has a primary listen, plus the Siegel YouTube video, into a `media/` folder. The build script automatically detects local files and swaps the iframes for native HTML5 audio/video players that play offline.

```bash
# One-time setup
pip3 install yt-dlp

# Download all media (~400 MB after everything resolves)
python3 scripts/download-media.py

# Rebuild the portable file; it'll pick up the local media
python3 scripts/build-portable.py
```

After that, `portable/talking-with-teens.html` references files in `media/` via `../media/filename.mp4`. To share the offline bundle with a colleague, zip the `portable/` folder together with the `media/` folder; they need to be siblings for the relative paths to work.

A few notes:

The `media/` folder is in `.gitignore`. None of the downloaded audio or video gets pushed to the public GitHub site. The site continues to use the online iframe embeds.

Some sources won't resolve via `yt-dlp` (NPR's media player is one; Apple Podcasts is another, since it's an aggregator not a host). The script logs which downloads failed and which were skipped, and the build falls back to iframes for any source that doesn't have a local file. To resolve a stubborn one manually, find the show's RSS feed, locate the episode's `.mp3` enclosure URL, and either drop the file in `media/` with the matching basename (see SOURCES in `scripts/download-media.py` for names) or paste the URL into `MANUAL_OVERRIDES` near the top of the same file.

Sharing the downloaded media is a copyright matter to make a deliberate decision about. Personal offline listening on a commute is fine. Posting the bundle on a Drive folder shared with a hundred colleagues is the kind of thing rights-holders care about more.

## To clone for Modules II–VI

Each module page follows the same skeleton:

1. **Header**: kicker (Module N · category), title, sub-line
2. **Essential question callout** (`.module-essential`)
3. **Meta bar**: time breakdown
4. **Intro paragraphs**: 2–3 paragraphs framing the module
5. **Thesis callout**: the one-sentence argument of the module
6. **Steps** (numbered, usually 3–4): each contains:
   - Step type (e.g. "Step One · Watch First")
   - Title + time chip
   - Source citation
   - Intro paragraph
   - Three `.ccc-phase` blocks: Chunk → Chew → Check
   - Optional `.pull` quote
7. **Module-level reflection** (`.reflection` block — maroon/gold)
8. **Closing paragraphs** bridging to next module
9. **Next-up nav**: back / library / continue

Copy `module-1.html`, swap the content, update navigation links and the entry in `index.html`.

## Audit notes

The library was audited against actual published material. Items that couldn't be verified were removed or rewritten. Confirmed pairings:

- **Brainstorm (Siegel)** → Talks at Google YouTube talk + Frances Jensen NPR Fresh Air interview
- **The Emotional Lives of Teenagers (Damour)** → TELUS Talks YouTube interview + Social Work Podcast Eps 134/135 + ongoing Ask Lisa podcast
- **How to Talk So Teens Will Listen (Faber & Mazlish)** → Adele Faber interview on The Psych Files podcast
- **Middle School Matters (Fagell)** → Psychologists Off the Clock Ep. 272 + Fagell's own Middle School Walk & Talk podcast (AMLE)
- **Decoding Boys (Natterson)** → On Boys Podcast + Natterson's own Puberty Podcast
- **Fires in the Middle School Bathroom (Cushman)** → no verified author interview; What Kids Can Do org links and Edutopia student-voice content used as thematic substitutes
- **Hold On to Your Kids (Neufeld & Maté)** → What Fresh Hell podcast (rare dual-author appearance) + Mindful Mama Ep. 481

The original Module I opened with a fabricated Lisa Damour TEDxCLE title ("The Two Most Important Questions to Ask a Stressed Teen"). That step now opens with the verified Frances Jensen NPR Fresh Air interview, which is a better fit for the module's brain-development focus anyway.

## Brand notes

- **Fonts**: Playfair Display (italic display) + Nunito (body) — Google Fonts
- **Palette**:
  - `--cream`: `#F8F1E2` (page background)
  - `--paper`: `#FDF9EE` (card background)
  - `--maroon`: `#7A1F1F` / `--maroon-deep`: `#5A1414`
  - `--gold`: `#B8892E` / `--gold-bright`: `#D4A93C` / `--gold-soft`: `#E8D49A`
  - `--ink`: `#2A1F14`

## Things you might add later

- Search box (lunr.js works without a backend on GH Pages)
- Progress indicator using localStorage
- Embedded YouTube players inside module pages
- Printable PDF version of each module (`@media print` rules are in `style.css`)
- An Obsidian template for capturing module reflections back into your vault
