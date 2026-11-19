# QQNTBOT 验证脚本
# 用途：改完代码后跑一遍，确认"真的生效了"，而不是"脚本没报错"。
# 背景：本项目踩过三次 str.replace() 静默失败的坑（见 docs/LESSONS.md §1）。
# 用法：在 PowerShell 里 `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`

$ErrorActionPreference = "Continue"
$ROOT = "D:\QQNTBOT"
$VENV = "$ROOT\apps\AstrBot\.venv\Scripts\python.exe"
$pass = 0; $fail = 0

function Check-Step($name, [scriptblock]$test) {
    try {
        $ok = & $test
        if ($ok) { Write-Host "[OK]   $name" -ForegroundColor Green; $script:pass++ }
        else     { Write-Host "[FAIL] $name" -ForegroundColor Red;   $script:fail++ }
    } catch {
        Write-Host "[ERR]  $name : $_" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "=== 1. AstrBot 6 处源码补丁存活检查 ===" -ForegroundColor Cyan
$patches = @(
    @{ name = "1 未授权私聊回复";      file = "$ROOT\apps\AstrBot\astrbot\core\pipeline\whitelist_check\stage.py";        pat = "no_permission_reply|未授权" },
    @{ name = "2 human分段间隔";        file = "$ROOT\apps\AstrBot\astrbot\core\pipeline\respond\stage.py";                pat = "0\.45 \+ chars / 7" },
    @{ name = "3 判官方法+按群开关";    file = "$ROOT\apps\AstrBot\astrbot\builtin_stars\astrbot\group_chat_context.py";   pat = "load_autoreply_config|_judge_reply" },
    @{ name = "4 主动回复建会话";       file = "$ROOT\apps\AstrBot\astrbot\builtin_stars\astrbot\main.py";                 pat = "created conversation for proactive" },
    @{ name = "5 GeneratorExit处理";    file = "$ROOT\apps\AstrBot\astrbot\builtin_stars\astrbot\main.py";                 pat = "except GeneratorExit" },
    @{ name = "6 禁止自动升级";         file = "$ROOT\apps\AstrBot\astrbot\core\updater.py";                               pat = "LOCAL_UPDATES_DISABLED = True" }
)
foreach ($p in $patches) {
    Check-Step $p.name { (Select-String -Path $p.file -Pattern $p.pat -Quiet) -eq $true }
}

Write-Host "`n=== 2. Python 语法编译检查 ===" -ForegroundColor Cyan
$pyFiles = Get-ChildItem -Path "$ROOT\apps\AstrBot\data\plugins" -Recurse -Filter *.py |
           Where-Object { $_.FullName -notmatch '__pycache__|\\tests\\' }
foreach ($f in $pyFiles) {
    Check-Step "compile $($f.Name)" {
        $r = & $VENV -m py_compile $f.FullName 2>&1
        return ($LASTEXITCODE -eq 0)
    }
}

Write-Host "`n=== 3. 指令词表匹配检查 ===" -ForegroundColor Cyan
Check-Step "dump_commands.py 可运行" {
    $r = & $VENV "$ROOT\scripts\archive\dump_commands.py" 2>&1
    Write-Host ($r | Select-Object -Last 3)
    return ($LASTEXITCODE -eq 0)
}

Write-Host "`n=== 结果: $pass 通过 / $fail 失败 ===" -ForegroundColor Cyan
if ($fail -gt 0) { Write-Host "有失败项，请逐条核对上面 [FAIL]/[ERR] 的条目。" -ForegroundColor Yellow }
