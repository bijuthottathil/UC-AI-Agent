# workflows/unity_workflow.py

from typing import Tuple
from typing_extensions import TypedDict

from langgraph.graph.state import StateGraph
from agents.unity_agents import UnityCatalogAgents
from langchain_openai import ChatOpenAI
from databricks.sdk import WorkspaceClient

# ── Define state schema using TypedDict ──
class UnityAccessState(TypedDict, total=False):
    catalog_list: Tuple[Tuple[str, Tuple[str, ...]], ...]
    user_list: Tuple[Tuple[str, ...], Tuple[str, ...]]
    grant_status: Tuple[str, ...]

def UnityManagementWorkflow():
    # Initialize clients
    client = WorkspaceClient()
    llm = ChatOpenAI(model="gpt-4.1-nano")
    agents = UnityCatalogAgents(client, llm)

    # Instantiate StateGraph with the state schema type
    graph = StateGraph(UnityAccessState)

    # Node wrappers
    def list_catalogs_node(state: UnityAccessState) -> dict:
        result = agents.list_catalogs_agent().run()
        # Convert dict of catalogs → schemas into hashable tuple
        catalogs_tuple = tuple((catalog, tuple(schemas)) for catalog, schemas in result.items())
        return {"catalog_list": catalogs_tuple}

    def list_users_node(state: UnityAccessState) -> dict:
        result = agents.list_users_groups_agent().run()
        users = tuple(result.get("users", []))
        groups = tuple(result.get("groups", []))
        return {"user_list": (users, groups)}

    def grant_access_node(state: UnityAccessState) -> dict:
        result = agents.grant_access_agent().run()
        if isinstance(result, dict):
            status = tuple(f"{k}:{v}" for k, v in result.items())
        else:
            status = (str(result),)
        return {"grant_status": status}

    # Add nodes by name
    graph.add_node("List Catalogs", list_catalogs_node)
    graph.add_node("List Users", list_users_node)
    graph.add_node("Grant Access", grant_access_node)

    # Define control flow edges
    from langgraph.graph.state import START, END
    graph.add_edge(START, "List Catalogs")
    graph.add_edge("List Catalogs", "List Users")
    graph.add_edge("List Users", "Grant Access")
    graph.add_edge("Grant Access", END)

    # Compile graph so it’s executable
    compiled_graph = graph.compile()
    return compiled_graph