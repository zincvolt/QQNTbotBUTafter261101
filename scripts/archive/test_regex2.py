import re
pat = re.compile(r"。(\s|$)")
samples = ["行吧。那我先躺一会。", "行吧。那我先躺一会", "他说。你好。。"]
for t in samples:
    print(repr(t), "->", repr(pat.sub("~", t)))
