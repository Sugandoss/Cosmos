# GCP Cost Monitor - Slack Bot

A Slack bot that provides RAG-powered cost monitoring capabilities, allowing users to query their GCP infrastructure costs using natural language.

## 🏗️ Architecture

```
Slack App → Slack Bot → RAG Integration → Chroma DB → LLM Response
     ↓           ↓           ↓           ↓           ↓
User Query   Process    Vector Search   Cost Data   Answer
```

## 🚀 Features

- **Natural Language Queries**: Ask about costs in plain English
- **RAG Integration**: Uses existing Chroma database and MiniLM embeddings
- **Real-time Responses**: Instant answers about your infrastructure costs
- **Multiple Interfaces**: App mentions, direct messages, and slash commands
- **LLM Integration**: Powered by Ollama for intelligent responses

## 📋 Prerequisites

1. **Slack App**: A configured Slack app with proper permissions
2. **AI/ML Pipeline**: The main AI/ML pipeline must be run first
3. **Ollama**: For LLM features (optional but recommended)
4. **Python 3.8+**: For running the bot

## 🛠️ Setup Instructions

### 1. Create Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name: "GCP Cost Monitor"
4. Select your workspace

### 2. Configure Bot Permissions

Go to "OAuth & Permissions" and add these Bot Token Scopes:
- `app_mentions:read`
- `chat:write`
- `commands`
- `im:history`
- `im:read`
- `im:write`

### 3. Install App to Workspace

1. Click "Install to Workspace"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. Configure Signing Secret

1. Go to "Basic Information"
2. Copy the "Signing Secret"

### 5. Enable Socket Mode

1. Go to "Socket Mode"
2. Enable Socket Mode
3. Create an App-Level Token (starts with `xapp-`)

### 6. Add Slash Commands

Go to "Slash Commands" and add:
- `/cost-query` - Ask about GCP costs
- `/cost-stats` - Get cost statistics  
- `/cost-help` - Show help

### 7. Configure Environment

```bash
# Copy the example file
cp env_example.txt .env

# Edit .env with your credentials
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_APP_TOKEN=xapp-your-app-token-here
```

### 8. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 9. Run the Bot

```bash
python3 slack_bot.py
```

## 📖 Usage Examples

### App Mentions
```
@GCP Cost Bot Which services are most expensive?
@GCP Cost Bot Show me recent anomalies
@GCP Cost Bot What are the cost trends?
```

### Direct Messages
Send a direct message to the bot:
```
Which projects have the highest costs?
How much did we spend yesterday?
Show me cost anomalies from last week
```

### Slash Commands
```
/cost-query Which services are most expensive?
/cost-stats
/cost-help
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token | Yes |
| `SLACK_SIGNING_SECRET` | App Signing Secret | Yes |
| `SLACK_APP_TOKEN` | App-Level Token | Yes |
| `LOG_LEVEL` | Logging level | No |
| `RAG_TIMEOUT` | LLM timeout (seconds) | No |
| `MAX_SEARCH_RESULTS` | Max search results | No |

### Customization

You can customize the bot behavior by modifying:
- `rag_integration.py`: RAG system configuration
- `slack_bot.py`: Bot behavior and responses
- Response formatting in `_format_for_slack()` method

## 🔍 How It Works

### 1. Query Processing
1. User sends a question via Slack
2. Bot extracts the query text
3. Query is processed by RAG system

### 2. RAG Integration
1. Query is converted to embeddings using MiniLM
2. Vector search finds relevant cost data in Chroma DB
3. Context is prepared with retrieved data

### 3. Response Generation
1. For simple questions: Fast response using pattern matching
2. For complex questions: LLM (Ollama) generates response
3. Response is formatted for Slack and sent back

### 4. Data Sources
- **Cost Data**: Service costs, project costs, daily totals
- **Anomaly Data**: Detected cost anomalies and alerts
- **Trend Data**: Cost trends and patterns

## 🚨 Troubleshooting

### Common Issues

1. **"RAG system not available"**
   - Ensure AI/ML pipeline has been run
   - Check Chroma database exists in `../ai_ml/chroma_db/`

2. **"Ollama connection error"**
   - Start Ollama: `ollama serve`
   - Check model availability: `ollama list`

3. **"Slack token invalid"**
   - Verify your tokens in `.env` file
   - Check app permissions and installation

4. **"No relevant data found"**
   - Run the Go framework to generate data
   - Check if JSON files exist in `../output/`

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python3 slack_bot.py
```

## 🔗 Integration

### With Existing Systems

The Slack bot integrates with:
- **Go Framework**: Uses JSON output for cost data
- **AI/ML Pipeline**: Shares Chroma database
- **Web Bot**: Same RAG system, different interface
- **Forecasting**: Can access forecast data

### Extending Functionality

To add new features:
1. Add new slash commands in `slack_bot.py`
2. Extend RAG integration in `rag_integration.py`
3. Add new response patterns in `generate_fast_response()`

## 📊 Performance

- **Response Time**: 1-5 seconds (fast mode), 5-15 seconds (LLM mode)
- **Concurrent Users**: Supports multiple simultaneous queries
- **Data Freshness**: Real-time access to latest cost data
- **Scalability**: Can handle high query volumes

## 🔮 Future Enhancements

- [ ] Interactive buttons and menus
- [ ] Scheduled cost reports
- [ ] Cost optimization suggestions
- [ ] Multi-workspace support
- [ ] Advanced analytics integration
- [ ] Custom alert configurations

## 📝 License

This project is part of the GCP Cost Monitoring system. 