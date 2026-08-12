#!/usr/bin/env python3
"""Bounded external evidence loop for isolated Git worktrees."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

__version__ = "0.3.0"
SCHEMA_VERSION = 1
MAX_CAPTURE_CHARS = 4_000
MAX_HISTORY_EVENTS = 40
TERMINAL_STATUSES = {
    "completed",
    "aborted",
    "stopped_iteration",
    "stopped_time",
    "stopped_no_progress",
    "stopped_acceptance_tampered",
}
FORBIDDEN_EXECUTABLES = {
    "bash",
    "cmd",
    "cmd.exe",
    "curl",
    "fish",
    "ftp",
    "pwsh",
    "pwsh.exe",
    "powershell",
    "powershell.exe",
    "scp",
    "sh",
    "ssh",
    "wget",
    "wsl",
    "zsh",
}
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,254}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
REDACTIONS = (
    # OpenAI-style keys
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    # Bearer tokens
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    # key=value / key: value assignments
    re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*"
        r"([^\s,;]{4,})"
    ),
    # AWS access keys
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    # GitHub tokens
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    # Slack tokens
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    # JWT compact tokens (header.payload.signature)
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
    ),
    # PEM private-key blocks
    re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
        r".*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        re.DOTALL,
    ),
)
SENSITIVE_FILE_NAMES = {
    ".env",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
}


class LoopError(RuntimeError):
    """A user-actionable evidence-loop contract error."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def is_within(path: Path, parent: Path) -> bool:
    try:
        path_value = os.path.normcase(os.path.realpath(path))
        parent_value = os.path.normcase(os.path.realpath(parent))
        return os.path.commonpath([path_value, parent_value]) == parent_value
    except ValueError:
        return False


def resolve_existing_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise LoopError(f"Directory does not exist: {path}")
    return path


def find_obsidian_vault(path: Path) -> Path | None:
    """Return the nearest Obsidian vault containing path, if one exists."""
    resolved = path.expanduser().resolve()
    candidates = (resolved, *resolved.parents)
    for candidate in candidates:
        if (candidate / ".obsidian").is_dir():
            return candidate
    return None


def run_git(worktree: Path, *args: str, text: bool = True) -> Any:
    try:
        return subprocess.run(
            ["git", "-C", str(worktree), *args],
            check=True,
            capture_output=True,
            text=text,
            timeout=30,
            shell=False,
        ).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise LoopError(f"Git validation failed for {worktree}: {exc}") from exc


def absolute_git_path(worktree: Path, value: str) -> Path:
    path = Path(value.strip())
    if not path.is_absolute():
        path = worktree / path
    return path.resolve()


def validate_linked_worktree(worktree: Path) -> None:
    root = absolute_git_path(
        worktree, run_git(worktree, "rev-parse", "--show-toplevel").strip()
    )
    if root != worktree:
        raise LoopError(f"Target must be the Git worktree root: {root}")

    git_dir = absolute_git_path(
        worktree, run_git(worktree, "rev-parse", "--git-dir").strip()
    )
    common_dir = absolute_git_path(
        worktree, run_git(worktree, "rev-parse", "--git-common-dir").strip()
    )
    if git_dir == common_dir:
        raise LoopError("Target is the main checkout, not an isolated linked worktree")


def git_identity(worktree: Path) -> dict[str, str]:
    branch = run_git(worktree, "symbolic-ref", "--quiet", "--short", "HEAD").strip()
    if not branch:
        raise LoopError("Detached HEAD is not allowed for an evidence loop")
    return {
        "base_commit": run_git(worktree, "rev-parse", "HEAD").strip(),
        "branch": branch,
        "git_dir": str(
            absolute_git_path(
                worktree, run_git(worktree, "rev-parse", "--git-dir").strip()
            )
        ),
        "common_dir": str(
            absolute_git_path(
                worktree, run_git(worktree, "rev-parse", "--git-common-dir").strip()
            )
        ),
    }


