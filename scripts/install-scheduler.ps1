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

    One task is registered:

      Vanna-Scheduler   every 30 minutes, fires whichever jobs are due
                        (config/scheduler.yaml). `gtm_cycle` is the one that
                        runs all 13 agents with no directive, so A02 picks
                        the topic itself — that is what makes it autonomous
                        rather than merely scheduled.

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

# The old Vanna-Worker task ran `-m core.worker --once` every 5 minutes. That
# is the `core/` pipeline, which is a different system from the founder's 13
# agents and no longer drives anything in this repo — so it woke every five
# minutes to drain a queue nothing fills. It is removed above and not
# re-registered; Vanna-Scheduler below is the whole schedule.

# StopExisting, not IgnoreNew: a hung cycle must not block every later one.
# A GTM cycle takes 2-5 minutes, so the 1-hour limit is generous headroom.
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances StopExisting `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5) `
    -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

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
Write-Output "  Get-ScheduledTaskInfo -TaskName '$schedTask' | Select LastRunTime,LastTaskResult,NextRunTime"
Write-Output ''
Write-Output 'Job state (what is due, what last ran):'
Write-Output "  .venv\Scripts\python.exe pipeline\scheduler\configurable_scheduler_daemon.py --status"
Write-Output ''
Write-Output 'StartWhenAvailable is set, so a run missed while the machine was asleep'
Write-Output 'fires on wake instead of being skipped silently.'
