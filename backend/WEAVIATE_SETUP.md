# Instructions for Fixing Weaviate Connection

## Issue
The Weaviate cloud connection is failing with a DNS/network error. This prevents the vector database from storing and retrieving code embeddings.

## Possible Causes
1. **Incorrect Cluster URL**: The hardcoded URL `https://asia-southeast1-gcp-free.weaviate.cloud` might not be your actual cluster
2. **Network/Firewall**: Your network might be blocking access to Weaviate cloud
3. **Invalid API Key**: The WEAVIATE_API_KEY in .env might be incorrect

## How to Fix

### Option 1: Get Your Correct Weaviate Cluster URL
1. Log in to your Weaviate Cloud account at https://console.weaviate.cloud/
2. Find your cluster and copy the cluster URL
3. Update the URL in `backend/_gemini.py` line 16

### Option 2: Create a New Weaviate Cluster
1. Go to https://console.weaviate.cloud/
2. Create a new free cluster (if you don't have one)
3. Copy the cluster URL and API key
4. Update `backend/_gemini.py` line 16 with the cluster URL
5. Update `backend/.env` with the API key

### Option 3: Use Local Weaviate (Docker)
If you prefer to run Weaviate locally:
```bash
docker run -d \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
  weaviate/weaviate:latest
```

Then update `_gemini.py` to use:
```python
client = weaviate.connect_to_local()
```

## Current Status
The system will still work without Weaviate, but:
- ✅ Q&A feature works (provides general answers)
- ❌ Context-aware answers (needs Weaviate)
- ✅ Documentation generation works
- ❌ Code-specific Q&A (needs Weaviate)

## Next Steps
Please check your Weaviate console and provide the correct cluster URL.
  