import streamlit as st
import pandas as pd
from databricks.sdk import WorkspaceClient

# Import the required data model for the grants API
# The correct class is PermissionsChange from databricks.sdk.service.catalog
from databricks.sdk.service.catalog import PermissionsChange, Privilege


# NOTE: The UnityManagementWorkflow class and its import were kept to maintain the original
# code's structure, even though it's not explicitly used in the modified databased operations.
from workflows.unity_workflow import UnityManagementWorkflow 

st.set_page_config(page_title="Databricks Unity Catalog Access Manager", layout="wide")

st.title("🧠 Databricks Unity Catalog Access Manager")
st.markdown("---")

# Initialize Databricks Workspace Client and Workflow
try:
    # Ensure client is initialized (requires DATABRICKS_HOST and DATABRICKS_TOKEN in env or similar setup)
    client = WorkspaceClient()
    workflow = UnityManagementWorkflow()
except Exception as e:
    st.error(f"Could not initialize Databricks WorkspaceClient. Please ensure your environment is configured correctly. Error: {e}")
    st.stop()


# Helper Functions for Data Fetching and Caching
@st.cache_data(ttl=600)
def get_all_users_and_groups():
    """Fetches and processes all users and groups from Databricks for caching."""
    users = client.users.list()
    groups = client.groups.list()
    
    # Process users into a serializable list of dictionaries
    user_data = []
    for u in users:
        user_data.append({
            "User Name": u.user_name,
            "Display Name": u.display_name,
            "Active": u.active
        })

    # Process groups into a serializable list of dictionaries
    group_data = [{"Group Name": g.display_name, "ID": g.id} for g in groups]
    
    # Return serializable tuple of lists of dicts
    return user_data, group_data

@st.cache_data(ttl=600)
def get_all_catalogs():
    """Fetches and processes all catalogs from Databricks for caching."""
    catalogs = client.catalogs.list()
    
    catalog_data = []
    for c in catalogs:
        catalog_data.append({
            "Catalog Name": c.name,
            "Owner": c.owner,
            "Created At": c.created_at
        })
    return catalog_data

@st.cache_data(ttl=600)
def get_schemas_in_catalog(catalog_name):
    """Fetches and processes all schemas in a given catalog for caching."""
    if not catalog_name:
        return []
        
    schemas = client.schemas.list(catalog_name=catalog_name)
    schema_data = []
    for s in schemas:
        schema_data.append({
            "Schema Name": s.name,
            "Owner": s.owner,
            "Created At": s.created_at
        })
    return schema_data

@st.cache_data(ttl=600)
def get_tables_in_schema(catalog_name, schema_name):
    """Fetches and processes all tables in a given schema for caching."""
    if not catalog_name or not schema_name:
        return []
        
    tables = client.tables.list(catalog_name=catalog_name, schema_name=schema_name)
    table_data = []
    for t in tables:
        # Check if table_type exists, default to 'TABLE' if missing (for robustness)
        table_data.append({
            "Name": t.name,
            "Type": getattr(t, 'table_type', 'TABLE'), 
            "Owner": t.owner,
            "Created At": t.created_at
        })
    return table_data


# ========== Tabs ==========
tab_users_groups, tab_catalogs, tab_schemas, tab_tables, tab_permissions = st.tabs(
    ["👥 Users & Groups", "📚 Catalogs", "📝 Schemas", "🗃️ Tables", "🔐 Manage Permissions"]
)

