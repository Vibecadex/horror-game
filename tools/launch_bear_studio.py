"""Open this checkout's local Bear Studio without installing dependencies."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


def health(url: str) -> dict | None:
    try:
        with urlopen(url + "/api/health", timeout=1) as response:
            return json.load(response)
    except (OSError, URLError, ValueError):
        return None


def same_path(value: str | None, expected: Path) -> bool:
    return bool(value) and Path(value).resolve() == expected.resolve()


def require_own_service(info: dict, data_dir: Path) -> None:
    if not (info.get("app") == "bear-studio" and info.get("ok")
            and same_path(info.get("workspace"), ROOT)
            and same_path(info.get("dataDir"), data_dir)):
        raise RuntimeError("This port belongs to another service, checkout or catalogue. "
                           "Choose another port with --port 8473.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8472)
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".team-local" / "bear-studio")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--foreground", action="store_true", help="Run until Ctrl+C")
    parser.add_argument("--status", action="store_true", help="Check without starting")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    data_dir = args.data_dir.resolve()
    url = f"http://127.0.0.1:{args.port}"
    info = health(url)
    if info:
        require_own_service(info, data_dir)
        print(f"Bear Studio is running: {url}")
    elif args.status:
        print(f"Bear Studio is not running at {url}")
        return 1
    else:
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", args.port)) == 0:
                raise RuntimeError(f"Port {args.port} is in use. Choose --port 8473.")
        data_dir.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-u", str(ROOT / "tools" / "bear_studio" / "server.py"),
                   "--port", str(args.port), "--data-dir", str(data_dir)]
        if args.foreground:
            print(f"Starting Bear Studio at {url}. Press Ctrl+C to stop.")
            return subprocess.call(command, cwd=ROOT)
        log_path = data_dir / "service.log"
        options: dict = {"cwd": ROOT, "stdin": subprocess.DEVNULL}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            options["start_new_session"] = True
        with log_path.open("ab") as log:
            process = subprocess.Popen(command, stdout=log, stderr=log, **options)
        (data_dir / "service-process.json").write_text(json.dumps({
            "pid": process.pid, "workspace": str(ROOT), "url": url,
            "dataDir": str(data_dir), "started": time.time(),
        }, indent=2) + "\n", encoding="utf-8")
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            info = health(url)
            if info:
                require_own_service(info, data_dir)
                break
            if process.poll() is not None:
                raise RuntimeError(f"Studio exited with {process.returncode}. See {log_path}")
            time.sleep(0.2)
        else:
            raise RuntimeError(f"Studio did not become ready. See {log_path}")
        print(f"Bear Studio started: {url}")
        print(f"Catalogue and logs: {data_dir}")
    if not args.no_browser and not args.status:
        webbrowser.open(url)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        print(f"Bear Studio: {exc}", file=sys.stderr)
        raise SystemExit(1)
