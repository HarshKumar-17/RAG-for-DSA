• Built an end-to-end full-stack Retrieval-Augmented Generation (RAG) assistant using Flask, ChromaDB, and LangChain, enabling context-grounded Q&A over complex Data Structures and Algorithms material with zero manual lookup.
• Architected a low-latency semantic search pipeline leveraging 384-dimensional all-MiniLM-L6-v2 ONNX embeddings and ChromaDB vector store, surfacing the top 5 most relevant document chunks per query under 50ms.
• Integrated multi-turn conversation memory with dynamic query reformulation, adapting follow-up user questions into standalone vector search queries for improved retrieval recall.
• Switched LLM inference to Groq (Llama 3.1 8B) with OpenAI fallback, achieving sub-second response latency while slashing operational costs to 100% free tier.
• Automated time-complexity checks (O(n), O(log n)) and code syntax verification in response validation filters; logged end-to-end telemetry for conversational analytics.
• Packaged and deployed a production-ready application to Render with Gunicorn, trimming dependency footprint from 2.5 GB (PyTorch/Transformers) down to < 100 MB for zero-OOM free-tier hosting.
• Tech: Python, Flask, LangChain, ChromaDB, Groq Cloud API, OpenAI API, Gunicorn, HTML5, CSS3, JavaScript, Git.
