# First Time Skeeters

A real-time web application that shows new users making their first post on Bluesky. It connects to the Bluesky firehose, monitors for new posts, and identifies users who are posting for the first time.

## Features

- Real-time monitoring of the Bluesky firehose
- Identifies users making their first post
- Displays posts with user profile information
- Links directly to user profiles on bsky.app
- Filters out replies to focus on original posts
- WebSocket-based for efficient real-time updates

## Technical Details

- Built with Node.js and vanilla JavaScript
- Uses the Bluesky WebSocket firehose API
- Implements the AT Protocol using @atproto/api
- Batches requests to the Bluesky API for efficiency
- Serves both HTTP (web interface) and WebSocket (real-time updates) on the same port

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the server:
```bash
npm start
```

3. Open your browser to `http://localhost:8080`

## How it Works

1. Connects to the Bluesky firehose WebSocket
2. Batches posts in groups of 25 for efficient API usage
3. Queries the Bluesky API to get profile information
4. Identifies users with a post count of 1 (first-time posters)
5. Streams the results in real-time to connected web clients

## Dependencies

- `ws`: WebSocket client and server
- `@atproto/api`: Bluesky API client
