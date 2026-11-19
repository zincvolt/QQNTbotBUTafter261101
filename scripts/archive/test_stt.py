import json, time, urllib.request, uuid
p = r"D:\LLM\logs\tts-test.wav"
boundary = uuid.uuid4().hex
with open(p, "rb") as f:
    data = f.read()
body = b""
body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-small-int8-ov\r\n".encode()
body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
body += data + b"\r\n"
body += f"--{boundary}--\r\n".encode()
req = urllib.request.Request("http://127.0.0.1:8096/v1/audio/transcriptions", data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
t0=time.time()
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print(f"{time.time()-t0:.1f}s", r.read()[:300])
except Exception as e:
    print("FAIL", e)
