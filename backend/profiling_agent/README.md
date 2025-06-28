# Profiling Agent MCP Server

A FastAPI-based MCP (Model Context Protocol) server that implements a conversational profiling agent. The agent collects user preferences and information to build comprehensive user profiles for art recommendation systems.

## Features

- **Conversational Interface**: Chat-based interaction to collect user information
- **Structured Data Collection**: Gathers specific fields for user profiling
- **Local Storage**: JSON-based profile persistence
- **Streaming Responses**: Real-time chat experience with Server-Sent Events
- **Tool Integration**: Uses Azure OpenAI function calling for structured data extraction

## User Profile Fields

The agent collects the following information:

- **past_favorite_work**: List of art pieces the user still loves
- **taste_genre**: Description of user's timeless taste/genre preferences
- **current_obsession**: What art/ideas they can't stop thinking about now
- **state_of_mind**: One-sentence snapshot of their current life/emotions
- **future_aspirations**: Who/where they want to be in the future

## Setup

### Prerequisites

- Python 3.11+
- Azure OpenAI API access

### Installation

1. Clone the repository and navigate to the profiling agent directory:
```bash
cd backend/profiling_agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Azure OpenAI credentials:
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_DEPLOYMENT=gpt-4o-profile

# Server Configuration
HOST=0.0.0.0
PORT=8080
```

### Running the Server

#### Local Development
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

#### Using Docker
```bash
docker build -t profiling-agent .
docker run -p 8080:8080 --env-file .env profiling-agent
```

## API Endpoints

### MCP Protocol Endpoints

- `GET /schema` - Returns the tool schema for the save_profile function
- `POST /chat` - Streams chat responses with tool calls

### Profile Management Endpoints

- `GET /profiles` - List all profile UUIDs
- `POST /profiles` - Create a new profile
- `GET /profiles/{user_uuid}` - Get a specific profile

### Health Check

- `GET /` - Health check endpoint

## Usage Examples

### Starting a Chat Session

```bash
curl -N -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session-1",
    "messages": []
  }'
```

### Getting Tool Schema

```bash
curl http://localhost:8080/schema
```

### Creating a Profile

```bash
curl -X POST http://localhost:8080/profiles
```

### Getting a Profile

```bash
curl http://localhost:8080/profiles/{user_uuid}
```

## Data Storage

Profiles are stored locally in JSON format under the `profiles/` directory. Each profile is saved as `{uuid}.json` with the following structure:

```json
{
  "uuid": "6e2d3c2c-...",
  "past_favorite_work": ["The Matrix", "Totoro"],
  "taste_genre": "philosophical sci-fi with hopeful endings",
  "current_obsession": ["A24 coming-of-age films"],
  "state_of_mind": "excited but overworked",
  "future_aspirations": "write a graphic novel",
  "complete": false,
  "created_at": "2025-01-21T19:04:18Z",
  "updated_at": "2025-01-21T19:04:18Z"
}
```

## Integration with Frontend

The server is designed to work with frontend applications that can:

1. Open an EventSource connection to `/chat`
2. Send user messages via POST requests
3. Handle streaming responses and tool calls
4. Retrieve completed profiles for further processing

## Development

### Project Structure

```
/profiling-agent
├── Dockerfile
├── requirements.txt
├── README.md
└── src/
    ├── __init__.py
    ├── main.py          # FastAPI application
    ├── storage.py       # Profile storage management
    └── chat_loop.py     # Azure OpenAI integration
```

### Adding New Features

1. **New Profile Fields**: Update the tool schema in `chat_loop.py` and storage structure in `storage.py`
2. **New Tools**: Add function definitions to the tool schema and implement handlers
3. **Storage Backends**: Extend the `ProfileStorage` class to support different storage systems

## Troubleshooting

### Common Issues

1. **Azure OpenAI Connection**: Ensure your `.env` file has correct credentials
2. **Port Conflicts**: Change the PORT in `.env` if 8080 is already in use
3. **Profile Storage**: Check that the `profiles/` directory is writable

### Logs

The server logs are available in the console output. For production deployments, consider adding structured logging.

## License

This project is part of the Art Recommender system. 