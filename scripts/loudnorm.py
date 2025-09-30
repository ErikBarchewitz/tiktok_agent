import argparse, subprocess
p=argparse.ArgumentParser(); p.add_argument("--in",dest="inp",required=True); p.add_argument("--out",required=True)
a=p.parse_args()
subprocess.run(["ffmpeg","-y","-i",a.inp,"-af","loudnorm=I=-14:TP=-1:LRA=11",a.out],check=True)
print(a.out)
