from pathlib import Path
p = Path(r"D:\QQNTBOT\dashboard\index.html")
h = p.read_text(encoding="utf-8")

# 1) 统一置灰函数
helper = '''
function greyLocalControls(memeOn, rulesOn) {
  const meme = document.getElementById('memeSlider');
  const rules = document.getElementById('rulesBox');
  if (meme) {
    meme.disabled = !memeOn;
    meme.style.opacity = memeOn ? 1 : 0.35;
    const v = document.getElementById('memeVal');
    if (v) v.textContent = memeOn ? Math.round(parseFloat(meme.value) * 100) + '%' : '已关闭';
  }
  if (rules) {
    rules.disabled = !rulesOn;
    rules.style.opacity = rulesOn ? 1 : 0.35;
    rules.placeholder = rulesOn ? '' : '已关闭（在上方“本地优化”面板里打开）';
  }
}

'''
if 'function greyLocalControls' not in h:
    h = h.replace('async function loadReply() {', helper + 'async function loadReply() {', 1)

# 2) loadReply 末尾调用置灰
old = '''  document.getElementById('rulesBox').value = (r.text_rules || [])
    .map(x => `${x.pattern} => ${x.to}`).join('\\n');
  } catch (e) { console.error('loadReply', e); }'''
new = '''  const rules = r.text_rules || [];
  document.getElementById('rulesBox').value = rules
    .map(x => `${x.pattern} => ${x.to}`).join('\\n');
  greyLocalControls((r.meme_chance || 0) > 0, rules.length > 0);
  } catch (e) { console.error('loadReply', e); }'''
if old in h:
    h = h.replace(old, new, 1)
    print("loadReply 置灰已接")

# 3) loadProfile 也同步（保存预设后立即反映）
h = h.replace(
    '''    document.getElementById('profRulesMeta').textContent = r.rules_on ? '（' + r.rule_count + ' 条）' : '（已关）';''',
    '''    document.getElementById('profRulesMeta').textContent = r.rules_on ? '（' + r.rule_count + ' 条）' : '（已关）';
    greyLocalControls(!!r.meme_on, !!r.rules_on);''',
    1,
)

# 4) applyProfile / toggleProfile 之后刷新回复面板
h = h.replace(
    '''  document.getElementById('profileMsg').textContent = r.msg || (r.ok ? '已应用' : '失败');
  loadProfile(); loadReply();''',
    '''  document.getElementById('profileMsg').textContent = r.msg || (r.ok ? '已应用' : '失败');
  loadProfile(); loadReply();
  const api = document.getElementById('profileMode').textContent.includes('第三方');
  greyLocalControls(document.getElementById('profMeme').checked,
                    document.getElementById('profRules').checked);''',
    1,
)
h = h.replace(
    '''  document.getElementById('profileMsg').textContent = r.msg || '已更新';
  loadProfile();''',
    '''  document.getElementById('profileMsg').textContent = r.msg || '已更新';
  loadProfile(); loadReply();''',
    1,
)

p.write_text(h, encoding="utf-8")
print("index.html 已更新")
