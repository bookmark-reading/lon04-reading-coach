# End-to-End Tests

This directory contains end-to-end tests for the reading coach WebSocket functionality.

## Prerequisites

The e2e tests assume the API server is **already running**. Make sure to start the server before running these tests.

### Starting the Server

Choose one of these methods:

```bash
# Method 1: Using the run script
python run_local.py

# Method 2: Using the shell script
./start_server.sh

# Method 3: Using uvicorn directly
uvicorn src.application.api:app --host 0.0.0.0 --port 8000 --reload
```

The server should be accessible at `http://localhost:8000`

## Running the Tests

### Run all e2e tests with pytest

```bash
pytest tests/e2e/ -v
```

### Run a specific test

```bash
pytest tests/e2e/test_websocket_e2e.py::test_session_initialization -v
```

### Run tests with detailed logging

```bash
pytest tests/e2e/ -v -s
```

The `-s` flag shows all logging output, which is useful for verifying that audio is being received by the server.

### Run the test file directly (for debugging)

```bash
python tests/e2e/test_websocket_e2e.py
```

This runs all tests sequentially and provides a summary report.

## Test Coverage

The e2e tests cover:

1. **Basic Connection**: Establishing and closing WebSocket connections
2. **Session Initialization**: Creating sessions with the `session.create` message
3. **Audio Streaming**: Sending binary audio data to the server
4. **Error Handling**: Testing error conditions (e.g., audio before initialization)
5. **Continuous Streaming**: Sending realistic continuous audio streams
6. **Multiple Sessions**: Testing concurrent WebSocket connections
7. **Reconnection**: Testing reconnect behavior

## Verifying Audio Reception

The tests send audio data to the server and verify the connection remains stable. To verify that the server is actually receiving and processing the audio:

1. **Check Server Logs**: When running the tests, watch the server console output. You should see log messages like:
   ```
   Session sess-xxxxx: Received audio chunk (3200 bytes)
   ```

2. **Reading Service Logs**: If the reading service is integrated, you should see:
   ```
   Session sess-xxxxx: Received audio chunk (3200 bytes, buffer size: X frames)
   ```

## Audio Format

The tests generate synthetic PCM16LE audio data:
- **Format**: PCM16LE (16-bit signed little-endian)
- **Sample Rate**: 16000 Hz (configurable)
- **Channels**: Mono
- **Chunk Size**: Typically 20-100ms chunks

## Troubleshooting

### Connection Refused

If you get `ConnectionRefusedError`:
- Make sure the server is running
- Check that it's listening on `localhost:8000`
- Verify no firewall is blocking the connection

### Timeout Errors

If tests timeout waiting for responses:
- Check server logs for errors
- Ensure the server is processing messages correctly
- Increase timeout values in test if needed

### Authentication Errors

If you get authentication/token errors:
- The tests use a simple token "test-token"
- Ensure the server's `debug` mode is enabled (accepts any token)
- Check `src/application/config.py` settings

## Configuration

To change the WebSocket URL or other settings, edit the constants at the top of `test_websocket_e2e.py`:

```python
WS_BASE_URL = "ws://localhost:8000/ws/session"  # Change if running on different host/port
```

## Future Enhancements

Planned additions:
- [ ] Tests for server-to-client messages (audio responses, page changes, feedback)
- [ ] Tests for error recovery and resilience
- [ ] Performance tests (latency, throughput)
- [ ] Tests with real audio file samples
- [ ] Integration with the full reading service workflow
