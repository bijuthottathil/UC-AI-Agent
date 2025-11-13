# Unity Catalog Permission Manager

An AI-powered agent system for managing Unity Catalog permissions, catalogs, and schemas using CrewAI, LangGraph, and Streamlit.

## Features

- **Intelligent Agent System**: Powered by CrewAI with specialized agents for different tasks:
  - Catalog Manager: Creates and manages catalogs and schemas
  - Permission Manager: Handles permission grants and revocations
  - Policy Advisor: Provides recommendations for data governance
  - Auditor: Reviews and audits existing permissions

- **LangGraph Workflow**: Automatic request classification and routing to appropriate agents
- **Interactive UI**: Streamlit-based web interface for easy interaction
- **Unity Catalog Integration**: Full integration with Databricks Unity Catalog via SDK

## Architecture

```
Streamlit UI
     |
     v
LangGraph Workflow
     |
     v
CrewAI Agents
     |
     v
Unity Catalog Tools
     |
     v
Databricks Unity Catalog
```

## Project Structure

```
mlagent/
├── src/
│   ├── agents/          # CrewAI agent definitions
│   │   └── uc_agents.py
│   ├── tools/           # Unity Catalog tools
│   │   └── unity_catalog_tools.py
│   ├── workflows/       # LangGraph workflows
│   │   └── uc_workflow.py
│   ├── ui/              # Streamlit UI
│   │   └── app.py
│   └── config/          # Configuration
│       └── settings.py
├── .env.example         # Example environment variables
├── pyproject.toml       # Project dependencies
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Databricks workspace with Unity Catalog enabled
- OpenAI API key
- Databricks personal access token

### Setup

1. **Clone the repository:**
   ```bash
   cd /path/to/mlagent
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=your_databricks_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Running the Streamlit UI

Launch the Streamlit application:

```bash
streamlit run src/ui/app.py
```

Then:
1. Configure your Databricks and OpenAI credentials in the sidebar
2. Click "Connect" to initialize the agents
3. Enter your requests in the chat interface

### Example Requests

**Catalog Management:**
- "Create a catalog named 'analytics_prod'"
- "Create a schema 'sales' in catalog 'analytics_prod'"
- "List all catalogs"
- "List all schemas in catalog 'analytics_prod'"

**Permission Management:**
- "Grant SELECT permission on catalog 'analytics_prod' to group 'data_analysts'"
- "Grant USE_CATALOG and USE_SCHEMA on catalog 'marketing' to user 'john@example.com'"
- "Revoke SELECT on schema 'analytics_prod.sales' from group 'contractors'"
- "List all permissions on catalog 'analytics_prod'"

**Policy Advisory:**
- "What are the best practices for organizing catalogs?"
- "How should I structure permissions for a multi-team data platform?"
- "Recommend a permission structure for my analytics catalog"

**Auditing:**
- "Audit permissions on catalog 'analytics_prod'"
- "Review access patterns for schema 'analytics_prod.sales'"
- "Check for over-privileged access in my catalogs"

### Programmatic Usage

You can also use the system programmatically:

```python
from databricks.sdk import WorkspaceClient
from langchain_openai import ChatOpenAI
from src.workflows.uc_workflow import UnityCatalogWorkflow

# Initialize clients
workspace_client = WorkspaceClient(
    host="https://your-workspace.cloud.databricks.com",
    token="your_token"
)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Create workflow
workflow = UnityCatalogWorkflow(workspace_client, llm)

# Execute a request
result = workflow.execute("Create a catalog named 'test_catalog'")
print(result['result'])
```

## Available Tools

### Catalog Tools
- `list_catalogs`: List all catalogs
- `create_catalog`: Create a new catalog
- `list_schemas`: List schemas in a catalog
- `create_schema`: Create a new schema

### Permission Tools
- `grant_permission`: Grant permissions on catalogs/schemas
- `revoke_permission`: Revoke permissions
- `list_permissions`: List all permissions on a resource

## Agent Types

### Catalog Manager Agent
Specializes in creating and organizing Unity Catalog resources. Handles catalog and schema creation, listing, and management.

### Permission Manager Agent
Focuses on access control. Grants and revokes permissions, manages user and group access to data resources.

### Policy Advisor Agent
Provides recommendations and best practices for data governance. Analyzes requirements and suggests appropriate permission structures.

### Auditor Agent
Reviews and audits existing permissions. Identifies security issues, generates compliance reports, and recommends remediation.

## Configuration

### Databricks Authentication

The system supports multiple authentication methods:
- **Personal Access Token** (recommended for development)
- **OAuth** (for production use)

### OpenAI Models

Supported models:
- `gpt-4o` (recommended, best performance)
- `gpt-4-turbo` (balanced)
- `gpt-3.5-turbo` (faster, lower cost)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black src/
ruff check src/
```

## Troubleshooting

### Connection Issues

If you encounter connection issues:
1. Verify your Databricks workspace URL is correct
2. Ensure your access token has the necessary permissions
3. Check that Unity Catalog is enabled in your workspace

### Permission Errors

If you get permission errors:
1. Ensure your Databricks user has admin privileges or appropriate permissions
2. Check that the resources you're trying to modify exist
3. Verify the principal (user/group) names are correct

### API Rate Limits

If you hit OpenAI rate limits:
1. Reduce the temperature setting
2. Use a lower-tier model (gpt-3.5-turbo)
3. Add delays between requests

## Security Best Practices

1. **Never commit `.env` files** - Keep credentials secure
2. **Use least privilege** - Grant only necessary permissions
3. **Regular audits** - Use the auditor agent to review permissions regularly
4. **Group-based access** - Prefer group grants over individual user grants
5. **Documentation** - Document permission policies in catalog/schema comments

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Check the Databricks Unity Catalog documentation
- Review CrewAI and LangGraph documentation

## Acknowledgments

- Built with CrewAI (https://www.crewai.com/)
- Powered by LangGraph (https://github.com/langchain-ai/langgraph)
- UI created with Streamlit (https://streamlit.io/)
- Databricks integration via Databricks SDK (https://github.com/databricks/databricks-sdk-py)
