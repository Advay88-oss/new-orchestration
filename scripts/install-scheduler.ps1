<#
    Register the Vanna worker + scheduler with Windows Task Scheduler.

    Why this exists
    ---------------
    The 2026-09-21 audit found the pipeline's scheduler was a bare `while True:`
    loop with no supervisor. When the process died, the schedule died silently —
    `research_collect` was ~25 hours overdue on a 12-hour interval, and
    `daemon_status.json` still claimed RUNNING with a pid that had been dead for
    a day.

    A bare loop is strictly worse than cron, because it drops cron's one
    guarantee: that something external restarts the schedule. This script hands
    that guarantee to the OS.

    Two tasks are registered:

      Vanna-Worker      every 5 minutes, drains the run queue (`--once`)
      Vanna-Scheduler   every 30 minutes, fires due recurring jobs

    Both use `--once` deliberately: the OS owns the cadence, the process owns
    one unit of work. A crash costs one cycle, not the schedule.

    Run this from an elevated PowerShell:
        powershell -ExecutionPolicy Bypass -File scripts\install-scheduler.ps1

    Remove with:
        powershell -ExecutionPolicy Bypass -File scripts\install-scheduler.ps1 -Uninstall
#>

param(
    [switch]$Uninstall,
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$workerTask = 'Vanna-Worker'
$schedTask = 'Vanna-Scheduler'

function Remove-TaskIfPresent([string]$name) {
    $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
        Write-Output "removed $name"
    }
}

if ($Uninstall) {
    Remove-TaskIfPresent $workerTask
    Remove-TaskIfPresent $schedTask
    Write-Output 'Uninstalled.'
    exit 0
}

if (-not (Test-Path $python)) {
    Write-Error "Interpreter not found at $python. Create the venv and install requirements.txt first."
}

# Fail fast rather than registering a task that cannot run. The audit's most
# expensive failure was a scheduler that looked configured and did nothing.
& $python -c "import pydantic, playwright, PIL, yaml" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "The venv at $python is missing dependencies. Run: $python -m pip install -r requirements.txt"
}

Remove-TaskIfPresent $workerTask
Remove-TaskIfPresent $schedTask

# --- worker: drain the queue every 5 minutes -----------------------------
$workerAction = New-ScheduledTaskAction -Execute $python `
    -Argument '-m core.worker --once' -WorkingDirectory $RepoRoot

$workerTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5)

# StopExisting, not IgnoreNew: a hung cycle must not block every later one.
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances StopExisting `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5) `
    -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $workerTask -Action $workerAction `
    -Trigger $workerTrigger -Settings $settings `
    -Description 'Vanna: drain the pipeline run queue (core.worker --once)' | Out-Null
Write-Output "registered $workerTask (every 5 min)"

# --- scheduler: fire due recurring jobs every 30 minutes -----------------
$schedScript = Join-Path $RepoRoot 'pipeline\scheduler\configurable_scheduler_daemon.py'
if (Test-Path $schedScript) {
    $schedAction = New-ScheduledTaskAction -Execute $python `
        -Argument 'pipeline\scheduler\configurable_scheduler_daemon.py --tick' `
        -WorkingDirectory $RepoRoot

    $schedTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 30)

    Register-ScheduledTask -TaskName $schedTask -Action $schedAction `
        -Trigger $schedTrigger -Settings $settings `
        -Description 'Vanna: fire due scheduled jobs (StartWhenAvailable covers missed runs)' | Out-Null
    Write-Output "registered $schedTask (every 30 min)"
} else {
    Write-Warning "Scheduler script not found at $schedScript; skipped $schedTask"
}

Write-Output ''
Write-Output 'Verify with:'
Write-Output "  Get-ScheduledTask -TaskName 'Vanna-*' | Select TaskName,State"
Write-Output "  Get-ScheduledTaskInfo -TaskName '$workerTask' | Select LastRunTime,LastTaskResult,NextRunTime"
Write-Output ''
Write-Output 'StartWhenAvailable is set, so a run missed while the machine was asleep'
Write-Output 'fires on wake instead of being skipped silently.'
