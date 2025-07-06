"""Discord bot service for handling commands in channels."""

import discord
from discord.ext import commands
import asyncio
import logging
from typing import Optional, Dict, Any

from ..core.service import BaseService, ServiceResponse
from ..core.config import settings
from ..core.service_manager import service_manager


class DiscordBotService(BaseService):
    """Discord bot service for handling channel commands."""

    def __init__(self):
        super().__init__("discord_bot")
        self.bot: Optional[commands.Bot] = None
        self.bot_token = settings.discord_bot_token
        self.command_channel = settings.discord_command_channel or "bot-commands"
        self.guild_id = settings.discord_guild_id
        self._bot_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the Discord bot."""
        if not self.bot_token or self.bot_token == "YOUR_BOT_TOKEN_HERE":
            self.logger.error("Discord bot token not configured. Please set DISCORD_BOT_TOKEN in your .env file")
            return False

        try:
            # Create bot with minimal intents (no privileged intents required)
            intents = discord.Intents.default()
            intents.message_content = True  # This is the only privileged intent we need
            # Don't request other privileged intents
            intents.members = False
            intents.presences = False
            
            self.bot = commands.Bot(
                command_prefix='!',
                intents=intents,
                case_insensitive=True,
                help_command=None  # Disable default help command
            )

            # Set up event handlers and commands
            self._setup_events()
            self._setup_commands()

            # Start the bot in a background task
            self._bot_task = asyncio.create_task(self._run_bot())
            
            # Wait a moment for the bot to start connecting
            await asyncio.sleep(2)
            
            self.logger.info("Discord bot task started")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to start Discord bot: {e}")
            return False

    async def health_check(self) -> ServiceResponse:
        """Check Discord bot health."""
        if not self.bot:
            return ServiceResponse(
                success=False,
                message="Discord bot not initialized"
            )
        
        if not self.bot.is_ready():
            return ServiceResponse(
                success=False,
                message="Discord bot not connected/ready"
            )

        return ServiceResponse(
            success=True,
            message="Discord bot is connected and ready",
            data={
                "bot_name": str(self.bot.user),
                "guild_count": len(self.bot.guilds),
                "command_channel": self.command_channel,
                "latency": round(self.bot.latency * 1000, 2)  # ms
            }
        )

    async def cleanup(self) -> None:
        """Cleanup Discord bot resources."""
        if self._bot_task and not self._bot_task.done():
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass
        
        if self.bot and not self.bot.is_closed():
            await self.bot.close()

    async def _run_bot(self):
        """Run the Discord bot."""
        try:
            await self.bot.start(self.bot_token)
        except discord.LoginFailure:
            self.logger.error("Bot login failed - check your bot token")
        except discord.PrivilegedIntentsRequired:
            self.logger.error("Privileged intents required - please enable Message Content Intent in Discord Developer Portal")
        except Exception as e:
            self.logger.error(f"Bot crashed: {e}")

    def _setup_events(self):
        """Set up Discord bot events."""
        
        @self.bot.event
        async def on_ready():
            self.logger.info(f"✅ Bot logged in as {self.bot.user}")
            
            # List all guilds the bot is in
            guild_names = [guild.name for guild in self.bot.guilds]
            self.logger.info(f"Bot is in {len(self.bot.guilds)} guilds: {', '.join(guild_names)}")
            
            # Find and log the command channel
            found_channels = []
            for guild in self.bot.guilds:
                channel = discord.utils.get(guild.channels, name=self.command_channel)
                if channel:
                    found_channels.append(f"#{channel.name} in {guild.name}")
            
            if found_channels:
                self.logger.info(f"Found command channels: {', '.join(found_channels)}")
            else:
                self.logger.warning(f"Command channel '#{self.command_channel}' not found in any guild")

        @self.bot.event
        async def on_guild_join(guild):
            self.logger.info(f"Bot joined guild: {guild.name}")

        @self.bot.event
        async def on_message(message):
            # Don't respond to ourselves
            if message.author == self.bot.user:
                return

            # Only respond in the command channel
            if message.channel.name != self.command_channel:
                return

            # Log command attempts
            if message.content.startswith('!'):
                self.logger.info(f"Command received from {message.author}: {message.content}")

            # Process commands
            await self.bot.process_commands(message)

        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send(f"❌ Unknown command. Type `!commands` for available commands.")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Missing required argument. Type `!commands` for help.")
            else:
                await ctx.send(f"❌ Error: {error}")
                self.logger.error(f"Command error in {ctx.command}: {error}")

    def _setup_commands(self):
        """Set up Discord bot commands."""
        
        @self.bot.command(name='ping')
        async def ping_command(ctx):
            """Check if bot is responsive."""
            latency = round(self.bot.latency * 1000, 2)
            await ctx.send(f"🏓 Pong! Latency: {latency}ms")

        @self.bot.command(name='scrape')
        async def scrape_command(ctx, scraper_name: str = "techcrunch", *, url: str = None):
            """Scrape trends and send a report.
            
            Usage: !scrape [scraper_name] [url]
            Example: !scrape techcrunch
            """
            await ctx.send(f"🕷️ Starting scrape with {scraper_name}...")
            
            try:
                # Get scraper service
                scraper_service = service_manager.get_service("scraper")
                if not scraper_service:
                    await ctx.send("❌ Scraper service not available")
                    return

                # Scrape trends
                result = await scraper_service.scrape_trends(scraper_name, url)
                
                if result.success:
                    # Send results to the webhook (detailed report)
                    discord_service = service_manager.get_service("discord")
                    if discord_service:
                        await self._send_scrape_report(discord_service, result.data, "detailed")
                    
                    await ctx.send(f"✅ Scraped {result.data.get('total_count', 0)} trends! Check the scraping channel for details.")
                else:
                    await ctx.send(f"❌ Scraping failed: {result.message}")
                    
            except Exception as e:
                await ctx.send(f"❌ Error during scraping: {str(e)}")
                self.logger.error(f"Scrape command error: {e}")

        @self.bot.command(name='quick')
        async def quick_scrape(ctx, scraper_name: str = "techcrunch"):
            """Quick scrape with summary report.
            
            Usage: !quick [scraper_name]
            """
            await ctx.send(f"⚡ Quick scraping {scraper_name}...")
            
            try:
                scraper_service = service_manager.get_service("scraper")
                if not scraper_service:
                    await ctx.send("❌ Scraper service not available")
                    return

                result = await scraper_service.scrape_trends(scraper_name)
                
                if result.success:
                    discord_service = service_manager.get_service("discord")
                    if discord_service:
                        await self._send_scrape_report(discord_service, result.data, "summary")
                    
                    await ctx.send(f"✅ Quick scrape complete! Found {result.data.get('total_count', 0)} trends.")
                else:
                    await ctx.send(f"❌ Quick scrape failed: {result.message}")
                    
            except Exception as e:
                await ctx.send(f"❌ Error: {str(e)}")

        @self.bot.command(name='status')
        async def status_command(ctx):
            """Check system status."""
            try:
                # Get service health
                health_results = await service_manager.health_check_all()
                
                status_text = "📊 **System Status**\n"
                for service_name, result in health_results.items():
                    status_icon = "✅" if result.success else "❌"
                    status_text += f"{status_icon} {service_name}: {result.message}\n"
                
                await ctx.send(status_text)
                
            except Exception as e:
                await ctx.send(f"❌ Error checking status: {str(e)}")

        @self.bot.command(name='commands')
        async def commands_list(ctx):
            """Show available commands."""
            help_text = """
🤖 **Quillix Bot Commands**

`!ping` - Check bot responsiveness
`!scrape [scraper] [url]` - Full scrape with detailed report
`!quick [scraper]` - Quick scrape with summary
`!status` - Check system status
`!commands` - Show this command list

**Available Scrapers:** techcrunch

**Examples:**
• `!ping` - Test bot connection
• `!scrape` - Scrape TechCrunch with full report
• `!quick techcrunch` - Quick TechCrunch summary
            """
            await ctx.send(help_text)

    async def _send_scrape_report(self, discord_service, scrape_data: Dict[str, Any], style: str = "detailed"):
        """Send scrape report using the existing reporting functions."""
        try:
            from ..routes.scraper_routes import _send_consolidated_report
            await _send_consolidated_report(discord_service, scrape_data, style)
        except ImportError:
            # Fallback if import fails
            trends_count = scrape_data.get('total_count', 0)
            source = scrape_data.get('source', 'Unknown')
            
            from ..services.discord_service import DiscordMessage
            message = DiscordMessage(
                content=f"📊 Scraping complete! Found {trends_count} trends from {source}",
                username="Quillix Bot"
            )
            await discord_service.send_message(message)