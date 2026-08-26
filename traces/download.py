from langsmith import Client
from dotenv import load_dotenv
import os 

load_dotenv()  # Load environment variables from .env file
client = Client()

runs = client.list_runs(
    project_name=os.getenv("LANGSMITH_PROJECT", "Grid-Puzzles-2")
)

with open("output.txt", "w") as fo:
    for run in runs:
        print(run.id, run.name, run.inputs, run.outputs, file=fo)