def parse_command(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LoopError(f"--check-json is not valid JSON: {exc}") from exc
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise LoopError("Each --check-json value must be a non-empty JSON string array")
    executable = Path(value[0]).name.lower()
    if executable in FORBIDDEN_EXECUTABLES:
        raise LoopError(
            f"Direct shell/network executable is forbidden for verification: {executable}"
        )
    if executable in {"node", "node.exe"} and len(value) > 1 and value[1] in {"-e", "--eval"}:
        raise LoopError("Inline Node.js evaluation is forbidden for verification")
    if (
        executable in {"python", "python.exe", "py", "py.exe"}
        or executable.startswith("python3")
    ) and len(value) > 1 and value[1] == "-c":
        raise LoopError("Inline Python evaluation is forbidden for verification")
    return value


def normalize_protected_paths(values: Sequence[str]) -> list[Path]:
    paths = [Path(value).expanduser().resolve() for value in values]
    return sorted(set(paths), key=lambda path: os.path.normcase(str(path)))


def contract_path_for(state_path: Path) -> Path:
    return state_path.with_name(f"{state_path.stem}.contract.json")


def contract_hash(contract: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(contract))


def validate_state_shape(state: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "run_id",
        "contract_file",
        "contract_hash",
        "state_hash",
        "revision",
        "iteration",
        "status",
        "worker_run_ids",
        "current_worker_run_id",
        "same_failure_streak",
        "history",
        "active_seconds",
    }
    missing = required.difference(state)
    if missing:
        raise LoopError(f"State is missing required fields: {sorted(missing)}")
    if state["schema_version"] != SCHEMA_VERSION:
        raise LoopError(f"Unsupported state schema: {state['schema_version']}")


def state_hash(state: dict[str, Any]) -> str:
    payload = {key: value for key, value in state.items() if key != "state_hash"}
    return sha256_bytes(canonical_json(payload))


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LoopError(f"Cannot read {label} file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LoopError(f"{label} root must be a JSON object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise LoopError(f"Cannot write state file {path}: {exc}") from exc


def make_readonly(path: Path) -> None:
    """Best-effort read-only marking; contract hashes remain the guarantee."""
    with suppress(OSError):
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def write_state(path: Path, state: dict[str, Any]) -> None:
    state["revision"] += 1
    state["state_hash"] = state_hash(state)
    write_json_atomic(path, state)


@contextmanager
def run_lock(state_path: Path) -> Any:
    lock_path = state_path.with_name(f"{state_path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


def read_bundle(
    state_path: Path,
    expected_contract_hash: str,
    expected_state_hash: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not SHA256_RE.fullmatch(expected_contract_hash):
        raise LoopError("Expected contract hash must be a lowercase SHA-256 value")
    if not SHA256_RE.fullmatch(expected_state_hash):
        raise LoopError("Expected state hash must be a lowercase SHA-256 value")
    state = read_json(state_path, "state")
    validate_state_shape(state)
    actual_state_hash = state_hash(state)
    if state["state_hash"] != actual_state_hash or expected_state_hash != actual_state_hash:
        raise LoopError("Pinned evidence-loop state does not match current state")
    contract_path = Path(state["contract_file"]).resolve()
    contract = read_json(contract_path, "contract")
    actual_hash = contract_hash(contract)
    if state["contract_hash"] != actual_hash or expected_contract_hash != actual_hash:
        raise LoopError("Pinned evidence-loop contract does not match current files")
    return state, contract


def append_event(state: dict[str, Any], event: str, **details: Any) -> None:
    item = {"at": isoformat(utc_now()), "event": event, **details}
    state["history"] = (state.get("history", []) + [item])[-MAX_HISTORY_EVENTS:]


def redact(value: str, max_chars: int = MAX_CAPTURE_CHARS) -> str:
    result = value
    for pattern in REDACTIONS:
        if pattern.groups >= 2:
            result = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", result)
        else:
            result = pattern.sub("[REDACTED]", result)
    if len(result) > max_chars:
        result = result[-max_chars:]
        result = f"[OUTPUT TRUNCATED]\n{result}"
    return result


def normalize_failure_text(value: str, worktree: Path) -> str:
    result = re.sub(
        re.escape(str(worktree)),
        "<WORKTREE>",
        value,
        flags=re.IGNORECASE,
    )
    result = re.sub(
        r"\b\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+Z?\b",
        "<TIMESTAMP>",
        result,
    )
    result = re.sub(r"\b\d+(?:\.\d+)?(?:ms|s|sec|seconds)\b", "<DURATION>", result)
    return result


def ensure_runtime_contract(
    state_path: Path, state: dict[str, Any], contract: dict[str, Any]
) -> Path:
    worktree = resolve_existing_dir(contract["worktree"])
    validate_linked_worktree(worktree)
    identity = git_identity(worktree)
    if identity != contract["git_identity"]:
        raise LoopError("Git branch, base commit, or worktree identity changed")
    for protected in (Path(value).resolve() for value in contract["protected_paths"]):
        if is_within(worktree, protected) or is_within(protected, worktree):
            raise LoopError(f"Worktree overlaps a protected path: {protected}")
    metadata_paths = (
        worktree,
        Path(contract["git_identity"]["git_dir"]).resolve(),
        Path(contract["git_identity"]["common_dir"]).resolve(),
    )
    for control_path in (state_path.resolve(), Path(state["contract_file"]).resolve()):
        if any(is_within(control_path, blocked) for blocked in metadata_paths):
            raise LoopError("Control files must remain outside worktree and Git metadata")
        for protected in (Path(value).resolve() for value in contract["protected_paths"]):
            if is_within(control_path, protected):
                raise LoopError("Control files must remain outside protected paths")
    return worktree


def stop_for_budget(
    state: dict[str, Any], contract: dict[str, Any]
) -> str | None:
    if utc_now() >= parse_time(contract["deadline"]):
        state["status"] = "stopped_time"
        state["stop_reason"] = "max_elapsed_time"
        append_event(state, "stopped", reason="max_elapsed_time")
        return "stopped_time"
    if state["iteration"] >= contract["limits"]["max_iterations"]:
        state["status"] = "stopped_iteration"
        state["stop_reason"] = "max_iterations"
        append_event(state, "stopped", reason="max_iterations")
        return "stopped_iteration"
    return None


def path_fingerprint(path: Path) -> str:
    path = path.resolve()
    digest = hashlib.sha256()
    if path.is_file():
        if is_sensitive_file(path):
            raise LoopError(f"Sensitive-looking file cannot be frozen: {path.name}")
        digest.update(path.name.encode("utf-8", errors="replace"))
        digest.update(path.read_bytes())
        return digest.hexdigest()
    if not path.is_dir():
        raise LoopError(f"Frozen acceptance path does not exist: {path}")
    for candidate in sorted(path.rglob("*"), key=lambda item: str(item).lower()):
        resolved = candidate.resolve()
        if not is_within(resolved, path):
            raise LoopError(f"Frozen acceptance path escapes through a link: {candidate}")
        if candidate.is_file():
            if is_sensitive_file(candidate):
                raise LoopError(
                    f"Sensitive-looking file cannot be frozen: {candidate.name}"
                )
            digest.update(str(candidate.relative_to(path)).encode("utf-8"))
            digest.update(candidate.read_bytes())
    return digest.hexdigest()


def is_sensitive_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        name in SENSITIVE_FILE_NAMES
        or name.startswith(".env.")
        or name.endswith((".key", ".pem", ".p12", ".pfx"))
    )


def validate_frozen_assets(contract: dict[str, Any]) -> None:
    for raw_path, expected_hash in contract["frozen_assets"].items():
        path = Path(raw_path).resolve()
        try:
            actual_hash = path_fingerprint(path)
        except (OSError, LoopError):
            actual_hash = "[MISSING_OR_UNREADABLE]"
        if actual_hash != expected_hash:
            raise LoopError(f"Frozen acceptance asset changed: {path}")


def source_fingerprint(worktree: Path, base_commit: str) -> str:
    digest = hashlib.sha256()
    diff = run_git(worktree, "diff", "--binary", base_commit, text=False)
    digest.update(diff)
    untracked = run_git(
        worktree, "ls-files", "--others", "--exclude-standard", "-z", text=False
    )
    for raw_name in sorted(name for name in untracked.split(b"\0") if name):
        digest.update(raw_name)
        try:
            relative = Path(os.fsdecode(raw_name))
            candidate = (worktree / relative).resolve()
            if not is_within(candidate, worktree) or not candidate.is_file():
                continue
            if is_sensitive_file(candidate):
                digest.update(b"[SENSITIVE_FILE_NOT_READ]")
            else:
                digest.update(sha256_bytes(candidate.read_bytes()).encode("ascii"))
        except OSError:
            digest.update(b"[UNREADABLE]")
    return digest.hexdigest()


def sanitized_environment(passthrough: Sequence[str] = ()) -> dict[str, str]:
    allowed = {
        # Windows
        "APPDATA",
        "COMMONPROGRAMFILES",
        "COMMONPROGRAMFILES(X86)",
        "COMMONPROGRAMW6432",
        "HOMEDRIVE",
        "HOMEPATH",
        "LOCALAPPDATA",
        "NUMBER_OF_PROCESSORS",
        "OS",
        "PATH",
        "PATHEXT",
        "PROCESSOR_ARCHITECTURE",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "WINDIR",
        # POSIX
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_COLLATE",
        "LC_CTYPE",
        "LC_MESSAGES",
        "LC_MONETARY",
        "LC_NUMERIC",
        "LC_TIME",
        "LOGNAME",
        "PWD",
        "SHELL",
        "TMPDIR",
        "USER",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_RUNTIME_DIR",
    }
    allowed.update(name.upper() for name in passthrough)
    return {key: value for key, value in os.environ.items() if key.upper() in allowed}


def validate_env_passthrough(names: Sequence[str]) -> list[str]:
    normalized = sorted({name.upper() for name in names})
    for name in normalized:
        if not ENV_NAME_RE.fullmatch(name):
            raise LoopError(f"Invalid environment variable name for passthrough: {name}")
    return normalized


def create_windows_kill_job(process: subprocess.Popen[bytes]) -> int:
    import ctypes
    from ctypes import wintypes

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    kernel32.AssignProcessToJobObject.argtypes = (
        wintypes.HANDLE,
        wintypes.HANDLE,
    )
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    information.BasicLimitInformation.LimitFlags = 0x00002000
    if not kernel32.SetInformationJobObject(
        job, 9, ctypes.byref(information), ctypes.sizeof(information)
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(job)
        raise OSError(error, "SetInformationJobObject failed")
    if not kernel32.AssignProcessToJobObject(job, int(process._handle)):  # type: ignore[attr-defined]
        error = ctypes.get_last_error()
        kernel32.CloseHandle(job)
        raise OSError(error, "AssignProcessToJobObject failed")
    return int(job)


def close_windows_handle(handle: int | None) -> None:
    if handle is None:
        return
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle(handle)


def terminate_process_tree(
    process: subprocess.Popen[bytes], windows_job: int | None
) -> bool:
    if os.name == "nt":
        close_windows_handle(windows_job)
    elif process.poll() is None:
        import signal

        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)  # type: ignore[attr-defined]
    try:
        process.wait(timeout=15)
        return True
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=5)
            return True
        except (OSError, subprocess.TimeoutExpired):
            return False


def read_capped_output(handle: Any, max_chars: int = MAX_CAPTURE_CHARS) -> str:
    handle.flush()
    size = handle.seek(0, os.SEEK_END)
    handle.seek(max(0, size - (max_chars * 4)))
    return redact(handle.read().decode("utf-8", errors="replace"), max_chars)


@contextmanager
def posix_signal_cleanup(process: subprocess.Popen[bytes]) -> Any:
    """On POSIX, kill the child process group when the parent is interrupted.

    Windows is covered by the Job Object; POSIX needs an explicit handler so a
    Ctrl-C on the controller does not leave descendant check processes alive.
    """
    if os.name == "nt":
        yield
        return
    import signal

    def _kill_child_group(_signum: int, _frame: Any) -> None:
        with suppress(ProcessLookupError, OSError):
            os.killpg(process.pid, signal.SIGKILL)  # type: ignore[attr-defined]

    previous_int = signal.signal(signal.SIGINT, _kill_child_group)
    previous_term = signal.signal(signal.SIGTERM, _kill_child_group)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous_int)
        signal.signal(signal.SIGTERM, previous_term)


def windows_wrapped_command(command: list[str]) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--internal-exec-check",
        json.dumps(command),
    ]


