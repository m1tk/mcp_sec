from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

# Uncomment to enable Prompt shield
#from llm_prompt_shield.integrations.langchain import PromptGuardCallbackHandler
#callback = PromptGuardCallbackHandler(block_on_detection=True)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    #callbacks=[callback]
)