# AI Service - E-Commerce Platform

## Overview

The AI Service provides intelligent features for the e-commerce platform including:
- **Deep Learning Product Recommendations** using Neural Collaborative Filtering
- **Knowledge Base** with vector embeddings for semantic search
- **RAG-based Consultation Chatbot** for customer support
- **Intent Recognition** and conversation management

## Features

### 1. Product Recommendation System
- **Neural Collaborative Filtering (NCF)**: Deep learning model combining MLP and GMF approaches
- **Content-Based Filtering**: Similarity-based recommendations using product embeddings
- **Hybrid Approach**: Combines multiple algorithms for better accuracy
- **Real-time Personalization**: User behavior tracking and dynamic recommendations

### 2. Knowledge Base (KB)
- **Vector Database**: ChromaDB for efficient similarity search
- **Document Management**: Upload, index, and search knowledge documents
- **FAQ System**: Categorized frequently asked questions
- **Product Knowledge**: Expert tips, usage guides, and troubleshooting info

### 3. Consultation Chatbot (RAG)
- **Retrieval-Augmented Generation**: Combines LLM with knowledge base
- **Context-Aware Responses**: Maintains conversation history
- **Multi-language Support**: Handles multiple languages
- **Feedback System**: Continuous improvement through user feedback

## Architecture

```
AI Service (Port 8010)
├── Django REST Framework
├── ML/DL Models (TensorFlow, PyTorch)
├── Vector Database (ChromaDB)
├── Embedding Models (SentenceTransformers)
└── LLM Integration (OpenAI API)
```

## API Endpoints

### Recommendation APIs
- `POST /api/v1/ai/recommendations/` - Get personalized recommendations
- `POST /api/v1/ai/track-behavior/` - Track user behavior
- `GET /api/v1/ai/models/` - List recommendation models
- `POST /api/v1/ai/models/train/` - Train new model
- `GET /api/v1/ai/embeddings/` - Get product embeddings

### Knowledge Base APIs
- `POST /api/v1/kb/documents/upload/` - Upload knowledge document
- `POST /api/v1/kb/documents/search/` - Search documents
- `GET /api/v1/kb/faqs/` - Get FAQs
- `POST /api/v1/kb/product-knowledge/index_product/` - Index product knowledge

### Chatbot APIs
- `POST /api/v1/chatbot/chat/` - Send chat message
- `POST /api/v1/chatbot/conversations/start/` - Start new conversation
- `GET /api/v1/chatbot/conversations/{id}/history/` - Get conversation history
- `POST /api/v1/chatbot/feedback/` - Submit feedback

## Configuration

### Environment Variables

```bash
# Database
DB_NAME=db_ai
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres

# Service
SERVICE_NAME=ai
SERVICE_PORT=8010

# AI/ML Models
EMBEDDING_MODEL=all-MiniLM-L6-v2  # SentenceTransformer model
LLM_MODEL=gpt-3.5-turbo             # OpenAI model
OPENAI_API_KEY=your_api_key_here    # Optional: for LLM features

# RAG Configuration
RAG_TOP_K_RESULTS=5
RAG_MIN_SIMILARITY=0.6
RAG_CONTEXT_WINDOW=2048

# Model Performance
MAX_CONTEXT_LENGTH=4096
TEMPERATURE=0.7
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd services/ai
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with the required environment variables (see above).

### 3. Initialize Database

```bash
python manage.py migrate
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run Service

```bash
python manage.py runserver 0.0.0.0:8010
```

Or with Docker:

```bash
docker-compose up ai
```

## Usage Examples

### Getting Recommendations

```bash
curl -X POST http://localhost:8010/api/v1/ai/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "algorithm": "neural_cf",
    "limit": 10
  }'
```

### Uploading Knowledge Document

```bash
curl -X POST http://localhost:8010/api/v1/kb/documents/upload/ \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "product",
    "title": "Product Guide",
    "content": "This is a detailed product guide...",
    "language": "en"
  }'
```

### Chatbot Interaction

```bash
curl -X POST http://localhost:8010/api/v1/chatbot/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your shipping options?",
    "language": "en",
    "use_rag": true
  }'
```

## Model Training

### Training a Recommendation Model

```bash
curl -X POST http://localhost:8010/api/v1/ai/models/train/ \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "neural_cf",
    "hyperparameters": {
      "embedding_dim": 64,
      "mlp_layers": [256, 128, 64],
      "dropout_rate": 0.2
    }
  }'
```

## Performance Optimization

### Caching Strategy
- Recommendations are cached for 1 hour
- Vector database uses persistent storage
- Model predictions are batched when possible

### Scaling
- Service can be horizontally scaled
- Vector database supports distributed deployments
- Models can be loaded/unloaded based on demand

## Monitoring

### Analytics Dashboard
Access chatbot analytics at:
```
GET /api/v1/chatbot/analytics/summary/
```

Returns:
- Total conversations
- Average conversation length
- RAG usage statistics
- Satisfaction scores

## Troubleshooting

### Common Issues

1. **Out of Memory Errors**
   - Reduce batch size in model training
   - Use smaller embedding models
   - Limit concurrent requests

2. **Slow Response Times**
   - Check vector database indexing
   - Optimize model batch sizes
   - Use caching for frequent queries

3. **Poor Recommendation Quality**
   - Ensure sufficient user behavior data
   - Train models regularly
   - Adjust recommendation weights

## Future Enhancements

- [ ] Advanced intent recognition
- [ ] Multi-modal product search
- [ ] Real-time model retraining
- [ ] A/B testing framework
- [ ] Advanced analytics dashboard

## Support

For issues and questions, please contact the development team.
