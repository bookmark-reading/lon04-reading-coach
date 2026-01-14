# Nova Sonic Integration - Complete Setup

## ✅ Current Status

### Backend (lon04-reading-coach)
- **Location**: `/workshop/lon04-reading-coach`
- **Branch**: Working copy with Nova integration
- **Status**: ✅ Running on port 8000
- **Agent**: SimpleReadingAgent (Nova SDK not installed)

### Frontend
- **Location**: `/workshop/ishita/public/app.html`
- **Version**: v47
- **URL**: `https://d2ly2yw37wzs0h.cloudfront.net/ports/3000/app.html?v=47`
- **Status**: ✅ Connected to backend WebSocket

### Nova Branch (Reference)
- **Location**: `/workshop/lon04-reading-coach-nova`
- **Branch**: `feature/add-nova`
- **Status**: ✅ Cloned from GitHub

## 📁 Files Integrated

### From Nova Branch → Working Backend

1. **Nova Sonic Core**
   - ✅ `src/infrastructure/nova_sonic.py` - Nova Sonic SDK client
   - ✅ `src/infrastructure/nova_sonic_reading_agent.py` - Reading agent implementation

2. **Configuration**
   - ✅ `src/application/config.py` - Added Nova config fields
   - ✅ `src/application/api.py` - Added agent selection logic
   - ✅ `.env` - Nova configuration file

3. **Demo/Test Scripts**
   - ✅ `demo_reading_agent.py` - WebSocket test client
   - ✅ `test_audio_logging.py` - Simple audio test

4. **Frontend Updates**
   - ✅ `public/app.html` - WebSocket audio streaming
   - ✅ AudioOutMessage with text field for TTS

## 🔧 Configuration Files

### .env (Backend)
```bash
# Agent Selection
READING_AGENT_TYPE=nova_sonic  # or "simple"

# AWS Configuration
AWS_REGION=us-west-2

# Nova Sonic Configuration
NOVA_MODEL_ID=amazon.nova-sonic-v1:0
NOVA_MAX_TOKENS=1024
NOVA_TEMPERATURE=0.7
NOVA_TOP_P=0.9
NOVA_SAMPLE_RATE_HZ=16000
NOVA_CHANNELS=1
```

## 🎯 How Audio Flows

### Current Flow (SimpleReadingAgent)
```
Frontend (Browser)
  ↓ WebSocket (PCM16 audio @ 16kHz)
Backend WebSocket Handler
  ↓ Binary messages
ReadingService
  ↓ Buffers 10+ frames
SimpleReadingAgent.coach()
  ↓ Counts chunks, decides page turns
WebSocket Response
  ↓ page_change / feedback messages
Frontend Updates
```

### Future Flow (Nova Sonic)
```
Frontend (Browser)
  ↓ WebSocket (PCM16 audio @ 16kHz)
Backend WebSocket Handler
  ↓ Binary messages
ReadingService
  ↓ Buffers audio
NovaSonicReadingAgent.coach()
  ↓ Sends to Nova Sonic
Amazon Nova Sonic (Bedrock)
  ↓ Processes speech, generates feedback
NovaSonicReadingAgent
  ↓ Returns AudioOutMessage with text
WebSocket Response
  ↓ audio_out message with TTS text
Frontend
  ↓ Plays audio / displays text
```

## 🚀 Testing Audio Reception

### Method 1: Frontend (Easiest)
1. Open: `https://d2ly2yw37wzs0h.cloudfront.net/ports/3000/app.html?v=47`
2. Click "Start Session"
3. Speak into microphone
4. Check backend logs:
```bash
tail -f /workshop/lon04-reading-coach/backend_nova.log
```

Look for:
- `Session {session_id}: Received audio chunk (X bytes, buffer size: Y frames)`
- `SimpleReadingAgent processing X audio frames`
- `Page change: 1 → 2 (agent decision)`

### Method 2: Test Script
```bash
cd /workshop/lon04-reading-coach
python3 test_audio_logging.py
```

This sends 20 fake audio chunks and shows:
- ✅ WebSocket connection
- ✅ Session creation
- ✅ Audio chunk transmission
- ✅ Backend responses

### Method 3: Demo Script (Requires pyaudio)
```bash
cd /workshop/lon04-reading-coach
python3 demo_reading_agent.py --websocket
```

Note: Requires `pyaudio` which needs system dependencies.

## 📊 Backend Logging

### Key Log Messages

**Session Start:**
```
INFO - ReadingService created for session {uuid}
INFO - ReadingService {uuid} started
INFO - Emitted session ready for session {uuid}
```

**Audio Reception:**
```
INFO - _receive_loop: Got audio data, X bytes
INFO - _receive_loop: Audio ingested successfully
DEBUG - Session {uuid}: Received audio chunk (X bytes, buffer size: Y frames)
```

**Agent Processing:**
```
DEBUG - SimpleReadingAgent processing X audio frames
INFO - SimpleReadingAgent deciding to turn to page Y from X (accumulated Z audio chunks)
INFO - Page change: X → Y (agent decision)
```

**WebSocket Messages:**
```
INFO - _send_loop got message: PageChangeMessage
INFO - _send_loop got message: FeedbackMessage
```

