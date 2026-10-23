# discord-server-manager (v1)

A Discord server manager bot use **discord.py**, and **Ollama**. Manage channels, roles, categories, and messages using natural language commands.

<img width="800" alt="Discord Server Manager preview" src="https://github.com/user-attachments/assets/cb9a7724-9404-43fd-a35c-caa67d3404fa" />

---

## Commands

`make install` = create virtual environment and install dependencies  
`make run` = start the Discord bot  
`make clean` = remove virtual environment and cached files  

## Prerequisites (Ollama)

If you don't have Ollama installed, install it with:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then pull the required model:

```bash
ollama pull qwen3:1.7b
```

## Setup

### 1. Install dependencies

Create a virtual environment and install the required dependencies:

```bash
make install
```

### 2. Configure your Discord Bot Token

The bot requires a Discord bot token to connect to your server. Create a `.env` file in the project root and add your token.

You can refer to [`.env.example`](.env.example) to see the required environment variable.

Create your `.env` file:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder with your actual Discord bot token:

```env
DISCORD_TOKEN=your_discord_bot_token
```

> **Need help getting your bot token?** Check out this [YouTube guide](https://www.youtube.com/watch?v=jqnul0VpBUQ).

### Discord Bot Permissions & Intents
In the [Discord Developer Portal](https://discord.com/developers/applications), navigate to **Bot**→**Privileged Gateway Intents** and enable all three:
- **Presence Intent**
- **Server Members Intent**
- **Message Content Intent**

<img width="800" alt="Discord Server Manager preview" src="https://github.com/user-attachments/assets/98893cee-03d7-4624-b5d9-02539466a607" />

## Run

```bash
make run
```

## Example Usage

Mention your bot in any authorized Discord channel:

### 1. Create a Category and Channel

```text
@server-manager create a category named "Projects" and add a text channel "updates" inside it
```

<img width="800" alt="Discord Server Manager preview" src="https://github.com/user-attachments/assets/85ba7327-d1c9-4693-913b-1d54c3f6873c" />

<img width="400" alt="Discord Server Manager preview" src="https://github.com/user-attachments/assets/22fb5090-34f0-46c8-b7a6-31a3f4915cf3" />

### 2. Delete Messages Sent by Bots

```text
@server-manager check the last 20 messages and delete all messages sent by bots
```

<img width="400" alt="image" src="https://github.com/user-attachments/assets/8cecb050-d77c-47d6-99cf-82dd59de6964" />

<img width="400" alt="image" src="https://github.com/user-attachments/assets/5c7f8483-55d0-4779-aec6-e2f7c33de213" />


