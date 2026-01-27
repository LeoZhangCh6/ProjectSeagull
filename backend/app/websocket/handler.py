"""WebSocket handler for real-time simulation streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import traceback

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_json(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)
    
    async def broadcast(self, data: dict):
        for websocket in self.active_connections.values():
            await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/simulation/{session_id}")
async def websocket_simulation(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for simulation streaming."""
    await manager.connect(websocket, session_id)
    print(f"[WebSocket] Client connected: {session_id}")
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            print(f"[WebSocket] Received: {data}")
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid JSON: {e}"
                })
                continue
            
            action = message.get("action")
            
            if action == "start":
                print(f"[WebSocket] Starting simulation for session: {session_id}")
                
                try:
                    # Import here to avoid circular imports
                    from app.services.simulation_runner import run_simulation_async
                    
                    job_ids = message.get("job_ids")
                    test_names = message.get("test_names")
                    
                    # Run simulation and stream results
                    await run_simulation_async(
                        session_id=session_id,
                        websocket=websocket,
                        job_ids=job_ids,
                        test_names=test_names
                    )
                    print(f"[WebSocket] Simulation completed for session: {session_id}")
                except Exception as e:
                    error_msg = f"Simulation error: {str(e)}"
                    print(f"[WebSocket] {error_msg}")
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "message": error_msg
                    })
            
            elif action == "stop":
                print(f"[WebSocket] Stop requested for session: {session_id}")
                await websocket.send_json({
                    "type": "status",
                    "status": "stopped",
                    "session_id": session_id
                })
                break
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })
    
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected: {session_id}")
        manager.disconnect(session_id)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except Exception:
            pass
        manager.disconnect(session_id)
