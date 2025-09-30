import argparse, json
from pathlib import Path
from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
p=argparse.ArgumentParser()
p.add_argument("--payload",required=True); p.add_argument("--script",required=True)
p.add_argument("--voice",default=""); p.add_argument("--out",required=True)
a=p.parse_args()
cfg={"W":1080,"H":1920,"FPS":30}
payload=json.loads(a.payload); script=json.loads(a.script)
texts=[script["hook"],*script["bullets"],script["cta"]]
dur=max(3, int(payload.get("laengeSek",25)//len(texts)))
clips=[]
for t in texts:
    tc=(TextClip(t, fontsize=64, color="white")
        .on_color(size=(cfg["W"],cfg["H"]), color=(0,0,0), col_opacity=0.85)
        .set_duration(dur))
    clips.append(tc)
final=concatenate_videoclips(clips).set_fps(cfg["FPS"])
if a.voice and Path(a.voice).exists() and Path(a.voice).stat().st_size>0:
    vo=AudioFileClip(a.voice); final=final.set_audio(vo)
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
final.write_videofile(a.out, codec="libx264", audio_codec="aac", bitrate="8000k")
print(a.out)
