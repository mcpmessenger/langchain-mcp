# Examples and Tutorials

## Quick Examples

### Example 1: Build a RAG Agent in 10 Lines

Here's how to create a simple RAG (Retrieval-Augmented Generation) agent using the MCP server:

```python
# Simple RAG agent example
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

# 1. Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 2. Define a simple search tool (replace with your RAG retrieval)
def search_docs(query: str) -> str:
    # Your RAG retrieval logic here
    return f"Retrieved: {query}"

# 3. Create tool
tools = [Tool(name="search", func=search_docs, description="Search documents")]

# 4. Get prompt and create agent
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)

# 5. Create executor
rag_agent = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 6. Use it!
result = rag_agent.invoke({"input": "What is in the documents about AI?"})
print(result["output"])
```

**That's it!** 10 lines of core code to build a RAG agent.

### Example 2: Custom Tool Integration

Add your own tools to the agent:

```python
# In src/agent.py

def my_custom_tool(query: str) -> str:
    """Your custom tool description."""
    # Your implementation
    return result

def create_agent_tools() -> List[Tool]:
    tools = [
        Tool(
            name="my_custom_tool",
            func=my_custom_tool,
            description="Description for the LLM"
        ),
        # ... existing tools
    ]
    return tools
```

### Example 3: Using the MCP Server

Once deployed, use the server from any MCP client:

```python
import requests

# Service URL
service_url = "https://langchain-agent-mcp-server-554655392699.us-central1.run.app"

# Invoke the agent
response = requests.post(
    f"{service_url}/mcp/invoke",
    json={
        "tool": "agent_executor",
        "arguments": {
            "query": "What is the weather in New York?"
        }
    }
)

result = response.json()
print(result["content"][0]["text"])
```

### Example 4: SlashMCP Integration

Register and use in SlashMCP:

```
/slashmcp add langchain-agent https://langchain-agent-mcp-server-554655392699.us-central1.run.app

/srv_xxxxx agent_executor query="Your question here"
```

## Advanced Examples

### Building a Document Q&A Agent

```python
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

llm = ChatOpenAI(model="gpt-4o-mini")

def search_documents(query: str) -> str:
    """Search through your document database."""
    # Implement your vector search or database query
    # This is a placeholder
    return f"Found documents related to: {query}"

def extract_answer(context: str, question: str) -> str:
    """Extract answer from context."""
    # Use LLM to extract answer
    return f"Answer based on: {context}"

tools = [
    Tool(name="search_documents", func=search_documents, 
         description="Search document database"),
    Tool(name="extract_answer", func=extract_answer,
         description="Extract answer from context")
]

prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

result = executor.invoke({"input": "What did the report say about revenue?"})
```

### Multi-Step Reasoning Agent

```python
# Agent that performs multiple steps
def get_data(query: str) -> str:
    """Fetch data from API."""
    return "Data: 1000 units"

def analyze_data(data: str) -> str:
    """Analyze the data."""
    return f"Analysis: {data} shows growth"

def generate_report(analysis: str) -> str:
    """Generate final report."""
    return f"Report: {analysis}"

tools = [
    Tool(name="get_data", func=get_data, description="Fetch data"),
    Tool(name="analyze_data", func=analyze_data, description="Analyze data"),
    Tool(name="generate_report", func=generate_report, description="Generate report")
]

# Agent will chain these tools together automatically
```

## Integration Examples

### FastAPI Client

```python
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.post("/ask")
async def ask_question(question: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/invoke",
            json={
                "tool": "agent_executor",
                "arguments": {"query": question}
            }
        )
        return response.json()
```

### Python Script

```python
import requests

def ask_agent(question: str):
    url = "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/invoke"
    response = requests.post(
        url,
        json={
            "tool": "agent_executor",
            "arguments": {"query": question}
        }
    )
    return response.json()["content"][0]["text"]

# Use it
answer = ask_agent("What is machine learning?")
print(answer)
```

---

**Want more examples?** Check out the [API Reference](api-reference.md) for detailed endpoint documentation.

