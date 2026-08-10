import hydra
import pandas as pd
from my_soln import my_sol_main
from llm_soln import llm_sol_main
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    filename = cfg.input_file
    if filename.endswith('.csv'):
        df = pd.read_csv(filename)
        for indx, row in df.iterrows():
            if cfg['solution']['brute_force']['enable']:
                print(f"Solving puzzle {indx + 1} using brute force...")
                result = my_sol_main(row)
                if cfg['solution']['brute_force']['save_results']:
                    df.at[indx, 'Solution'] = result['solution']
                return
            elif cfg['solution']['llm_force']['enable']:
                print(f"Solving puzzle {indx + 1} using LLM...")
                result = llm_sol_main(row)
                if cfg['solution']['llm_force']['save_results']:
                    if cfg['solution']['llm_force']['verification']:
                        df.at[indx, 'Verifier'] = result['verifier_code']
                    # df.at[indx, 'Solution'] = result['solution']
                return
            else:
                print("No solution method specified in the configuration.")
                return
        df.to_csv(filename, index=False)
    else:
        print("Unsupported file format. Please provide a CSV file.")
        return


if __name__ == "__main__":
    main()