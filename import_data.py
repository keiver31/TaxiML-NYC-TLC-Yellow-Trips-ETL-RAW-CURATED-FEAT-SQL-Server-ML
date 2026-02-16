from pathlib import Path
import requests
from tqdm import tqdm

BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"
OUT_DIR = Path("data/raw/yellow")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def download_file(url: str, out_path: Path, chunk_size=1024 * 1024):
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"Ya existe: {out_path.name}")
        return

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(out_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=out_path.name) as pbar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

def yellow_url(year: int, month: int) -> str:
    return f"{BASE}/yellow_tripdata_{year}-{month:02d}.parquet"

# Ejemplo: descargar 3 meses (cámbialo como quieras)
for (y, m) in [(2025, 8), (2025, 9), (2025, 10)]:
    url = yellow_url(y, m)
    out = OUT_DIR / f"yellow_tripdata_{y}-{m:02d}.parquet"
    download_file(url, out)
