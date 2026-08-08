import hydra
import pandas as pd
from pprint import pprint
from utils import parse_puzzle
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    filename = cfg.input_file
    if filename.endswith('.csv'):
        df = pd.read_csv(filename)
        for indx, row in df.iterrows():
            result = parse_puzzle(row['Puzzle'])
            # pprint(result)
    else:
        print("Unsupported file format. Please provide a CSV file.")
        return


if __name__ == "__main__":
    main()