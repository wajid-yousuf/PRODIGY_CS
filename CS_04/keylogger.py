from __future__ import annotations
import sys
import argparse
import time
import json
import os
import platform
from typing import List, Dict

DEFAULT_OUTPUT = "keylog_cli_consented.json"

def confirm_consent() -> bool:
    print("CONSENT REQUIRED")
    print("This tool will record every key you type into this terminal while it runs.")
    print("Do NOT use this on anyone else's device without explicit written consent.")
    answer = input("Do you consent to start recording? (yes/no): ").strip().lower()
    return answer in ("y", "yes")

def write_json(out_path: str, events: List[Dict], meta: Dict) -> None:
    data = {
        "meta": meta,
        "events": events
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"[Saved JSON] {len(events)} events -> {out_path}")

def write_jsonl(out_path: str, events: List[Dict], meta: Dict) -> None:
    # header meta line then each event as newline JSON
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"meta": meta}, ensure_ascii=False) + "\n")
        for ev in events:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"[Saved JSONL] {len(events)} events -> {out_path}")

def write_txt(out_path: str, events: List[Dict], meta: Dict) -> None:
    # concatenate printable characters into a single string (escape sequences included as repr)
    printable_parts: List[str] = []
    for ev in events:
        if ev.get("type") == "char":
            # ev['repr'] contains quotes like "'a'" or "'\\r'"
            printable_parts.append(ev["repr"])
        else:
            printable_parts.append(f"[{ev.get('type')}:{ev.get('repr')}]")
    content = " ".join(printable_parts)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(f"Meta: {json.dumps(meta, ensure_ascii=False)}\n")
        fh.write("Captured (joined representation):\n")
        fh.write(content + "\n")
    print(f"[Saved TXT] {len(events)} events -> {out_path}")

def write_csv(out_path: str, events: List[Dict], meta: Dict) -> None:
    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["time", "type", "repr", "ord"])
        for ev in events:
            writer.writerow([ev.get("time",""), ev.get("type",""), ev.get("repr",""), ev.get("ord","")])
    print(f"[Saved CSV] {len(events)} events -> {out_path}")

def save_events(out_path: str, fmt: str, events: List[Dict], meta: Dict) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if fmt == "json":
        write_json(out_path, events, meta)
    elif fmt == "jsonl":
        write_jsonl(out_path, events, meta)
    elif fmt == "txt":
        write_txt(out_path, events, meta)
    elif fmt == "csv":
        write_csv(out_path, events, meta)
    else:
        raise ValueError("Unknown format: " + fmt)

# ----- capture implementations -----
def run_unix_capture(out_file: str, fmt: str, meta: Dict) -> None:
    import tty, termios, select
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    events: List[Dict] = []
    try:
        print("\n[Recording] Type in this terminal. Press Ctrl-C to stop and save.\n", flush=True)
        tty.setraw(fd)
        while True:
            r, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not r:
                continue
            ch = sys.stdin.read(1)
            ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

            if ch == '\x03':  # Ctrl-C in raw mode
                print("\n\n[Ctrl-C detected] Stopping and saving...", flush=True)
                break

            if ch == '\x1b':
                seq = ch
                while True:
                    r2, _, _ = select.select([sys.stdin], [], [], 0.02)
                    if r2:
                        nxt = sys.stdin.read(1)
                        seq += nxt
                        if len(seq) > 10 or (nxt.isalpha() and len(seq) > 1):
                            break
                    else:
                        break
                ev = {"time": ts, "type": "escape", "repr": repr(seq), "hex": seq.encode('utf-8', 'replace').hex()}
                print(ev["repr"], end="", flush=True)
            else:
                ev = {"time": ts, "type": "char", "repr": repr(ch), "ord": ord(ch)}
                print(ev["repr"], end="", flush=True)

            events.append(ev)

    except Exception as e:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        raise
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        save_events(out_file, fmt, events, meta)

def run_windows_capture(out_file: str, fmt: str, meta: Dict) -> None:
    import msvcrt
    events: List[Dict] = []
    print("\n[Recording] Type in this terminal. Press Ctrl-C to stop and save.\n", flush=True)
    try:
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
                if ch == '\x03':
                    print("\n\n[Ctrl-C detected] Stopping and saving...", flush=True)
                    break
                ev = {"time": ts, "type": "char", "repr": repr(ch), "ord": ord(ch)}
                events.append(ev)
                print(ev["repr"], end="", flush=True)
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n\n[Stopped] Saving events...", flush=True)
    finally:
        save_events(out_file, fmt, events, meta)

# ----- main -----
def main():
    parser = argparse.ArgumentParser(description="Consent-based CLI keystroke capture (visible).")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="Output file path")
    parser.add_argument("--format", "-f", default="json", choices=["json","jsonl","txt","csv"],
                        help="Output format (json = single JSON with events array)")
    args = parser.parse_args()

    if not sys.stdin.isatty():
        print("This program must be run in an interactive terminal.")
        sys.exit(1)

    if not confirm_consent():
        print("Consent not given. Exiting.")
        sys.exit(0)

    meta = {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "host": platform.node(),
        "user": os.getenv("USER") or os.getenv("USERNAME") or "",
        "format": args.format
    }

    print(f"\nStarting capture. Output file: {args.output}  (format: {args.format})")
    print("Press Ctrl-C at any time to stop and save.\n", flush=True)

    try:
        if platform.system() == "Windows":
            run_windows_capture(args.output, args.format, meta)
        else:
            run_unix_capture(args.output, args.format, meta)
    except Exception as e:
        print("Error during capture:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
