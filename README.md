# LINE Event Logger Service

A high-performance event logging service for LINE Platform built with FastAPI. This service captures and processes LINE platform events including messages and group activities, with integrated SharePoint cloud storage capabilities for file management.

### Core Features

- 🚀 Asynchronous event processing with FastAPI
- 📱 Full LINE Webhook event handling implementation
- 💾 Event persistence with MongoDB
- 📊 Structured event data storage
- 🔍 Flexible event querying with MongoDB aggregation
- ☁️ SharePoint integration for file storage

### Supported Events

- Message Events
  - Text messages
  - Image messages (auto-upload to SharePoint)
- Group Events
  - Join group
  - Leave group
- Member Events
  - Member join
  - Member leave

## Technical Stack

- FastAPI for async API handling
- MongoDB for event persistence
- Docker for containerization
- Microsoft SharePoint for file storage
- LINE Messaging API for webhook events

## Technical Requirements

### Infrastructure

- Python 3.9+
- MongoDB 5.0+
- Docker 20.10+
- Docker Compose 2.0+
- Microsoft 365 Account (SharePoint access)

## Architecture Overview

```plaintext
Client (LINE Platform) --> LINE Webhook --> FastAPI Service --> MongoDB
                                                          --> SharePoint Storage
```

## Deployment

### Using Docker (Recommended)

1. Clone the repository

```bash
git clone https://github.com/JT-427/line-event-logger.git
cd 儲存庫名稱
```

2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build and start the containers

```bash
docker-compose up -d
```

### Environment Variables

```plaintext
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_access_token
MONGODB_URI=mongodb://mongodb:27017
SHAREPOINT_SITE_URL=your_sharepoint_site_url
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret
```

## API Documentation

After deployment, API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Monitoring

The service includes basic health check endpoint:

- Health check: `GET /health`

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── webhook.py
│   ├── core/
│   │   └── storage.py
│   ├── models/
│   │   ├── message.py
│   │   ├── group.py
│   │   └── account.py
│   └── main.py
├── Dockerfile
└── requirements.txt
```
