import argparse, subprocess, pathlib, sys
p=argparse.ArgumentParser()
p.add_argument("--text",required=True); p.add_argument("--lang",default="de"); p.add_argument("--voice",default="de_thorsten")
a=p.parse_args()
out=pathlib.Path("out"); out.mkdir(parents=True, exist_ok=True)
wav=str(out/"voiceover.wav")
try:
    subprocess.run(["tts","--text",a.text,"--model_name","tts_models/de/thorsten/tacotron2-DDC","--out_path",wav],check=True)
except Exception:
    open(wav,"wb").close()
print(wav)
