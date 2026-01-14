# Examples

This directory contains examples for testing the Reading Coach backend.

## Quick Start

### 1. Start the Backend Server

The `setup_and_run.py` script sets up sample data and starts the server:

```bash
uv run python examples/setup_and_run.py
```

This will:
- ✓ Create a sample book ("The Cat in the Hat", book-001)
- ✓ Create a sample user profile (Alice Johnson, Grade 3)
- ✓ Start the FastAPI server on http://localhost:8000

### 2. Test with Jupyter Notebook

Open the Jupyter notebook for interactive audio streaming:

```bash
jupyter notebook examples/audio_websocket_client.ipynb
```

The notebook allows you to:
- 🎤 Capture audio from your microphone
- 📡 Stream audio to the WebSocket server
- 📥 Receive server responses
- 🎮 Control session state (page changes, etc.)

## Sample Data

### Book
- **ID**: `book-001`
- **Name**: The Bathtub Safari
- **Reading Age**: 6

### User Profile
- **ID**: `12345678-1234-5678-1234-567812345678`
- **Name**: Alice Johnson
- **Grade**: 3

### WebSocket Connection
- **URL**: `ws://localhost:8000/ws`
- **Token**: `test-token` (dev mode only)

## Audio Configuration

The examples use the following audio settings:
- **Sample Rate**: 16 kHz
- **Channels**: Mono
- **Format**: PCM16LE (16-bit signed integer)
- **Chunk Size**: 1024 samples (~64ms)

## Features Demonstrated

### In setup_and_run.py
- Provider initialization (Book, User Profile)
- Sample data creation
- Server startup

### In audio_websocket_client.ipynb
- WebSocket connection establishment
- Session initialization handshake
- Real-time audio streaming from microphone
- Bidirectional message handling
- Interactive widgets for easy testing
- Manual control for advanced testing

## Requirements

The Jupyter notebook requires:
```bash
pip install websockets pyaudio numpy ipywidgets
```

Note: On macOS, you may need to install PortAudio first:
```bash
brew install portaudio
```

## Troubleshooting

### PyAudio Installation Issues
On macOS:
```bash
brew install portaudio
pip install pyaudio
```

On Linux:
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### Microphone Permissions
Make sure to grant microphone access when prompted by your browser/Jupyter.

### WebSocket Connection Failed
Ensure the backend server is running on port 8000:
```bash
curl http://localhost:8000/health
```

## Next Steps

After testing with the examples:
1. Review the WebSocket protocol in `WEBSOCKET_README.md`
2. Check the E2E tests in `tests/e2e/`
3. Implement your own client using the patterns shown