def run_check(
    command: list[str],
    worktree: Path,
    timeout_seconds: int,
    passthrough: Sequence[str] = (),
    max_chars: int = MAX_CAPTURE_CHARS,
) -> dict[str, Any]:
    started = time.monotonic()
    windows_job: int | None = None
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            actual_command = windows_wrapped_command(command) if os.name == "nt" else command
            process = subprocess.Popen(
                actual_command,
                cwd=worktree,
                stdin=subprocess.PIPE if os.name == "nt" else subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                shell=False,
                env=sanitized_environment(passthrough),
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
                start_new_session=os.name != "nt",
            )
            if os.name == "nt":
                try:
                    windows_job = create_windows_kill_job(process)
                except OSError:
                    process.kill()
                    process.wait(timeout=5)
                    raise
                assert process.stdin is not None
                process.stdin.write(b"1")
                process.stdin.close()
                process.stdin = None
            try:
                with posix_signal_cleanup(process):
                    process.wait(timeout=timeout_seconds)
                timed_out = False
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                returncode = None
                terminated = terminate_process_tree(process, windows_job)
                windows_job = None
                if not terminated:
                    returncode = -1
            finally:
                close_windows_handle(windows_job)
            return {
                "command": command,
                "returncode": returncode,
                "timed_out": timed_out,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": read_capped_output(stdout_file, max_chars),
                "stderr": read_capped_output(stderr_file, max_chars),
            }
        except OSError as exc:
            return {
                "command": command,
                "returncode": None,
                "timed_out": False,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": read_capped_output(stdout_file, max_chars),
                "stderr": redact(str(exc), max_chars),
            }


