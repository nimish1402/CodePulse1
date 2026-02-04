from dotenv import load_dotenv
import os
import google.generativeai as genai
import asyncio
from typing import List

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Groq client
try:
    from groq import Groq
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    groq_available = True
    print("Groq client initialized successfully")
except Exception as e:
    print(f"Warning: Groq not available: {e}")
    groq_available = False
    groq_client = None

# Initialize Weaviate client
try:
    import weaviate
    from weaviate.classes.config import Configure, Property, DataType
    
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url="https://opbbo1qysuwd9s67rowxg.c0.asia-southeast1.gcp.weaviate.cloud",
        auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
    )
    weaviate_available = True
    print("Weaviate client initialized successfully")
except Exception as e:
    print(f"Warning: Weaviate not available: {e}")
    weaviate_available = False
    client = None


def ensure_collection_exists(namespace: str):
    """
    Ensure the Weaviate collection exists for the given namespace (repository)
    """
    if not weaviate_available or client is None:
        print("Weaviate not available, skipping collection creation")
        return False
    
    try:
        # Sanitize namespace to create valid Weaviate collection name
        # Remove all special characters: :, ., -, /
        sanitized = namespace.replace(':', '_').replace('.', '_').replace('-', '_').replace('/', '_')
        collection_name = f"CodeDoc_{sanitized}"
        
        # Check if collection exists
        if client.collections.exists(collection_name):
            print(f"Collection {collection_name} already exists")
            return True
        
        # Create collection with proper schema
        client.collections.create(
            name=collection_name,
            properties=[
                Property(name="source", data_type=DataType.TEXT),
                Property(name="content", data_type=DataType.TEXT),
                Property(name="summary", data_type=DataType.TEXT),
            ],
            # Configure vectorizer to use custom embeddings
            vectorizer_config=Configure.Vectorizer.none(),
        )
        print(f"Created collection: {collection_name}")
        return True
    except Exception as e:
        print(f"Error creating collection: {e}")
        return False


async def store_embeddings(documents: list, namespace: str):
    """
    Store document embeddings in Weaviate
    documents: list of documents with metadata including 'source', 'content', 'summary', and 'embedding'
    namespace: repository identifier
    """
    if not weaviate_available or client is None:
        print("Weaviate not available, skipping embedding storage")
        return False
    
    try:
        # Sanitize namespace to create valid Weaviate collection name
        sanitized = namespace.replace(':', '_').replace('.', '_').replace('-', '_').replace('/', '_')
        collection_name = f"CodeDoc_{sanitized}"
        collection = client.collections.get(collection_name)
        
        # Delete existing documents for this namespace (fresh start)
        try:
            collection.data.delete_many(where=None)
            print(f"Cleared existing documents from {collection_name}")
        except Exception as e:
            print(f"Note: Could not clear collection (might be empty): {e}")
        
        # Batch insert documents
        with collection.batch.dynamic() as batch:
            for doc in documents:
                batch.add_object(
                    properties={
                        "source": doc.get("source", ""),
                        "content": doc.get("content", "")[:10000],  # Limit content size
                        "summary": doc.get("summary", ""),
                    },
                    vector=doc.get("embedding", [])
                )
        
        print(f"Stored {len(documents)} documents in Weaviate")
        return True
    except Exception as e:
        print(f"Error storing embeddings: {e}")
        return False


async def retrieve_relevant_docs(query: str, namespace: str, limit: int = 5):
    """
    Retrieve relevant documents from Weaviate using vector similarity search
    """
    if not weaviate_available or client is None:
        print("Weaviate not available, cannot retrieve documents")
        return []
    
    try:
        # Sanitize namespace to create valid Weaviate collection name
        sanitized = namespace.replace(':', '_').replace('.', '_').replace('-', '_').replace('/', '_')
        collection_name = f"CodeDoc_{sanitized}"
        
        # Check if collection exists
        if not client.collections.exists(collection_name):
            print(f"Collection {collection_name} does not exist")
            return []
        
        # Get query embedding - this may raise QUOTA_EXCEEDED
        query_embedding = await getEmbeddings(query)
        
        # Search for similar documents
        collection = client.collections.get(collection_name)
        results = collection.query.near_vector(
            near_vector=query_embedding,
            limit=limit,
            return_properties=["source", "content", "summary"]
        )
        
        # Extract documents
        docs = []
        for item in results.objects:
            docs.append({
                "source": item.properties.get("source", ""),
                "content": item.properties.get("content", ""),
                "summary": item.properties.get("summary", ""),
            })
        
        print(f"Retrieved {len(docs)} relevant documents")
        return docs
    except Exception as e:
        if "QUOTA_EXCEEDED" in str(e):
            # Re-raise quota errors so ask() can handle them
            raise
        print(f"Error retrieving documents: {e}")
        return []


