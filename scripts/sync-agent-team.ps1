[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "High")]
param(
    [ValidateSet("Verify", "Install", "Uninstall", "Restore")]
    [string]$Mode = "Verify",

    [string]$Destination = (Join-Path ([Environment]::GetFolderPath("UserProfile")) ".codex\skills\agent-team"),

    [ValidateRange(1, 50)]
    [int]$KeepBackups = 5,

    [string]$BackupName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

function Test-ManagedRelativePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    if ($RelativePath -eq "SKILL.md") {
        return $true
    }

    $parts = $RelativePath.Split("/")
    if ($parts.Length -lt 2) {
        return $false
    }

    $extension = [IO.Path]::GetExtension($RelativePath).ToLowerInvariant()
    switch ($parts[0].ToLowerInvariant()) {
        "agents" { return $extension -in @(".yaml", ".yml") }
        "references" { return $extension -eq ".md" }
        "templates" { return $extension -eq ".md" }
        "scripts" { return $extension -eq ".py" }
        default { return $false }
    }
}

function Get-ManagedFiles {
    param([Parameter(Mandatory = $true)][string]$Root)

    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        return @()
    }

    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path.TrimEnd("\")
    $files = foreach ($file in Get-ChildItem -Recurse -File -LiteralPath $resolvedRoot) {
        $relativePath = $file.FullName.Substring($resolvedRoot.Length).TrimStart("\").Replace("\", "/")
        if (Test-ManagedRelativePath $relativePath) {
            [pscustomobject]@{
                RelativePath = $relativePath
                FullName = $file.FullName
                Hash = Get-NormalizedHash $file.FullName
            }
        }
    }

    return @($files | Sort-Object RelativePath)
}

function Compare-ManagedFiles {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][array]$SourceFiles,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][array]$DestinationFiles
    )

    $sourceByPath = @{}
    foreach ($file in $SourceFiles) {
        $sourceByPath[$file.RelativePath] = $file
    }

    $destinationByPath = @{}
    foreach ($file in $DestinationFiles) {
        $destinationByPath[$file.RelativePath] = $file
    }

    $missing = @($sourceByPath.Keys | Where-Object { -not $destinationByPath.ContainsKey($_) } | Sort-Object)
    $changed = @(
        $sourceByPath.Keys |
            Where-Object { $destinationByPath.ContainsKey($_) -and $sourceByPath[$_].Hash -ne $destinationByPath[$_].Hash } |
            Sort-Object
    )
    $stale = @($destinationByPath.Keys | Where-Object { -not $sourceByPath.ContainsKey($_) } | Sort-Object)

    return [pscustomobject]@{
        Missing = $missing
        Changed = $changed
        Stale = $stale
        HasDrift = ($missing.Count + $changed.Count + $stale.Count) -gt 0
    }
}

function Write-PathGroup {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][array]$Paths
    )

    if ($Paths.Count -eq 0) {
        return
    }

    Write-Output "${Label}:"
    foreach ($path in $Paths) {
        Write-Output "  - $path"
    }
}

function Write-Drift {
    param([Parameter(Mandatory = $true)]$Drift)

    Write-PathGroup "Missing from runtime" $Drift.Missing
    Write-PathGroup "Changed in runtime" $Drift.Changed
    Write-PathGroup "Stale in runtime" $Drift.Stale
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Get-AbsolutePath (Join-Path $repositoryRoot "skill\agent-team")
$destinationRoot = Get-AbsolutePath $Destination

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "Canonical Skill source is missing: $sourceRoot"
}

if ((Test-PathWithin $sourceRoot $destinationRoot) -or (Test-PathWithin $destinationRoot $sourceRoot)) {
    throw "Source and destination must not overlap."
}

$sourceFiles = @(Get-ManagedFiles $sourceRoot)
if ($sourceFiles.Count -eq 0) {
    throw "Canonical Skill source contains no managed files."
}

$destinationFiles = @(Get-ManagedFiles $destinationRoot)
$drift = Compare-ManagedFiles $sourceFiles $destinationFiles

if ($Mode -eq "Verify") {
    if ($drift.HasDrift) {
        Write-Drift $drift
        Write-Error "agent-team runtime copy differs from canonical source." -ErrorAction Continue
        exit 2
    }

    Write-Output "agent-team source and runtime copy match ($($sourceFiles.Count) managed files)."
    exit 0
}

