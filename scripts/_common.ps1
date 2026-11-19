# Shared helpers for the QQNTBOT start/stop scripts.
# ASCII only on purpose: PowerShell 5.1 reads a BOM-less .ps1 as ANSI.
#
# Dot-source from the repo root:   . "$PSScriptRoot\scripts\_common.ps1"
# Dot-source from scripts\:        . "$PSScriptRoot\_common.ps1"

$BotRoot   = 'D:\QQNTBOT'
$BotPython = 'D:\QQNTBOT\apps\AstrBot\.venv\Scripts\python.exe'

function Repair-Env {
    # A Windows process block can hold HTTP_PROXY and http_proxy at the same time.
    # PowerShell 5.1 then throws "An item with the same key has already been added"
    # for ANY env enumeration, and Start-Process dies with a useless message.
    # Collapse each known pair into one upper-case entry, keeping the value.
    foreach ($name in @('http_proxy', 'https_proxy', 'no_proxy', 'all_proxy')) {
        $value = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $null, 'Process')
        [Environment]::SetEnvironmentVariable($name.ToUpper(), $null, 'Process')
        if ($value) {
            [Environment]::SetEnvironmentVariable($name.ToUpper(), $value, 'Process')
        }
    }
}

function Test-Port {
    param([int]$Port)
    $client = New-Object Net.Sockets.TcpClient
    try {
        $client.Connect('127.0.0.1', $Port)
        return $true
    } catch {
        return $false
    } finally {
        try { $client.Close() } catch { }
    }
}

function Wait-Port {
    param([int]$Port, [int]$Seconds)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port $Port) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Get-PortPid {
    # Owner PID(s) of a listening port. Faster and more reliable than matching
    # command lines: the AstrBot process is started by uv and only shows
    # "python.exe main.py", which breaks regex based detection.
    param([int]$Port)
    $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if (-not $conns) { return @() }
    return @($conns | Select-Object -ExpandProperty OwningProcess -Unique)
}

function Stop-Port {
    param([int]$Port, [string]$Label = '')
    $owners = Get-PortPid $Port
    if ($owners.Count -eq 0) { return $true }
    foreach ($owner in $owners) {
        if (-not $owner -or $owner -eq 0) { continue }
        $proc = Get-Process -Id $owner -ErrorAction SilentlyContinue
        $name = if ($proc) { $proc.ProcessName } else { 'gone' }
        Write-Host ("  port {0,-5} {1,-14} pid {2} ({3})" -f $Port, $Label, $owner, $name)
        Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
    }
    for ($i = 0; $i -lt 30; $i++) {
        if (-not (Test-Port $Port)) { return $true }
        Start-Sleep -Milliseconds 200
    }
    return $false
}

function Start-Detached {
    # Launch through WMI so the new process belongs to WmiPrvSE, not to this
    # shell. Closing the terminal (or the job object of whatever started us)
    # then no longer takes the whole stack down with it.
    # Trade-off: no stdout/stderr redirection - services must log themselves.
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = ''
    )
    $parts = @('"' + $FilePath + '"')
    foreach ($a in $ArgumentList) {
        $parts += if ($a -match '\s') { '"' + $a + '"' } else { $a }
    }
    $wmiArgs = @{ CommandLine = ($parts -join ' ') }
    if ($WorkingDirectory) { $wmiArgs['CurrentDirectory'] = $WorkingDirectory }
    try {
        $res = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments $wmiArgs -ErrorAction Stop
    } catch {
        Write-Host ("  WARN: detached launch failed: {0}" -f $_.Exception.Message) -ForegroundColor Yellow
        return $null
    }
    if ($res.ReturnValue -eq 0) { return $res.ProcessId }
    Write-Host ("  WARN: WMI Win32_Process.Create returned {0}" -f $res.ReturnValue) -ForegroundColor Yellow
    return $null
}

