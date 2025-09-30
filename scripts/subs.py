import argparse, subprocess, pathlib
p=argparse.ArgumentParser(); p.add_argument("--in",dest="inp",required=True); p.add_argument("--lang",default="de"); p.add_argument("--out",required=True)
a=p.parse_args()
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["whisper",a.inp,"--language",a.lang,"--task","transcribe","--output_format","srt","--output_dir",str(pathlib.Path(a.out).parent)],check=True)
print(a.out)
