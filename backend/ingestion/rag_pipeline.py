import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
import qdrant_client
from llama_index.readers.file import PyMuPDFReader, DocxReader, HTMLTagReader

from backend.config import config

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 100
        Settings.node_parser = TokenTextSplitter(chunk_size=1024, chunk_overlap=100)

        if config.QDRANT_URL and config.QDRANT_API_KEY:
            self.client = qdrant_client.QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        else:
            self.client = qdrant_client.QdrantClient(location=":memory:")

        # Initialize Local Readers (High Speed)
        self.file_extractor = {
            ".pdf": PyMuPDFReader(),
            ".html": HTMLTagReader(),
            ".htm": HTMLTagReader(),
            ".docx": DocxReader()
        }


    def _clean_sec_text(self, text: str) -> str:
        """Strips SGML tags and boilerplate from raw SEC submissions."""
        import re
        # Remove SGML headers/tags
        clean = re.sub(r'<SEC-HEADER>.*?</SEC-HEADER>', '', text, flags=re.DOTALL)
        clean = re.sub(r'<.*?>', '', clean)
        # Remove excessive newlines
        clean = re.sub(r'\n\s*\n', '\n\n', clean)
        return clean.strip()

    def ingest_directory(self, directory_path: str, ticker: str):
        """Ingests a directory of filings, optimizing for SEC text files."""
        # 1. Prefer full-submission.txt for SEC filings to avoid slow HTML parsing
        documents = []
        sec_text_files = []
        
        for root, _, files in os.walk(directory_path):
            for f in files:
                if f == "full-submission.txt":
                    sec_text_files.append(os.path.join(root, f))
        
        if sec_text_files:
            from llama_index.core import Document
            for file_path in sec_text_files:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    cleaned = self._clean_sec_text(content)
                    documents.append(Document(
                        text=cleaned, 
                        metadata={
                            "file_path": file_path, 
                            "ticker": ticker,
                            "source_type": "Official SEC Filing",
                            "provider": "EDGAR"
                        }
                    ))
            
            # [FIX] Always include the DEI summary if it exists, even in optimized mode
            summary_path = os.path.join(directory_path, "dei_summary.txt")
            if os.path.exists(summary_path):
                with open(summary_path, "r", encoding="utf-8") as f:
                    documents.append(Document(
                        text=f.read(),
                        metadata={
                            "file_path": summary_path,
                            "ticker": ticker,
                            "source_type": "Canonical Identity Data",
                            "provider": "System"
                        }
                    ))
            
            logger.info(f"RAG: Optimized ingestion of {len(sec_text_files)} SEC text files + DEI summary for {ticker}")

        else:
            # Fallback to standard reader for other file types
            reader = SimpleDirectoryReader(
                input_dir=directory_path,
                file_extractor=self.file_extractor,
                recursive=True
            )
            documents = reader.load_data()
            for doc in documents:
                doc.metadata["ticker"] = ticker
                doc.metadata["source_type"] = "Supporting Document"
                doc.metadata["provider"] = "Local FS"
        
        if not documents:
            logger.warning(f"RAG: No documents found to ingest for {ticker}")
            return None

        # [SCALING] Use a shared collection with metadata partitioning
        collection_name = "onist_research_v1"
        
        # Ensure collection exists with proper indexing
        self._ensure_collection(collection_name)

        vector_store = QdrantVectorStore(
            client=self.client, 
            collection_name=collection_name
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Increased batch size to 500 for high-speed cloud uploads (fewer HTTP round-trips)
        batch_size = 500
        
        from llama_index.core.node_parser import TokenTextSplitter
        parser = TokenTextSplitter(chunk_size=1024, chunk_overlap=128)
        
        logger.info(f"RAG: Bulk Parsing {len(documents)} documents for {ticker}...")
        nodes = parser.get_nodes_from_documents(documents)
        logger.info(f"RAG: Created {len(nodes)} nodes. Starting high-speed upload...")

        # Initialize index with the first batch to create the collection
        first_batch = nodes[:batch_size]
        index = VectorStoreIndex(first_batch, storage_context=storage_context)
        
        # Insert remaining nodes in larger batches
        for i in range(batch_size, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            progress = (i + len(batch)) / len(nodes) * 100
            logger.info(f"RAG: Uploading [{progress:.1f}%] - Batch {i//batch_size + 1}/{(len(nodes)-1)//batch_size + 1}")
            index.insert_nodes(batch)
            
        return index

    def delete_collection(self, ticker: str):
        """Removes points for a specific ticker from the shared collection."""
        collection_name = "onist_research_v1"
        try:
            from qdrant_client.http import models as qmodels
            self.client.delete(
                collection_name=collection_name,
                points_selector=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="ticker",
                            match=qmodels.MatchValue(value=ticker)
                        )
                    ]
                )
            )
            logger.info(f"Successfully removed points for ticker {ticker} from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error removing points for {ticker} from {collection_name}: {e}")
            return False

    def _get_tier(self, metadata: Dict[str, Any]) -> str:
        """Categorizes sources into Tier 1 (SEC), Tier 2 (News), or Tier 3 (Other)."""
        file_path = metadata.get("file_path", "").lower()
        if "sec-edgar-filings" in file_path or "proxy" in file_path:
            return "tier_1"
        elif "news" in file_path or "article" in file_path:
            return "tier_2"
        return "tier_3"

    def _sanitize_context(self, text: str) -> str:
        """Scrubs common prompt injection patterns from scraped content."""
        patterns = [
            "ignore all previous instructions",
            "system prompt",
            "you are now",
            "assistant:",
            "user:",
            "### instruction"
        ]
        sanitized = text
        for p in patterns:
            sanitized = sanitized.replace(p, "[REDACTED_PATTERN]")
        return sanitized

    def _ensure_collection(self, collection_name: str):
        """Ensures the shared collection exists and has a payload index on 'ticker'."""
        collections = self.client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            logger.info(f"RAG: Creating shared collection {collection_name}...")
            # We assume 768 dims for BGE-small (actually 384 for bge-small)
            # FastEmbed bge-small-en-v1.5 is 384
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_client.http.models.VectorParams(
                    size=384, 
                    distance=qdrant_client.http.models.Distance.COSINE
                )
            )
            # Create payload index for scaling
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="ticker",
                field_schema=qdrant_client.http.models.PayloadSchemaType.KEYWORD
            )
            logger.info(f"RAG: Shared collection {collection_name} initialized with ticker index.")

    def query_index(self, ticker: str, query_text: str, layer: int = 1, run_type: str = "cold", min_creation_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Queries the shared vectorized collection using metadata filtering for the specific ticker.
        Supports dynamic retrieval settings for Layer 1 and Layer 2.
        """
        try:
            collection_name = "onist_research_v1"
            
            from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter, MetadataFilter, FilterOperator
            
            filters = [
                MetadataFilter(
                    key="ticker",
                    value=ticker,
                    operator=FilterOperator.EQ
                )
            ]
            
            if min_creation_date and run_type == "delta":
                filters.append(
                    MetadataFilter(
                        key="filed_date",
                        value=min_creation_date,
                        operator=FilterOperator.GT
                    )
                )
            
            metadata_filters = MetadataFilters(filters=filters)

            vector_store = QdrantVectorStore(
                client=self.client, 
                collection_name=collection_name
            )
            index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            
            # Retrieval Settings based on Layer and Run Type
            if layer == 1:
                top_k = 10 if run_type == "cold" else 5
                similarity_threshold = 0.55
            else: # Layer 2
                top_k = 15 if run_type == "cold" else 8
                similarity_threshold = 0.60

            # Configure retriever with metadata filtering
            retriever = index.as_retriever(
                similarity_top_k=top_k,
                filters=metadata_filters
            )
            
            nodes = retriever.retrieve(query_text)
            
            # Filter by similarity threshold
            filtered_nodes = [n for n in nodes if n.get_score() >= similarity_threshold]
                
            raw_context = "\n\n---\n\n".join([n.text for n in filtered_nodes])
            context = self._sanitize_context(raw_context)
            
            # Build Source Map
            source_tier_map = {}
            source_texts = {}
            for node in filtered_nodes:
                node_id = node.node_id
                source_tier_map[node_id] = self._get_tier(node.metadata)
                source_texts[node_id] = {
                    "text": node.text,
                    "metadata": node.metadata or {}
                }
                
            return {
                "context": context,
                "chunk_count": len(filtered_nodes),
                "source_tier_map": source_tier_map,
                "source_texts": source_texts,
                "source_ids": [n.node_id for n in filtered_nodes]
            }

        except Exception as e:
            logger.error(f"RAG: Query Error for {ticker}: {str(e)}")
            return {
                "context": "",
                "chunk_count": 0,
                "source_tier_map": {},
                "source_texts": {},
                "source_ids": []
            }

rag_pipeline = RAGPipeline()