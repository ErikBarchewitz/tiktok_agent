import argparse, json
p=argparse.ArgumentParser()
p.add_argument("--video",required=True); p.add_argument("--caption",default=""); p.add_argument("--hashtags",default="")
a=p.parse_args()
print(json.dumps({"status":"skipped","reason":"no_api_config","video":a.video}, ensure_ascii=False))
