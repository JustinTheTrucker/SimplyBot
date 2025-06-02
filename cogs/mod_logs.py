import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ModLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Try to get mod log channel name from environment variable, or use default
        self.mod_log_channel_name = os.getenv("MOD_LOG_CHANNEL", "mod-logs")
        # Try to get mod log channel ID from environment variable (if set)
        self.mod_log_channel_id = None
        if os.getenv("MOD_LOG_CHANNEL_ID"):
            try:
                self.mod_log_channel_id = int(os.getenv("MOD_LOG_CHANNEL_ID"))
            except ValueError:
                pass  # If it's not a valid integer, ignore it
        
        # Staff server support
        self.staff_server_id = None
        if os.getenv("STAFF_SERVER_ID"):
            try:
                self.staff_server_id = int(os.getenv("STAFF_SERVER_ID"))
            except ValueError:
                pass  # If it's not a valid integer, ignore it
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event"""
        print("🎭 Delirium Den Mod Logs cog loaded successfully")
        
    async def get_mod_log_channel(self, guild):
        """Get the mod log channel either in the current guild or in the staff server if configured"""
        # First check if we should use the staff server
        staff_guild = None
        if self.staff_server_id:
            staff_guild = self.bot.get_guild(self.staff_server_id)
        
        # Determine which guild to use (staff guild if available, otherwise current guild)
        target_guild = staff_guild if staff_guild else guild
        
        # Try using the ID if available
        if self.mod_log_channel_id:
            channel = target_guild.get_channel(self.mod_log_channel_id)
            if channel:
                return channel
        
        # If ID failed or isn't set, try using the name
        channel = discord.utils.get(target_guild.text_channels, name=self.mod_log_channel_name)
        return channel
    
    async def perform_moderation_action(self, ctx_or_interaction, user, action_type, reason):
        """Actually perform the moderation action"""
        # Get guild from either context or interaction
        guild = ctx_or_interaction.guild if hasattr(ctx_or_interaction, 'guild') else ctx_or_interaction.guild
        author = ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author
        
        try:
            if action_type == "ban":
                # Check if user is in the guild
                member = guild.get_member(user.id)
                if member:
                    await member.ban(reason=f"[{author}] {reason}")
                else:
                    # Ban by user ID (for users not in server)
                    await guild.ban(user, reason=f"[{author}] {reason}")
                return True, "User banned successfully"
                
            elif action_type == "kick":
                member = guild.get_member(user.id)
                if not member:
                    return False, "User is not in the server"
                await member.kick(reason=f"[{author}] {reason}")
                return True, "User kicked successfully"
                
            elif action_type == "mute":
                member = guild.get_member(user.id)
                if not member:
                    return False, "User is not in the server"
                
                # Timeout for 1 hour by default (you can modify this)
                timeout_duration = timedelta(hours=1)
                await member.timeout(timeout_duration, reason=f"[{author}] {reason}")
                return True, f"User muted for {timeout_duration}"
                
            elif action_type == "unban":
                try:
                    await guild.unban(user, reason=f"[{author}] {reason}")
                    return True, "User unbanned successfully"
                except discord.NotFound:
                    return False, "User is not banned"
                    
            elif action_type in ["warn", "note"]:
                # These are log-only actions
                return True, f"{action_type.title()} logged successfully"
                
            else:
                return False, "Unknown action type"
                
        except discord.Forbidden:
            return False, "I don't have permission to perform this action"
        except discord.HTTPException as e:
            return False, f"Discord API error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    async def create_mod_log_embed(self, user, action_type, reason, moderator, guild, action_success, action_message):
        """Create a moderation log embed"""
        # Colors for different action types
        action_colors = {
            "warn": discord.Color.gold(),
            "mute": discord.Color.orange(),
            "kick": discord.Color.red(),
            "ban": discord.Color.dark_red(),
            "unban": discord.Color.green(),
            "note": discord.Color.light_grey()
        }
        
        # Icons for different action types
        action_icons = {
            "warn": "⚠️",
            "mute": "🔇",
            "kick": "👢",
            "ban": "🔨",
            "unban": "🔓",
            "note": "📝"
        }
        
        # Create the log embed
        log_embed = discord.Embed(
            title=f"{action_icons[action_type]} Moderation Action: {action_type.upper()}",
            description=f"A moderation action has been taken against a user.",
            color=action_colors[action_type],
            timestamp=datetime.utcnow()
        )
        
        # Add user information
        log_embed.add_field(
            name="User",
            value=f"{user.mention} ({user.name}#{user.discriminator})",
            inline=True
        )
        
        # Add user ID for reference
        log_embed.add_field(
            name="User ID",
            value=f"`{user.id}`",
            inline=True
        )
        
        # Add moderator information
        log_embed.add_field(
            name="Moderator",
            value=f"{moderator.mention} ({moderator.name}#{moderator.discriminator})",
            inline=True
        )
        
        # Add reason
        log_embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        # Add action status
        if action_success:
            log_embed.add_field(
                name="Status",
                value=f"✅ {action_message}",
                inline=False
            )
        else:
            log_embed.add_field(
                name="Status",
                value=f"⚠️ Action logged but not executed: {action_message}",
                inline=False
            )
        
        # Include user's join date if available (and user is/was in server)
        member = guild.get_member(user.id)
        if member and hasattr(member, 'joined_at') and member.joined_at:
            join_date = member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            log_embed.add_field(
                name="User Joined",
                value=join_date,
                inline=True
            )
        
        # Add account creation date
        creation_date = user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        log_embed.add_field(
            name="Account Created",
            value=creation_date,
            inline=True
        )
        
        # Add source server information (for cross-server logging)
        if self.staff_server_id and guild.id != self.staff_server_id:
            log_embed.add_field(
                name="Source Server",
                value=f"{guild.name} (ID: {guild.id})",
                inline=False
            )
        
        # Add case ID (timestamp-based for uniqueness)
        case_id = int(datetime.utcnow().timestamp())
        log_embed.set_footer(
            text=f"Delirium Den • Case ID: {case_id}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        # Set thumbnail to user's avatar
        log_embed.set_thumbnail(url=user.display_avatar.url)
        
        return log_embed, case_id
    
    async def send_mod_log(self, ctx_or_interaction, user, action_type, reason):
        """Send moderation log and perform action"""
        guild = ctx_or_interaction.guild
        moderator = ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author
        
        # Find the mod-logs channel
        mod_logs_channel = await self.get_mod_log_channel(guild)
        
        if not mod_logs_channel:
            error_msg = f"❌ Could not find a channel named `{self.mod_log_channel_name}`. Please create this channel first or set the MOD_LOG_CHANNEL environment variable."
            if hasattr(ctx_or_interaction, 'response'):
                await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(error_msg)
            return
        
        # Perform the actual moderation action first
        action_success, action_message = await self.perform_moderation_action(ctx_or_interaction, user, action_type, reason)
        
        if not action_success and action_type not in ["warn", "note"]:
            error_msg = f"❌ Failed to {action_type} user: {action_message}"
            if hasattr(ctx_or_interaction, 'response'):
                await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(error_msg)
            return
        
        # Create the log embed
        log_embed, case_id = await self.create_mod_log_embed(user, action_type, reason, moderator, guild, action_success, action_message)
        
        # Send the log to the mod-logs channel
        await mod_logs_channel.send(embed=log_embed)
        
        # Create response message
        response_embed = discord.Embed(
            title=f"✅ Action Complete: {action_type.upper()}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        response_embed.add_field(name="User", value=user.mention, inline=True)
        response_embed.add_field(name="Action", value=action_type.title(), inline=True)
        response_embed.add_field(name="Status", value=action_message, inline=True)
        response_embed.add_field(name="Reason", value=reason, inline=False)
        response_embed.set_footer(
            text=f"Delirium Den • Case ID: {case_id}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        # Send response
        if hasattr(ctx_or_interaction, 'response'):
            await ctx_or_interaction.response.send_message(embed=response_embed)
        else:
            msg = await ctx_or_interaction.send(embed=response_embed)
            # Clean up after 30 seconds for prefix commands
            await asyncio.sleep(30)
            try:
                await msg.delete()
                await ctx_or_interaction.message.delete()
            except:
                pass

    # Slash Commands
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(
        user="The user to ban",
        reason="Reason for the ban"
    )
    @app_commands.default_permissions(ban_members=True)
    async def slash_ban(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await self.send_mod_log(interaction, user, "ban", reason)
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(
        user="The user to kick",
        reason="Reason for the kick"
    )
    @app_commands.default_permissions(kick_members=True)
    async def slash_kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        await self.send_mod_log(interaction, user, "kick", reason)
    
    @app_commands.command(name="mute", description="Mute a user (1 hour timeout)")
    @app_commands.describe(
        user="The user to mute",
        reason="Reason for the mute"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def slash_mute(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        await self.send_mod_log(interaction, user, "mute", reason)
    
    @app_commands.command(name="warn", description="Issue a warning to a user")
    @app_commands.describe(
        user="The user to warn",
        reason="Reason for the warning"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def slash_warn(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await self.send_mod_log(interaction, user, "warn", reason)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(
        user="The user to unban (provide their ID if not in server)",
        reason="Reason for the unban"
    )
    @app_commands.default_permissions(ban_members=True)
    async def slash_unban(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await self.send_mod_log(interaction, user, "unban", reason)
    
    @app_commands.command(name="note", description="Add a moderation note for a user")
    @app_commands.describe(
        user="The user to add a note for",
        reason="The note content"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def slash_note(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await self.send_mod_log(interaction, user, "note", reason)

    @commands.command(name="punish")
    @commands.has_permissions(manage_messages=True)
    async def mod_log(self, ctx, user: discord.User = None, action_type=None, *, reason=None):
        """Create a moderation log entry and perform the action
        
        Usage: !punish @user <action_type> <reason>
        
        Action types: warn, mute, kick, ban, unban, note
        """
        if not user or not action_type:
            # Show help if parameters are missing
            help_embed = discord.Embed(
                title="📋 Punish Command Usage",
                description="Use this command to perform moderation actions and log them consistently.",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            help_embed.add_field(
                name="Command Syntax",
                value="```!punish @user <action_type> <reason>```",
                inline=False
            )
            
            help_embed.add_field(
                name="Action Types",
                value="• `warn` - Issue a warning (log only)\n• `mute` - Timeout user for 1 hour\n• `kick` - Kick user from server\n• `ban` - Ban user from server\n• `unban` - Unban user from server\n• `note` - Add a mod note (log only)",
                inline=False
            )
            
            help_embed.add_field(
                name="Examples",
                value="```!punish @Username ban Repeated rule violations after warnings\n!punish @Username mute Spamming in chat\n!punish @Username warn First offense```",
                inline=False
            )
            
            help_embed.add_field(
                name="Note",
                value="⚠️ **This command will actually perform the moderation action** (except for warn/note which are log-only)",
                inline=False
            )
            
            help_embed.add_field(
                name="Slash Commands Available",
                value="You can also use `/ban`, `/kick`, `/mute`, `/warn`, `/unban`, `/note` slash commands!",
                inline=False
            )
            
            help_embed.set_footer(
                text="Delirium Den • Moderation Help",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            return await ctx.send(embed=help_embed)
            
        # Normalize action type
        action_type = action_type.lower()
        
        # Validate action type
        valid_actions = ["warn", "mute", "kick", "ban", "unban", "note"]
        if action_type not in valid_actions:
            return await ctx.send(f"❌ Invalid action type. Must be one of: {', '.join(valid_actions)}")
        
        # If reason is not provided
        if not reason:
            return await ctx.send("❌ Please provide a reason for this moderation action.")
        
        await self.send_mod_log(ctx, user, action_type, reason)

async def setup(bot):
    """Add the ModLogs cog to the bot"""
    await bot.add_cog(ModLogs(bot))
    print("🎭 Delirium Den ModLogs cog loaded successfully")