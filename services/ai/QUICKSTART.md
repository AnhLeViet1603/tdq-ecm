# AI Service - Quick Start Guide

## 🚀 Quick Start

### 1. Build and Start Services

```bash
# Build the AI service
docker-compose build ai

# Start all services
docker-compose up -d

# Check AI service logs
docker-compose logs -f ai
```

### 2. Initial Setup

```bash
# Access the AI service container
docker-compose exec ai bash

# Run setup script
chmod +x setup_ai_service.sh
./setup_ai_service.sh
```

### 3. Test the Services

#### Test Chatbot
```bash
curl -X POST http://localhost:8010/api/v1/chatbot/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! What are your shipping options?",
    "language": "en",
    "use_rag": true
  }'
```

#### Test Knowledge Base Search
```bash
curl -X POST http://localhost:8010/api/v1/kb/documents/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "shipping options",
    "top_k": 5,
    "min_similarity": 0.6
  }'
```

#### Test Recommendations
```bash
curl -X POST http://localhost:8010/api/v1/ai/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "algorithm": "neural_cf",
    "limit": 10
  }'
```

## 📚 Key Features

### 1. Product Recommendations
- **Neural Collaborative Filtering**: Deep learning-based recommendations
- **Content-Based Filtering**: Similarity-based product suggestions
- **Hybrid Approach**: Combines multiple algorithms

### 2. Knowledge Base
- **Vector Search**: Semantic document search using embeddings
- **FAQ Management**: Organized frequently asked questions
- **Product Knowledge**: Expert tips and troubleshooting guides

### 3. RAG Chatbot
- **Context-Aware**: Maintains conversation history
- **Knowledge-Augmented**: Uses retrieved documents for accurate responses
- **Multi-Language**: Supports multiple languages

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```bash
# AI Service Configuration
SERVICE_NAME=ai
SERVICE_PORT=8010
OPENAI_API_KEY=your_api_key_here

# Model Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gpt-3.5-turbo

# RAG Settings
RAG_TOP_K_RESULTS=5
RAG_MIN_SIMILARITY=0.6
```

## 📖 Common Use Cases

### 1. Add Product Knowledge

```bash
curl -X POST http://localhost:8010/api/v1/kb/product-knowledge/index_product/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod-123",
    "product_name": "Wireless Headphones",
    "expert_tips": "For best battery life, charge fully before first use",
    "common_issues": [
      {"issue": "Not connecting", "solution": "Reset Bluetooth and try again"}
    ],
    "usage_guide": "Press and hold power button for 3 seconds to turn on"
  }'
```

### 2. Track User Behavior

```bash
curl -X POST http://localhost:8010/api/v1/ai/track-behavior/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "action_type": "view",
    "product_id": "prod-123",
    "metadata": {"source": "search", "position": 1}
  }'
```

### 3. Upload Knowledge Document

```bash
curl -X POST http://localhost:8010/api/v1/kb/documents/upload/ \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "policy",
    "title": "Return Policy",
    "content": "Our return policy allows returns within 30 days...",
    "language": "en"
  }'
```

## 🎯 Best Practices

### 1. Model Training
- Train models regularly with fresh data
- Use sufficient interaction data (minimum 1000+ interactions)
- Monitor model performance metrics

### 2. Knowledge Base
- Keep documents updated and relevant
- Use clear, concise language
- Structure FAQ categories logically

### 3. Chatbot
- Provide clear follow-up suggestions
- Monitor conversation quality
- Collect and act on user feedback

## 🔍 Monitoring

### Check Analytics
```bash
curl http://localhost:8010/api/v1/chatbot/analytics/summary/
```

### View Vector DB Stats
```bash
curl http://localhost:8010/api/v1/kb/vector-indices/stats/
```

## 🐛 Troubleshooting

### Service Not Starting
```bash
# Check logs
docker-compose logs ai

# Check database connection
docker-compose exec ai python manage.py dbshell
```

### Poor Recommendations
```bash
# Train new model
curl -X POST http://localhost:8010/api/v1/ai/models/train/ \
  -H "Content-Type: application/json" \
  -d '{"model_type": "neural_cf"}'
```

### Chatbot Not Responding
```bash
# Check vector DB has documents
curl http://localhost:8010/api/v1/kb/vector-indices/stats/

# Add more knowledge documents
# See upload example above
```

## 📞 Support

For issues and questions:
- Admin Panel: http://localhost:8010/admin/
- API Docs: http://localhost:8010/api/v1/
- Check logs: `docker-compose logs -f ai`

## 🔄 Updating

### Pull Latest Changes
```bash
docker-compose pull ai
docker-compose up -d ai
```

### Rebuild Service
```bash
docker-compose build ai
docker-compose up -d ai
```

## 📈 Performance Tips

1. **Caching**: Recommendations are cached for 1 hour
2. **Batch Processing**: Use bulk operations for large datasets
3. **Vector DB**: Use persistent volumes for vector database
4. **Model Loading**: Keep frequently used models in memory

## 🚀 Next Steps

1. Configure your OpenAI API key for LLM features
2. Add product knowledge documents
3. Train recommendation models with your data
4. Customize chatbot prompts for your brand
5. Set up monitoring and analytics
6. Integrate with frontend applications