def init_run(args: argparse.Namespace) -> int:
    if not IDENTIFIER_RE.fullmatch(args.run_id):
        raise LoopError("Run ID must use 1-128 safe identifier characters")
    worktree = resolve_existing_dir(args.worktree)
    vault_root = find_obsidian_vault(worktree)
    if vault_root is not None:
        raise LoopError(f"Evidence loop cannot target an Obsidian vault: {vault_root}")
    validate_linked_worktree(worktree)
    if run_git(worktree, "status", "--porcelain=v1").strip():
        raise LoopError("Evidence-loop worktree must be clean at initialization")
    identity = git_identity(worktree)
    state_path = Path(args.state_file).expanduser().resolve()
    contract_path = contract_path_for(state_path)

    protected_paths = normalize_protected_paths(args.protected_path)
    for protected in protected_paths:
        if is_within(worktree, protected) or is_within(protected, worktree):
            raise LoopError(f"Worktree overlaps a protected path: {protected}")

    env_passthrough = validate_env_passthrough(args.env_passthrough)

    checks = [parse_command(raw) for raw in args.check_json]
    frozen_paths = [Path(value).expanduser().resolve() for value in args.frozen_path]
    harnesses = [
        Path(value).expanduser().resolve() for value in args.controller_harness
    ]
    if not frozen_paths and not harnesses:
        raise LoopError(
            "Freeze acceptance assets or provide a controller-owned external harness"
        )
    for frozen_path in frozen_paths:
        if not is_within(frozen_path, worktree):
            raise LoopError("--frozen-path values must be inside the target worktree")

    metadata_paths = (
        worktree,
        Path(identity["git_dir"]).resolve(),
        Path(identity["common_dir"]).resolve(),
    )
    for control_path in (state_path, contract_path):
        if any(is_within(control_path, blocked) for blocked in metadata_paths):
            raise LoopError("Control files must be outside worktree and Git metadata")
        if find_obsidian_vault(control_path) is not None:
            raise LoopError("Control files must be outside Obsidian vaults")
        if any(is_within(control_path, path) for path in protected_paths):
            raise LoopError("Control files must be outside protected paths")

    flattened_commands = {
        os.path.normcase(os.path.realpath(token))
        for command in checks
        for token in command
        if Path(token).is_absolute()
    }
    for harness in harnesses:
        if not harness.is_file():
            raise LoopError(f"Controller harness is not a file: {harness}")
        if (
            is_within(harness, worktree)
            or find_obsidian_vault(harness) is not None
            or any(is_within(harness, path) for path in protected_paths)
        ):
            raise LoopError("Controller harness must be outside writable/protected paths")
        if os.path.normcase(os.path.realpath(harness)) not in flattened_commands:
            raise LoopError(f"Controller harness is not referenced by a check: {harness}")

    frozen_assets: dict[str, str] = {}
    for path in sorted(
        set(frozen_paths + harnesses), key=lambda item: os.path.normcase(str(item))
    ):
        frozen_assets[str(path)] = path_fingerprint(path)

    created = utc_now()
    active_budget_seconds = args.active_budget_seconds or (args.max_minutes * 60)
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "objective_hash": sha256_bytes(args.objective.encode("utf-8")),
        "worktree": str(worktree),
        "checks": checks,
        "frozen_assets": frozen_assets,
        "controller_harnesses": [str(path) for path in harnesses],
        "git_identity": identity,
        "limits": {
            "max_iterations": args.max_iterations,
            "max_minutes": args.max_minutes,
            "command_timeout_seconds": args.command_timeout,
            "same_failure_limit": args.same_failure_limit,
            "active_budget_seconds": active_budget_seconds,
            "review_grace_minutes": args.review_grace_minutes,
            "max_capture_chars": args.max_capture_chars,
        },
        "require_review": True,
        "protected_paths": [str(path) for path in protected_paths],
        "env_passthrough": env_passthrough,
        "created_at": isoformat(created),
        # Wall-clock backstop, deliberately much larger than the active budget:
        # agent-in-the-loop planning between init and verify must not consume
        # the enforcement budget.
        "deadline": isoformat(
            created + timedelta(minutes=args.max_minutes * 8)
        ),
    }
    pinned_hash = contract_hash(contract)
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "contract_file": str(contract_path),
        "contract_hash": pinned_hash,
        "state_hash": "",
        "revision": 0,
        "iteration": 0,
        "status": "active",
        "worker_run_ids": [],
        "current_worker_run_id": None,
        "same_failure_streak": 0,
        "last_failure_fingerprint": None,
        "last_verification": None,
        "last_review": None,
        "stop_reason": None,
        "active_seconds": 0.0,
        "history": [],
    }
    append_event(state, "initialized")
    lock_path = state_path.with_name(f"{state_path.name}.lock")
    try:
        with run_lock(state_path):
            if state_path.exists() or contract_path.exists():
                raise LoopError(f"Run control files already exist for: {state_path}")
            write_json_atomic(contract_path, contract)
            make_readonly(contract_path)
            write_state(state_path, state)
    except BaseException:
        # Failed init leaves an orphan lock; remove it so the next attempt
        # can lock cleanly. Only safe because init created the lock anew.
        with suppress(OSError):
            lock_path.unlink(missing_ok=True)
        raise
    print_summary(state, contract)
    return 0


