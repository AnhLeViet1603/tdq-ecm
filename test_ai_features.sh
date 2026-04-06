#!/bin/bash

echo "🧪 TESTING GUIDE - AI Features E-Commerce Platform"
echo "=============================================="
echo ""

echo "✅ STEP 1: Test AI Service Directly"
echo "-----------------------------------"
echo "Testing AI Chatbot..."
curl -s -X POST http://localhost:8010/api/v1/chatbot/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your shipping options?", "language": "vi", "use_rag": false}' \
  | python -m json.tool | grep -A 2 "content"

echo ""
echo "Testing AI Knowledge Base..."
curl -s http://localhost:8010/api/v1/kb/faq-categories/ \
  | python -m json.tool | grep -A 1 "\"name\"" | head -3

echo ""
echo "✅ STEP 2: Test AI Features Through Gateway"
echo "----------------------------------------------"
echo "Open your browser and navigate to:"
echo "🌐 http://localhost:8000"
echo ""
echo "Then:"
echo "1. Login with: admin@shopvn.com / admin123"
echo "2. Look at the LEFT SIDEBAR"
echo "3. You should see a new section: 🤖 AI Features"
echo "4. Click on each AI feature:"
echo "   - 🤖 Trợ lý AI (AI Chatbot)"
echo "   - 🎯 Gợi ý AI (AI Recommendations)"
echo "   - 📚 Kiến thức AI (Knowledge Base)"

echo ""
echo "✅ STEP 3: Test Each AI Feature"
echo "---------------------------------"
echo "🤖 AI CHATBOT TEST:"
echo "1. Click '🤖 Trợ lý AI' in sidebar"
echo "2. Type: 'Chính sách đổi trả như thế nào?'"
echo "3. Click Send button (➤)"
echo "4. You should see AI response"

echo ""
echo "🎯 AI RECOMMENDATIONS TEST:"
echo "1. Click '🎯 Gợi ý AI' in sidebar"
echo "2. You should see product recommendations"
echo "3. Check for Neural CF insights and scores"

echo ""
echo "📚 KNOWLEDGE BASE TEST:"
echo "1. Click '📚 Kiến thức AI' in sidebar"
echo "2. Use the search bar to search: 'giao hàng'"
echo "3. Check FAQ categories and suggestions"

echo ""
echo "✅ STEP 4: Test AI APIs Directly"
echo "-----------------------------------"
echo "Test Chatbot API:"
echo "curl -X POST http://localhost:8000/api/ai/v1/chatbot/chat/ \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"message\": \"Hello\", \"language\": \"vi\", \"use_rag\": true}'"

echo ""
echo "Test Knowledge Base:"
echo "curl http://localhost:8000/api/ai/v1/kb/faq-categories/"

echo ""
echo "Test Recommendations:"
echo "curl -X POST http://localhost:8000/api/ai/v1/ai/recommendations/ \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"user_id\": \"test-user\", \"algorithm\": \"neural_cf\", \"limit\": 5}'"

echo ""
echo "🔍 TROUBLESHOOTING"
echo "------------------"
echo "If AI features don't show in sidebar:"
echo "1. Clear browser cache (Ctrl+Shift+Delete)"
echo "2. Hard refresh (Ctrl+F5)"
echo "3. Check browser console for errors (F12)"
echo "4. Make sure you're logged in"

echo ""
echo "If clicks don't work:"
echo "1. Check browser console (F12) for JavaScript errors"
echo "2. Make sure gateway service is running:"
echo "   docker-compose ps gateway"
echo "3. Check gateway logs:"
echo "   docker-compose logs gateway --tail=20"

echo ""
echo "📊 Current Service Status"
echo "-------------------------"
docker-compose ps | grep -E "gateway|ai|NAME"

echo ""
echo "🎉 READY TO TEST!"
echo "=================="
echo "All AI features should now be accessible through the UI."
echo "Start at: http://localhost:8000"
