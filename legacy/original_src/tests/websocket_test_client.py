"""
WebSocket Test Client for Veem API MCP Server (OAuth)

This script demonstrates how to connect to and interact with the WebSocket server
using OAuth authentication.
"""

import asyncio
import json
import websockets
import uuid
from urllib.parse import urlencode


async def test_websocket():
    """Test the WebSocket connection with OAuth authentication."""
    
    # OAuth credentials (QA environment)
    client_id = "TexasRoadhouse-c75825fa"
    client_secret = "1ac6156a-e353-440b-9885-1350953b7626"
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Build WebSocket URL with OAuth credentials
    query_params = urlencode({
        "client_id": client_id,
        "client_secret": client_secret
    })
    url = f"ws://localhost:8000/ws/{session_id}?{query_params}"
    
    print("=" * 80)
    print("WebSocket Test Client (OAuth)")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Client ID: {client_id}")
    print(f"Connecting to server...")
    print("=" * 80)
    print()
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected successfully!")
            print()
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📨 Server: {json.dumps(welcome_data, indent=2)}")
            
            if welcome_data.get("account_id"):
                print(f"\n🔐 Authenticated as Account ID: {welcome_data['account_id']}")
            print()
            
            # Test conversation (no need to provide credentials!)
            test_messages = [
                "Get my account information",
                "Get my payment methods",
                "Get my payees",
                "How many payment methods do I have?"
            ]
            
            for user_message in test_messages:
                print(f"💬 You: {user_message}")
                
                # Send message
                message = {
                    "type": "message",
                    "content": user_message
                }
                await websocket.send(json.dumps(message))
                
                # Receive responses (status + response)
                while True:
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    
                    if response_data["type"] == "status":
                        print(f"⏳ Status: {response_data['message']}")
                    elif response_data["type"] == "response":
                        print(f"🤖 Assistant: {response_data['content'][:200]}...")
                        print()
                        print("-" * 80)
                        print()
                        break
                    elif response_data["type"] == "error":
                        print(f"❌ Error: {response_data['message']}")
                        print()
                        break
                
                # Small delay between messages
                await asyncio.sleep(1)
            
            print()
            print("=" * 80)
            print("✅ Test completed successfully!")
            print("=" * 80)
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with status code: {e.status_code}")
        print(f"   This usually means authentication failed.")
        print(f"   Check that the server is running and credentials are correct.")
    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("   Make sure the server is running:")
        print("   python application_websocket.py")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")


async def interactive_client():
    """Interactive WebSocket client with OAuth authentication."""
    
    # OAuth credentials (QA environment)
    client_id = "TexasRoadhouse-c75825fa"
    client_secret = "1ac6156a-e353-440b-9885-1350953b7626"
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Build WebSocket URL with OAuth credentials
    query_params = urlencode({
        "client_id": client_id,
        "client_secret": client_secret
    })
    url = f"ws://localhost:8000/ws/{session_id}?{query_params}"
    
    print("=" * 80)
    print("Interactive WebSocket Client (OAuth)")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Client ID: {client_id}")
    print(f"Connecting to server...")
    print("=" * 80)
    print()
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected! Type your messages (or 'exit' to quit)\n")
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📨 Server: {welcome_data.get('message', welcome)}")
            
            if welcome_data.get("account_id"):
                print(f"🔐 Authenticated as Account ID: {welcome_data['account_id']}")
            print()
            
            # Start a task to receive messages
            async def receive_messages():
                try:
                    while True:
                        response = await websocket.recv()
                        response_data = json.loads(response)
                        
                        if response_data["type"] == "status":
                            print(f"\n[Status] {response_data['message']}")
                        elif response_data["type"] == "response":
                            print(f"\nAssistant: {response_data['content']}\n")
                            print("You: ", end="", flush=True)
                        elif response_data["type"] == "error":
                            print(f"\n[Error] {response_data['message']}\n")
                            print("You: ", end="", flush=True)
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed by server")
            
            # Start receiving task
            receive_task = asyncio.create_task(receive_messages())
            
            try:
                while True:
                    # Get user input
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "You: "
                    )
                    
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        print("Goodbye!")
                        break
                    
                    if not user_input.strip():
                        continue
                    
                    # Send message
                    message = {
                        "type": "message",
                        "content": user_input
                    }
                    await websocket.send(json.dumps(message))
            
            except KeyboardInterrupt:
                print("\nInterrupted by user")
            finally:
                receive_task.cancel()
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with status code: {e.status_code}")
        print(f"   This usually means authentication failed.")
    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("   Make sure the server is running:")
        print("   python application_websocket.py")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        print("Starting interactive WebSocket client...")
        asyncio.run(interactive_client())
    else:
        print("Running automated test...")
        asyncio.run(test_websocket())