def next_iteration(args: argparse.Namespace) -> int:
    if not IDENTIFIER_RE.fullmatch(args.worker_run_id):
        raise LoopError("Worker run ID must use 1-128 safe identifier characters")
    state_path = Path(args.state_file).expanduser().resolve()
    with run_lock(state_path):
        state, contract = read_bundle(
            state_path, args.expected_contract_hash, args.expected_state_hash
        )
        ensure_runtime_contract(state_path, state, contract)
        if state["status"] in TERMINAL_STATUSES:
            raise LoopError(f"Run is terminal: {state['status']}")
        if state["status"] != "active":
            raise LoopError(f"Run cannot start an iteration from: {state['status']}")
        if args.worker_run_id in state["worker_run_ids"]:
            raise LoopError("Each outer iteration requires a fresh worker run ID")
        try:
            validate_frozen_assets(contract)
        except LoopError:
            state["status"] = "stopped_acceptance_tampered"
            state["stop_reason"] = "acceptance_assets_changed"
            append_event(state, "stopped", reason="acceptance_assets_changed")
            write_state(state_path, state)
            print_summary(state, contract)
            return 3
        if stop_for_budget(state, contract):
            write_state(state_path, state)
            print_summary(state, contract)
            return 3
        state["iteration"] += 1
        state["status"] = "running"
        state["current_worker_run_id"] = args.worker_run_id
        state["worker_run_ids"].append(args.worker_run_id)
        append_event(
            state,
            "iteration_started",
            iteration=state["iteration"],
            worker_run_id=args.worker_run_id,
        )
        write_state(state_path, state)
    print_summary(state, contract)
    return 0


