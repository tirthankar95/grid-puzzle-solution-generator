import hydra
import pandas as pd
from utils.py_soln import my_sol_main as py_sol
from utils.asp_soln import my_sol_main as asp_sol
from omegaconf import DictConfig
from llm_direct import llm_direct_main
from llm_verifier_py import llm_sol_main as py_main
from llm_verifier_asp import llm_sol_main as asp_main

verifier_runners = {
    "py": py_sol,
    "asp": asp_sol,
}

@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    if cfg.llm_verifier_py.enable:
        in_file = cfg.llm_verifier_py.input_file
        out_file = cfg.llm_verifier_py.output_file
        df = pd.read_csv(in_file)
        df_out = {'Key': [], 'Code': []}
        for indx, row in df.iterrows():
            print(f"Generating py-verifier for puzzle {indx + 1} using LLM...")
            result = py_main(row)
            if cfg.llm_verifier_py.save_results:
                df_out['Key'].append(row['Key'])
                df_out['Code'].append(result['verifier_code'])
        pd.DataFrame(df_out).to_csv(out_file, index=False)
    
    if cfg.llm_verifier_asp.enable:
        in_file = cfg.llm_verifier_asp.input_file
        out_file = cfg.llm_verifier_asp.output_file
        df = pd.read_csv(in_file)
        df_out = {'Key': [], 'Code': []}
        for indx, row in df.iterrows():
            print(f"Generating asp-verifier for puzzle {indx + 1} using LLM...")
            result = asp_main(row)
            if cfg.llm_verifier_asp.save_results:
                df_out['Key'].append(row['Key'])
                df_out['Code'].append(result['verifier_code'])
        pd.DataFrame(df_out).to_csv(out_file, index=False)
    
    if cfg.llm_direct.enable:
        in_file = cfg.llm_direct.input_file
        out_file = cfg.llm_direct.output_file
        df = pd.read_csv(in_file)
        df_out = {'Key': [], 'Solution': []}
        for indx, row in df.iterrows():
            print(f"Running LLM direct for puzzle {indx + 1}...")
            result = llm_direct_main(row)
            if cfg.llm_direct.save_results:
                df_out['Key'].append(row['Key'])
                df_out['Solution'].append(result['solution'])
        pd.DataFrame(df_out).to_csv(out_file, index=False)
    
    if cfg.run_llm_verifier.enable:
        in_file = cfg.run_llm_verifier.input_file
        out_file = cfg.run_llm_verifier.output_file
        main_file = cfg.run_llm_verifier.main_file
        df = pd.read_csv(in_file)
        df_main = pd.read_csv(main_file)
        merged_df = df.merge(df_main, on="Key", how="inner")
        solutions_by_key = {}
        my_sol_main = verifier_runners.get(cfg.run_llm_verifier.type)
        if my_sol_main is None:
            valid_types = ", ".join(sorted(verifier_runners))
            raise ValueError(
                f"Unsupported run_llm_verifier.type '{cfg.run_llm_verifier.type}'. "
                f"Expected one of: {valid_types}."
            )
        for indx, row in merged_df.iterrows():
            print(f"Running LLM {cfg.run_llm_verifier.type}-verifier for puzzle {indx + 1}...")
            result = my_sol_main(row)
            solutions_by_key[row["Key"]] = result.get("solution")

        if cfg.run_llm_verifier.save_results:
            df_out = df.copy()
            df_out["Solution"] = df_out["Key"].map(solutions_by_key)
            df_out.to_csv(out_file, index=False)


if __name__ == "__main__":
    main()