async def getEmbeddings(text: str) -> List[float]:
    """
    Get embeddings for the given text using Gemini's embedding model
    """
    try:
        # Use Gemini's most basic embedding model (text-embedding-004)
        # Clean the text
        cleaned_text = text.replace("\n", " ").strip()
        
        # Generate embeddings using the basic model
        result = await asyncio.to_thread(
            genai.embed_content,
            model="models/text-embedding-004",
            content=cleaned_text,
            task_type="retrieval_document"
        )
        
        return result['embedding']
    except Exception as e:
        error_str = str(e)
        if "quota" in error_str.lower() or "429" in error_str:
            print(f"⚠️ Gemini API quota exceeded: {e}")
            # Raise a specific exception for quota errors
            raise Exception("QUOTA_EXCEEDED") from e
        else:
            print(f"Error getting embeddings: {e}")
            # Return a default embedding vector for other errors
            return [0.0] * 768  # Standard embedding dimension


async def getSummary(source: str, code: str) -> str:
    """
    Generate a summary of the code file using Groq (for documentation)
    """
    print("getting summary for", source)
    if len(code) > 10000:
        code = code[:10000]
    
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            if not groq_available or groq_client is None:
                raise Exception("Groq not available")
            
            prompt = f"""You are an intelligent senior software engineer who specialise in onboarding junior software engineers onto projects.

You are onboarding a junior software engineer and explaining to them the purpose of the {source} file
here is the code:
---
{code}
---
give a summary no more than 100 words of the code above"""

            response = await asyncio.to_thread(
                groq_client.chat.completions.create,
                model="llama-3.1-8b-instant",  # Lighter, faster model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            print("got back summary from Groq", source)
            return response.choices[0].message.content
            
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"⚠️ Rate limit for {source}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
            print(f"Error getting summary for {source}: {e}")
            return f"Unable to generate summary for {source}"
    
    return f"Unable to generate summary for {source}"


async def ask(query: str, namespace: str) -> str:
    """
    Answer questions about the codebase using Gemini (with Groq failsafe)
    """
    try:
        print(f"Asking: {query} for namespace: {namespace}")
        
        # Try to retrieve relevant documents from Weaviate
        relevant_docs = []
        quota_exceeded = False
        try:
            relevant_docs = await retrieve_relevant_docs(query, namespace, limit=5)
        except Exception as retrieval_error:
            if "QUOTA_EXCEEDED" in str(retrieval_error):
                print("⚠️ Embedding quota exceeded, proceeding without context")
                quota_exceeded = True
            else:
                raise  # Re-raise other errors
        
        # Build context from retrieved documents
        context = ""
        if quota_exceeded:
            context = """⚠️ Note: The Gemini API embedding quota has been exceeded. I cannot retrieve specific code context at this moment, but I'll provide a general answer.

To restore full functionality:
- Wait for the quota to reset (typically per minute/hour/day limits)
- Consider upgrading your Gemini API plan for higher quotas
- Visit: https://ai.google.dev/gemini-api/docs/rate-limits

For now, I'll provide a general answer based on common software development practices.

"""
        elif relevant_docs:
            context = "Here is relevant code context from the repository:\\n\\n"
            for i, doc in enumerate(relevant_docs, 1):
                context += f"--- File: {doc['source']} ---\\n"
                context += f"Summary: {doc['summary']}\\n"
                context += f"Content:\\n{doc['content'][:2000]}\\n\\n"  # Limit content to avoid token limits
        else:
            if not weaviate_available:
                context = """Note: The vector database (Weaviate) is currently not available. This might be due to:
- Network connectivity issues
- Incorrect Weaviate cluster URL
- Missing or invalid WEAVIATE_API_KEY

To enable full context-aware Q&A functionality, please:
1. Verify your Weaviate cluster URL in _gemini.py
2. Check your WEAVIATE_API_KEY in the .env file
3. Ensure you have network access to the Weaviate cloud instance

For now, I'll provide a general answer based on common software development practices.

"""
            else:
                context = "Note: No specific code context was found in the vector database. The repository might not have been indexed yet.\\n\\n"
        
        prompt = f"""You are Dionysus, an intelligent AI assistant specialized in helping developers understand codebases.

You have access to a specific codebase and should answer questions based on the actual code context provided below.

{context}

User Question: {query}

Instructions:
- Answer the question based on the code context provided above
- If the context contains relevant information, use it to provide specific, accurate answers
- Include file names and code snippets when relevant
- Format your response in HTML with proper tags for readability
- If you cannot find relevant information in the context, say so honestly and provide general guidance
- Be helpful, clear, and concise

Answer:"""

        # Try Gemini first
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            print("Got back answer from Gemini")
            return response.text
        except Exception as gemini_error:
            error_str = str(gemini_error)
            # If quota exceeded, fallback to Groq
            if "quota" in error_str.lower() or "429" in error_str:
                print("⚠️ Gemini quota exceeded, falling back to Groq")
                if groq_available and groq_client is not None:
                    response = await asyncio.to_thread(
                        groq_client.chat.completions.create,
                        model="llama-3.1-8b-instant",  # Lighter model for Q/A
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.5,
                        max_tokens=2000
                    )
                    print("Got back answer from Groq (failsafe)")
                    # Add a note that Groq was used
                    groq_answer = response.choices[0].message.content
                    return f"""<div style="padding: 10px; background-color: #e8f5e9; border-left: 4px solid #4caf50; margin-bottom: 15px;">
<small>ℹ️ <strong>Powered by Groq</strong> - Gemini quota exceeded, using Groq as failsafe</small>
</div>

{groq_answer}"""
                else:
                    raise  # Re-raise if Groq not available
            else:
                raise  # Re-raise non-quota errors
                
    except Exception as e:
        error_str = str(e)
        print(f"Error answering query: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide more specific error messages
        if "quota" in error_str.lower() or "429" in error_str:
            return """<div style="padding: 20px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
<h3>⚠️ API Quota Exceeded</h3>
<p>I'm currently unable to process your question because the Gemini API quota has been exceeded.</p>
<p><strong>What this means:</strong> The free tier of Gemini API has limits on requests per minute/hour/day.</p>
<p><strong>Solutions:</strong></p>
<ul>
<li>Wait a few minutes and try again</li>
<li>Check your quota at: <a href="https://ai.google.dev/gemini-api/docs/rate-limits" target="_blank">Gemini API Rate Limits</a></li>
<li>Consider upgrading your API plan for higher quotas</li>
</ul>
</div>"""
        elif "api" in error_str.lower() and "key" in error_str.lower():
            return """<div style="padding: 20px; background-color: #f8d7da; border-left: 4px solid #dc3545;">
<h3>❌ API Key Error</h3>
<p>There seems to be an issue with the Gemini API key. Please check that your GEMINI_API_KEY is correctly set in the .env file.</p>
</div>"""
        else:
            return "I'm sorry, but I encountered an error while processing your question. Please try again or contact support if the issue persists."


def summarise_commit(diff: str) -> str:
    """
    Summarize a git commit diff using Groq (for documentation)
    """
    try:
        if not groq_available or groq_client is None:
            raise Exception("Groq not available")
        
        prompt = f"""You are an expert programmer, and you are trying to summarize a git diff.
Reminders about the git diff format:
For every file, there are a few metadata lines, like (for example):
```
diff --git a/lib/index.js b/lib/index.js
index aadf691..bfef603 100644
--- a/lib/index.js
+++ b/lib/index.js
```
This means that `lib/index.js` was modified in this commit. Note that this is only an example.
Then there is a specifier of the lines that were modified.
A line starting with `+` means it was added.
A line that starting with `-` means that line was deleted.
A line that starts with neither `+` nor `-` is code given for context and better understanding.
It is not part of the diff.
[...]
EXAMPLE SUMMARY COMMENTS:
```
* Raised the amount of returned recordings from `10` to `100` [packages/server/recordings_api.ts], [packages/server/constants.ts]
* Fixed a typo in the github action name [.github/workflows/gpt-commit-summarizer.yml]
* Moved the `octokit` initialization to a separate file [src/octokit.ts], [src/index.ts]
* Added a Gemini API for completions [packages/utils/apis/gemini.ts]
* Lowered numeric tolerance for test files
```
Most commits will have less comments than this examples list.
The last comment does not include the file names,
because there were more than two relevant files in the hypothetical commit.
Do not include parts of the example in your summary.
It is given only as an example of appropriate comments.

Please summarise the following diff file: 

{diff}"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Lighter model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error summarizing commit: {e}")
        return "Unable to summarize commit changes"