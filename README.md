# Claude Code Discord Agent

A Discord bot that uses Claude Code (`claude --print`) with full flag support.

## !!! USE WITH CAUTION !!! THIS ALLOWS DISCORD MESSAGES TO CONTROL YOUR COMPUTER !!!
<img width="794" height="104" alt="image" src="https://github.com/user-attachments/assets/7dd836d9-3b7a-46c6-b3cb-a86d6947c144" />


## Features

- **Claude CLI Integration**: Uses `claude` command with full flag support
- **Conversation Memory**: Maintains context across messages
- **Debug Output**: Real-time terminal logging of all activity
- **Periodic Messages**: Send random messages on schedule
- **Flexible Monitoring**: @mentions or all messages in channels
- **Channel Filtering**: Restrict to specific channels
- **Message Splitting**: Handles long responses automatically

## Quick Start

1. **Install Claude Code CLI**:
   ```bash
   npm install -g @anthropic/claude-code
   ```

2. Set up your Discord bot:
   - Create a new application at [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a bot and copy the token
   - Enable required privileged intents:
     - MESSAGE CONTENT INTENT
     - PRESENCE INTENT
     - SERVER MEMBERS INTENT
   - Invite the bot to your server using OAuth2 URL Generator

3. **Install Discord.py**:
   ```bash
   pip install discord.py
   ```

4. **Create config.json**:
   ```json
   {
     "discord_token": "YOUR_DISCORD_BOT_TOKEN",
     "command_prefix": "!",
     "monitor_mentions": true,
     "monitor_all_messages": true,
     "allowed_channels": [],
     "max_message_length": 2000,
     "context_messages": 5,
     "claude_flags": ["--verbose"],
     "random_messages_enabled": false,
     "random_message_interval": 60,
     "random_message_channels": [],
     "random_message_prompt": "Generate an interesting message for this Discord channel."
   }
   ```

5. **Run the bot**:
   ```bash
   python claude_code-discord_agent.py
   ```

## Configuration

### Basic Settings
- `discord_token`: Your Discord bot token (required)
- `command_prefix`: Bot prefix (default: "!")
- `monitor_mentions`: Respond to @mentions (default: true)
- `monitor_all_messages`: Respond to all messages in allowed channels (default: false)  
- `allowed_channels`: List of channel IDs (empty = all channels)
- `max_message_length`: Max Discord message length (default: 2000)

### New Features
- `context_messages`: Number of previous messages to include as context (default: 5, 0 = disabled)
- `claude_flags`: Array of additional Claude CLI flags (e.g., `["--verbose", "--model", "opus", "--allowedTools", "Write"]`) 
  - note: the `"--allowedTools", "Write"` (and similar) flags allow Claude Code to write to your filesystem!!! USE WITH CAUTION!
- `random_messages_enabled`: Enable periodic random messages (default: false)
- `random_message_interval`: Minutes between random messages (default: 60)
- `random_message_channels`: Channel IDs for random messages
- `random_message_prompt`: Prompt for generating random messages

## Usage

### Mention the bot:
```
@YourBot What's the weather like?
```

### Or monitor all messages:
Set `"monitor_all_messages": true` and add channel IDs to `"allowed_channels"`.

### With conversation memory:
```json
{
  "context_messages": 10
}
```

### With periodic messages:
```json
{
  "random_messages_enabled": true,
  "random_message_interval": 30,
  "random_message_channels": ["1234567890"],
  "random_message_prompt": "Share a programming tip or interesting fact."
}
```

### With custom Claude flags:
```json
{
  "claude_flags": ["--model", "opus", "--verbose", "--max-turns", "3"]
}
```

## Debug Output

The bot shows real-time activity in the terminal:

```
[1:33 PM] APP Bot ready: ClaudeBot (ID: 1234567890)
[1:34 PM] MSG RECEIVED: #general john_doe: Hey @ClaudeBot, how's it going?
[1:34 PM] MSG PROCESSING: Responding to message from john_doe
[1:34 PM] CLAUDE: Running command: claude --verbose --print [prompt]
[1:34 PM] CLAUDE: Response length: 45 chars
[1:34 PM] MSG SENT: Reply to john_doe: Hey there! I'm doing great, thanks for asking!
[1:35 PM] RANDOM: Generating message for #general
[1:35 PM] RANDOM: Sent message to #general
```

## One-Liner Run

```bash
DISCORD_TOKEN=your_token python claude_code-discord_agent.py
```

## Minimal Setup Script

```bash
#!/bin/bash
# setup.sh
pip install discord.py
echo '{"discord_token":"'$1'","monitor_mentions":true}' > config.json
python claude_code-discord_agent.py
```

Run with: `./setup.sh YOUR_DISCORD_TOKEN`

## claude_flags (put in config.json)
### CLI commands

| Command | Description | Example |
|---------|-------------|---------|
| `claude -p "query"` | Query via SDK, then exit | `claude -p "explain this function"` |
| `cat file \| claude -p "query"` | Process piped content | `cat logs.txt \| claude -p "explain"` |
| `claude -c -p "query"` | Continue via SDK | `claude -c -p "Check for type errors"` |
| `claude -r "<session-id>" "query"` | Resume session by ID | `claude -r "abc123" "Finish this PR"` |
| `claude update` | Update to latest version | `claude update` |
| `claude mcp` | Configure Model Context Protocol (MCP) servers | See the Claude Code MCP documentation |
### CLI flags

| Flag | Description | Example |
|------|-------------|---------|
| `--add-dir` | Add additional working directories for Claude to access (validates each path exists as a directory) | `claude --add-dir ../apps ../lib` |
| `--allowedTools` | A list of tools that should be allowed without prompting the user for permission, in addition to `settings.json` files | `"Bash(git log:*)"` `"Bash(git diff:*)"` `"Read"` |
| `--disallowedTools` | A list of tools that should be disallowed without prompting the user for permission, in addition to `settings.json` files | `"Bash(git log:*)"` `"Bash(git diff:*)"` `"Edit"` |
| `--print`, `-p` | Print response without interactive mode (see SDK documentation for programmatic usage details) | `claude -p "query"` |
| `--output-format` | Specify output format for print mode (options: `text`, `json`, `stream-json`) | `claude -p "query" --output-format json` |
| `--input-format` | Specify input format for print mode (options: `text`, `stream-json`) | `claude -p --output-format json --input-format stream-json` |
| `--verbose` | Enable verbose logging, shows full turn-by-turn output (helpful for debugging in both print and interactive modes) | `claude --verbose` |
| `--max-turns` | Limit the number of agentic turns in non-interactive mode | `claude -p --max-turns 3 "query"` |
| `--model` | Sets the model for the current session with an alias or full model name | `claude --model claude-sonnet-4-20250514` |
| `--permission-mode` | Begin in a specified permission mode | `claude --permission-mode plan` |
| `--permission-prompt-tool` | Specify an MCP tool to handle permission prompts in non-interactive mode | `claude -p --permission-prompt-tool mcp_auth_tool "query"` |
| `--resume` | Resume a specific session by ID, or by choosing in interactive mode | `claude --resume abc123 "query"` |
| `--continue` | Load the most recent conversation in the current directory | `claude --continue` |
| `--dangerously-skip-permissions` | Skip permission prompts (use with caution) | `claude --dangerously-skip-permissions` |

