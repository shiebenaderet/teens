#!/usr/bin/env python3
from __future__ import annotations
"""Download all referenced podcasts and the Siegel video for offline playback.

What this does
--------------
For each media reference used by the modules (the Step 1 and Step 4 listens),
this script tries to download a local copy into media/. The build script then
detects local files automatically and swaps the online iframe embeds for
native HTML5 audio/video players that work offline.

Usage
-----
One-time setup:

    pip3 install yt-dlp

Then, from the project root:

    python3 scripts/download-media.py

The script is idempotent. Files that already exist are skipped, so rerunning
after a partial failure just fills in the gaps.

Output
------
    media/                 (gitignored; for personal use only)

This is personal-use territory. Sharing the downloaded media files is a
copyright matter you should make a deliberate decision about. The script
makes the files; you decide whether they leave your machine.

Known limits
------------
yt-dlp handles YouTube cleanly and many podcast hosts via its generic
extractor. A few sources won't resolve automatically (Apple Podcasts URLs
in particular). For those, find the show's RSS feed, locate the episode's
.mp3 enclosure URL, and either:
    a) Drop the .mp3 into media/ manually with the matching basename, or
    b) Add it to MANUAL_OVERRIDES below as a direct URL.

The build will use whatever local files it finds, and fall back to the
iframe embeds for anything still missing.
"""

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "media"


# Each entry: (basename, kind, source_url, notes)
#
# kind values:
#   "yt-video"    -> yt-dlp, video as mp4 up to 480p
#   "yt-audio"    -> yt-dlp, audio extracted as m4a
#   "yt-generic"  -> yt-dlp on a podcast page; treat as audio
#   "direct-mp3"  -> plain HTTP download of a direct .mp3 / .m4a URL
#   "skip"        -> documented as known-difficult; not attempted
#
# The basename MUST match the local_basename used in the build script's
# EMBED_REGISTRY so the build can find the file.
SOURCES = [
    # ----- Module I -----
    (
        "m1-s1-npr-fresh-air-jensen",
        "skip",
        "https://www.npr.org/2016/04/15/474348291/why-teens-are-impulsive-addiction-prone-and-should-protect-their-brains",
        "NPR audio isn't reliably resolvable via yt-dlp. To enable: download the mp3 from NPR's page (look for the audio download link in the article) and drop it in as m1-s1-npr-fresh-air-jensen.mp3.",
    ),
    (
        "m1-s4-siegel-talks-at-google",
        "yt-video",
        "https://www.youtube.com/watch?v=kHZzhKyBW-I",
        "Daniel Siegel's Brainstorm talk at Google (~1 hour, 480p).",
    ),
    # ----- Module II -----
    (
        "m2-s1-faber-psych-files-135",
        "yt-generic",
        "https://thepsychfiles.libsyn.com/episode-135-adele-faber-interview-on-parenting-part-1",
        "Pointing directly at the Libsyn page. The old thepsychfiles.com URL now redirects to a rebuilt site that yt-dlp doesn't recognize. If the Libsyn page also fails, the show host has noted all episodes are also on his YouTube channel at @MichaelBritt_ThePsychFiles; find Ep 135 there and add the YouTube URL to MANUAL_OVERRIDES.",
    ),
    (
        "m2-s4-damour-kate-bowler",
        "yt-generic",
        "https://katebowler.com/podcasts/how-to-talk-to-teenagers/",
        "Omny.fm-hosted episode page; yt-dlp generally handles Omny.",
    ),
    # ----- Module III -----
    (
        "m3-s1-natterson-on-boys",
        "yt-generic",
        "https://www.on-boys-podcast.com/decoding-boys-with-dr-cara-natterson/",
        "Likely Libsyn or Blubrry; yt-dlp generic extractor.",
    ),
    (
        "m3-s4-natterson-mindful-mama-570",
        "yt-generic",
        "https://www.youtube.com/watch?v=a-QEsvMQi0E",
        "Mindful Mama Mentor Ep. 570 with Cara Natterson. YouTube hosts the full episode so yt-dlp handles it cleanly.",
    ),
    # ----- Module IV -----
    (
        "m4-s1-mate-neufeld-what-fresh-hell",
        "yt-generic",
        "https://www.whatfreshhellpodcast.com/fresh-take-dr-gabor-mate-and-dr-gordon-neufeld-on-maintaining-healthy-connection-with-our-kids/",
        "What Fresh Hell episode with both Maté and Neufeld. yt-dlp's generic extractor should handle the embedded player; if not, paste the direct .mp3 URL from the page into MANUAL_OVERRIDES.",
    ),
    (
        "m4-s4-mate-mindful-mama-481",
        "yt-generic",
        "https://www.youtube.com/watch?v=5fmlixIHyj4",
        "Mindful Mama Mentor Ep. 481 with Gabor Maté solo. YouTube version handled cleanly by yt-dlp.",
    ),
    # ----- Module V -----
    (
        "m5-s1-faber-king-silverman",
        "yt-generic",
        "https://drrobynsilverman.com/how-to-talk-when-kids-wont-listen-with-joanna-faber-julie-king-rerelease/",
        "Try yt-dlp first; the show is hosted on a standard podcast platform.",
    ),
    (
        "m5-s4-damour-ask-lisa-170",
        "yt-generic",
        "https://www.youtube.com/watch?v=i9oqGi9m7P8",
        "Ask Lisa Ep 170 is also on YouTube (Damour publishes there). Swapped to the YouTube URL so yt-dlp handles it cleanly.",
    ),
    # ----- Module VI -----
    (
        "m6-s1-fagell-off-the-clock-272",
        "yt-generic",
        "https://offtheclockpsych.com/middle-school-matters/",
        "Try yt-dlp; the show is on Art19 (RSS feed at rss.art19.com/psychologists-off-the-clock).",
    ),
]

