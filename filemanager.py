import pandas as pd
from omegaconf import DictConfig
from pathlib import Path


def _ensure_output_file(ofile: str, columns: list[str]) -> None:
    path = Path(ofile)
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=columns).to_csv(path, index=False)

def is_present(cfg: DictConfig, out_row: dict) -> bool:
    ofile = cfg.output_file
    if not Path(ofile).exists():
        return False
    df_out = pd.read_csv(ofile)
    if out_row['Key'] in df_out['Key'].values:
        print(f"Puzzle {out_row['Key']} already processed. Skipping...")
        return True
    return False

def write_to_csv(cfg: DictConfig, out_row: dict):
    if cfg.save_results:
        ofile = cfg.output_file
        _ensure_output_file(ofile, list(out_row.keys()))
        df_out = pd.read_csv(ofile)
        df_out = pd.concat([df_out, pd.DataFrame([out_row])], ignore_index=True)
        df_out.to_csv(ofile, index=False)