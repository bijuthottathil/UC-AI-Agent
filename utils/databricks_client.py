from databricks.sdk import WorkspaceClient

def get_workspace_client():
    """Return a Databricks WorkspaceClient using environment credentials."""
    return WorkspaceClient()