# Direct-URL overrides for sources that yt-dlp can't resolve. If you find the
# direct .mp3 or .m4a URL for one of the "skip" entries, add it here. Keys
# must match the SOURCES basename; values must be direct HTTP(S) URLs to the
# audio file.
#
# Example:
#   MANUAL_OVERRIDES = {
#       "m1-s1-npr-fresh-air-jensen":
#           "https://traffic.npr.org/path/to/the/specific/episode.mp3",
#   }
MANUAL_OVERRIDES: dict[str, str] = {
    # On Boys hosts on Blubrry (Podtrac-tracked). Using the full URL from the
    # episode page's Download button so all tracking redirects resolve cleanly.
    # I tried a stripped-down version earlier and it failed; Blubrry seems to
    # require the tracking query string to be present.
    "m3-s1-natterson-on-boys":
        "https://pdst.fm/e/media.blubrry.com/on_boys/dts.podtrac.com/redirect.mp3/mc.blubrry.com/on_boys/217_Cara_Natterson_Decoding_Boys_TAKE_TWO.mp3?awCollectionId=529689&aw_0_azn.pgenre=Kids+%26+Family&aw_0_1st.ri=blubrry&aw_0_azn.pcountry=US&aw_0_azn.planguage=en-us&aw_0_cnt.rss=https%3A%2F%2Fwww.on-boys-podcast.com%2Ffeed%2Fpodcast%2F",
    # Psych Files Ep. 135 (Faber Pt 1) on Libsyn. Direct URL provided after
    # the libsyn page failed via yt-dlp; this is the Podtrac-redirected
    # traffic.libsyn.com .mp3 that the show's RSS feed publishes.
    "m2-s1-faber-psych-files-135":
        "https://dts.podtrac.com/redirect.mp3/traffic.libsyn.com/secure/thepsychfiles/TPF_135_FaberInterview_111910.mp3?dest-id=10763",
    # NPR Fresh Air Frances Jensen interview. NPR's on-demand audio URL is
    # not predictable from the article page; this one was extracted from
    # the player on the NPR page.
    "m1-s1-npr-fresh-air-jensen":
        "https://ondemand.npr.org/anon.npr-mp3/npr/fa/2016/04/20160415_fa_01.mp3?d=2282&e=474348291&t=progseg&seg=1&p=13&sc=siteplayer&aw_0_1st.playerid=siteplayer",
}


def have_yt_dlp() -> bool:
    return shutil.which("yt-dlp") is not None


def already_have(basename: str):
    """Return the first non-empty existing file matching this basename, or None.
    Zero-byte files are treated as not-yet-downloaded so the script can recover
    from interrupted downloads or stray empty files."""
    matches = [m for m in MEDIA.glob(f"{basename}.*") if m.stat().st_size > 0]
    return matches[0] if matches else None


