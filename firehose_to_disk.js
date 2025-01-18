const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB in bytes
const OUTPUT_DIR = process.argv[2] || 'output';

// Create output directory if it doesn't exist
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR);
}

let currentFileStream = null;
let currentFileSize = 0;
let fileCounter = 0;

function createNewFile() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = path.join(OUTPUT_DIR, `bsky-data-${timestamp}-${fileCounter}.jsonp`);
    fileCounter++;
    
    // Close existing stream if it exists
    if (currentFileStream) {
        currentFileStream.end('\n]);'); // Close the JSONP array
        currentFileStream.close();
    }
    
    currentFileStream = fs.createWriteStream(filename);
    currentFileSize = 0;
    
    // Start JSONP wrapper
    currentFileStream.write('callback([\n');
    console.log(`Created new file: ${filename}`);
}

function writeToFile(data) {
    const jsonString = JSON.stringify(data);
    const dataToWrite = currentFileSize === 0 ? 
        jsonString : 
        ',\n' + jsonString;
    
    const dataSize = Buffer.byteLength(dataToWrite);
    
    // Check if we need to create a new file
    if (currentFileSize + dataSize > MAX_FILE_SIZE) {
        createNewFile();
    }
    
    currentFileStream.write(dataToWrite);
    currentFileSize += dataSize;
}

// Create the first file
createNewFile();

// Connect to the WebSocket
const ws = new WebSocket('wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post');

ws.on('open', function open() {
    console.log('Connected to BlueSky WebSocket');
});

ws.on('message', function incoming(data) {
    try {
        const jsonData = JSON.parse(data);
        writeToFile(jsonData);
    } catch (error) {
        console.error('Error processing message:', error);
    }
});

ws.on('error', function error(err) {
    console.error('WebSocket error:', err);
});

ws.on('close', function close() {
    console.log('Disconnected from WebSocket');
    if (currentFileStream) {
        currentFileStream.end('\n]);');
        currentFileStream.close();
    }
});

// Handle process termination
process.on('SIGINT', () => {
    console.log('Closing application...');
    if (currentFileStream) {
        currentFileStream.end('\n]);');
        currentFileStream.close();
    }
    ws.close();
    process.exit();
});
