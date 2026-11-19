# Point QQ's app entry at NapCat core in single-process mode (run as admin)
$ErrorActionPreference = 'Stop'
$root = 'C:\Program Files\Tencent\QQNT'
$cfg  = Get-Content (Join-Path $root 'versions\config.json') -Raw | ConvertFrom-Json
$ver  = Join-Path $root "versions\$($cfg.curVersion)"
$app  = Join-Path $ver 'resources\app'
$pj   = Join-Path $app 'package.json'
$log  = 'D:\QQNTBOT\_backup\napcat_entry.txt'

$loader = @'
// NapCat entry shim: run the locally built core in single-process mode.
const fs = require("node:fs");
const { pathToFileURL } = require("node:url");

const CORE = "D:/QQNTBOT/apps/NapCat/napcat.mjs";
const LOG  = "D:/QQNTBOT/_backup/plugin.log";

function log(m) {
  try { fs.appendFileSync(LOG, `[${new Date().toISOString()}] ${m}\n`); } catch (e) {}
}

process.env.NAPCAT_DISABLE_MULTI_PROCESS = "1";
process.env.NAPCAT_WORKDIR = "D:/QQNTBOT/apps/NapCat";
process.env.NAPCAT_ENABLE_VERBOSE_LOG = "1";
process.env.NAPCAT_WEBUI_PREFERRED_PORT = "6099";

process.on("uncaughtException", (e) => log("uncaught: " + (e && e.stack || e)));
process.on("unhandledRejection", (e) => log("unhandled: " + (e && e.stack || e)));

log("shim start, cwd=" + process.cwd());
import(pathToFileURL(CORE).href)
  .then(() => log("core imported"))
  .catch((e) => log("core failed: " + (e && e.stack || e)));
'@

[System.IO.File]::WriteAllText((Join-Path $app 'loadNapCat.js'), $loader, (New-Object System.Text.UTF8Encoding $false))

$json = (Get-Content $pj -Raw) -replace '("main"\s*:\s*")[^"]*(")', '${1}./loadNapCat.js${2}'
[System.IO.File]::WriteAllText($pj, $json, (New-Object System.Text.UTF8Encoding $false))

@(
  "at   : $(Get-Date -Format s)",
  "ver  : $($cfg.curVersion)",
  "main : $((Get-Content $pj -Raw | ConvertFrom-Json).main)"
) | Out-File -Encoding utf8 $log
Write-Host "done"