if ($Mode -eq "Uninstall") {
    if ($destinationFiles.Count -eq 0) {
        Write-Output "No managed agent-team files installed; nothing to uninstall."
        exit 0
    }
    $operation = "Remove $($destinationFiles.Count) managed agent-team files"
    if (-not $PSCmdlet.ShouldProcess($destinationRoot, $operation)) {
        Write-Output "Uninstall canceled."
        exit 2
    }
    foreach ($file in $destinationFiles) {
        Remove-Item -LiteralPath $file.FullName -Force -ErrorAction SilentlyContinue
    }
    # Prune empty managed directories left by uninstall.
    $managedDirs = @(Get-ChildItem -Directory -Recurse -LiteralPath $destinationRoot | Sort-Object { $_.FullName.Length } -Descending)
    foreach ($dir in $managedDirs) {
        if (@(Get-ChildItem -Force -LiteralPath $dir.FullName).Count -eq 0) {
            Remove-Item -LiteralPath $dir.FullName -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Output "Uninstalled agent-team runtime copy ($($destinationFiles.Count) managed files)."
    exit 0
}

if ($Mode -eq "Restore") {
    if (-not $BackupName) {
        throw "Restore requires -BackupName."
    }
    $backupBase = Join-Path (Split-Path -Parent $destinationRoot) ".agent-team-backups"
    $backupRoot = Join-Path $backupBase $BackupName
    if (-not (Test-Path -LiteralPath $backupRoot -PathType Container)) {
        throw "Backup does not exist: $backupRoot"
    }
    $operation = "Restore managed agent-team files from $BackupName"
    if (-not $PSCmdlet.ShouldProcess($destinationRoot, $operation)) {
        Write-Output "Restore canceled."
        exit 2
    }
    $backupFiles = @(Get-ManagedFiles $backupRoot)
    if ($backupFiles.Count -eq 0) {
        throw "Backup contains no managed files: $backupRoot"
    }
    New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null
    foreach ($file in $backupFiles) {
        $destinationFile = Join-Path $destinationRoot $file.RelativePath
        $destinationDirectory = Split-Path -Parent $destinationFile
        if (-not (Test-Path -LiteralPath $destinationDirectory)) {
            New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $file.FullName -Destination $destinationFile -Force
    }
    $restoredFiles = @(Get-ManagedFiles $destinationRoot)
    $restoredDrift = Compare-ManagedFiles $backupFiles $restoredFiles
    if ($restoredDrift.HasDrift) {
        Write-Drift $restoredDrift
        throw "agent-team restore did not converge to the backup."
    }
    Write-Output "Restored agent-team runtime copy from $BackupName ($($backupFiles.Count) managed files)."
    exit 0
}

if (-not $drift.HasDrift) {
    Write-Output "agent-team runtime copy is already current ($($sourceFiles.Count) managed files)."
    exit 0
}

Write-Drift $drift
$operation = "Back up and synchronize $($sourceFiles.Count) managed agent-team files"
if (-not $PSCmdlet.ShouldProcess($destinationRoot, $operation)) {
    Write-Output "Install canceled."
    exit 2
}

$backupPath = $null
if ($destinationFiles.Count -gt 0) {
    $destinationParent = Split-Path -Parent $destinationRoot
    $backupBase = Join-Path $destinationParent ".agent-team-backups"
    $backupName = (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + [guid]::NewGuid().ToString("N").Substring(0, 8)
    $backupPath = Join-Path $backupBase $backupName

    foreach ($file in $destinationFiles) {
        $backupFile = Join-Path $backupPath $file.RelativePath
        $backupDirectory = Split-Path -Parent $backupFile
        if (-not (Test-Path -LiteralPath $backupDirectory)) {
            New-Item -ItemType Directory -Path $backupDirectory | Out-Null
        }
        Copy-Item -LiteralPath $file.FullName -Destination $backupFile
    }
}

if (-not (Test-Path -LiteralPath $destinationRoot)) {
    New-Item -ItemType Directory -Path $destinationRoot | Out-Null
}

foreach ($file in $sourceFiles) {
    $destinationFile = Join-Path $destinationRoot $file.RelativePath
    $destinationDirectory = Split-Path -Parent $destinationFile
    if (-not (Test-Path -LiteralPath $destinationDirectory)) {
        New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
    }
    Copy-Item -LiteralPath $file.FullName -Destination $destinationFile -Force
}

foreach ($relativePath in $drift.Stale) {
    $stalePath = Join-Path $destinationRoot $relativePath
    if (Test-Path -LiteralPath $stalePath -PathType Leaf) {
        Remove-Item -LiteralPath $stalePath -Force
    }
}

# Prune empty managed directories left by stale-file removal.
$managedDirs = @(Get-ChildItem -Directory -Recurse -LiteralPath $destinationRoot | Sort-Object { $_.FullName.Length } -Descending)
foreach ($dir in $managedDirs) {
    if (@(Get-ChildItem -Force -LiteralPath $dir.FullName).Count -eq 0) {
        Remove-Item -LiteralPath $dir.FullName -Force -ErrorAction SilentlyContinue
    }
}

$postInstallFiles = @(Get-ManagedFiles $destinationRoot)
$postInstallDrift = Compare-ManagedFiles $sourceFiles $postInstallFiles
if ($postInstallDrift.HasDrift) {
    Write-Drift $postInstallDrift
    throw "agent-team installation did not converge to canonical source."
}

Write-Output "Installed agent-team runtime copy ($($sourceFiles.Count) managed files)."
if ($null -ne $backupPath) {
    Write-Output "Backup: $backupPath"
}

# Prune old backups, keeping the most recent $KeepBackups directories.
$backupBase = Join-Path (Split-Path -Parent $destinationRoot) ".agent-team-backups"
if (Test-Path -LiteralPath $backupBase -PathType Container) {
    $backupDirs = @(
        Get-ChildItem -Directory -LiteralPath $backupBase |
            Sort-Object Name -Descending
    )
    foreach ($dir in $backupDirs | Select-Object -Skip $KeepBackups) {
        Remove-Item -LiteralPath $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
}
exit 0
