import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { batchFirehose, getFirstTimers } from "./first_timers.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PORT = 8080;

// Create HTTP server
const server = createServer(async (req, res) => {
    if (req.url === '/') {
        try {
            // Serve client.html
            const data = await readFile(join(__dirname, 'client.html'));
            res.writeHead(200, {
                'Content-Type': 'text/html'
            });
            res.end(data);
        } catch (err) {
            res.writeHead(500);
            res.end('Error loading client.html');
        }
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

// Create WebSocket server attached to HTTP server
const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
    console.log('Client connected to WebSocket');

    const closeStream = batchFirehose(async (data) => {
        const results = await getFirstTimers(data);
        for (const result of results) {
            ws.send(JSON.stringify(result));
        }
    })

    ws.on('close', () => {
        console.log('Client disconnected from WebSocket');
        closeStream();
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        closeStream();
    });
});

server.listen(PORT, () => {
    console.log(`Server running on:
- HTTP: http://localhost:${PORT}
- WebSocket: ws://localhost:${PORT}`);
});
