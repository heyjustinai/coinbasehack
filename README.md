# Coinbase Trading Bot with AgentKit

A trading bot that uses Coinbase's AgentKit to execute trades on Base mainnet.

## Prerequisites

- Node.js 18+
- Coinbase Developer Platform (CDP) API Key
- OpenAI API Key

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
Copy `.env.example` to `.env` and fill in your API keys:
```
CDP_API_KEY_NAME=your_api_key_name
CDP_API_KEY_PRIVATE=your_api_key_private
OPENAI_API_KEY=your_openai_api_key
```

## Usage

Run the trading bot:
```bash
npm start
```

The bot is configured to use the Base mainnet and can execute trades based on natural language commands through the LangChain + GPT-4 integration.

Example commands:
- "Buy 0.1 ETH at market price"
- "Sell 50 USDC for ETH"
- "Check my current balance"

## Features

- Natural language trading commands
- Integration with Coinbase's CDP API
- Secure wallet management
- Base mainnet support
- GPT-4 powered trade execution

## Security

Never share your API keys or private keys. The `.env` file is included in `.gitignore` to prevent accidental exposure of sensitive information.
