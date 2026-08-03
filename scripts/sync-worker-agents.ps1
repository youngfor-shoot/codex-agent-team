[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "High")]
param(
    [ValidateSet("Verify", "Install")]
    [string]$Mode = "Verify",

    [string]$Destination = (Join-Path ([Environment]::GetFolderPath("UserProfile")) ".codex\agents")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Join-Path $repositoryRoot "agents"
$managedNames = @("luna-worker.toml", "terra-worker.toml")

function Get-AbsolutePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }

    return [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Path))
}

function Test-PathWithin {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$Parent
    )

    $candidatePath = (Get-AbsolutePath $Candidate).TrimEnd("\")
    $parentPath = (Get-AbsolutePath $Parent).TrimEnd("\")
    return $candidatePath.Equals($parentPath, [StringComparison]::OrdinalIgnoreCase) -or
        $candidatePath.StartsWith($parentPath + "\", [StringComparison]::OrdinalIgnoreCase)
}

function Get-NormalizedHash {
    param([Parameter(Mandatory = $true)][string]$Path)

    $content = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8)
    $normalized = $content.Replace("`r`n", "`n").Replace("`r", "`n")
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($normalized)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace("-", "")
    }
    finally {
        $sha256.Dispose()
    }
}

$sourceRoot = Get-AbsolutePath $sourceRoot
$destinationRoot = Get-AbsolutePath $Destination
if ((Test-PathWithin $sourceRoot $destinationRoot) -or (Test-PathWithin $destinationRoot $sourceRoot)) {
    throw "Source and destination must not overlap."
}

$states = foreach ($name in $managedNames) {
    $source = Join-Path $sourceRoot $name
    $destination = Join-Path $destinationRoot $name
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Canonical worker profile is missing: $source"
    }

    $sourceHash = Get-NormalizedHash $source
    $destinationExists = Test-Path -LiteralPath $destination -PathType Leaf
    [pscustomobject]@{
        Name = $name
        Source = $source
        Destination = $destination
        SourceHash = $sourceHash
        DestinationExists = $destinationExists
        Matches = $destinationExists -and $sourceHash -eq (Get-NormalizedHash $destination)
    }
}

$drift = @($states | Where-Object { -not $_.Matches })
if ($Mode -eq "Verify") {
    if ($drift.Count -gt 0) {
        foreach ($state in $drift) {
            $reason = if ($state.DestinationExists) { "changed" } else { "missing" }
            Write-Output "$reason worker profile: $($state.Name)"
        }
        Write-Error "worker Agent runtime profiles differ from canonical source." -ErrorAction Continue
        exit 1
    }

    Write-Output "worker Agent source and runtime profiles match ($($states.Count) files)."
    exit 0
}

if ($drift.Count -eq 0) {
    Write-Output "worker Agent runtime profiles are already current ($($states.Count) files)."
    exit 0
}

if (-not $PSCmdlet.ShouldProcess($destinationRoot, "Back up and synchronize two worker Agent profiles")) {
    Write-Output "Install canceled."
    exit 2
}

$backupPath = $null
$existing = @($states | Where-Object { $_.DestinationExists })
if ($existing.Count -gt 0) {
    $backupBase = Join-Path (Split-Path -Parent $destinationRoot) ".agent-team-agent-backups"
    $backupName = (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + [guid]::NewGuid().ToString("N").Substring(0, 8)
    $backupPath = Join-Path $backupBase $backupName
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    foreach ($state in $existing) {
        Copy-Item -LiteralPath $state.Destination -Destination (Join-Path $backupPath $state.Name)
    }
}

New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null
foreach ($state in $states) {
    Copy-Item -LiteralPath $state.Source -Destination $state.Destination -Force
}

foreach ($state in $states) {
    if ((Get-NormalizedHash $state.Source) -ne (Get-NormalizedHash $state.Destination)) {
        throw "Worker profile synchronization failed: $($state.Name)"
    }
}

Write-Output "Installed worker Agent runtime profiles ($($states.Count) files)."
if ($null -ne $backupPath) {
    Write-Output "Backup: $backupPath"
}
