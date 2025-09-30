import argparse, subprocess
p=argparse.ArgumentParser()
p.add_argument("--video",required=True); p.add_argument("--srt",required=True); p.add_argument("--out",required=True)
a=p.parse_args()
subprocess.run([
 "ffmpeg","-y","-i",a.video,"-vf",
 f"subtitles='{a.srt}':force_style='Fontsize=36,BorderStyle=3,Outline=2'",
 "-c:a","copy",a.out
],check=True)
print(a.out)
