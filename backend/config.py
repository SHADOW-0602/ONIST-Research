import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    OPENFIGI_API_KEY = os.getenv("OPENFIGI_API_KEY")
    
    # DB connection
    DATABASE_URL = os.getenv("DATABASE_URL")


    # Azure OpenAI
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")


config = Config()
