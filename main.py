import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.all()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.last_sync_file = 'last_sync.json'
        
    async def setup_hook(self):
        # Load all cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Loaded cog: {filename[:-3]}')
                except Exception as e:
                    print(f'❌ Failed to load cog {filename[:-3]}: {e}')
        
        # Auto-sync only if it's been more than 23 hours (to avoid rate limits)
        # and only in development mode
        if os.getenv('AUTO_SYNC') == 'true':
            if self.should_sync():
                try:
                    synced = await self.tree.sync()
                    print(f"🔄 Auto-synced {len(synced)} command(s)")
                    self.save_sync_time()
                except Exception as e:
                    print(f"❌ Error auto-syncing commands: {e}")
            else:
                print("⏳ Skipping auto-sync (too recent or rate limited)")

    def should_sync(self):
        """Check if enough time has passed since last sync"""
        try:
            if os.path.exists(self.last_sync_file):
                with open(self.last_sync_file, 'r') as f:
                    data = json.load(f)
                    last_sync = datetime.fromisoformat(data['last_sync'])
                    # Only sync if it's been more than 23 hours
                    return datetime.now() - last_sync > timedelta(hours=23)
            return True  # No previous sync recorded
        except Exception:
            return True  # If we can't read the file, allow sync

    def save_sync_time(self):
        """Save the current time as last sync time"""
        try:
            with open(self.last_sync_file, 'w') as f:
                json.dump({'last_sync': datetime.now().isoformat()}, f)
        except Exception as e:
            print(f"Warning: Could not save sync time: {e}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📊 Bot is in {len(bot.guilds)} guilds')
    
    # Display loaded commands
    slash_commands = len(bot.tree.get_commands())
    prefix_commands = len([cmd for cmd in bot.commands if not cmd.hidden])
    print(f'⚡ {slash_commands} slash commands loaded')
    print(f'🔧 {prefix_commands} prefix commands loaded')

@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx, guild_only: bool = False, force: bool = False):
    """
    Manually sync slash commands with rate limit protection
    
    Usage:
    !sync - Global sync (checks rate limits)
    !sync true - Guild-only sync (faster, for testing)
    !sync false true - Force global sync (ignores rate limits)
    """
    
    # Check rate limits unless forcing
    if not force and not guild_only and not bot.should_sync():
        last_sync_info = "recently"
        try:
            if os.path.exists(bot.last_sync_file):
                with open(bot.last_sync_file, 'r') as f:
                    data = json.load(f)
                    last_sync = datetime.fromisoformat(data['last_sync'])
                    hours_ago = (datetime.now() - last_sync).total_seconds() / 3600
                    last_sync_info = f"{hours_ago:.1f} hours ago"
        except Exception:
            pass
            
        embed = discord.Embed(
            title="⚠️ Rate Limit Protection",
            description=f"Last sync was {last_sync_info}. Discord limits global syncs to once per day.",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Options",
            value="• `!sync true` - Sync to this guild only (no rate limit)\n• `!sync false true` - Force global sync (ignore rate limit)",
            inline=False
        )
        return await ctx.send(embed=embed)
    
    try:
        if guild_only:
            # Sync to current guild only (faster, good for testing)
            synced = await bot.tree.sync(guild=ctx.guild)
            embed = discord.Embed(
                title="✅ Guild Sync Complete",
                description=f"Synced {len(synced)} command(s) to **{ctx.guild.name}**",
                color=discord.Color.green()
            )
        else:
            # Global sync (slower, for production)
            synced = await bot.tree.sync()
            bot.save_sync_time()  # Save sync time for rate limiting
            embed = discord.Embed(
                title="✅ Global Sync Complete",
                description=f"Synced {len(synced)} command(s) globally",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Note",
                value="Global syncs are limited to once per day by Discord.",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except discord.HTTPException as e:
        if e.status == 429:  # Rate limited
            embed = discord.Embed(
                title="🚫 Rate Limited",
                description="Discord is rate limiting slash command syncs. Try again later or use guild-only sync.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Alternative",
                value="Use `!sync true` to sync to this guild only (no rate limit)",
                inline=False
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'❌ HTTP Error syncing commands: {e}')
    except Exception as e:
        await ctx.send(f'❌ Error syncing commands: {e}')

@bot.command()
@commands.has_permissions(administrator=True)
async def listcommands(ctx):
    """List all registered slash commands"""
    commands_list = []
    for command in bot.tree.get_commands():
        commands_list.append(f"**/{command.name}** - {command.description}")
    
    if commands_list:
        # Split commands into chunks if too many
        chunks = [commands_list[i:i+10] for i in range(0, len(commands_list), 10)]
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"📋 Registered Slash Commands {f'(Page {i+1})' if len(chunks) > 1 else ''}",
                description="\n".join(chunk),
                color=discord.Color.blue()
            )
            embed.set_footer(
                text="Cephalo • Bot Commands",
                icon_url="https://i.imgur.com/pKBQZJE.png"
            )
            
            if i == 0:
                embed.add_field(
                    name="Total Commands",
                    value=f"{len(commands_list)} slash commands registered",
                    inline=False
                )
            
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="📋 No Slash Commands",
            description="No slash commands registered yet. Try running `!sync` first.",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Tip",
            value="Use `!sync true` for guild-only sync (faster) or `!sync` for global sync",
            inline=False
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def debugcogs(ctx):
    """Debug cog commands and sync status"""
    debug_info = []
    
    # Bot status
    debug_info.append(f"**Bot Status:**")
    debug_info.append(f"- Guilds: {len(bot.guilds)}")
    debug_info.append(f"- Latency: {bot.latency * 1000:.1f}ms")
    
    # Sync status
    last_sync = "Never"
    try:
        if os.path.exists(bot.last_sync_file):
            with open(bot.last_sync_file, 'r') as f:
                data = json.load(f)
                last_sync_dt = datetime.fromisoformat(data['last_sync'])
                hours_ago = (datetime.now() - last_sync_dt).total_seconds() / 3600
                last_sync = f"{hours_ago:.1f} hours ago"
    except Exception:
        pass
    
    debug_info.append(f"- Last Global Sync: {last_sync}")
    debug_info.append("")
    
    # List all loaded cogs
    debug_info.append("**Loaded Cogs:**")
    for name, cog in bot.cogs.items():
        debug_info.append(f"- {name}")
        
        # Check for app commands in each cog
        cog_commands = []
        for attr_name in dir(cog):
            attr = getattr(cog, attr_name)
            if isinstance(attr, app_commands.Command):
                cog_commands.append(f"  - /{attr.name}")
        
        if cog_commands:
            debug_info.extend(cog_commands)
    
    debug_info.append("")
    
    # List all tree commands
    debug_info.append("**Registered Slash Commands:**")
    tree_commands = bot.tree.get_commands()
    if tree_commands:
        for command in tree_commands:
            debug_info.append(f"- /{command.name} - {command.description}")
    else:
        debug_info.append("- None (try running !sync)")
    
    # Create and send embed
    embed = discord.Embed(
        title="🔧 Bot Debug Information",
        description="\n".join(debug_info),
        color=discord.Color.gold()
    )
    embed.set_footer(
        text="Cephalo • Debug Info",
        icon_url="https://i.imgur.com/pKBQZJE.png"
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension):
    """Reload a cog (does not auto-sync)"""
    try:
        await bot.reload_extension(f'cogs.{extension}')
        embed = discord.Embed(
            title="✅ Cog Reloaded",
            description=f"Successfully reloaded **{extension}**",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Next Step",
            value="Use `!sync true` to sync commands to this guild, or `!sync` for global sync",
            inline=False
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Reload Failed",
            description=f"Error reloading **{extension}**: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    """Load a cog"""
    try:
        await bot.load_extension(f'cogs.{extension}')
        embed = discord.Embed(
            title="✅ Cog Loaded",
            description=f"Successfully loaded **{extension}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Load Failed",
            description=f"Error loading **{extension}**: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension):
    """Unload a cog"""
    try:
        await bot.unload_extension(f'cogs.{extension}')
        embed = discord.Embed(
            title="✅ Cog Unloaded",
            description=f"Successfully unloaded **{extension}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Unload Failed",
            description=f"Error unloading **{extension}**: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Add error handling for app commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    """Global error handler for slash commands"""
    if isinstance(error, app_commands.CommandOnCooldown):
        embed = discord.Embed(
            title="⏱️ Command on Cooldown",
            description=f"Try again in {error.retry_after:.1f} seconds",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title="🚫 Missing Permissions",
            description="You don't have permission to use this command",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="❌ Command Error",
            description="An error occurred while processing your command",
            color=discord.Color.red()
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"Slash command error: {error}")

if __name__ == "__main__":
    print("🚀 Starting Cephalo Discord Bot...")
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please check your .env file")
        import sys
        sys.exit(1)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ ERROR: Invalid Discord token!")
        print("Please check your DISCORD_TOKEN in the .env file")
    except Exception as e:
        print(f"❌ ERROR: Bot crashed with exception: {e}")
        import traceback
        traceback.print_exc()