def verify_iteration(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file).expanduser().resolve()
    with run_lock(state_path):
        state, contract = read_bundle(
            state_path, args.expected_contract_hash, args.expected_state_hash
        )
        worktree = ensure_runtime_contract(state_path, state, contract)
        if state["status"] != "running":
            raise LoopError(f"Run cannot verify from: {state['status']}")
        try:
            validate_frozen_assets(contract)
        except LoopError:
            state["status"] = "stopped_acceptance_tampered"
            state["stop_reason"] = "acceptance_assets_changed"
            append_event(state, "stopped", reason="acceptance_assets_changed")
            write_state(state_path, state)
            print_summary(state, contract)
            return 3
        if utc_now() >= parse_time(contract["deadline"]):
            state["status"] = "stopped_time"
            state["stop_reason"] = "max_elapsed_time"
            append_event(state, "stopped", reason="max_elapsed_time")
            write_state(state_path, state)
            print_summary(state, contract)
            return 3

        results: list[dict[str, Any]] = []
        passthrough = contract.get("env_passthrough", [])
        active_budget = contract["limits"]["active_budget_seconds"]
        for command in contract["checks"]:
            remaining = int(
                (parse_time(contract["deadline"]) - utc_now()).total_seconds()
            )
            if remaining <= 0:
                state["status"] = "stopped_time"
                state["stop_reason"] = "max_elapsed_time"
                append_event(state, "stopped", reason="max_elapsed_time")
                write_state(state_path, state)
                print_summary(state, contract)
                return 3
            timeout_seconds = max(
                1,
                min(contract["limits"]["command_timeout_seconds"], remaining),
            )
            result = run_check(
                command,
                worktree,
                timeout_seconds,
                passthrough,
                contract["limits"].get("max_capture_chars", MAX_CAPTURE_CHARS),
            )
            results.append(result)
            state["active_seconds"] += result.get("duration_seconds", 0.0)
            if state["active_seconds"] > active_budget:
                state["status"] = "stopped_time"
                state["stop_reason"] = "active_budget_exceeded"
                append_event(
                    state,
                    "stopped",
                    reason="active_budget_exceeded",
                    active_seconds=state["active_seconds"],
                )
                write_state(state_path, state)
                print_summary(state, contract)
                return 3
            if utc_now() >= parse_time(contract["deadline"]):
                state["status"] = "stopped_time"
                state["stop_reason"] = "max_elapsed_time"
                append_event(state, "stopped", reason="max_elapsed_time")
                write_state(state_path, state)
                print_summary(state, contract)
                return 3

        passed = all(
            result["returncode"] == 0 and not result["timed_out"]
            for result in results
        )
        source_hash = source_fingerprint(
            worktree, contract["git_identity"]["base_commit"]
        )
        evidence_payload = {
            "iteration": state["iteration"],
            "worker_run_id": state["current_worker_run_id"],
            "passed": passed,
            "source_fingerprint": source_hash,
            "checks": results,
        }
        evidence_payload["evidence_hash"] = sha256_bytes(
            canonical_json(evidence_payload)
        )
        state["last_verification"] = evidence_payload

        if passed:
            state["same_failure_streak"] = 0
            state["last_failure_fingerprint"] = None
            state["status"] = "verification_passed"
            state["verification_passed_at"] = isoformat(utc_now())
            append_event(
                state,
                "verification_passed",
                iteration=state["iteration"],
                evidence_hash=evidence_payload["evidence_hash"],
            )
            write_state(state_path, state)
            print_summary(state, contract)
            return 0

        failure_fingerprint = sha256_bytes(
            canonical_json(
                {
                    "source_fingerprint": source_hash,
                    "checks": [
                        {
                            "command": result["command"],
                            "returncode": result["returncode"],
                            "timed_out": result["timed_out"],
                            "stdout": normalize_failure_text(
                                result["stdout"], worktree
                            ),
                            "stderr": normalize_failure_text(
                                result["stderr"], worktree
                            ),
                        }
                        for result in results
                    ],
                }
            )
        )
        if failure_fingerprint == state.get("last_failure_fingerprint"):
            state["same_failure_streak"] += 1
        else:
            state["same_failure_streak"] = 1
        state["last_failure_fingerprint"] = failure_fingerprint

        if (
            state["same_failure_streak"]
            >= contract["limits"]["same_failure_limit"]
        ):
            state["status"] = "stopped_no_progress"
            state["stop_reason"] = "same_failure_repeated"
            append_event(
                state,
                "stopped",
                reason="same_failure_repeated",
                iteration=state["iteration"],
                failure_fingerprint=failure_fingerprint,
            )
            exit_code = 3
        else:
            state["status"] = "active"
            append_event(
                state,
                "verification_failed",
                iteration=state["iteration"],
                failure_fingerprint=failure_fingerprint,
            )
            exit_code = 2

        write_state(state_path, state)
    print_summary(state, contract)
    return exit_code