def download_via_yt_dlp(name: str, kind: str, url: str) -> Path | None:
    # Remove any zero-byte files matching this basename so yt-dlp can write fresh.
    # Modern yt-dlp refuses to overwrite by default, so a stray empty file would
    # silently make the download a no-op.
    for stray in MEDIA.glob(f"{name}.*"):
        if stray.stat().st_size == 0:
            print(f"    removing empty stray: {stray.name}")
            stray.unlink()

    output_template = str(MEDIA / f"{name}.%(ext)s")
    if kind == "yt-video":
        args = [
            "yt-dlp",
            "-f", "best[height<=480][ext=mp4]/best[height<=480]",
            "--no-playlist",
            "-o", output_template,
            url,
        ]
    else:  # yt-audio or yt-generic
        args = [
            "yt-dlp",
            "-x", "--audio-format", "m4a",
            "--no-playlist",
            "-o", output_template,
            url,
        ]
    print(f"    running: yt-dlp ... {url}")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        last = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "(no stderr)"
        print(f"    failed: {last}")
        return None
    matches = list(MEDIA.glob(f"{name}.*"))
    return matches[0] if matches else None


def download_direct(name: str, url: str) -> Path | None:
    # Infer extension from URL
    ext = url.rsplit(".", 1)[-1].split("?")[0].lower()
    if ext not in ("mp3", "m4a", "mp4", "ogg", "webm"):
        ext = "mp3"
    out = MEDIA / f"{name}.{ext}"
    print(f"    fetching: {url}")
    # Some podcast CDNs (Blubrry, Megaphone) gate plain Python user-agents;
    # send a normal-looking UA to avoid 403s.
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) talking-with-teens-downloader/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(out, "wb") as fout:
            shutil.copyfileobj(r, fout)
        if out.stat().st_size == 0:
            print(f"    failed: download produced an empty file")
            out.unlink(missing_ok=True)
            return None
        return out
    except Exception as e:
        print(f"    failed: {type(e).__name__}: {e}")
        if out.exists():
            out.unlink(missing_ok=True)
        return None


def main():
    if not have_yt_dlp():
        sys.exit(
            "yt-dlp is not installed. Install it with:\n"
            "    pip3 install yt-dlp\n"
        )
    MEDIA.mkdir(exist_ok=True)
    print(f"Downloading media to {MEDIA.relative_to(ROOT)}/\n")

    succeeded = []
    failed = []
    skipped = []

    for name, kind, url, notes in SOURCES:
        print(f"  [{name}]")
        existing = already_have(name)
        if existing:
            size_mb = existing.stat().st_size / 1024 / 1024
            print(f"    already have: {existing.name} ({size_mb:.1f} MB)")
            succeeded.append((name, existing))
            continue

        if name in MANUAL_OVERRIDES:
            result = download_direct(name, MANUAL_OVERRIDES[name])
        elif kind == "skip":
            print(f"    skip: {notes}")
            skipped.append((name, notes))
            continue
        elif kind in ("yt-video", "yt-audio", "yt-generic"):
            result = download_via_yt_dlp(name, kind, url)
        else:
            print(f"    unknown kind: {kind}")
            failed.append((name, "unknown kind"))
            continue

        if result and result.exists():
            size_mb = result.stat().st_size / 1024 / 1024
            print(f"    ok: {result.name} ({size_mb:.1f} MB)")
            succeeded.append((name, result))
        else:
            failed.append((name, notes))

    print("\n" + "=" * 60)
    print(f"  Downloaded: {len(succeeded)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Skipped: {len(skipped)}")

    if failed:
        print("\nFailed downloads (build will fall back to online iframes):")
        for name, notes in failed:
            print(f"  - {name}")
            if notes:
                print(f"      {notes}")

    if skipped:
        print("\nSkipped (intentional; need manual setup):")
        for name, notes in skipped:
            print(f"  - {name}")
            if notes:
                print(f"      {notes}")

    if succeeded:
        total_mb = sum(p.stat().st_size for _, p in succeeded) / 1024 / 1024
        print(f"\nTotal media size: {total_mb:.1f} MB")
        print("\nNext step: rerun the portable build to embed local players where files exist.")
        print("    python3 scripts/build-portable.py")


if __name__ == "__main__":
    main()
