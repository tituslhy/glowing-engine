import os
from dotenv import load_dotenv, find_dotenv
import warnings
from typing import Dict, Optional, Annotated, Tuple, List
import yaml

from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from openai import OpenAI
from tqdm import tqdm

_ = load_dotenv(find_dotenv())
warnings.filterwarnings("ignore")

__curdir__ = os.getcwd()
if "notebooks" in __curdir__:
    chroma_path = "../chroma"
    yaml_file_path = "../config/training.yaml"
else:
    chroma_path = "./chroma"
    yaml_file_path = "./config/training.yaml"

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    """Our main Vanna handler. Inherits from Vanna's ChromaDB_VectorStore
    and OpenAI_Chat which implement many of the abstract methods in Vanna's
    Base class. The only thing we need to do is define the constructor where
    we initialize the different objects."""
    
    def __init__(
        self, 
        config: Optional[Annotated[
            Dict[str, str], 
            """The configuration for the vector store or the LLM you want to use. 
            For e.g. {'model':'gpt-4o'}"""
        ]]
    ) -> None:
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(
            self,
            client = OpenAI(),
            config = config
        )

def load_query_data(yaml_file_path: str) -> List[Tuple[str, str]]:
    """Returns a list of training queries for LLM training.
    
    This is a mission critical function.
    """
    try:
        with open(yaml_file_path, 'r') as file:
            try:
                documents = yaml.safe_load(file)
                if not isinstance(documents, list):
                    raise ValueError("YAML content is not a list of documents.")
            except yaml.YAMLError as yaml_error:
                raise ValueError(f"Error parsing YAML file: {yaml_error}") from yaml_error
    except FileNotFoundError as fnf_error:
        raise FileNotFoundError(f"Error: The file at {yaml_file_path} was not found.") from fnf_error
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e

    return [(doc.get('question'), doc.get('answer')) for doc in documents]
    
print("Instantiating Vanna...")
vn = MyVanna(config={
    "model": "gpt-4o",
    "path": chroma_path, #this is the specific key that Vanna looks for (reference: Vanna's ChromaDB_VectorStore source code)
})

print("Connecting Vanna to SQL database...")
vn.connect_to_sqlite("./database/stocks.db")

print("Training Vanna...")
df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
for ddl in df_ddl['sql'].to_list():
    vn.train(ddl=ddl)
vn.train(documentation="Illumina is defined as ilmn")
vn.train(documentation="Apple is defined as aapl")
vn.train(documentation="NVIDIA is defined as nvda")

queries = load_query_data(yaml_file_path=yaml_file_path)
for question, sql in tqdm(queries):
    vn.train(question=question, sql=sql)

if __name__ == "__main__":
    from vanna.flask import VannaFlaskApp
    
    app = VannaFlaskApp(vn)
    app.run()
