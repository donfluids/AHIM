#!/usr/bin/env python3
"""Point the Watch Online section at the newest services on the YouTube channel.

The church streams a service every Sunday and it lands on the "Sunday Service"
playlist the following Monday. This reads that playlist's Atom feed, puts the
newest service in the featured player, the next three on the cards below it, and
saves a thumbnail for each one alongside the site's other images.

Thumbnails are copied into assets/ rather than linked because the page's
Content-Security-Policy only allows images the site serves itself.

Run it by hand at any time:

    python3 scripts/refresh_videos.py

It rewrites nothing unless the playlist has actually moved on.
"""

import datetime
import io
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from PIL import Image

# The "Sunday Service" playlist on youtube.com/@AronHaBrit.International holds
# the live-streamed services, as opposed to Messages, Testimonies or Worship songs.
PLAYLIST_ID = "PLgukQ1ZjRUXqIS7zrMnMSG6qmduATsJNk"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "index.html")
THUMB_DIR = os.path.join(REPO, "assets", "videos")

# One featured video plus three cards.
CARD_COUNT = 3
WANTED = CARD_COUNT + 1

THUMB_SIZE = (640, 360)
USER_AGENT = "AHIM-website-refresh/1.0 (+https://ahimchurch.org)"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def get(url, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_playlist():
    """The playlist's videos, newest first."""
    root = ET.fromstring(get(FEED_URL))
    videos = []
    for entry in root.findall("atom:entry", NS):
        published = entry.find("atom:published", NS).text
        videos.append(
            {
                "id": entry.find("yt:videoId", NS).text,
                "title": entry.find("atom:title", NS).text or "",
                "published": datetime.datetime.fromisoformat(published.replace("Z", "+00:00")),
            }
        )
    # The feed follows playlist order, which the church could re-sort at any
    # time, so sort by date ourselves.
    videos.sort(key=lambda v: v["published"], reverse=True)
    return videos


def service_date(published):
    """The Sunday the service was streamed.

    Uploads land on the Monday after the service, so this is the most recent
    Sunday on or before the upload. Titles carry the date too, but they are
    written by hand and at least one of them is wrong.
    """
    date = published.date()
    return date - datetime.timedelta(days=(date.weekday() + 1) % 7)


def short_title(title):
    """A card-sized name for a service.

    Titles on the channel range from '||Sunday Service|| Pr. Monish Stephen: …'
    to '🔴🅻🅸🆅🅴 || Sunday Service || …' to 'DELIVERANCE SUNDAY | Pr. Shajan
    George | …', so take the opening phrase and tidy it up.
    """
    text = re.sub(r"[^\w\s|:,\-—&']", " ", title, flags=re.UNICODE)
    text = re.split(r"[|:,]|\s[-—]\s", text)[0]
    text = re.sub(r"\s+", " ", text).strip(" -—|:")

    if not text or re.fullmatch(r"(?i)live", text):
        return "Sunday Service"
    if re.search(r"(?i)sunday\s+service", text):
        return "Sunday Service"
    if len(text) > 34:
        return "Sunday Service"
    # Shouty titles read better in title case; leave mixed-case ones alone.
    return text.title() if text.isupper() else text


def save_thumbnail(video_id):
    """Store a 16:9 thumbnail for a video, and return its path from the page."""
    path = os.path.join(THUMB_DIR, f"{video_id}.jpg")
    web_path = f"assets/videos/{video_id}.jpg"
    if os.path.exists(path):
        return web_path

    for name in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            data = get(f"https://i.ytimg.com/vi/{video_id}/{name}.jpg", timeout=20)
        except urllib.error.HTTPError:
            continue
        image = Image.open(io.BytesIO(data)).convert("RGB")
        width, height = image.size
        # sddefault and hqdefault are 4:3 with black bars top and bottom.
        target = THUMB_SIZE[0] / THUMB_SIZE[1]
        if width / height > target:
            crop = int(height * target)
            image = image.crop(((width - crop) // 2, 0, (width + crop) // 2, height))
        else:
            crop = int(width / target)
            image = image.crop((0, (height - crop) // 2, width, (height + crop) // 2))
        image = image.resize(THUMB_SIZE, Image.LANCZOS)
        os.makedirs(THUMB_DIR, exist_ok=True)
        image.save(path, "JPEG", quality=82, optimize=True, progressive=True)
        return web_path

    raise RuntimeError(f"no thumbnail available for {video_id}")


def featured_block(video):
    date = service_date(video["published"])
    return (
        '        <div class="video-frame">\n'
        "          <iframe\n"
        f'            src="https://www.youtube.com/embed/{video["id"]}"\n'
        f'            title="{short_title(video["title"])} at AHIM Jesus Reigns Worship '
        f'Center, {date:%B} {date.day}, {date:%Y}"\n'
        '            allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        'gyroscope; picture-in-picture"\n'
        "            allowfullscreen loading=\"lazy\"></iframe>\n"
        "        </div>\n"
    )


def recent_block(videos):
    lines = ['      <div class="recent">']
    for video in videos:
        date = service_date(video["published"])
        name = short_title(video["title"])
        thumb = save_thumbnail(video["id"])
        lines += [
            f'        <button class="vcard reveal" type="button" data-video="{video["id"]}"'
            f' aria-label="Play: {name}, {date:%B} {date.day}">',
            '          <span class="vthumb">',
            f'            <img src="{thumb}" alt="" loading="lazy">',
            '            <span class="vplay" aria-hidden="true"><span><svg viewBox="0 0 24 24">'
            '<path d="M8 5v14l11-7z"/></svg></span></span>',
            "          </span>",
            f'          <div class="vtitle">{name}</div>',
            f'          <time datetime="{date:%Y-%m-%d}">{date:%B} {date.day}, {date:%Y}</time>',
            "        </button>",
        ]
    lines.append("      </div>")
    return "\n".join(lines) + "\n"


def splice(html, marker, block):
    start = f"<!-- videos:{marker}:start -->"
    end = f"<!-- videos:{marker}:end -->"
    pattern = re.compile(
        re.escape(start) + r"\n.*?" + r"^(\s*)" + re.escape(end),
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(html)
    if not match:
        raise RuntimeError(f"could not find the {marker} markers in index.html")
    return html[: match.start()] + start + "\n" + block + match.group(1) + end + html[match.end():]


def prune_thumbnails(html):
    """Delete thumbnails the page no longer shows."""
    if not os.path.isdir(THUMB_DIR):
        return []
    removed = []
    for name in sorted(os.listdir(THUMB_DIR)):
        if f"assets/videos/{name}" not in html:
            os.remove(os.path.join(THUMB_DIR, name))
            removed.append(name)
    return removed


def main():
    try:
        videos = fetch_playlist()
    except Exception as error:
        sys.exit(f"Could not read the Sunday Service playlist: {error}")

    if len(videos) < WANTED:
        sys.exit(
            f"The playlist returned only {len(videos)} videos; "
            f"{WANTED} are needed. Leaving the page alone."
        )

    videos = videos[:WANTED]
    original = open(INDEX, encoding="utf-8").read()

    html = splice(original, "featured", featured_block(videos[0]))
    html = splice(html, "recent", recent_block(videos[1:]))

    for video in videos:
        date = service_date(video["published"])
        print(f"  {video['id']}  {date}  {short_title(video['title'])}")

    if html == original:
        removed = prune_thumbnails(html)
        print("Already up to date." + (f" Removed {', '.join(removed)}." if removed else ""))
        return

    open(INDEX, "w", encoding="utf-8").write(html)
    removed = prune_thumbnails(html)
    print(f"Updated index.html." + (f" Removed {', '.join(removed)}." if removed else ""))


if __name__ == "__main__":
    main()
