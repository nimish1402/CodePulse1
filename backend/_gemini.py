from dotenv import load_dotenv
import os
import google.generativeai as genai
import asyncio
from typing import List

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Weaviate client (optional for now)
try:
    import weaviate
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url="https://asia-southeast1-gcp-free.weaviate.cloud",
        auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
    )
    weaviate_available = True
    print("Weaviate client initialized successfully")
except Exception as e:
    print(f"Warning: Weaviate not available: {e}")
    weaviate_available = False
    client = None


async def getEmbeddings(text: str) -> List[float]:
    """
    Get embeddings for the given text using Gemini's embedding model
    """
    try:
        # Use Gemini's embedding model
        model = genai.GenerativeModel('embedding-001')
        
        # Clean the text
        cleaned_text = text.replace("\n", " ").strip()
        
        # Generate embeddings
        result = await asyncio.to_thread(
            genai.embed_content,
            model="models/embedding-001",
            content=cleaned_text,
            task_type="retrieval_document"
        )
        
        return result['embedding']
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        # Return a default embedding vector if there's an error
        return [0.0] * 768  # Standard embedding dimension


async def getSummary(source: str, code: str) -> str:
    """
    Generate a summary of the code file using Gemini
    """
    print("getting summary for", source)
    if len(code) > 10000:
        code = code[:10000]
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""You are an intelligent senior software engineer who specialise in onboarding junior software engineers onto projects.

You are onboarding a junior software engineer and explaining to them the purpose of the {source} file
here is the code:
---
{code}
---
give a summary no more than 100 words of the code above"""

        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        print("got back summary", source)
        return response.text
    except Exception as e:
        print(f"Error getting summary for {source}: {e}")
        return f"Unable to generate summary for {source}"


async def ask(query: str, namespace: str) -> str:
    """
    Answer questions about the codebase using Gemini
    Note: Simplified version without vector search for now
    """
    try:
        print("asking", query)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
AI assistant is a brand new, powerful, human-like artificial intelligence.
The traits of AI include expert knowledge, helpfulness, cleverness, and articulateness.
AI is a well-behaved and well-mannered individual.
AI will answer all questions in the HTML format. including code snippets, proper HTML formatting
AI is always friendly, kind, and inspiring, and he is eager to provide vivid and thoughtful responses to the user.
AI has the sum of all knowledge in their brain, and is able to accurately answer nearly any question about any topic in conversation.

User question: {query}

Note: This is a simplified response as the vector database integration is being updated. 
Please provide a general answer based on your knowledge about software development and the query context."""

        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        print("got back answer")
        return response.text
    except Exception as e:
        print(f"Error answering query: {e}")
        return "I'm sorry, but I encountered an error while processing your question."


def summarise_commit(diff: str) -> str:
    """
    Summarize a git commit diff using Gemini
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error summarizing commit: {e}")
        return "Unable to summarize commit changes"