import WebSocket from 'ws';

export function streamFirehose(on_message) {
    // Connect to the WebSocket
    const ws = new WebSocket('wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post');

    ws.on('open', function open() {
        console.log('Connected to BlueSky WebSocket');
    });

    ws.on('message', function incoming(data) {
        try {
            const jsonData = JSON.parse(data);
            on_message(jsonData);
        } catch (error) {
            console.error('Error processing message:', error);
        }
    });

    ws.on('error', function error(err) {
        console.error('WebSocket error:', err);
    });

    ws.on('close', function close() {
        console.log('Disconnected from WebSocket');
    });

    // Provide a function to shut down the stream
    return function() {
        ws.close();
    }
}