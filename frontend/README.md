# Reading Buddy Frontend

Interactive reading coach frontend with PDF viewer, WebSocket audio streaming, and video recording.

## Features

- 📚 PDF book viewer with page navigation
- 🦊 Fable the Fox animated avatar with speech bubbles
- 🎤 Real-time audio streaming to backend via WebSocket
- 📹 Video recording with S3 upload
- 🎨 Custom branding (orange/dark blue theme)

## Access

### Local Development
```
http://localhost:3000/
```

### CloudFront (Remote)
```
https://d2ly2yw37wzs0h.cloudfront.net/ports/3000/
```

## Configuration

The frontend automatically detects the environment:
- **localhost**: Connects to `http://localhost:8000` (backend)
- **CloudFront**: Connects to `https://d2ly2yw37wzs0h.cloudfront.net/ports/8000`

## Audio Streaming

- **Format**: PCM16LE (16-bit Linear PCM)
- **Sample Rate**: 16,000 Hz
- **Channels**: Mono (1)
- **Transport**: WebSocket binary frames
- **Chunk Size**: 4096 samples

## WebSocket Protocol

### Client → Server
```javascript
// Session creation
{
  "type": "session.create",
  "student_id": "uuid",
  "book_id": "book-id",
  "current_page": 1
}

// Audio data (binary)
ArrayBuffer (PCM16 audio)
```

### Server → Client
```javascript
// Session ready
{
  "type": "session.ready",
  "session_id": "uuid",
  "book_id": "book-id",
  "current_page": 1
}

// Page change
{
  "type": "page_change",
  "page": 2,
  "direction": "next"
}

// Feedback
{
  "type": "feedback",
  "message": "Great job!"
}

// Audio output (future Nova Sonic)
{
  "type": "audio_out",
  "text": "Keep reading!",
  "timestamp": 1234567890
}
```

## Browser Requirements

- Chrome/Edge 88+ (recommended)
- Firefox 85+
- Safari 14+
- Microphone and camera permissions required

## Testing

1. Open `index.html` in browser
2. Allow camera/microphone permissions
3. Select a book from left panel
4. Click "Start Session"
5. Speak into microphone
6. Check browser console for WebSocket messages

## Integration with Backend

The frontend connects to the backend at:
- `/books` - Get available books
- `/pdf/{book_id}` - Load PDF
- `/upload-recording` - Upload video
- `/ws` - WebSocket for audio streaming

## File Structure

```
frontend/
├── index.html          # Main application
└── README.md          # This file
```

## Notes

- Version parameter removed for cleaner URLs
- Auto-detects localhost vs CloudFront
- WebSocket reconnection not implemented (refresh page to reconnect)
- ScriptProcessorNode is deprecated (future: migrate to AudioWorklet)
