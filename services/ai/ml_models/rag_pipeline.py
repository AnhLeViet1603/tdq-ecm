import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
import numpy as np
from openai import OpenAI
import os
from django.conf import settings


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for consultation chatbot
    Implements document retrieval, context augmentation, and response generation
    """

    def __init__(self, collection_name: str = "knowledge_base"):
        self.collection_name = collection_name
        self.embedding_model = None
        self.vector_db = None
        self.collection = None
        self.llm_client = None
        self.initialize()

    def initialize(self):
        """Initialize embedding model, vector database, and LLM client"""
        # Initialize sentence transformer for embeddings
        model_name = getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.embedding_model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        vector_db_path = getattr(settings, 'VECTOR_DB_PATH', './vector_db')
        self.vector_db = chromadb.PersistentClient(
            path=vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        try:
            self.collection = self.vector_db.get_collection(name=self.collection_name)
        except:
            self.collection = self.vector_db.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

        # Initialize OpenAI client if API key is available
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if api_key:
            self.llm_client = OpenAI(api_key=api_key)

    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """Add a document to the vector database"""
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()

        # Add to collection
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            ids=[doc_id],
            metadatas=metadata or {}
        )

    def add_documents_batch(self, documents: List[Dict]):
        """Add multiple documents in batch"""
        texts = [doc['text'] for doc in documents]
        doc_ids = [doc['id'] for doc in documents]
        metadatas = [doc.get('metadata', {}) for doc in documents]

        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            ids=doc_ids,
            metadatas=metadatas
        )

    def retrieve_documents(self, query: str, top_k: int = 5,
                          min_similarity: float = 0.6) -> List[Dict]:
        """Retrieve relevant documents based on query"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Search in vector database
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        retrieved_docs = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
                if similarity >= min_similarity:
                    retrieved_docs.append({
                        'id': doc_id,
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': similarity
                    })

        return retrieved_docs

    def generate_response(self, query: str, retrieved_docs: List[Dict],
                         context: Dict = None, max_tokens: int = 500) -> str:
        """Generate response using LLM with retrieved context"""
        if not self.llm_client:
            return self._generate_fallback_response(query, retrieved_docs)

        # Build context from retrieved documents
        context_text = self._build_context(retrieved_docs)

        # Create prompt with context
        system_prompt = self._get_system_prompt(context)
        user_message = self._build_user_prompt(query, context_text)

        try:
            response = self.llm_client.chat.completions.create(
                model=getattr(settings, 'LLM_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=getattr(settings, 'TEMPERATURE', 0.7)
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return self._generate_fallback_response(query, retrieved_docs)

    def _build_context(self, retrieved_docs: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        if not retrieved_docs:
            return "No relevant information found."

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"[Source {i}] {doc['text']}")

        return "\n\n".join(context_parts)

    def _get_system_prompt(self, context: Dict = None) -> str:
        """Get system prompt for the LLM"""
        base_prompt = """You are a helpful e-commerce assistant for an online store.
Your role is to assist customers with:
- Product information and recommendations
- Order inquiries and support
- Shipping and delivery questions
- Return and refund policies
- General shopping assistance

Use the provided context to give accurate, helpful responses.
If the context doesn't contain relevant information, be honest and suggest contacting customer support.
Always be friendly, professional, and concise."""

        if context and 'language' in context:
            language = context['language']
            if language != 'en':
                base_prompt += f"\n\nPlease respond in {language}."

        return base_prompt

    def _build_user_prompt(self, query: str, context_text: str) -> str:
        """Build user prompt with context"""
        return f"""Context information:
{context_text}

Customer question: {query}

Please provide a helpful response based on the context information above."""

    def _generate_fallback_response(self, query: str,
                                    retrieved_docs: List[Dict]) -> str:
        """Generate fallback response when LLM is unavailable"""
        if retrieved_docs:
            best_match = retrieved_docs[0]
            if best_match['similarity'] > 0.8:
                return f"Based on our knowledge base: {best_match['text']}"
            elif best_match['similarity'] > 0.6:
                return f"I found some relevant information: {best_match['text']}\n\nWould you like me to connect you with a customer support agent for more details?"

        return "I'm sorry, I couldn't find specific information about your question. Would you like me to connect you with a customer support agent who can better assist you?"

    def delete_document(self, doc_id: str):
        """Delete a document from the vector database"""
        try:
            self.collection.delete(ids=[doc_id])
        except Exception as e:
            print(f"Error deleting document {doc_id}: {e}")

    def update_document(self, doc_id: str, text: str, metadata: Dict = None):
        """Update a document in the vector database"""
        self.delete_document(doc_id)
        self.add_document(doc_id, text, metadata)

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'embedding_model': getattr(settings, 'EMBEDDING_MODEL', 'unknown'),
                'llm_available': self.llm_client is not None
            }
        except Exception as e:
            return {'error': str(e)}


class ProductKnowledgeExtractor:
    """Extract and structure product knowledge for RAG"""

    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine

    def process_product_data(self, product_data: Dict) -> List[str]:
        """Process product data and create knowledge documents"""
        documents = []

        # Product overview
        overview = f"""Product: {product_data.get('name', 'Unknown')}
Description: {product_data.get('description', 'No description available')}
Category: {product_data.get('category', 'Unknown')}
Price: ${product_data.get('price', 0)}
"""
        documents.append(overview)

        # Product specifications
        if 'specifications' in product_data:
            spec_text = f"Specifications for {product_data['name']}: {product_data['specifications']}"
            documents.append(spec_text)

        # Product features
        if 'features' in product_data:
            feature_text = f"Key features of {product_data['name']}: {', '.join(product_data['features'])}"
            documents.append(feature_text)

        return documents

    def index_product_knowledge(self, product_id: str, product_data: Dict,
                               expert_tips: str = None, common_issues: List[str] = None):
        """Index product knowledge into RAG system"""
        documents = []

        # Process basic product data
        product_docs = self.process_product_data(product_data)
        documents.extend(product_docs)

        # Add expert tips
        if expert_tips:
            tip_doc = f"Expert tips for {product_data.get('name', 'product')}: {expert_tips}"
            documents.append(tip_doc)

        # Add common issues and solutions
        if common_issues:
            issues_doc = f"Common issues for {product_data.get('name', 'product')}: " + \
                        "; ".join([f"Issue: {issue.get('issue')}, Solution: {issue.get('solution')}"
                                  for issue in common_issues])
            documents.append(issues_doc)

        # Add documents to RAG engine
        for i, doc_text in enumerate(documents):
            doc_id = f"{product_id}_{i}"
            metadata = {
                'product_id': product_id,
                'doc_type': 'product_knowledge',
                'section': i
            }
            self.rag_engine.add_document(doc_id, doc_text, metadata)


class ConversationManager:
    """Manage conversation context and history for RAG"""

    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
        self.conversation_history = {}

    def add_message(self, conversation_id: str, role: str, content: str):
        """Add message to conversation history"""
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []

        self.conversation_history[conversation_id].append({
            'role': role,
            'content': content
        })

    def get_conversation_context(self, conversation_id: str,
                                max_history: int = 5) -> List[Dict]:
        """Get recent conversation context"""
        if conversation_id not in self.conversation_history:
            return []

        history = self.conversation_history[conversation_id]
        return history[-max_history:] if len(history) > max_history else history

    def generate_contextual_query(self, conversation_id: str,
                                 current_query: str) -> str:
        """Generate contextual query considering conversation history"""
        context = self.get_conversation_context(conversation_id)

        if not context:
            return current_query

        # Build contextual query
        context_parts = []
        for msg in context:
            context_parts.append(f"{msg['role']}: {msg['content']}")

        context_parts.append(f"user: {current_query}")

        return " | ".join(context_parts)

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
