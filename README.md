# Talking with Teens — a reader for teachers and parents

A curated mini-course on understanding and communicating with middle schoolers. Built around 7 books, each paired with a verified audio/video companion, organized into 6 thematic modules using the Chunk-Chew-Check format.

Live at [teens.mrbsocialstudies.org](https://teens.mrbsocialstudies.org/).

## What's here

The public site is the HTML and CSS at the repo root, plus `site.js` and `favicon.svg`. GitHub Pages publishes that set. Working source materials stay local.

```
/
├── index.html                The Path — six modules as a vertical journey
├── scenarios.html            Twelve situations, parent/teacher views
├── library.html              Seven books + verified author interviews
├── module-1.html … module-6.html
├── style.css
├── site.js                   Role toggle, progress, HTTPS upgrade
├── favicon.svg
├── CNAME                     teens.mrbsocialstudies.org
├── _config.yml               Keeps portable/ and scripts/ off Pages
│
├── books/                    Raw EPUB/PDF sources. Local only, don't deploy.
├── excerpts/                 Extracted chapters as markdown, per module.
├── media/                    Downloaded audio/video for offline portable use.
├── portable/                 Single-file builds with embedded excerpts.
│                             Local only. Do not commit or deploy.
└── scripts/
    ├── build-portable.py     Regenerates portable/*.html
    ├── extract-excerpts.py   Pulls chapters from books/ into excerpts/
    └── download-media.py     Optional offline audio/video into media/
```

`books/`, `excerpts/`, `media/`, and `portable/` are gitignored. They contain copyrighted text or media.

## The reader

- **The Path** (`index.html`) — six modules, each with an essential question, source books, and a time estimate for the core path (steps 1–3 plus Checks). Optional Step 4 listens are extra. Progress is stored in the browser.
- **Scenarios** (`scenarios.html`) — twelve common situations with the move to try. Parent and teacher views; the same toggle lives in the header on every page.
- **The Library** (`library.html`) — seven books, each paired with a real, currently-published audio or video companion, plus a flip-side cheat sheet.
- **Module I** — Foundations. The Adolescent Brain. Siegel and Damour.
- **Module II** — Communication Base. Listening Before Talking. Faber & Mazlish and Damour.
- **Module III** — When the Door Closes. Silence, Shutdown, and Boys. Natterson and Damour.
- **Module IV** — The Social World. Friendship and Belonging. Neufeld & Maté and Fagell.
- **Module V** — Friction. Conflict, Limits, and Repair. Faber & Mazlish, Siegel, and Damour.
- **Module VI** — Practice. What Students Actually Want from Us. Cushman & Rogers and Fagell.

Core path is about **14 hours**. Optional listens add more.

## Building the portable file

There is a single-file edition that bundles the site, the brand styling, and the chapter excerpts into one HTML file. Double-click it, the browser opens it, no install needed. It is for sharing with a colleague directly — not for the public site, because it embeds copyrighted chapter text.

To regenerate it after adding a module or excerpts:

```bash
pip3 install markdown
python3 scripts/build-portable.py
```

That writes (locally, gitignored):

- `portable/talking-with-teens.html` — uses files in `media/` when present
- `portable/talking-with-teens-shareable.html` — iframe embeds only; still excerpted

When you add a module, edit the `PAGES` and `EXCERPTS_BY_STEP` dicts near the top of `scripts/build-portable.py`.

### Downloading podcasts and video for offline playback (optional)

```bash
pip3 install yt-dlp
python3 scripts/download-media.py
python3 scripts/build-portable.py
```

After that, `portable/talking-with-teens.html` references files in `media/` via `../media/filename.mp4`. To share the offline bundle, zip `portable/` together with `media/` as siblings.

Some sources will not resolve via yt-dlp (NPR's player; Apple Podcasts as an aggregator). The script logs failures; the build falls back to iframes. For a stubborn one, find the show's RSS enclosure URL and either drop the file in `media/` with the matching basename or paste the URL into `MANUAL_OVERRIDES` in `scripts/download-media.py`.

Sharing downloaded media is a copyright decision. Personal offline listening is one thing. Posting the bundle on a Drive folder for a hundred colleagues is another.

## Module skeleton

Each module page follows the same shape:

1. **Header**: kicker (Module N · category), title, sub-line
2. **Essential question** (`.module-essential`)
3. **Meta bar**: time breakdown for the core path (optional Step 4 not counted)
4. **Intro**: 2–3 paragraphs framing the module
5. **Thesis**: the one-sentence argument
6. **Steps** (usually 4; Step 4 is optional): Chunk → Chew → Check. Checks that are role-specific use `data-audience="parent"` / `data-audience="teacher"`.
7. **Module-level reflection**
8. **Mark as done** (browser-local progress)
9. **Next-up nav**

Copy `module-1.html`, swap the content, update navigation and the entry in `index.html`.

## Audit notes

The library was audited against actual published material. Items that couldn't be verified were removed or rewritten. Confirmed pairings:

- **Brainstorm (Siegel)** → Talks at Google YouTube talk + Frances Jensen NPR Fresh Air interview
- **The Emotional Lives of Teenagers (Damour)** → TELUS Talks YouTube interview + Social Work Podcast Eps 134/135 + ongoing Ask Lisa podcast
- **How to Talk So Teens Will Listen (Faber & Mazlish)** → Adele Faber interview on The Psych Files podcast
- **Middle School Matters (Fagell)** → Psychologists Off the Clock Ep. 272 + Fagell's own Middle School Walk & Talk podcast (AMLE)
- **Decoding Boys (Natterson)** → On Boys Podcast + Natterson's own Puberty Podcast
- **Fires in the Middle School Bathroom (Cushman)** → no verified author interview; What Kids Can Do org links and Edutopia student-voice content used as thematic substitutes
- **Hold On to Your Kids (Neufeld & Maté)** → What Fresh Hell podcast (rare dual-author appearance) + Mindful Mama Ep. 481

The original Module I opened with a fabricated Lisa Damour TEDxCLE title ("The Two Most Important Questions to Ask a Stressed Teen"). That step now opens with the verified Frances Jensen NPR Fresh Air interview.

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
- Embedded YouTube players inside the public module pages
- Printable PDF version of each module (`@media print` rules are in `style.css`)
- An Obsidian template for capturing module reflections back into your vault
- Enforce HTTPS in the GitHub Pages settings (the site already upgrades `http://teens.mrbsocialstudies.org` in the browser)
