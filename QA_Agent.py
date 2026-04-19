#pip install -U langchain-google-genai langchain-community faiss-cpu pypdf google-generativeai
import os
import time
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langchain_core.tools import Tool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic import hub
from langchain_core.prompts import ChatPromptTemplate

from agent_response_parser import clean_agent_output

import calculate
import Weather

# 1. Setup API Key and Model
#os.environ["GOOGLE_API_KEY"] = ""
os.environ["GOOGLE_API_KEY"] = "your Google API Key"
os.environ["llm_model"] = "models/gemini-2.5-flash"
os.environ["embedding_model"] = "models/gemini-embedding-001"
os.environ["prompt_template"] = "hwchase17/openai-functions-agent"
os.environ["pdf_file_path"] = "files/Java-for-Dummies.pdf"


genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

"""
 #available genai models
for model in genai.list_models():
    if 'embedContent' in model.supported_generation_methods:
        print(f" {model.name}") 

"""

# 1. configure ChatGoogleGenerativeAI llm & embeddings

#embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
embeddings = GoogleGenerativeAIEmbeddings(model=os.environ.get("embedding_model"))

# 2. Process Large PDF Data
# Using PyPDFLoader to read and RecursiveCharacterTextSplitter for chunking
#pdfLoader = PyPDFLoader("files/Java-for-Dummies.pdf")
pdfLoader = PyPDFLoader(os.environ.get("pdf_file_path"))
docs = pdfLoader.load()
print(f" No. of pages: {len(docs)}")

# Chunking is critical for large PDFs to fit in context windows
text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
splits = text_splitter.split_documents(docs)
print(f"Total chunks created: {len(splits)}")


"""
# 3. Create FAISS Vector Store from documents - pass document splits & embiddings
vector_store = FAISS.from_documents(documents=splits, embedding=embeddings)
data_retriever = vector_store.as_retriever()
"""

# 3. Process in small batches (e.g., 20 chunks at a time)
batch_size = 20 
vector_store = None

# Define your local index path
index_path = "faiss_pdf_index"

# if index is available locally, then load from local 
# otherwise create and store the vector store index locally
if os.path.exists(index_path):
    # 1. Load existing index from local disk
    print("Local index found. Loading...")
    vector_store = FAISS.load_local(
        index_path, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
else:
    for i in range(0, len(splits), batch_size):
        # for testing purpose store only 100 chunks, otherwise limit will exhaust
        # check for rate limit https://ai.dev/rate-limit
        if i < 100:
            batch = splits[i : i + batch_size]

            if vector_store is None:
                # Create the initial store
                vector_store = FAISS.from_documents(batch, embeddings)
            else:
                # Add to the existing store
                vector_store.add_documents(batch)
            
            print(f"Indexed chunks {i} to {i + len(batch)}...")

            ## CRITICAL: Wait to reset the 100 RPM quota
            # Gemini Free Tier is strict; a 15-20 second sleep is safer for large files
            time.sleep(20) 

    vector_store.save_local("faiss_pdf_index")
    print(f"Index saved successfully to {index_path}")


# use vector store for data retriever
data_retriever = vector_store.as_retriever()


# 4. Define the Agent's Tool and add to tools
# This allows the agent to search the PDF
java_pdf_reader = create_retriever_tool(
        retriever=data_retriever, 
        name="pdf_search", 
        description = "Search for information about the document contents. For any questions about the PDF, you must use this tool!"
    )

my_calc = calculate.Calc()

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers like 7 and 8"""
    return my_calc.add(a, b)

@tool
def sub_numbers(a: int, b: int) -> int:
    """substract two numbers like 7 and 8"""
    return my_calc.sub(a, b)

@tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers like 7 and 8"""
    return my_calc.multiply(a, b)

@tool
def div_numbers(a: int, b: int) -> int:
    """Division of two numbers like 7 and 8"""
    return my_calc.division(a, b)

#tools = [add_numbers, sub_numbers, multiply_numbers, div_numbers]

# fetch weather from weather API tool
weather_api = Weather.WeatherAPI()
@tool
def get_Current_Weather(location: str):
    """get current weather for a given location like Bengaluru."""
    print(f"Location entered : {str}")
    res = weather_api.get_Current_Weather(location)
    return res

@tool
def get_Weather_Forecast(location: str, days: int):
    """get weather forecast for a given location like Bengaluru for number of days 3"""
    print(f"Location and days entered : {str} - {days}")
    res = weather_api.get_Weather_Forecast(location, days)
    return res

tools = [get_Current_Weather, get_Weather_Forecast]

# 5. Initialize the Agent
# use a standard pre-defined prompt template for tool-calling agents
# pull the prompt from langchin hub
#prompt = hub.pull("hwchase17/openai-functions-agent")
prompt = hub.pull(os.environ.get("prompt_template"))
#force for always return human readable text as output not json or list or anything else.
"""prompt = ChatPromptTemplate.from_messages(
    [
        ("system", 
         "IMPORTANT: Always return final answers as plain human-readable text. "
         "Do NOT return JSON, lists, or dictionaries."),
    ] + base_prompt.messages
)"""

print(f"SPrompt from langchain - hwchase17/openai-functions-agent : \n ")
#print(f" - {prompt}")
"""
#create own prompt instead of from template
from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that can use tools when needed."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
"""

# configure llm model - models/gemini-2.0-flash
# temperature=0 -> predictable, Less creative, more factual
#llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0)
llm = ChatGoogleGenerativeAI(model=os.environ.get("llm_model"), temperature=0)
# define tool calling agent using llm, tools & prompt defined earlier
# tools → functions it can use (like search, calculator, API). In this case pdf file(first 100 pages)
agent = create_tool_calling_agent(llm, tools, prompt)
#AgentEexecutor -> Actual execution of agent. Verbose=True -> step-by-step logs
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# 6. Run the Agent with question
#response = agent_executor.invoke({"input": "Who is prime minister of india?"})
# parse the output as human readable test
#text_response = clean_agent_output(response["output"])
#print(text_response)

#create interactive chat until user enters exit or quit
print("Enter Exit or Quit to stop the interaction: ")
while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting... 👋")
        break

    try:
        response = agent_executor.invoke({"input": user_input})
        text_response = clean_agent_output(response["output"])
        print("\nBot:", text_response)
    except Exception as e:
        print(f"\n❌ Error: {e}")




