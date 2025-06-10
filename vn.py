import os
from dotenv import load_dotenv, find_dotenv
import warnings
from typing import Dict, Optional, Annotated

_ = load_dotenv(find_dotenv())
warnings.filterwarnings("ignore")

from vanna.openai.openai_chat import OpenAI_Chat
from openai import AzureOpenAI
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
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
            client = AzureOpenAI(
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                azure_deployment=os.environ["AZURE_OPENAI_GPT4O_DEPLOYMENT_NAME"],
                api_version=os.environ["AZURE_API_VERSION"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],                
            ),
            config = config
        )

print("Instantiating Vanna")
vn = MyVanna(config={"model": "gpt4-o"})

print("Connecting Vanna to SQL database")
vn.connect_to_sqlite("./database/stocks.db")
db_information_schema = vn.run_sql(
    "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"
)

plan = vn.get_training_plan_generic()