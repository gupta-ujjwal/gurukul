#!/usr/bin/env python3
"""
WebSocket Test Script for Learning Agent

This script tests the WebSocket connection to the Learning Agent server.
It sends a test message and verifies that a response is received.

Usage:
    python test_websocket.py [--url URL] [--message MESSAGE]

Options:
    --url URL         The WebSocket URL to connect to (default: ws://localhost:5000/socket.io/)
    --message MESSAGE The message to send (default: "let's start")
"""

import argparse
import asyncio
import json
import sys
import time
import websockets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def test_websocket(url, message):
    """Test the WebSocket connection by sending a message and waiting for a response."""
    logger.info(f"Connecting to {url}...")
    
    try:
        # Connect to the WebSocket server
        async with websockets.connect(url) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send a message
            logger.info(f"Sending message: {message}")
            await websocket.send(json.dumps({
                "message": message
            }))
            
            # Wait for a response with a timeout
            logger.info("Waiting for response...")
            response_received = False
            timeout = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Set a short timeout for each receive attempt
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    logger.info(f"Received response: {response}")
                    response_received = True
                    break
                except asyncio.TimeoutError:
                    # Check if we've exceeded the overall timeout
                    if time.time() - start_time >= timeout:
                        logger.error("Timeout waiting for response")
                        break
                    # Otherwise, continue waiting
                    logger.info("Still waiting for response...")
                    continue
            
            if response_received:
                logger.info("Test PASSED: Response received")
                return True
            else:
                logger.error("Test FAILED: No response received within timeout")
                return False
                
    except Exception as e:
        logger.error(f"Error connecting to WebSocket: {str(e)}")
        return False

def main():
    """Parse command line arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test WebSocket connection to Learning Agent")
    parser.add_argument("--url", default="ws://localhost:5000/socket.io/", help="WebSocket URL")
    parser.add_argument("--message", default="let's start", help="Message to send")
    args = parser.parse_args()
    
    logger.info("Starting WebSocket test")
    result = asyncio.run(test_websocket(args.url, args.message))
    
    if result:
        logger.info("WebSocket test completed successfully")
        sys.exit(0)
    else:
        logger.error("WebSocket test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
