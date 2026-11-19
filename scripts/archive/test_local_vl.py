import base64, json, time
from pathlib import Path
import httpx
img = Path(r'')
url = 'data:image/png;base64,' + base64.b64encode(img.read_bytes()).decode()
payload = {
    'model': 'Qwen3VL-4B-Instruct',
    'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': '用中文简短描述这张图：有文字就照抄要点，再说画面是什么，不超过 80 字。'},
        {'type': 'image_url', 'image_url': {'url': url}},
    ]}],
    'max_tokens': 160, 'temperature': 0.2,
}
t = time.time()
r = httpx.post('http://127.0.0.1:8085/v1/chat/completions', json=payload, timeout=180)
print('状态', r.status_code, '耗时', round(time.time()-t, 1), '秒')
print((r.json()['choices'][0]['message']['content'] or '')[:200])
