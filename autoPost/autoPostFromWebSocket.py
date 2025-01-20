#automatically reply bot welcomes new users of bluesky on there first post
"""
Bluesky Welcome Bot
------------------

This bot automatically welcomes new users to Bluesky by responding to their first posts.

Configuration:
-------------
Update the following variables with your credentials:

BLUESKY_USERNAME: Your Bluesky bot account username
BLUESKY_PASSWORD: Your Bluesky app-specific password 
OPENAI_API_KEY: Your OpenAI API key for generating personalized welcome messages
WEBSOCKET_URL: WebSocket endpoint for receiving new post notifications

To set up:
1. Create a Bluesky account for your bot
2. Generate an app password in Bluesky settings
3. Get an OpenAI API key from platform.openai.com
4. Update the credentials in this file

The bot will:
- Monitor for new user posts via WebSocket
- Generate a personalized welcome message using GPT-4
- Reply to the user's first post
- Optionally connect new users to other recent joiners

Note: Please be mindful of Bluesky's rate limits and terms of service when running bots.
"""



from atproto import Client
import asyncio
import json
import time
from openai import OpenAI
import websockets

BLUESKY_USERNAME = 'welcomewagon.bsky.social'
BLUESKY_PASSWORD = 'yourpassword'
DEBUG_MODE = False
WEBSOCKET_URL = 'wss://first-time-skeeters.onrender.com/'

# OpenAI configuration
OPENAI_API_KEY = 'yourkeys'
client = OpenAI(api_key=OPENAI_API_KEY)

# Store the last welcomed user
last_welcomed_user = None
last_welcomed_did = None

def generate_welcome_message(post_text, handle, last_user=None):
    try:
        base_prompt = f"""
        Create a friendly, personalized welcome message for a new Bluesky user based on their first post.
        Their handle is {handle} and their post was: "{post_text}"
        """
        
        if last_user:
            base_prompt += f"\nAlso mention that @{last_user} just joined recently too - suggest they say hello to each other!"
            
        base_prompt += """
        The message should:
        1. Be warm and welcoming
        2. Reference something specific from their post
        3. Give a genuine compliment
        4. Be brief (max 2 sentences)
        5. Be casual and friendly in tone
        
        Don't use hashtags or emojis.
        Don't include quotes from their post - we'll add that separately.
        """
        
        print(f"\nGenerating welcome message for post: {post_text}")
        
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{
                "role": "user",
                "content": base_prompt
            }]
        )
        
        generated_message = response.choices[0].message.content.strip()
        print(f"LLM Generated message: {generated_message}")
        return generated_message
    except Exception as e:
        print(f"Error generating welcome message: {e}")
        return f"Welcome to Bluesky! Thanks for sharing your thoughts."

async def post_to_bluesky(message, facets=None):
    try:
        client = Client()
        print("Client created")
        
        login_response = client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)
        print(f"Login successful! Logged in as: {login_response.handle}")
        
        try:
            response = client.send_post(text=message, facets=facets)
            print('Posted successfully:', response)
            return response
        except Exception as post_error:
            error_str = str(post_error)
            if 'RateLimitExceeded' in error_str or 'Rate Limit Exceeded' in error_str:
                # Extract reset time from headers if available
                if hasattr(post_error, 'response') and 'ratelimit-reset' in post_error.response.headers:
                    reset_time = int(post_error.response.headers['ratelimit-reset'])
                    current_time = int(time.time())
                    wait_time = max(reset_time - current_time + 5, 300)  # Add 5 seconds buffer
                else:
                    wait_time = 300  # Default 5 minutes
                
                print(f'Rate limit hit. Waiting {wait_time} seconds before retrying...')
                await asyncio.sleep(wait_time)
                
                # Try again after waiting
                print('Retrying post...')
                response = client.send_post(text=message, facets=facets)
                print('Posted successfully after waiting:', response)
                return response
            else:
                print(f'Non-rate-limit error: {error_str}')
                raise post_error
                
    except Exception as error:
        print(f'Error type: {type(error)}')
        print(f'Error posting to Bluesky: {str(error)}')
        print(f'Message that failed: {message}')
        print(f'Facets that failed: {facets}')
        raise error

async def process_post(post_data):
    try:
        global last_welcomed_user, last_welcomed_did
        
        # Add initial delay to help prevent rate limiting
        await asyncio.sleep(30)  # Wait 30 seconds between posts
        
        data = json.loads(post_data)
        print("\nProcessing new post:")
        
        # Extract the handle and text from the new structure
        handle = data['profile']['handle']
        post_text = data['post']['commit']['record'].get('text', '')
        did = data['did']
        
        print(f"Author: {handle}")
        print(f"DID: {did}")
        print(f"Text: {post_text}")
        
        # Skip if the post is empty
        if not post_text:
            print("Skipping empty post")
            return
        
        # Generate personalized welcome message with last user reference
        welcome_message = generate_welcome_message(post_text, handle, last_welcomed_user)
        
        # Combine welcome message and mention, keeping the quote on a new line
        message = f"{welcome_message} @{handle}\n\nRe: \"{post_text}\""
        
        # Calculate byte positions for mentions
        full_text = message.encode('utf-8')
        facets = []
        
        # Add current user mention
        handle_text = f"@{handle}".encode('utf-8')
        mention_start = full_text.find(handle_text)
        mention_end = mention_start + len(handle_text)
        
        facets.append({
            "index": {
                "byteStart": mention_start,
                "byteEnd": mention_end
            },
            "features": [{
                "$type": "app.bsky.richtext.facet#mention",
                "did": did
            }]
        })
        
        # Add last user mention if exists
        if last_welcomed_user and last_welcomed_did:
            last_handle_text = f"@{last_welcomed_user}".encode('utf-8')
            last_mention_start = full_text.find(last_handle_text)
            if last_mention_start != -1:  # Only if the mention exists in the text
                last_mention_end = last_mention_start + len(last_handle_text)
                facets.append({
                    "index": {
                        "byteStart": last_mention_start,
                        "byteEnd": last_mention_end
                    },
                    "features": [{
                        "$type": "app.bsky.richtext.facet#mention",
                        "did": last_welcomed_did
                    }]
                })
        
        print("\nFinal message to post:", message)
        
        # Post the message
        await post_to_bluesky(message, facets)
        
        # Update last welcomed user
        last_welcomed_user = handle
        last_welcomed_did = did
        
    except Exception as e:
        print(f"Error processing post: {e}")
        print("Post data:", post_data)

async def main():
    while True:
        try:
            print("Connecting to WebSocket...")
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                print("Connected to WebSocket!")
                
                while True:
                    try:
                        message = await websocket.recv()
                        print("\nReceived new post from WebSocket")
                        await process_post(message)
                        
                    except websockets.ConnectionClosed:
                        print("WebSocket connection closed. Reconnecting...")
                        break
                    
                    except Exception as e:
                        print(f"Error handling message: {e}")
                        continue
                        
        except Exception as e:
            print(f"Connection error: {e}")
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
