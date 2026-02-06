"""
Test OAuth WebSocket connection with the MCP server.

This script tests the OAuth authentication flow and displays all logs.
"""

import asyncio
import json
import websockets
import uuid


async def test_oauth_connection():
    """Test OAuth WebSocket connection."""
    
    # OAuth credentials (QA environment)
    client_id = "TexasRoadhouse-c75825fa"
    client_secret = "1ac6156a-e353-440b-9885-1350953b7626"
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Build WebSocket URL with OAuth credentials
    url = f"ws://localhost:8000/ws/{session_id}?client_id={client_id}&client_secret={client_secret}"
    
    print("=" * 80)
    print("Testing OAuth WebSocket Connection")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Client ID: {client_id}")
    print(f"Connecting to: {url}")
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
            print()
            
            # Test messages (no need to provide credentials!)
            test_messages = [
                "Get my account information",
                "Get my funding methods",
                "Get my contacts",
                "How many funding methods do I have?"
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


if __name__ == "__main__":
    print()
    print("🚀 OAuth WebSocket Test Client")
    print()
    print("Make sure the server is running in another terminal:")
    print("  python application_websocket.py")
    print()
    input("Press Enter when the server is ready...")
    print()
    
    asyncio.run(test_oauth_connection())
