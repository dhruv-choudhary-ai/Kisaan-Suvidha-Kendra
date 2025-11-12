"""
Test WebSocket voice endpoint
"""
import asyncio
import websockets
import json
import base64

async def test_websocket():
    uri = "ws://localhost:8000/ws/voice"
    
    print("🔌 Connecting to WebSocket...")
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected!")
        
        # Start session
        await websocket.send(json.dumps({
            "type": "start",
            "language": "hindi",
            "session_id": "test-session-123"
        }))
        
        response = await websocket.recv()
        print(f"📨 Received: {response}")
        
        # Simulate sending some audio (dummy data for test)
        print("\n🎤 Sending dummy audio...")
        dummy_audio = b'\x00' * 1600  # 100ms of silence at 16kHz
        audio_b64 = base64.b64encode(dummy_audio).decode('utf-8')
        
        for i in range(5):
            await websocket.send(json.dumps({
                "type": "audio",
                "data": audio_b64
            }))
            await asyncio.sleep(0.1)
        
        print("✅ Audio sent")
        
        # Listen for responses
        print("\n👂 Listening for responses...")
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 {data.get('type')}: {str(data)[:100]}...")
                
                if data.get('type') == 'response':
                    print("\n✅ Got AI response!")
                    break
        except asyncio.TimeoutError:
            print("\n⏱️ Timeout waiting for response (expected with dummy audio)")
        
        # Stop session
        print("\n🛑 Stopping session...")
        await websocket.send(json.dumps({"type": "stop"}))
        
        final = await websocket.recv()
        print(f"📨 Final: {final}")
        
        print("\n✅ Test complete!")

if __name__ == "__main__":
    print("🧪 Testing WebSocket Voice Endpoint\n")
    asyncio.run(test_websocket())