def record_review(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file).expanduser().resolve()
    for label, value in (
        ("reviewer run ID", args.reviewer_run_id),
        ("reviewer backend", args.reviewer_backend),
    ):
        if not IDENTIFIER_RE.fullmatch(value):
            raise LoopError(f"{label} must use 1-128 safe identifier characters")
    if not SHA256_RE.fullmatch(args.artifact_hash):
        raise LoopError("Review artifact hash must be a lowercase SHA-256 value")
    with run_lock(state_path):
        state, contract = read_bundle(
            state_path, args.expected_contract_hash, args.expected_state_hash
        )
        worktree = ensure_runtime_contract(state_path, state, contract)
        if state["status"] != "verification_passed":
            raise LoopError(f"Run cannot record review from: {state['status']}")
        try:
            validate_frozen_assets(contract)
        except LoopError:
            state["status"] = "stopped_acceptance_tampered"
            state["stop_reason"] = "acceptance_assets_changed_after_verification"
            append_event(
                state,
                "stopped",
                reason="acceptance_assets_changed_after_verification",
            )
            write_state(state_path, state)
            print_summary(state, contract)
            return 3
        current_source_hash = source_fingerprint(
            worktree, contract["git_identity"]["base_commit"]
        )
        if current_source_hash != state["last_verification"]["source_fingerprint"]:
            state["status"] = "active"
            state["stop_reason"] = None
            append_event(
                state,
                "verification_invalidated",
                reason="source_changed_after_verification",
            )
            write_state(state_path, state)
            print_summary(state, contract)
            return 2
        if utc_now() >= parse_time(contract["deadline"]):
            state["status"] = "stopped_time"
            state["stop_reason"] = "max_elapsed_time"
            append_event(state, "stopped", reason="max_elapsed_time")
            write_state(state_path, state)
            print_summary(state, contract)
            return 3
        # Review grace window: once verification passed, the run may complete
        # review even if the wall-clock deadline lapsed, within a bounded grace.
        passed_at = state.get("verification_passed_at")
        grace_minutes = contract["limits"].get("review_grace_minutes", 15)
        if passed_at and utc_now() > parse_time(passed_at) + timedelta(
            minutes=grace_minutes
        ):
            state["status"] = "stopped_time"
            state["stop_reason"] = "review_grace_expired"
            append_event(state, "stopped", reason="review_grace_expired")
            write_state(state_path, state)
            print_summary(state, contract)
            return 3
        if args.reviewer_run_id in state["worker_run_ids"]:
            raise LoopError("Reviewer must be independent from every worker iteration")
        if args.result == "fail" and not args.reason_code:
            raise LoopError("A failed review requires --reason-code")
        if args.reason_code and not REASON_CODE_RE.fullmatch(args.reason_code):
            raise LoopError(
                "Review reason code must use 1-64 lowercase safe characters"
            )

        state["last_review"] = {
            "at": isoformat(utc_now()),
            "result": args.result,
            "reason_code": args.reason_code,
            "reviewer_run_id": args.reviewer_run_id,
            "reviewer_backend": args.reviewer_backend,
            "artifact_hash": args.artifact_hash,
            "verification_evidence_hash": state["last_verification"][
                "evidence_hash"
            ],
        }
        if args.result == "pass":
            state["status"] = "completed"
            append_event(
                state,
                "review_passed",
                iteration=state["iteration"],
                reviewer_run_id=args.reviewer_run_id,
            )
            exit_code = 0
        else:
            state["status"] = "active"
            append_event(
                state,
                "review_failed",
                iteration=state["iteration"],
                reason_code=args.reason_code,
                reviewer_run_id=args.reviewer_run_id,
            )
            exit_code = 2
        write_state(state_path, state)
    print_summary(state, contract)
    return exit_code


def read_state_unpinned(state_path: Path) -> dict[str, Any]:
    """Read state without hash verification for the deliberate recovery path."""
    state = read_json(state_path, "state")
    validate_state_shape(state)
    return state


def read_contract_unpinned(state: dict[str, Any]) -> dict[str, Any]:
    contract_path = Path(state["contract_file"]).resolve()
    return read_json(contract_path, "contract")


def abort_run(args: argparse.Namespace) -> int:
    if not REASON_CODE_RE.fullmatch(args.reason_code):
        raise LoopError("Abort reason code must use 1-64 lowercase safe characters")
    state_path = Path(args.state_file).expanduser().resolve()
    with run_lock(state_path):
        if getattr(args, "acknowledge_unpinned", False):
            state = read_state_unpinned(state_path)
            contract = read_contract_unpinned(state)
            append_event(
                state, "unpinned_abort", reason_code=args.reason_code
            )
        else:
            state, contract = read_bundle(
                state_path, args.expected_contract_hash, args.expected_state_hash
            )
        if state["status"] in TERMINAL_STATUSES:
            raise LoopError(f"Run is already terminal: {state['status']}")
        state["status"] = "aborted"
        state["stop_reason"] = args.reason_code
        append_event(state, "aborted", reason_code=args.reason_code)
        write_state(state_path, state)
    print_summary(state, contract)
    return 0


def inspect_run(args: argparse.Namespace) -> int:
    """Recovery inspection that does not require pinned hashes."""
    if not getattr(args, "acknowledge_unpinned", False):
        raise LoopError("inspect requires --acknowledge-unpinned")
    state_path = Path(args.state_file).expanduser().resolve()
    with run_lock(state_path):
        state = read_state_unpinned(state_path)
        contract = read_contract_unpinned(state)
        append_event(state, "unpinned_inspection")
        write_state(state_path, state)
    print(
        "WARNING: unpinned inspection bypassed hash verification. "
        "Verify the run_id and state path before trusting this output.",
        file=sys.stderr,
    )
    print_summary(state, contract, verbose=args.verbose)
    return 0


def show_status(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file).expanduser().resolve()
    with run_lock(state_path):
        state, contract = read_bundle(
            state_path, args.expected_contract_hash, args.expected_state_hash
        )
    print_summary(state, contract, verbose=args.verbose)
    return 0


