# Reading Coach - Complete Project

AI-powered reading companion with Nova Sonic integration for real-time speech feedback.

## 📁 Project Structure

```
lon04-reading-coach/
├── frontend/              # Web application
│   ├── index.html        # Main UI (PDF viewer, WebSocket, recording)
│   └── README.md         # Frontend documentation
├── src/
│   ├── application/      # FastAPI app layer
│   │   ├── api.py       # REST & WebSocket endpoints
│   │   ├── config.py    # Settings (Nova config included)
│   │   ├── controller.py # Session management
│   │   └── websocket_handler.py # WebSocket message handling
│   ├── domain/          # Business logic
│   │   ├── agents/
│   │   │   └── simple_reading_agent.py # Simple page-turn agent
│   │   ├── entities/    # Data models
│   │   └── services/
│   │       └── reading_service.py # Audio buffering, agent coordination
│   └── infrastructure/  # External integrations
│       ├── aws_book_provider.py # DynamoDB book provider
│       ├── local_book_provider.py # Local book provider
│       ├── nova_sonic.py # Nova Sonic SDK client
│       ├── nova_sonic_mock.py # Mock for testing
│       └── nova_sonic_reading_agent.py # Nova agent implementation
├── .env                 # Configuration (agent type, Nova settings)
├── demo_reading_agent.py # WebSocket test client
├── test_audio_logging.py # Simple audio test
├── verify_setup.sh      # Quick verification script
└── NOVA_INTEGRATION_STATUS.md # Complete setup guide
```

## 🚀 Quick Start

### 1. Start Backend
```bash
cd /workshop/lon04-reading-coach
uv run uvicorn src.application.api:app --host 0.0.0.0 --port 8000
```

### 2. Access Frontend
**Local**: `http://localhost:3000/`
**Remote**: `https://d2ly2yw37wzs0h.cloudfront.net/ports/3000/`

### 3. Test Audio
1. Open frontend
2. Click "Start Session"
3. Speak into microphone
4. Check logs: `tail -f /tmp/backend.log`

## 🎯 Current Status

- ✅ Backend running on port 8000
- ✅ Frontend migrated to repository
- ✅ WebSocket audio streaming working
- ✅ Nova Sonic integration ready (mock mode)
- ⏳ Nova SDK not installed (requires Python 3.12+)

## 🔧 Configuration

### Agent Selection (.env)
```bash
READING_AGENT_TYPE=nova_sonic  # or "simple"
```

### Nova Sonic Settings
```bash
NOVA_MODEL_ID=amazon.nova-sonic-v1:0
NOVA_TEMPERATURE=0.7
NOVA_SAMPLE_RATE_HZ=16000
```

## 📊 Audio Flow

```
Frontend (Browser)
  ↓ PCM16 @ 16kHz via WebSocket
Backend (FastAPI)
  ↓ Buffer & process
Reading Agent (Simple or Nova)
  ↓ Analyze speech
Response (page_change, feedback, audio_out)
  ↓ WebSocket
Frontend (Display/Play)
```

## 🧪 Testing

### Verify Setup
```bash
./verify_setup.sh
```

### Test Audio Reception
```bash
python3 test_audio_logging.py
```

### Full WebSocket Test (requires pyaudio)
```bash
python3 demo_reading_agent.py --websocket
```

## 📚 Documentation

- `NOVA_INTEGRATION_STATUS.md` - Complete Nova setup guide
- `frontend/README.md` - Frontend documentation
- `src/infrastructure/README_NOVA_SONIC.md` - Nova Sonic details (in nova branch)

## 🔑 Key Features

- **PDF Viewer**: Canvas-based rendering with PDF.js
- **Audio Streaming**: Real-time PCM16 audio via WebSocket
- **Video Recording**: MediaRecorder with S3 upload
- **Nova Sonic**: AI reading coach (mock mode active)
- **Page Control**: Automatic page turns based on reading
- **Fable the Fox**: Animated avatar with speech bubbles

## 🌐 API Endpoints

- `GET /health` - Health check
- `GET /books?user_id={uuid}` - Get books for user
- `GET /pdf/{book_id}` - Serve PDF from S3
- `POST /upload-recording` - Upload video to S3
- `WS /ws?token={token}` - WebSocket for audio streaming

## 🎤 Audio Specifications

**Input (Frontend → Backend)**
- Format: PCM16LE
- Sample Rate: 16,000 Hz
- Channels: Mono
- Chunk Size: 4096 samples

**Output (Backend → Frontend)**
- Format: PCM16LE
- Sample Rate: 24,000 Hz (Nova Sonic)
- Channels: Mono
- Transport: Binary or JSON with text

## 🔐 Test User

```
User ID: 12345678-1234-5678-1234-567812345678
Reading Level: 3
Books: Monkey Business, The Lion who Wouldn't Try
```

## 📦 Dependencies

- FastAPI
- Uvicorn
- Boto3 (AWS S3)
- WebSockets
- Pydantic
- PDF.js (frontend)

## 🚧 Future Enhancements

- [ ] Install Nova SDK (requires Python 3.12+)
- [ ] Add AWS credentials for Nova Sonic
- [ ] Migrate to AudioWorklet (ScriptProcessorNode deprecated)
- [ ] Add WebSocket reconnection logic
- [ ] Implement real Textract integration
- [ ] Add user authentication

## 📄 License

Internal project for Bookmark Reading
