#!/bin/sh
# Copies and encodes the redesign-v3 media into assets/v3/. Re-runnable. Source: ~/VisorVolt/website_redesign_v3/media
set -e
SRC="${V3_MEDIA:-$HOME/VisorVolt/website_redesign_v3/media}"
cd "$(dirname "$0")/.."
D=assets/v3
mkdir -p $D/hero $D/clips $D/illustrations $D/stills $D/video $D/og
for e in mp4 webm; do cp "$SRC/hero/hero-gate-exit.$e" $D/hero/; done
cp "$SRC/hero/hero-gate-exit.webp" $D/hero/hero-gate-exit-1280.webp
cwebp -quiet -q 72 -resize 720 0 "$SRC/hero/hero-gate-exit.webp" -o $D/hero/hero-gate-exit-720.webp
for f in "$SRC"/clips/*; do cp "$f" $D/clips/; done
for f in "$SRC"/illustrations/* "$SRC"/illustration/*; do cp "$f" $D/illustrations/; done
for e in mp4 webm; do cp "$SRC/video_site/visorvolt-checkpoints-site.$e" $D/video/; done
cp "$SRC/video_site/visorvolt-checkpoints-site.txt" $D/video/transcript.txt
cp "$SRC/video_site/visorvolt-checkpoints-site.webp" $D/video/visorvolt-checkpoints-site-poster.webp
for s in still-gate-plate-read still-dock-truck still-people-line still-gate-car still-packing-line; do
  for w in 800 1200; do cwebp -quiet -q 76 -resize $w 0 "$SRC/stills/$s-1600.webp" -o $D/stills/$s-$w.webp; done
done
cwebp -quiet -q 78 -resize 480 0 assets/founder.jpg -o $D/founder-480.webp
# Open Graph images (JPEG 1200x630)
og() { ffmpeg -loglevel error -y -i "$1" -vf "scale=1200:630:force_original_aspect_ratio=increase,crop=1200:630" -q:v 4 "$D/og/$2.jpg"; }
og "$SRC/stills/still-gate-plate-read-1600.webp" og-gate
og "$SRC/stills/still-packing-line-1600.webp" og-packing
og "$SRC/stills/still-dock-truck-1600.webp" og-dock
du -sh $D/*
