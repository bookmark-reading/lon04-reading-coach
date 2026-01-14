# lon04-reading-coach

A Python reading coach application with real-time WebSocket communication for audio streaming and session management.

## Features

- 🎤 **Real-time Audio Streaming** - Full-duplex WebSocket for student microphone and AI voice
- 📚 **Session Management** - Track reading sessions with state management
- 🔐 **Token Authentication** - Secure WebSocket connections with JWT tokens
- 📊 **User Profiles** - DynamoDB integration for user data persistence
- ✅ **Comprehensive Testing** - 42 passing tests with pytest
- 📖 **Interactive API Docs** - FastAPI with OpenAPI/Swagger documentation

## Quick Start

### Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### Running the Server

```bash
# Start server with sample data
./examples/start.sh

# Or using Python directly
uv run python examples/setup_and_run.py
```

This will:
- Set up a sample book and user profile
- Start the FastAPI server on http://localhost:8000

The server will be available at:
- **API**: http://localhost:8000
- **Interactive docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws?token=test-token

### Testing with Audio Streaming

Use the Jupyter notebook for interactive audio capture and streaming:

```bash
# Open the notebook
jupyter notebook examples/audio_websocket_client.ipynb
```

The notebook provides:
- 🎤 Live microphone audio capture
- 📡 Real-time WebSocket streaming
- 🎮 Interactive controls and widgets
- 📊 Message monitoring

See [examples/README.md](examples/README.md) for detailed instructions.

## WebSocket API

The WebSocket endpoint provides full-duplex communication for real-time reading coaching sessions.

### Endpoint

```
WebSocket /ws?token=YOUR_TOKEN
```

### Supported Message Types

The WebSocket supports two message formats:

**Binary messages** - PCM16LE audio (16kHz, mono, 20-50ms chunks)
- Student microphone input → Server
- AI voice response → Student

**JSON messages** - Session control and UI events
- Session initialization and state management
- UI action commands (page turns, highlights)
- Acknowledgements and keepalive

### Connection Flow

```
1. Client connects with authentication token
2. Client sends session_init with student and book info
3. Server responds with session_ready confirmation
4. Bidirectional audio and JSON messages flow
5. On disconnect, server finalizes session and releases resources
```

### Quick Example

```python
import websockets
import json

async with websockets.connect('ws://localhost:8000/ws?token=demo') as ws:
    # Initialize session
    await ws.send(json.dumps({
        "type": "session_init",
        "student_id": "student-123",
        "current_page": 1,
        "book_id": "book-42",
        "sample_rate": 16000
    }))
    
    # Receive session_ready
    response = await ws.recv()
    print(response)  # {"type": "session_ready", "session_id": "sess-xxx"}
    
    # Send audio chunk (binary)
    audio_data = b'\x00\x01\x02...'  # PCM16LE audio
    await ws.send(audio_data)
    
    # Update reader state
    await ws.send(json.dumps({
        "type": "reader_state",
        "current_page": 2,
        "visible_text": "The cat sat on the mat"
    }))
```

### WebSocket Architecture

The implementation uses a layered architecture:

- **[api.py](src/application/api.py)** - FastAPI WebSocket endpoint and routing
- **[websocket_handler.py](src/application/websocket_handler.py)** - Connection lifecycle and message processing
- **[session_manager.py](src/application/session_manager.py)** - Session state management and validation
- **[websocket_messages.py](src/domain/entities/websocket_messages.py)** - Message type definitions
- **[session.py](src/domain/entities/reading_session.py)** - Session entity with state tracking

For complete WebSocket documentation including all message types, error codes, and advanced usage, see **[WEBSOCKET_README.md](WEBSOCKET_README.md)**.

## Development

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_websocket.py -v

# Run with coverage
uv run pytest --cov=src

# Format code
uv run ruff format

