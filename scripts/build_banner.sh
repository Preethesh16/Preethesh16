#!/usr/bin/env bash
# Stationary portrait with three animated work-area titles; nine-second loop.
# Requires ffmpeg with drawtext/fontconfig. Run from any directory.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
filter="[0:v]trim=duration=9,scale=960:400:flags=lanczos,setsar=1"
titles=('Web experiences.' 'Applied AI.' 'Mobile products.')
skills=('React / Next.js / TypeScript' 'Python / FastAPI / AI integrations' 'Flutter / Kotlin / Cross-platform')
for index in 0 1 2; do
  start=$((index * 3))
  alpha="if(lt(t,$start),0,if(lt(t,$start+0.4),(t-$start)/0.4,if(lt(t,$start+2.6),1,if(lt(t,$start+3),($start+3-t)/0.4,0))))"
  title_y="296+8*(1-clip((t-$start)/0.4,0,1))"
  filter+=",drawtext=font='DejaVu Sans':text='${titles[$index]}':fontsize=26:fontcolor=0x32d7ff:x=68:y='$title_y':alpha='$alpha'"
  filter+=",drawtext=font='DejaVu Sans':text='${skills[$index]}':fontsize=13:fontcolor=0xb4c3cc:x=69:y=336:alpha='$alpha'"
done
filter+=",split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle[out]"
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 20 -i "$root/profile/banner-source.png" \
  -filter_complex "$filter" -map '[out]' -t 9 -loop 0 "$root/banner.gif"
