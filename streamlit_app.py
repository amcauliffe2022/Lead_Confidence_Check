import streamlit as st
import pandas as pd
from DatabaseSearch import APIConnections

st.set_page_config(page_title="Lead Confidence Check", layout="wide")

# Initialize API connections
@st.cache_resource
def get_api_connections():
    return APIConnections()

api_conn = get_api_connections()
connection_status = api_conn.validate_connections()

st.title("Hubspot Database Search")
st.caption("HubSpot CRM")

# Sidebar for connection status
with st.sidebar:
    st.header("API Connection Status")
    for api, connected in connection_status.items():
        if connected:
            st.success(f"{api}: Connected")
        else:
            st.error(f"{api}: Not Connected")

search_term = st.text_input("Search Contacts", placeholder="e.g., find John from Google")
if st.button("Search", use_container_width=True):
    if search_term:
        st.write("Processing...")
        query, error = api_conn.interpret_search_term(search_term)
        
        if error:
            st.error(f"Error interpreting search term: {error}")
        else:
            with st.expander("Show/Hide HubSpot Search Query"):
                st.code(query, language="json")
            
            st.write("Searching HubSpot databases...")
            results, search_error = api_conn.search_contacts(query)
            
            if search_error:
                st.error(f"Search error: {search_error}")
            else:
                tabs = st.tabs(list(results.keys()))
                for i, (hubspot_name, contacts) in enumerate(results.items()):
                    with tabs[i]:
                        if isinstance(contacts, str):
                            st.error(contacts)
                        elif not contacts:
                            st.info(f"No contacts found in {hubspot_name}.")
                        else:
                            st.success(f"Found {len(contacts)} contact(s) in {hubspot_name}.")
                            
                            # Flatten contact data for DataFrame
                            data = []
                            for contact in contacts:
                                contact_dict = contact.to_dict()
                                # Extract properties and other useful info
                                flat_contact = {
                                    "ID": contact_dict.get("id"),
                                    "Created At": contact_dict.get("created_at"),
                                    "Updated At": contact_dict.get("updated_at"),
                                }
                                # Add all properties
                                properties = contact_dict.get("properties", {})
                                flat_contact.update(properties)
                                data.append(flat_contact)
                            
                            df = pd.DataFrame(data)
                            
                            # Reorder columns to put ID, First Name, Last Name, Email first if they exist
                            cols = df.columns.tolist()
                            priority_cols = ["ID", "firstname", "lastname", "email"]
                            existing_priority = [c for c in priority_cols if c in cols]
                            other_cols = [c for c in cols if c not in priority_cols]
                            df = df[existing_priority + other_cols]
                            
                            st.dataframe(df, use_container_width=True)
                            
                            # Option to see raw JSON
                            with st.expander("View Raw JSON"):
                                for contact in contacts:
                                    st.json(contact.to_dict())
    else:
        st.warning("Please enter a search term first.")

