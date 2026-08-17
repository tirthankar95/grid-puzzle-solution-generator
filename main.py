import hydra
import pandas as pd
from my_soln import my_sol_main
from omegaconf import DictConfig
from llm_direct import llm_direct_main
from llm_verifier_py import llm_sol_main


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    if cfg.llm_verifier_py.enable:
        in_file = cfg.llm_verifier_py.input_file
        out_file = cfg.llm_verifier_py.output_file
        df = pd.read_csv(in_file)
        df_out = {'Key': [], 'Code': []}
        for indx, row in df.iterrows():
            print(f"Generating verifier for puzzle {indx + 1} using LLM...")
            result = llm_sol_main(row)
            if cfg.llm_verifier_py.save_results:
                df_out['Key'].append(row['Key'])
                df_out['Code'].append(result['verifier_code'])
        pd.DataFrame(df_out).to_csv(out_file, index=False)
    
    if cfg.run_llm_verifier.enable:
        in_file = cfg.run_llm_verifier.input_file
        out_file = cfg.run_llm_verifier.output_file
        df = pd.read_csv(in_file)
        df_out = {'Key': [], 'Solution': []}
        for indx, row in df.iterrows():
            print(f"Running LLM verifier for puzzle {indx + 1}...")
            result = my_sol_main(row)
            if cfg.run_llm_verifier.save_results:
                df_out['Key'].append(row['Key'])
                df_out['Solution'].append(result['solution'])
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


if __name__ == "__main__":
    main()