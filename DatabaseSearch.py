import os
import json
from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

class APIConnections:
    def __init__(self):
        self.hubspot_client_CURVE = self._init_hubspot(os.getenv("HUBSPOT_ACCESS_KEY_CURVE"))
        self.hubspot_client_FLEX = self._init_hubspot(os.getenv("HUBSPOT_ACCESS_KEY_FLEX"))
        self.hubspot_client_DHQ = self._init_hubspot(os.getenv("HUBSPOT_ACCESS_KEY_DHQ"))
        self.openai_client = self._init_openai(os.getenv("OPENAI_API_KEY"))

    def _init_hubspot(self, api_key):
        if not api_key:
            return None
        return HubSpot(access_token=api_key)

    def _init_openai(self, api_key):
        if not api_key:
            return None
        return OpenAI(api_key=api_key)

    def validate_connections(self):
        status = {
            "CURVE": self.hubspot_client_CURVE is not None,
            "FLEX": self.hubspot_client_FLEX is not None,
            "DHQ": self.hubspot_client_DHQ is not None,
            "OpenAI": self.openai_client is not None,
        }
        return status

    def interpret_search_term(self, search_term):
        if not self.openai_client:
            return None, "OpenAI client not initialized"

        prompt = f"""
        Convert the following plain text search term into a HubSpot CRM Search API filter object in JSON format.
        The search is for 'contacts'.
        
        Search Term: "{search_term}"
        
        Example Output format:
        {{
            "filterGroups": [
                {{
                    "filters": [
                        {{
                            "propertyName": "firstname",
                            "operator": "EQ",
                            "value": "John"
                        }}
                    ]
                }}
            ],
            "properties": ["firstname", "lastname", "email"],
            "limit": 1000
        }}
        
        Always include 'firstname', 'lastname', and 'email' in the "properties" array.
        The default "limit" should be 1000 unless a different amount is specifically requested.
        Provide ONLY the JSON object.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that converts plain text into HubSpot API search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            query_json = response.choices[0].message.content.strip()
            # Basic cleanup if OpenAI returns markdown
            if query_json.startswith("```json"):
                query_json = query_json[7:-3].strip()
            elif query_json.startswith("```"):
                query_json = query_json[3:-3].strip()
                
            return query_json, None
        except Exception as e:
            return None, str(e)

    def search_contacts(self, query_json):
        try:
            # HubSpot SDK usually expects snake_case for parameters in the constructor
            # But the Search API JSON often uses camelCase.
            # We can try to convert the keys or just pass the dict if the SDK handles it.
            # However, the error showed PublicObjectSearchRequest doesn't like 'filterGroups'.
            query_dict = json.loads(query_json)
            
            # Map camelCase to snake_case for PublicObjectSearchRequest
            mapping = {
                "filterGroups": "filter_groups",
                "sorts": "sorts",
                "query": "query",
                "properties": "properties",
                "limit": "limit",
                "after": "after"
            }
            
            mapped_query = {}
            for k, v in query_dict.items():
                if k in mapping:
                    mapped_query[mapping[k]] = v
                else:
                    mapped_query[k] = v
            
            # Set a default limit if not provided
            if "limit" not in mapped_query:
                mapped_query["limit"] = 100
                    
            search_request = PublicObjectSearchRequest(**mapped_query)
        except Exception as e:
            return None, f"Invalid query format: {str(e)}"

        results = {}
        clients = {
            "CURVE": self.hubspot_client_CURVE,
            "FLEX": self.hubspot_client_FLEX,
            "DHQ": self.hubspot_client_DHQ
        }

        for name, client in clients.items():
            if client:
                try:
                    search_results = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
                    results[name] = search_results.results
                except Exception as e:
                    results[name] = f"Error: {str(e)}"
            else:
                results[name] = "Not connected"

        return results, None
