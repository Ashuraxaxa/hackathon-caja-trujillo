"""Descarga las fuentes públicas de la Fase 0 con reintentos y reanudación.

Uso:
    python fase0/download.py               # todas las fuentes auto + optional
    python fase0/download.py sunat_ruc     # solo una
    python fase0/download.py --force       # re-descarga aunque ya exista

Escribe data/raw/manifest.json con tamaño, sha256 y fecha de cada archivo.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from sources import SOURCES  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "manifest.json"
UA = {"User-Agent": "Mozilla/5.0 (hackathon-fase0 downloader)"}
CHUNK = 1 << 20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url: str, dest: Path, retries: int = 5) -> None:
    """Descarga en streaming a dest.part, reanudando con Range si se corta."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        have = part.stat().st_size if part.exists() else 0
        headers = dict(UA)
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            with requests.get(url, headers=headers, stream=True, timeout=(30, 120)) as r:
                if r.status_code == 416:  # ya completo
                    break
                r.raise_for_status()
                mode = "ab" if have and r.status_code == 206 else "wb"
                total = int(r.headers.get("content-length", 0)) + (have if mode == "ab" else 0)
                done = have if mode == "ab" else 0
                last = time.time()
                with part.open(mode) as f:
                    for chunk in r.iter_content(CHUNK):
                        f.write(chunk)
                        done += len(chunk)
                        if time.time() - last > 10 and total:
                            print(f"    {done / total:5.1%} de {total / 1e6:,.0f} MB", flush=True)
                            last = time.time()
            break
        except requests.RequestException as e:
            wait = 5 * attempt
            print(f"    intento {attempt}/{retries} falló: {e.__class__.__name__}: {e}. Reintento en {wait}s")
            if attempt == retries:
                raise
            time.sleep(wait)
    part.replace(dest)


def main(argv: list[str]) -> int:
    force = "--force" in argv
    wanted = [a for a in argv if not a.startswith("--")] or list(SOURCES)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    failures = []

    for key in wanted:
        src = SOURCES[key]
        dest = RAW / src["dest"]
        if src["mode"] == "manual":
            print(f"[manual]   {key}: {src['how']}")
            continue
        if dest.exists() and not force and dest.stat().st_size >= src["min_bytes"]:
            print(f"[ok]       {key}: ya existe ({dest.stat().st_size / 1e6:,.1f} MB)")
        else:
            print(f"[descarga] {key}: {src['url']}")
            try:
                fetch(src["url"], dest)
            except Exception as e:  # noqa: BLE001
                level = "AVISO" if src["mode"] == "optional" else "ERROR"
                print(f"[{level}]   {key}: no se pudo descargar ({e})")
                if src["mode"] != "optional":
                    failures.append(key)
                continue
        manifest[key] = {
            "file": str(dest.relative_to(ROOT)),
            "url": src["url"],
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
            "downloaded_at": dt.datetime.fromtimestamp(dest.stat().st_mtime).isoformat(timespec="seconds"),
        }

    RAW.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest: {MANIFEST.relative_to(ROOT)}")
    if failures:
        print(f"Fallaron fuentes obligatorias: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
