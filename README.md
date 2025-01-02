# Video Translation Service

This repository contains two implementations of a video translation service client library, built for video translation platform.

## Two Approaches

### Initial Approach: Polling-Based Implementation
A straightforward solution using FastAPI with intelligent polling mechanisms:
- Asynchronous job processing
- Smart polling with progressive delays to reduce server load
- Simple error handling and retry logic
- Easy to understand and implement

### Enhanced Approach: WebSocket with DLQ (Current)
An improved version focusing on reliability and real-time updates:
- Real-time status updates using WebSocket
- Dead Letter Queue (DLQ) for handling failed jobs
- Redis caching for better performance
- More robust error handling

## Why the New Approach?

The WebSocket + DLQ implementation better serves Heygen's video translation needs by:
- Eliminating polling overhead with instant status updates
- Ensuring no failed jobs are lost through DLQ
- Providing better scalability for multiple concurrent translations
- Improving user experience with real-time feedback