## 🔍 Verify Audio is Working

### Check 1: WebSocket Connection
```bash
curl -s http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### Check 2: Books Endpoint
```bash
curl -s "http://localhost:8000/books?user_id=12345678-1234-5678-1234-567812345678"
# Should return list of books
```

### Check 3: Live Logs
```bash
# Terminal 1: Watch logs
tail -f /workshop/lon04-reading-coach/backend_nova.log

# Terminal 2: Open frontend and click "Start Session"
# You should see logs appear in Terminal 1
```

## 🎤 Audio Format Specifications

### Frontend → Backend
- **Format**: PCM16LE (Linear PCM, 16-bit, Little Endian)
- **Sample Rate**: 16,000 Hz
- **Channels**: 1 (Mono)
- **Chunk Size**: ~4096 samples (variable)
- **Transport**: WebSocket binary frames

### Backend → Frontend (Future Nova)
- **Format**: PCM16LE
- **Sample Rate**: 24,000 Hz (Nova Sonic output)
- **Channels**: 1 (Mono)
- **Transport**: WebSocket binary frames OR JSON with text

## 🐛 Troubleshooting

### Audio Not Being Received

1. **Check WebSocket Connection**
```bash
# Should show WebSocket connection logs
grep "WebSocket" /workshop/lon04-reading-coach/backend_nova.log | tail -5
```

2. **Check Session Creation**
```bash
# Should show session.create and session.ready
grep "session" /workshop/lon04-reading-coach/backend_nova.log | tail -10
```

3. **Check Audio Ingestion**
```bash
# Should show "Got audio data" messages
grep "audio data" /workshop/lon04-reading-coach/backend_nova.log | tail -10
```

4. **Frontend Console**
- Open browser DevTools (F12)
- Check Console for WebSocket messages
- Look for: "🎤 Audio streaming started"

### Backend Not Starting

```bash
# Check for errors
cat /workshop/lon04-reading-coach/backend_nova.log | tail -50

# Restart backend
pkill -f uvicorn
cd /workshop/lon04-reading-coach
uv run uvicorn src.application.api:app --host 0.0.0.0 --port 8000 > backend_nova.log 2>&1 &
```

## 📝 Next Steps to Enable Nova Sonic

### 1. Install Nova SDK
```bash
# When SDK becomes available
pip install aws-sdk-bedrock-runtime
```

### 2. Set AWS Credentials
Add to `.env`:
```bash
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_SESSION_TOKEN=your-token  # if using temporary credentials
```

### 3. Restart Backend
```bash
pkill -f uvicorn
cd /workshop/lon04-reading-coach
uv run uvicorn src.application.api:app --host 0.0.0.0 --port 8000 > backend_nova.log 2>&1 &
```

### 4. Verify Nova Agent Loaded
```bash
tail -20 /workshop/lon04-reading-coach/backend_nova.log | grep agent
# Should show: "✅ Using Nova Sonic reading agent"
```

## 📚 Key Files Reference

### Backend
- `src/application/api.py` - FastAPI app, WebSocket endpoint
- `src/application/controller.py` - Session management
- `src/application/websocket_handler.py` - WebSocket message handling
- `src/domain/services/reading_service.py` - Audio buffering, agent coordination
- `src/domain/agents/simple_reading_agent.py` - Simple agent (current)
- `src/infrastructure/nova_sonic_reading_agent.py` - Nova agent (future)
- `src/infrastructure/nova_sonic.py` - Nova SDK client

### Frontend
- `public/app.html` - Main UI with PDF viewer, WebSocket, audio recording

### Configuration
- `.env` - Backend configuration
- `src/application/config.py` - Settings schema

### Testing
- `demo_reading_agent.py` - Full WebSocket test with microphone
- `test_audio_logging.py` - Simple audio chunk test

## ✅ Verification Checklist

- [x] Backend running on port 8000
- [x] Frontend accessible via CloudFront
- [x] WebSocket endpoint responding
- [x] Nova files integrated
- [x] Configuration files created
- [x] Agent selection logic implemented
- [x] Audio streaming in frontend
- [x] AudioOutMessage has text field
- [ ] Nova SDK installed (pending)
- [ ] AWS credentials configured (pending)
- [ ] Nova Sonic agent active (pending)

## 🎉 Summary

Everything is in place from the `feature/add-nova` branch:
- ✅ Nova Sonic client and agent code
- ✅ Configuration and agent selection
- ✅ Frontend WebSocket audio streaming
- ✅ Backend audio reception and logging
- ✅ Demo and test scripts

**To verify audio is working right now:**
1. Open `https://d2ly2yw37wzs0h.cloudfront.net/ports/3000/app.html?v=47`
2. Click "Start Session"
3. Speak into microphone
4. Run: `tail -f /workshop/lon04-reading-coach/backend_nova.log`
5. Look for "Got audio data" messages

**To enable Nova Sonic:**
1. Install SDK: `pip install aws-sdk-bedrock-runtime`
2. Add AWS credentials to `.env`
3. Restart backend
4. Audio will flow through Nova Sonic automatically!
