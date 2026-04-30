# Lead Confidence Check

A Streamlit app with a HubSpot CRM connection.

## HubSpot setup

Create `.streamlit/secrets.toml` with your HubSpot private app access token:

```toml
[connections.hubspot]
access_token = "pat-na1-your-private-app-token"
```

You can also set `HUBSPOT_ACCESS_TOKEN` in your environment.

### How to run it on your own machine

1. Install the requirements

   ```powershell
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```powershell
   $ streamlit run streamlit_app.py
   ```
