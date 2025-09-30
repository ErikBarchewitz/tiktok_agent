import argparse, json
p=argparse.ArgumentParser(); p.add_argument("--payload",required=True)
a=p.parse_args(); d=json.loads(a.payload)
sec=int(d.get("laengeSek",25)); kern=d["kernbotschaft"]
hook=f"{kern.split('.')[0]} – in {sec} Sekunden!"
bullets=[kern,"Konkreter Tipp #1","Konkreter Tipp #2"][:2]
resp={"hook":hook,"bullets":bullets,"cta":d.get("cta","Folgen für mehr!")}
print(json.dumps(resp, ensure_ascii=False))