# Lint code
uv run ruff check
```

## Project Structure

```
lon04-reading-coach/
├── src/
│   ├── application/
│   │   ├── api.py                    # FastAPI app & WebSocket endpoint
│   │   ├── config.py                 # Application configuration
│   │   ├── session_manager.py        # Session state management
│   │   └── websocket_handler.py      # WebSocket message handling
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── session.py            # Session entity with state
│   │   │   ├── user_profile.py       # User profile entity
│   │   │   └── websocket_messages.py # WebSocket message models
│   │   └── interfaces/
│   │       └── user_profile_provider.py
│   └── infrastructure/
│       └── dynamodb_user_profile_provider.py
├── tests/
│   ├── test_websocket.py             # WebSocket tests (20 tests)
│   ├── test_user_profile_entities.py # User profile tests
│   └── ...
├── examples/
│   └── websocket_client_example.py   # Example WebSocket client
├── WEBSOCKET_README.md               # Detailed WebSocket documentation
└── start_server.sh                   # Server startup script
```

## API Endpoints

### HTTP Endpoints

- `GET /health` - Health check endpoint

### WebSocket Endpoints

- `WebSocket /ws` - Full-duplex reading coach session
  - **Query param**: `token` (authentication token)
  - **Binary messages**: PCM16LE audio chunks
  - **JSON messages**: Session control and events

## Message Types

### Client → Server

- **`session_init`** - Initialize a reading session with student ID, book ID, and starting page
- **`reader_state`** - Update current page and visible text on the screen
- **`client_ack`** - Acknowledge successful execution of a UI event
- **`ping`** - Keepalive heartbeat

### Server → Client

- **`session_ready`** - Session initialized successfully, includes session ID
- **`ui_event`** - UI action command (turn page, highlight text, show prompt, etc.)
  - Actions: `TURN_PAGE`, `GO_TO_PAGE`, `HIGHLIGHT_TEXT`, `SHOW_PROMPT`
- **`server_notice`** - Non-blocking informational message
- **`error`** - Error occurred with error code and message
  - Codes: `INVALID_STATE`, `INVALID_MESSAGE`, `INVALID_PAGE`, `AUTH_FAILED`, `SESSION_NOT_FOUND`, `INTERNAL_ERROR`
- **`pong`** - Ping response

### Audio Messages

- **Format**: Raw PCM16LE binary data
- **Sample Rate**: 16 kHz
- **Channels**: Mono
- **Chunk Size**: 20-50ms (320-800 bytes)
- **Direction**: Bidirectional (student microphone ↔ AI voice)

## Configuration

Configuration is managed via environment variables:

```bash
# .env file example
APP_NAME="Reading Coach"
APP_VERSION="0.1.0"
DEBUG=true
# Add your configuration here
```

## Testing

The project includes comprehensive tests:
- ✅ 20 WebSocket tests (session management, message handling, validation)
- ✅ 9 User profile tests
- ✅ 8 DynamoDB provider tests
- ✅ 5 Configuration tests
- **Total: 42 passing tests**

## Validation Rules

- Page numbers must be ≥ 1
- Page turns must be sequential (next/prev only)
- Cannot jump more than 5 pages at once
- Session must be initialized before audio streaming
- Authentication token required for WebSocket connections

## Performance

- **Target latency**: < 250ms end-to-end audio
- **Audio chunk size**: 20-50ms (320-800 bytes at 16kHz)
- **WebSocket resilience**: Handles brief network interruptions

## Future Enhancements

See [WEBSOCKET_README.md](WEBSOCKET_README.md) for planned features:
- AI model integration for audio processing
- Persistent session storage
- Session recovery after disconnect
- Real-time transcription
- Performance monitoring

## Contributing

1. Create a feature branch
2. Make your changes with tests
3. Run the test suite: `uv run pytest`
4. Format code: `uv run ruff format`
5. Submit a pull request

## License

See LICENSE file for details.

## Usage

```python
from lon04_reading_coach import hello

print(hello())
```
