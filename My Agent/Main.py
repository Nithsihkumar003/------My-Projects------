from langchain_ollama import ChatOllama

# Initialize local LLM
llm = ChatOllama(model="qwen2.5:7b", temperature=0)

# Test it
response = llm.invoke("Say hello and confirm you're running locally")
print(response.content)
