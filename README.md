# BlueSky WebSocket Logger

This application connects to the BlueSky websocket and logs the received data to JSONP files. The files are automatically split when they reach 100MB in size.

## Features

- Connects to BlueSky's WebSocket feed
- Saves data in JSONP format
- Automatically splits files at 100MB
- Handles graceful shutdown
- Creates timestamped files

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run the application:
```bash
npm start
```

The application will create an `output` directory and start saving files there. Each file will be named in the format: `bsky-data-[timestamp]-[counter].jsonp`

## Output Format

The data is saved in JSONP format, which wraps the JSON data in a callback function. Each file will contain an array of messages received from the websocket.

## Shutdown

The application can be stopped safely by pressing Ctrl+C. It will properly close the current file and websocket connection before exiting.
# bsky-hackathon
