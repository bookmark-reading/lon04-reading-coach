import asyncio
import json
import logging
from dataclasses import asdict

from starlette.websockets import WebSocket, WebSocketDisconnect

from ..domain.entities import (
    AudioOutMessage,
    OutboundMessage,
)
from ..domain.entities.messages import (
    SessionReadyMessage,
    PageChangeMessage,
    ErrorOutMessage,
    NoticeMessage,
    FeedbackMessage,
    SessionEndedMessage,
    TranscriptMessage
)
from ..domain.services import ReadingService

logger = logging.getLogger(__name__)


class WebSocketHandler:

    def __init__(self, reading_service: ReadingService):
        self._reading_service = reading_service

    async def handle_websocket(self, websocket: WebSocket) -> None:
        # Note: websocket.accept() is called by the API endpoint before this
        logger.info(f"handle_websocket starting, creating send and receive tasks")
        send_task = asyncio.create_task(self._send_loop(websocket))
        receive_task = asyncio.create_task(self._receive_loop(websocket))
        logger.info("Tasks created, waiting for first exception or completion")
        done, pending = await asyncio.wait(
            {send_task, receive_task},
            return_when=asyncio.FIRST_EXCEPTION,
        )
        logger.info(f"asyncio.wait returned: done={[t.get_name() for t in done]}, pending={[t.get_name() for t in pending]}")
        try: 
            for task in done: 
                exc = task.exception()
                if exc:
                    raise exc
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {websocket.client}")
            await self._reading_service.pause()
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            await self._reading_service.stop()
        finally:
            await self._reading_service.stop()
            for t in (send_task, receive_task):
                if not t.done():
                    t.cancel()
            await asyncio.gather(send_task, receive_task, return_exceptions=True)

            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}", exc_info=True)
                pass
            logger.info(f"WebSocket connection closed: {websocket.client}")

    async def _send_loop(self, websocket: WebSocket) -> None:
        logger.info(f"_send_loop started, _running={self._reading_service._running}")
        while self._reading_service._running:
            logger.debug(f"_send_loop waiting for outbound message, _running={self._reading_service._running}")
            item: OutboundMessage = await self._reading_service.outbound_queue.get()
            logger.info(f"_send_loop got message: {type(item).__name__}")
            
            match item:
                case SessionReadyMessage():
                    # Send session ready as JSON
                    data = {"type": "session.ready", **asdict(item)}
                    logger.info(f"_send_loop sending session.ready: {data}")
                    await websocket.send_text(json.dumps(data))
                    logger.info("_send_loop sent session.ready successfully")
                
                case AudioOutMessage():
                    # Send audio feedback as binary WebSocket frame
                    await websocket.send_bytes(item.pcm_bytes)
                
                case PageChangeMessage():
                    # Send page change instruction as JSON
                    data = {
                        "type": "page_change",
                        "page": item.page,
                        "direction": item.direction,
                        "page_change": json.loads(item.page_change.model_dump_json())
                    }
                    await websocket.send_text(json.dumps(data))
                
                case ErrorOutMessage():
                    # Send error message as JSON
                    data = {"type": "error", **asdict(item)}
                    await websocket.send_text(json.dumps(data))
                
                case NoticeMessage():
                    # Send notice message as JSON
                    data = {
                        "type": "notice",
                        "message": item.message,
                        "notice": json.loads(item.notice.model_dump_json())
                    }
                    await websocket.send_text(json.dumps(data))
                
                case FeedbackMessage():
                    # Send feedback message as JSON
                    data = {
                        "type": "feedback",
                        "message": item.message,
                        "feedback_type": item.feedback_type,
                        "highlight_text": item.highlight_text,
                        "feedback": json.loads(item.feedback.model_dump_json())
                    }
                    await websocket.send_text(json.dumps(data))
                
                case SessionEndedMessage():
                    # Send session ended message as JSON
                    data = {"type": "session.ended", **asdict(item)}
                    await websocket.send_text(json.dumps(data))
                
                case TranscriptMessage():
                    # Send transcript message as JSON
                    data = {
                        "type": "transcript",
                        "text": item.text,
                        "is_final": item.is_final,
                        "confidence": item.confidence
                    }
                    await websocket.send_text(json.dumps(data))
                
                case _:
                    # Unknown message type
                    raise ValueError(f"Unknown OutboundMessage type: {type(item)}")

    async def _receive_loop(self, websocket: WebSocket) -> None:
        """Receive messages from client and forward to reading service."""
        logger.info("_receive_loop started")
        while True:
            logger.debug("_receive_loop waiting for message...")
            data = await websocket.receive()
            logger.info(f"_receive_loop received: type={data.get('type')}, keys={list(data.keys())}")
            
            # Handle binary messages (audio)
            if data.get("type") == "websocket.receive" and "bytes" in data:
                # Audio data - ingest it
                pcm_bytes = data["bytes"]
                logger.info(f"_receive_loop: Got audio data, {len(pcm_bytes)} bytes")
                timestamp = asyncio.get_event_loop().time()
                await self._reading_service.ingest_audio(pcm_bytes, timestamp)
                logger.info("_receive_loop: Audio ingested successfully")
            
            # Handle text messages (JSON control messages)
            elif data.get("type") == "websocket.receive" and "text" in data:
                try:
                    message = json.loads(data["text"])
                    await self._handle_control_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message: {e}")
            
            # Handle disconnect
            elif data.get("type") == "websocket.disconnect":
                logger.info(f"Client disconnected - received disconnect message: {data}")
                await self._reading_service.close()
                logger.info("Called reading_service.close(), breaking receive loop")
                break
    
    async def _handle_control_message(self, message: dict) -> None:
        """Handle JSON control messages from client."""
        msg_type = message.get("type")
        
        if msg_type == "event.ack":
            # Client acknowledging an event
            event_id = message.get("event_id")
            status = message.get("status", "ok")
            await self._reading_service.ack_event(event_id, status)
        
        elif msg_type == "reader.update":
            # Client updating reader state
            current_page = message.get("current_page")
            visible_text = message.get("visible_text", "")
            await self._reading_service.update_reader_state(current_page, visible_text)
        
        else:
            logger.warning(f"Unknown control message type: {msg_type}")