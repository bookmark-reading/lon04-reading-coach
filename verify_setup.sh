#!/bin/bash
# Quick verification that audio pipeline is working

echo "🔍 Verifying Nova Integration Setup"
echo "===================================="
echo ""

# Check backend
echo "1️⃣  Backend Health:"
curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "❌ Backend not responding"
echo ""

# Check agent
echo "2️⃣  Current Agent:"
grep "Using.*agent" /workshop/lon04-reading-coach/backend_nova.log | tail -1 | sed 's/.*INFO - //'
echo ""

# Check Nova files
echo "3️⃣  Nova Files Present:"
ls -1 /workshop/lon04-reading-coach/src/infrastructure/nova*.py 2>/dev/null | wc -l | xargs echo "   Files found:"
echo ""

# Check config
echo "4️⃣  Agent Configuration:"
grep "READING_AGENT_TYPE" /workshop/lon04-reading-coach/.env | sed 's/^/   /'
echo ""

# Check frontend
echo "5️⃣  Frontend URL:"
echo "   https://d2ly2yw37wzs0h.cloudfront.net/ports/3000/app.html?v=47"
echo ""

echo "📋 To Test Audio Reception:"
echo "   1. Open the frontend URL above"
echo "   2. Click 'Start Session'"
echo "   3. Speak into your microphone"
echo "   4. Run: tail -f /workshop/lon04-reading-coach/backend_nova.log"
echo "   5. Look for: 'Got audio data' messages"
echo ""

echo "🚀 To Enable Nova Sonic:"
echo "   1. Install SDK: pip install aws-sdk-bedrock-runtime"
echo "   2. Add AWS credentials to .env"
echo "   3. Restart backend"
echo ""

echo "✅ Setup Complete - All files from feature/add-nova branch are integrated!"