function Start-Hidden {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = '',
        [string]$OutLog = '',
        [string]$ErrLog = ''
    )
    $splat = @{
        FilePath     = $FilePath
        ArgumentList = $ArgumentList
        WindowStyle  = 'Hidden'
        PassThru     = $true
        ErrorAction  = 'Stop'
    }
    if ($WorkingDirectory) { $splat['WorkingDirectory'] = $WorkingDirectory }
    if ($OutLog) { $splat['RedirectStandardOutput'] = $OutLog }
    if ($ErrLog) { $splat['RedirectStandardError'] = $ErrLog }
    try {
        return (Start-Process @splat)
    } catch {
        Write-Host ("  WARN: launch failed: {0}" -f $_.Exception.Message) -ForegroundColor Yellow
        return $null
    }
}

function Start-ScriptService {
    param([int]$Port, [string]$Label, [string]$ScriptPath, [int]$Timeout = 120)
    if (Test-Port $Port) {
        Write-Host ("      {0} already up ({1})" -f $Label, $Port)
        return $true
    }
    if (-not (Test-Path $ScriptPath)) {
        Write-Host ("      WARN: script missing: {0}" -f $ScriptPath) -ForegroundColor Yellow
        return $false
    }
    if ($global:BotDetach) {
        Start-Detached -FilePath 'powershell.exe' `
            -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ScriptPath) | Out-Null
    } else {
        Start-Hidden -FilePath 'powershell.exe' `
            -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ScriptPath) | Out-Null
    }
    if (Wait-Port $Port $Timeout) {
        Write-Host ("      {0} ready ({1})" -f $Label, $Port)
        return $true
    }
    Write-Host ("      WARN: {0} not up after {1}s" -f $Label, $Timeout) -ForegroundColor Yellow
    return $false
}

function Start-PythonService {
    param(
        [int]$Port,
        [string]$Label,
        [string]$Python,
        [string[]]$Arguments,
        [string]$WorkingDirectory = '',
        [string]$OutLog = '',
        [string]$ErrLog = '',
        [int]$Timeout = 60
    )
    if (Test-Port $Port) {
        Write-Host ("      {0} already up ({1})" -f $Label, $Port)
        return $true
    }
    if (-not (Test-Path $Python)) {
        Write-Host ("      WARN: python missing: {0}" -f $Python) -ForegroundColor Yellow
        return $false
    }
    if ($global:BotDetach) {
        # No redirection possible through WMI; these services log on their own.
        Start-Detached -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory | Out-Null
    } else {
        Start-Hidden -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory `
            -OutLog $OutLog -ErrLog $ErrLog | Out-Null
    }
    if (Wait-Port $Port $Timeout) {
        Write-Host ("      {0} ready ({1})" -f $Label, $Port)
        return $true
    }
    Write-Host ("      WARN: {0} not up after {1}s" -f $Label, $Timeout) -ForegroundColor Yellow
    return $false
}

function Get-ProviderId {
    # Single source of truth for local vs third-party mode: the AstrBot agent
    # runner config, not data/api_mode.json (that file is only a bookkeeping log).
    $cfg = 'D:\QQNTBOT\apps\AstrBot\data\cmd_config.json'
    if (-not (Test-Path $cfg)) { return '' }
    try {
        $json = Get-Content $cfg -Raw -Encoding UTF8 | ConvertFrom-Json
        $id = $json.agent_runner.config.model.provider_id
        if ($id) { return [string]$id }
    } catch {
        return ''
    }
    return ''
}

function Test-ThirdPartyAstrBot {
    param([string]$ProviderId)
    if (-not $ProviderId) { return $false }
    return -not ($ProviderId -match 'local|llama')
}

function Show-Status {
    param([object[]]$Ports)
    Write-Host ''
    foreach ($entry in $Ports) {
        $up = Test-Port $entry.Port
        $state = if ($up) { 'UP  ' } else { 'down' }
        $color = if ($up) { 'Green' } else { 'DarkGray' }
        Write-Host ("  {0,-5} {1}  {2}" -f $entry.Port, $state, $entry.Label) -ForegroundColor $color
    }
}