with tab_users_groups:
    st.header("All Users and Groups")
    
    if st.button("Refresh User & Group Lists"):
        st.cache_data.clear() # Clear cache on refresh
        st.experimental_rerun()
    
    try:
        user_data, group_data = get_all_users_and_groups()

        # Display Users
        st.subheader("Users")
        st.dataframe(pd.DataFrame(user_data), use_container_width=True)

        # Display Groups
        st.subheader("Groups")
        st.dataframe(pd.DataFrame(group_data), use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching users and groups: {e}")

with tab_catalogs:
    st.header("Unity Catalog List")

    if st.button("Refresh Catalog List"):
        st.cache_data.clear() 
        st.experimental_rerun()
        
    try:
        catalog_data = get_all_catalogs()
        st.dataframe(pd.DataFrame(catalog_data), use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching catalogs: {e}")


with tab_schemas:
    st.header("Schemas by Catalog")
    
    try:
        all_catalog_data = get_all_catalogs()
        catalog_names = [c["Catalog Name"] for c in all_catalog_data]
        
        selected_catalog = st.selectbox(
            "Select Catalog to view Schemas:", 
            catalog_names,
            index=0 if catalog_names else None,
            key="schema_tab_catalog_select"
        )
        
        if selected_catalog:
            st.subheader(f"Schemas in Catalog: **{selected_catalog}**")
            schema_data = get_schemas_in_catalog(selected_catalog)
            st.dataframe(pd.DataFrame(schema_data), use_container_width=True)
        else:
            st.info("No catalogs found or selected.")

    except Exception as e:
        st.error(f"Error fetching schemas: {e}")


with tab_tables:
    st.header("Tables by Schema")

    try:
        all_catalog_data = get_all_catalogs()
        catalog_names = [c["Catalog Name"] for c in all_catalog_data]
        
        selected_catalog_t = st.selectbox(
            "Select Catalog to view Tables:", 
            catalog_names,
            index=0 if catalog_names else None,
            key="table_catalog_select"
        )
        
        selected_schema_t = None
        if selected_catalog_t:
            schema_data = get_schemas_in_catalog(selected_catalog_t)
            schema_names = [s["Schema Name"] for s in schema_data] or ["... No Schemas Available ..."]

            selected_schema_t = st.selectbox(
                f"Select Schema in {selected_catalog_t}:",
                schema_names,
                index=0,
                key="table_schema_select"
            )
            # Prevent API call if the placeholder is selected
            if selected_schema_t == "... No Schemas Available ...":
                 selected_schema_t = None
        
        if selected_schema_t:
            st.subheader(f"Tables in {selected_catalog_t}.**{selected_schema_t}**")
            table_data = get_tables_in_schema(selected_catalog_t, selected_schema_t)
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)
        else:
            st.info("Select a catalog and schema to view tables.")

    except Exception as e:
        st.error(f"Error fetching tables: {e}")


with tab_permissions:
    st.header("Assign Role and Permission")
    st.caption("Grants or revokes a privilege on a Unity Catalog securable object.")

    # --- Principal Selection (User/Group) ---
    principal = ""
    try:
        user_data, group_data = get_all_users_and_groups()
        user_names = [u["User Name"] for u in user_data]
        group_names = [g["Group Name"] for g in group_data]

        # Combine users and groups into a single list with separators
        principal_options = ["--- Select User or Group ---"]
        if user_names:
            principal_options.append("--- USERS ---")
            principal_options.extend(user_names)
        if group_names:
            principal_options.append("--- GROUPS ---")
            principal_options.extend(group_names)

        selected_principal = st.selectbox(
            "1. Select **Principal** (User or Group):",
            options=principal_options,
            key="perm_principal_select"
        )
        
        # Only set principal if a valid user or group is selected (not the placeholder or separator)
        if not selected_principal.startswith("--- "):
            principal = selected_principal
             
    except Exception as e:
        st.error(f"Error fetching principals for selection: {e}")
        # Fallback to text input if fetching fails
        principal = st.text_input("1. Enter **User or Group Name** (Principal) - Fallback due to error", key="principal_fallback")
    
    # --- End Principal Selection ---

    action = st.radio("2. Select Action:", ["GRANT", "REVOKE"], horizontal=True)

    object_type = st.selectbox(
        "3. Select Object Type:", 
        ["CATALOG", "SCHEMA", "TABLE", "VIEW", "FUNCTION", "STORAGE_CREDENTIAL"],
        key="perm_obj_type"
    )
    
    # --- Dynamic Object Name Input ---
    final_object_name = ""
    
    if object_type == "CATALOG":
        all_catalog_data = get_all_catalogs()
        catalog_names = [c["Catalog Name"] for c in all_catalog_data] or ["... No Catalogs Available ..."]
        
        selected_catalog_p = st.selectbox(
            "4. Select Catalog Name:", 
            catalog_names,
            key="perm_catalog_select"
        )
        if selected_catalog_p != "... No Catalogs Available ...":
            final_object_name = selected_catalog_p
        
    elif object_type in ["SCHEMA", "TABLE"]:
        all_catalog_data = get_all_catalogs()
        catalog_names = [c["Catalog Name"] for c in all_catalog_data] or ["... No Catalogs Available ..."]

        selected_catalog_p = st.selectbox(
            "4.1. Select Catalog:", 
            catalog_names,
            key="perm_catalog_select_2"
        )
        
        if selected_catalog_p != "... No Catalogs Available ...":
            schema_data = get_schemas_in_catalog(selected_catalog_p)
            schema_names = [s["Schema Name"] for s in schema_data] or ["... No Schemas Available ..."]

            selected_schema_p = st.selectbox(
                "4.2. Select Schema:",
                schema_names,
                key="perm_schema_select"
            )
            
            if selected_schema_p != "... No Schemas Available ...":
                if object_type == "SCHEMA":
                    final_object_name = f"{selected_catalog_p}.{selected_schema_p}"
                
                elif object_type == "TABLE":
                    table_data = get_tables_in_schema(selected_catalog_p, selected_schema_p)
                    table_names = [t["Name"] for t in table_data] or ["... No Tables Available ..."]
                    
                    selected_table_p = st.selectbox(
                        "4.3. Select Table:",
                        table_names,
                        key="perm_table_select_p"
                    )
                    
                    if selected_table_p != "... No Tables Available ...":
                        final_object_name = f"{selected_catalog_p}.{selected_schema_p}.{selected_table_p}"

    else:
        # Default text input for other securable types (VIEW, FUNCTION, etc.)
        st.info(f"Enter the full, qualified name for the {object_type}.")
        text_input = st.text_input("4. Enter **Full Object Name** (e.g., `schema.view`)", key="perm_text_input")
        final_object_name = text_input

    # Display the final name that will be used for the API call
    if final_object_name:
        st.markdown(f"**Object Name to be used for API:** `{final_object_name}`")
    
    # Common privileges for selection
    available_privileges = [
        "SELECT", "MODIFY", "USE_CATALOG", "USE_SCHEMA", 
        "CREATE_CATALOG", "CREATE_SCHEMA", "ALL_PRIVILEGES"
    ]
    privilege = st.selectbox("5. Select Privilege to apply:", available_privileges)

    # Button Logic Check: Ensure a principal is entered AND a valid object name is selected/entered
    object_is_selected = final_object_name and not final_object_name.startswith("...")
    
    if st.button(f"{action} Access", disabled=not (principal and object_is_selected)):
        if not (principal and object_is_selected and privilege):
            st.warning("Please fill in the Principal, Object Name, and Privilege.")
        else:
            try:
                # Convert privilege string to Privilege enum
                privilege_enum = Privilege[privilege]

                # Use PermissionsChange from databricks.sdk.service.catalog
                if action == "GRANT":
                    changes = [PermissionsChange(principal=principal, add=[privilege_enum])]
                    success_msg = f"✅ **Granted** {privilege} on {object_type} **{final_object_name}** to **{principal}**"
                else: # REVOKE
                    changes = [PermissionsChange(principal=principal, remove=[privilege_enum])]
                    success_msg = f"✅ **Revoked** {privilege} on {object_type} **{final_object_name}** from **{principal}**"

                # Perform the update operation
                # Use string for SCHEMA to avoid SDK enum bug
                securable_type_str = object_type if object_type != "SCHEMA" else "SCHEMA"

                client.grants.update(
                    securable_type=securable_type_str,
                    full_name=final_object_name,
                    changes=changes
                )
                st.success(success_msg)
            except KeyError:
                st.error(f"❌ Invalid privilege: {privilege}. Please select a valid privilege.")
            except Exception as e:
                st.error(f"❌ Operation Failed: {e}")