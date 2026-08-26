import hydra
import omegaconf
import pandas as pd
import filemanager as fm
from omegaconf import DictConfig, OmegaConf
from dotenv import load_dotenv
from llm_direct import llm_direct_main
from utils.py_soln import my_sol_main as py_sol
from utils.asp_soln import my_sol_main as asp_sol
from llm_verifier_py import llm_sol_main as py_main
from llm_verifier_asp import llm_sol_main as asp_main


# Load environment variables from .env file for langsmith
load_dotenv()  
verifier_runners = {
    "py": py_sol,
    "asp": asp_sol,
}


def check_cfg(cfg: DictConfig):
    enable_cnt = 0
    for key in cfg:
        if isinstance(cfg[key], omegaconf.dictconfig.DictConfig) and "enable" in cfg[key]:
            if key == 'run_llm_verifier' and cfg[key]["enable"]:
                if cfg["output_file"] == cfg[key]["intermediate_file"]:
                    raise ValueError("The 'output_file' and 'intermediate_file' cannot be the same when 'run_llm_verifier' is enabled.")
            if cfg[key]["enable"]:
                enable_cnt += 1
    if enable_cnt > 1:
        raise ValueError("Only one 'enable' can be set to true in the configuration.")


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    check_cfg(cfg)
    in_file = cfg.input_file
    if cfg.llm_verifier_py.enable:
        df = pd.read_csv(in_file)
        for indx, row in df.iterrows():
            out_row = {'Key': row['Key'], 'Code': ''}
            if fm.is_present(cfg, out_row):
                continue
            print(f"Generating py-verifier for puzzle {indx + 1} using LLM...")
            result = py_main(row)
            out_row['Code'] = result.get('verifier_code', '')
            fm.write_to_csv(cfg, out_row)
    
    if cfg.llm_verifier_asp.enable:
        df = pd.read_csv(in_file)
        for indx, row in df.iterrows():
            out_row = {'Key': row['Key'], 'Code': ''}
            if fm.is_present(cfg, out_row):
                continue
            print(f"Generating asp-verifier for puzzle {indx + 1} using LLM...")
            result = asp_main(row)
            out_row['Code'] = result.get('verifier_code', '')
            fm.write_to_csv(cfg, out_row)
    
    if cfg.llm_direct.enable:
        df = pd.read_csv(in_file)
        for indx, row in df.iterrows():
            out_row = {'Key': row['Key'], 'Solution': ''}
            if fm.is_present(cfg, out_row):
                continue
            print(f"Running LLM direct for puzzle {indx + 1}...")
            result = llm_direct_main(row)
            out_row['Solution'] = result.get('solution', '')
            fm.write_to_csv(cfg, out_row)
    
    if cfg.run_llm_verifier.enable:
        df = pd.read_csv(cfg.run_llm_verifier.intermediate_file)
        df_main = pd.read_csv(in_file)
        merged_df = df.merge(df_main, on="Key", how="inner")
        my_sol_main = verifier_runners.get(cfg.run_llm_verifier.type)
        if my_sol_main is None:
            valid_types = ", ".join(sorted(verifier_runners))
            raise ValueError(
                f"Unsupported run_llm_verifier.type '{cfg.run_llm_verifier.type}'. "
                f"Expected one of: {valid_types}."
            )
        for indx, row in merged_df.iterrows():
            out_row = {'Key': row['Key'], 'Code': row['Code'], 'Solution': ''}
            if fm.is_present(cfg, out_row):
                continue
            print(f"Running LLM {cfg.run_llm_verifier.type}-verifier for puzzle {indx + 1}...")
            result = my_sol_main(row)
            out_row['Solution'] = result.get('solution', '')
            fm.write_to_csv(cfg, out_row)


if __name__ == "__main__":
    main()