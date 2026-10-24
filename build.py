
import re
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = "https://thirud4a4.github.io/movies_m3u/playlist.m3u"

def ident(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:55]
    digest = hashlib.sha1(title.encode()).hexdigest()[:10]
    return (slug or "movie") + "-" + digest

req = urllib.request.Request(
    SOURCE, headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=60) as r:
    lines = r.read().decode("utf-8-sig", "replace").splitlines()

items = []
for i, line in enumerate(lines):
    if line.strip().startswith("#EXTINF:"):
        j = i + 1
        while j < len(lines) and (
            not lines[j].strip() or lines[j].strip().startswith("#")
        ):
            j += 1
        if j < len(lines) and lines[j].strip().startswith(("http://", "https://")):
            title = line.rsplit(",", 1)[-1].strip() or "Untitled movie"
            items.append((line.strip(), lines[j].strip(), title))

if not items:
    raise RuntimeError("No playable M3U entries found")

tv = ET.Element("tv", {"generator-info-name": "Movie Catalogue EPG"})
out = ['#EXTM3U x-tvg-url="movie_epg.xml"']
base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

for n, (extinf, url, title) in enumerate(items):
    cid = "movie-" + ident(title)
    ch = ET.SubElement(tv, "channel", {"id": cid})
    ET.SubElement(ch, "display-name").text = title

    start = base + timedelta(hours=2*n)
    stop = start + timedelta(hours=2)
    fmt = lambda d: d.strftime("%Y%m%d%H%M%S +0000")

    p = ET.SubElement(tv, "programme", {
        "start": fmt(start), "stop": fmt(stop), "channel": cid
    })
    ET.SubElement(p, "title", {"lang": "en"}).text = title
    ET.SubElement(p, "desc", {"lang": "en"}).text = (
        "Movie catalogue entry; time slot is artificial."
    )

    # Replace existing tvg-id/name attributes, if present.
    extinf = re.sub(r'\s+tvg-id="[^"]*"', "", extinf)
    extinf = re.sub(r'\s+tvg-name="[^"]*"', "", extinf)
    extinf = extinf.replace(
        "#EXTINF:", f'#EXTINF: tvg-id="{cid}" tvg-name="{title}"', 1
    )
    out.extend([extinf, url])

ET.indent(tv, space="  ")
ET.ElementTree(tv).write(
    "movie_epg.xml", encoding="utf-8", xml_declaration=True
)
Path("playlist_with_epg.m3u").write_text(
    "\n".join(out) + "\n", encoding="utf-8"
)
print(f"Generated EPG and playlist for {len(items)} entries.")