def print_summary(
    state: dict[str, Any], contract: dict[str, Any], verbose: bool = False
) -> None:
    summary: dict[str, Any] = {
        "run_id": state["run_id"],
        "status": state["status"],
        "revision": state["revision"],
        "contract_hash": state["contract_hash"],
        "state_hash": state["state_hash"],
        "iteration": state["iteration"],
        "current_worker_run_id": state["current_worker_run_id"],
        "max_iterations": contract["limits"]["max_iterations"],
        "deadline": contract["deadline"],
        "same_failure_streak": state["same_failure_streak"],
        "stop_reason": state.get("stop_reason"),
    }
    if state.get("last_verification"):
        summary["last_verification"] = {
            "passed": state["last_verification"]["passed"],
            "evidence_hash": state["last_verification"]["evidence_hash"],
        }
    if state.get("last_review"):
        summary["last_review"] = state["last_review"]
    if verbose:
        summary["history"] = state["history"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def bounded_int(minimum: int, maximum: int) -> Any:
    def parse(value: str) -> int:
        integer = int(value)
        if not minimum <= integer <= maximum:
            raise argparse.ArgumentTypeError(
                f"must be between {minimum} and {maximum}"
            )
        return integer

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a bounded external evidence loop in a linked Git worktree."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init", help="Freeze a new run contract")
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--objective", required=True)
    init_parser.add_argument("--worktree", required=True)
    init_parser.add_argument("--state-file", required=True)
    init_parser.add_argument("--check-json", action="append", required=True)
    init_parser.add_argument("--frozen-path", action="append", default=[])
    init_parser.add_argument("--controller-harness", action="append", default=[])
    init_parser.add_argument("--protected-path", action="append", default=[])
    init_parser.add_argument("--env-passthrough", action="append", default=[])
    init_parser.add_argument(
        "--max-iterations", type=bounded_int(1, 10), default=4
    )
    init_parser.add_argument("--max-minutes", type=bounded_int(1, 240), default=45)
    init_parser.add_argument(
        "--command-timeout", type=bounded_int(1, 3_600), default=900
    )
    init_parser.add_argument(
        "--same-failure-limit", type=bounded_int(1, 5), default=2
    )
    init_parser.add_argument(
        "--review-grace-minutes", type=bounded_int(1, 240), default=15
    )
    init_parser.add_argument(
        "--active-budget-seconds",
        type=bounded_int(1, 14_400),
        default=None,
        help="Active check-execution budget; defaults to max-minutes * 60",
    )
    init_parser.add_argument(
        "--max-capture-chars",
        type=bounded_int(1, 65_536),
        default=MAX_CAPTURE_CHARS,
        help="Captured output tail per stream (default: 4000)",
    )
    init_parser.set_defaults(handler=init_run)

    next_parser = commands.add_parser("next")
    next_parser.add_argument("--state-file", required=True)
    next_parser.add_argument("--expected-contract-hash", required=True)
    next_parser.add_argument("--expected-state-hash", required=True)
    next_parser.add_argument("--worker-run-id", required=True)
    next_parser.set_defaults(handler=next_iteration)

    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--state-file", required=True)
    verify_parser.add_argument("--expected-contract-hash", required=True)
    verify_parser.add_argument("--expected-state-hash", required=True)
    verify_parser.set_defaults(handler=verify_iteration)

    review_parser = commands.add_parser("review")
    review_parser.add_argument("--state-file", required=True)
    review_parser.add_argument("--expected-contract-hash", required=True)
    review_parser.add_argument("--expected-state-hash", required=True)
    review_parser.add_argument("--result", choices=("pass", "fail"), required=True)
    review_parser.add_argument("--reason-code")
    review_parser.add_argument("--reviewer-run-id", required=True)
    review_parser.add_argument("--reviewer-backend", required=True)
    review_parser.add_argument("--artifact-hash", required=True)
    review_parser.set_defaults(handler=record_review)

    abort_parser = commands.add_parser("abort")
    abort_parser.add_argument("--state-file", required=True)
    abort_parser.add_argument("--expected-contract-hash", default="")
    abort_parser.add_argument("--expected-state-hash", default="")
    abort_parser.add_argument("--acknowledge-unpinned", action="store_true")
    abort_parser.add_argument("--reason-code", required=True)
    abort_parser.set_defaults(handler=abort_run)

    inspect_parser = commands.add_parser(
        "inspect", help="Inspect a run without pinned hashes (recovery only)"
    )
    inspect_parser.add_argument("--state-file", required=True)
    inspect_parser.add_argument("--acknowledge-unpinned", action="store_true")
    inspect_parser.add_argument("--verbose", action="store_true")
    inspect_parser.set_defaults(handler=inspect_run)

    status_parser = commands.add_parser("status")
    status_parser.add_argument("--state-file", required=True)
    status_parser.add_argument("--expected-contract-hash", required=True)
    status_parser.add_argument("--expected-state-hash", required=True)
    status_parser.add_argument("--verbose", action="store_true")
    status_parser.set_defaults(handler=show_status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except LoopError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def exec_check_main(raw_command: str) -> int:
    # This trampoline is private to the helper. Reject interactive TTY use so
    # a user cannot casually treat it as a general command runner.
    if sys.stdin.isatty():
        return 127
    try:
        command = parse_command(raw_command)
        if sys.stdin.buffer.read(1) != b"1":
            return 125
        return subprocess.run(
            command,
            shell=False,
            env=os.environ.copy(),
        ).returncode
    except (LoopError, OSError):
        return 126


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--internal-exec-check":
        raise SystemExit(exec_check_main(sys.argv[2]))
    raise SystemExit(main())
