#!/usr/bin/env python3
"""
Claude Code Discord Agent
Uses claude CLI command for responses with full flag support
"""

import os
import json
import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Optional, List, Set, Dict

import discord
from discord.ext import commands, tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('claude-discord-bot-simple')

# Debug logger for terminal output
debug_logger = logging.getLogger('discord-debug')
debug_handler = logging.StreamHandler()
debug_handler.setLevel(logging.INFO)
debug_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%I:%M %p')
debug_handler.setFormatter(debug_formatter)
debug_logger.addHandler(debug_handler)
debug_logger.setLevel(logging.INFO)
debug_logger.propagate = False


class ConversationHistory:
    """Simple conversation history manager"""
    
    def __init__(self, max_messages: int = 5):
        self.max_messages = max_messages
        self.conversations: Dict[int, List[Dict]] = {}
    
    def add_message(self, channel_id: int, author: str, content: str, is_bot: bool = False):
        """Add message to history"""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
        
        self.conversations[channel_id].append({
            'author': author,
            'content': content,
            'is_bot': is_bot,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent messages
        if len(self.conversations[channel_id]) > self.max_messages:
            self.conversations[channel_id] = self.conversations[channel_id][-self.max_messages:]
    
    def get_context(self, channel_id: int) -> str:
        """Get conversation context as string"""
        if channel_id not in self.conversations or not self.conversations[channel_id]:
            return ""
        
        context_lines = ["Previous conversation:"]
        for msg in self.conversations[channel_id]:
            role = "Bot" if msg['is_bot'] else msg['author']
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines) + "\n\nCurrent message:"


class SimpleClaudeBot(commands.Bot):
    """Enhanced simple Discord bot using claude CLI"""
    
    def __init__(self, config: dict):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=config.get('command_prefix', '!'),
            intents=intents
        )
        
        self.config = config
        self.processing_messages: Set[int] = set()
        self.conversation_history = ConversationHistory(
            config.get('context_messages', 5)
        )
        
    async def setup_hook(self):
        """Setup bot hooks"""
        # Start periodic messages if enabled
        if self.config.get('random_messages_enabled', False):
            self.random_message_task.start()
            debug_logger.info("APP Started periodic message task")
        
    async def on_ready(self):
        """Bot is ready"""
        debug_logger.info(f"APP Bot ready: {self.user.name} (ID: {self.user.id})")
        logger.info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        logger.info(f'Monitor mentions: {self.config.get("monitor_mentions", True)}')
        logger.info(f'Monitor all messages: {self.config.get("monitor_all_messages", False)}')
        logger.info(f'Context messages: {self.config.get("context_messages", 5)}')
        logger.info(f'Claude flags: {self.config.get("claude_flags", [])}')
        if self.config.get('allowed_channels'):
            logger.info(f'Allowed channels: {self.config["allowed_channels"]}')
        if self.config.get('random_messages_enabled'):
            logger.info(f'Random messages every {self.config.get("random_message_interval", 60)} minutes')
    
    async def should_respond(self, message: discord.Message) -> bool:
        """Check if bot should respond"""
        # Don't respond to self
        if message.author == self.user:
            return False
        
        # Check if already processing
        if message.id in self.processing_messages:
            return False
        
        # Check allowed channels
        allowed_channels = self.config.get('allowed_channels', [])
        if allowed_channels and str(message.channel.id) not in allowed_channels:
            return False
        
        # Check mentions
        if self.config.get('monitor_mentions', True) and self.user.mentioned_in(message):
            return True
        
        # Check all messages
        if self.config.get('monitor_all_messages', False):
            return True
        
        return False
    
    async def on_message(self, message: discord.Message):
        """Handle messages"""
        # Debug output for all messages
        if not message.author.bot:
            debug_logger.info(f"MSG RECEIVED: #{message.channel.name} {message.author.name}: {message.content[:100]}{'...' if len(message.content) > 100 else ''}")
        
        if not await self.should_respond(message):
            return
        
        debug_logger.info(f"MSG PROCESSING: Responding to message from {message.author.name}")
        
        # Mark as processing
        self.processing_messages.add(message.id)
        
        try:
            # Show typing
            async with message.channel.typing():
                await self.process_message(message)
        except Exception as e:
            debug_logger.error(f"ERROR: Processing message: {e}")
            logger.error(f"Error processing message: {e}")
        finally:
            self.processing_messages.discard(message.id)
    
    async def get_claude_response(self, prompt: str, context: str = "") -> str:
        """Get response using claude CLI with configurable flags"""
        try:
            # Build command with configurable flags
            cmd = ['claude']
            
            # Add configured flags
            claude_flags = self.config.get('claude_flags', [])
            cmd.extend(claude_flags)
            
            # Always add --print at the end
            if '--print' not in claude_flags and '-p' not in claude_flags:
                cmd.append('--print')
            
            # Build full prompt with context
            full_prompt = f"{context}\n{prompt}" if context else prompt
            cmd.append(full_prompt)
            
            debug_logger.info(f"CLAUDE: Running command: {' '.join(cmd[:3])} [prompt]")
            
            # Run command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                debug_logger.error(f"CLAUDE: Execution error: {error_msg}")
                logger.error(f"Claude error: {error_msg}")
                return "Sorry, I encountered an error."
            
            response = stdout.decode().strip()
            debug_logger.info(f"CLAUDE: Response length: {len(response)} chars")
            
            return response
            
        except Exception as e:
            debug_logger.error(f"ERROR: Claude command failed: {e}")
            logger.error(f"Error calling claude: {e}")
            return "Sorry, I couldn't process your request."
    
    async def process_message(self, message: discord.Message):
        """Process message and respond"""
        # Clean content
        content = message.content
        for mention in message.mentions:
            if mention == self.user:
                content = content.replace(f'<@{mention.id}>', '').strip()
                content = content.replace(f'<@!{mention.id}>', '').strip()
        
        # Add to conversation history
        self.conversation_history.add_message(
            message.channel.id,
            message.author.name,
            content
        )
        
        # Get conversation context if enabled
        context = ""
        if self.config.get('context_messages', 5) > 0:
            context = self.conversation_history.get_context(message.channel.id)
        
        # Get response
        debug_logger.info(f"CLAUDE: Sending prompt (with context: {len(context) > 0})")
        response = await self.get_claude_response(content, context)
        
        # Add bot response to history
        self.conversation_history.add_message(
            message.channel.id,
            self.user.name,
            response,
            is_bot=True
        )
        
        # Send response
        max_length = self.config.get('max_message_length', 2000)
        if len(response) <= max_length:
            sent_msg = await message.reply(response)
            debug_logger.info(f"MSG SENT: Reply to {message.author.name}: {response[:100]}{'...' if len(response) > 100 else ''}")
        else:
            # Split into chunks
            chunks = [response[i:i+max_length] 
                     for i in range(0, len(response), max_length)]
            sent_msg = await message.reply(chunks[0])
            debug_logger.info(f"MSG SENT: Long reply to {message.author.name} ({len(chunks)} parts)")
            for chunk in chunks[1:]:
                await message.channel.send(chunk)
    
    @tasks.loop(minutes=1)
    async def random_message_task(self):
        """Send random messages at configured intervals"""
        current_time = datetime.now()
        interval_minutes = self.config.get('random_message_interval', 60)
        
        # Check if it's time to send (every N minutes)
        if current_time.minute % interval_minutes != 0:
            return
        
        channels = self.config.get('random_message_channels', [])
        if not channels:
            return
        
        for channel_id in channels:
            try:
                channel = self.get_channel(int(channel_id))
                if not channel:
                    debug_logger.warning(f"RANDOM: Channel {channel_id} not found")
                    continue
                
                # Get random message prompt
                prompt = self.config.get('random_message_prompt', 
                    "Generate an interesting and helpful message for this Discord channel.")
                
                debug_logger.info(f"RANDOM: Generating message for #{channel.name}")
                
                response = await self.get_claude_response(prompt)
                
                await channel.send(response)
                debug_logger.info(f"RANDOM: Sent message to #{channel.name}")
                
            except Exception as e:
                debug_logger.error(f"ERROR: Random message failed: {e}")
    
    @random_message_task.before_loop
    async def before_random_message_task(self):
        """Wait until bot is ready"""
        await self.wait_until_ready()


async def main():
    """Main function"""
    # Load config
    config_path = os.getenv('BOT_CONFIG_PATH', 'config.json')
    
    if not os.path.exists(config_path):
        # Create example config
        example = {
            "discord_token": "YOUR_DISCORD_BOT_TOKEN",
            "command_prefix": "!",
            "monitor_mentions": True,
            "monitor_all_messages": False,
            "allowed_channels": [],
            "max_message_length": 2000,
            "context_messages": 5,
            "claude_flags": ["--verbose"],
            "random_messages_enabled": False,
            "random_message_interval": 60,
            "random_message_channels": [],
            "random_message_prompt": "Generate an interesting and helpful message for this Discord channel."
        }
        
        with open('config.example.json', 'w') as f:
            json.dump(example, f, indent=2)
        
        logger.error(f"Config not found: {config_path}")
        logger.info("Created config.example.json - rename and update it")
        return
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
    # Create and run bot
    bot = SimpleClaudeBot(config)
    
    try:
        await bot.start(config['discord_token'])
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.close()
    except Exception as e:
        logger.error(f"Bot error: {e}")
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())