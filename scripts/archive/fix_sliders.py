from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
h = p.read_text(encoding="utf-8")

# 1) 思维链：第三方也允许拖预算（映射成 low/high/max）
old = '''    if (api) {
      dj.checked = false;
      document.getElementById('thinkBudgetVal').textContent =
        ({low:'低', high:'中', max:'高'}[r.effort] || '中') + '（reasoning_effort）';
      document.getElementById('thinkBudget').disabled = true;
      document.getElementById('thinkBudget').style.opacity = 0.35;
    }'''
new = '''    if (api) {
      dj.checked = false;
      const slider = document.getElementById('thinkBudget');
      slider.disabled = false;
      slider.style.opacity = 1;
      slider.min = 400;
      slider.max = 2400;
      slider.step = 100;
      const toEffort = v => (v <= 800 ? 'low（低）' : (v <= 1500 ? 'high（中）' : 'max（高）'));
      document.getElementById('thinkBudgetVal').textContent =
        r.budget + ' tok ≈ ' + toEffort(r.budget);
      slider.oninput = function () {
        document.getElementById('thinkBudgetVal').textContent =
          this.value + ' tok ≈ ' + toEffort(parseInt(this.value, 10));
      };
    }'''
if old in h:
    h = h.replace(old, new, 1)
    print("思维链预算可拖（映射 effort）")

# 2) 单条上限：第三方放宽到 2000
old2 = '''    const rpNote = document.getElementById('rpVal');
    rpNote.textContent = api ? 'API 不支持' : r.repeat_penalty;'''
new2 = '''    const rpNote = document.getElementById('rpVal');
    rpNote.textContent = api ? 'API 不支持' : r.repeat_penalty;

    // 单条上限：本地 40~600，第三方 40~2000
    const mt = document.getElementById('mtSlider');
    mt.min = 40;
    mt.max = api ? 2000 : 600;
    mt.step = api ? 20 : 10;
    if (parseInt(mt.value, 10) > parseInt(mt.max, 10)) mt.value = mt.max;
    document.getElementById('mtVal').textContent =
      mt.value + ' tok' + (api ? '' : '（本地）');'''
if old2 in h:
    h = h.replace(old2, new2, 1)
    print("单条上限滑块已放宽")

# 3) 面板说明同步
h = h.replace(
    '<span>单条上限 <span class="meta">token 数，80 约 55 个汉字</span></span>',
    '<span>单条上限 <span class="meta">token 数；第三方模式可拖到 2000</span></span>',
    1,
)
h = h.replace(
    '<span>思考预算 <span class="meta">总输出 token 上限；当前模型不认 thinking_budget，只能控总长</span></span>',
    '<span>思考预算 <span class="meta">本地=总输出上限；第三方=换算成 reasoning_effort(low/high/max)</span></span>',
    1,
)

p.write_text(h, encoding="utf-8")
print("index.html 已更新")
