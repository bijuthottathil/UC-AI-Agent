from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from databricks.sdk import WorkspaceClient
from typing import List

class UnityCatalogAgents:
    def __init__(self, workspace_client: WorkspaceClient, llm: ChatOpenAI):
        self.workspace_client = workspace_client
        self.llm = llm

    def list_catalogs_agent(self):
        return Agent(
            role="CatalogLister",
            goal="List all catalogs and schemas in Unity Catalog",
            backstory="Expert at Databricks Unity Catalog data organization",
            llm=self.llm,
            tools=[self._list_catalogs_and_schemas]
        )

    def list_users_groups_agent(self):
        return Agent(
            role="UserGroupLister",
            goal="List all workspace users and groups",
            backstory="Knows how to read users and groups from Databricks Workspace",
            llm=self.llm,
            tools=[self._list_users_groups]
        )

    def grant_access_agent(self):
        return Agent(
            role="AccessManager",
            goal="Grant catalog/schema/table access to new users",
            backstory="Expert at managing Unity Catalog permissions",
            llm=self.llm,
            tools=[self._grant_access]
        )

    # ====== Tool Functions =======
    def _list_catalogs_and_schemas(self):
        catalogs = [c.name for c in self.workspace_client.catalogs.list()]
        result = {}
        for c in catalogs:
            schemas = [s.name for s in self.workspace_client.schemas.list(catalog_name=c)]
            result[c] = schemas
        return result

    def _list_users_groups(self):
        users = [u.user_name for u in self.workspace_client.users.list()]
        groups = [g.display_name for g in self.workspace_client.groups.list()]
        return {"users": users, "groups": groups}

    def _grant_access(self, principal: str, object_type: str, object_name: str, privilege: str):
        """Grant privilege to principal (user/group) on Unity Catalog objects."""
        try:
            self.workspace_client.grants.update(
                object_type=object_type,
                object_name=object_name,
                changes=[
                    {
                        "principal": principal,
                        "add": [privilege]
                    }
                ]
            )
            return f"Granted {privilege} on {object_type} {object_name} to {principal}"
        except Exception as e:
            return f"Failed to grant access: {e}"