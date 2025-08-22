import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Qdrant
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.client = QdrantClient(url=config.QDRANT_URL)
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=config.OPENAI_API_KEY,
            model=config.EMBEDDINGS_MODEL
        )
        self.llm = ChatOpenAI(
            openai_api_key=config.OPENAI_API_KEY,
            model_name=config.CHAT_MODEL,
            temperature=0
        )
        
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            embeddings=self.embeddings,
            content_payload_key="content",
            metadata_payload_key="metadata",
        )
        
        self.qa_chain = self._create_qa_chain()
    
    def _create_qa_chain(self):
        """Create the retrieval QA chain with custom prompt."""
        
        prompt_template = """
            You are a helpful AI assistant for Intercom customer support. Use the following pieces of context from Intercom's help articles to answer the user's question. 

            Guidelines:
            - Provide clear, concise, and step-by-step answers when appropriate
            - Include relevant links if they are mentioned in the context
            - If the question is about integrations, provide a bullet list format
            - For yes/no questions, start with a clear yes or no, then explain the details
            - For customization questions, provide a brief overview with steps
            - If you cannot find the answer in the context, say "I don't have information about this in the available Intercom help articles."

            Context from Intercom Help Articles:
            {context}

            Question: {question}

            Answer:"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        return qa_chain
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system and return answer with sources."""
        try:
            logger.info(f"Processing query: {question}")
            
            result = self.qa_chain.invoke({"query": question})
            
            sources = []
            for doc in result.get("source_documents", []):
                if not doc.page_content or doc.page_content.strip() == "":
                    logger.warning(f"Skipping document with empty content: {doc.metadata}")
                    continue
            
                title = doc.metadata.get("title", "")
                url = doc.metadata.get("url", "")
                
                if not title and "Title:" in doc.page_content:
                    title_start = doc.page_content.find("Title:") + 6
                    title_end = doc.page_content.find("\n", title_start)
                    if title_end == -1:
                        title_end = len(doc.page_content)
                    title = doc.page_content[title_start:title_end].strip()
                
                source_info = {
                    "title": title,
                    "url": url,
                    "content_snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "article_id": doc.metadata.get("article_id"),
                    "chunk_id": doc.metadata.get("chunk_id")
                }
                sources.append(source_info)
            
            response = {
                "answer": result.get("result", ""),
                "sources": sources,
                "query": question
            }
            
            logger.info(f"Successfully processed query: {question}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "sources": [],
                "query": question,
                "error": str(e)
            }
    
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection."""
        try:
            collection_info = self.client.get_collection(config.QDRANT_COLLECTION_NAME)
            return {
                "collection_name": config.QDRANT_COLLECTION_NAME,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "status": "connected"
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "collection_name": config.QDRANT_COLLECTION_NAME,
                "status": "error",
                "error": str(e)
            }

