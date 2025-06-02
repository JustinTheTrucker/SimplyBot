import discord
from discord.ext import commands
import asyncio
import json
import os

class EmptyMessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monitored_users = {}  # {guild_id: {user_id: channel_id or 'all'}}
        self.data_file = 'monitored_users.json'
        self.load_data()
        
    def load_data(self):
        """Load monitored users from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to integers
                    self.monitored_users = {
                        int(guild_id): {
                            int(user_id): channel_data 
                            for user_id, channel_data in users.items()
                        }
                        for guild_id, users in data.items()
                    }
        except Exception as e:
            print(f"Error loading monitored users: {e}")
            self.monitored_users = {}
    
    def save_data(self):
        """Save monitored users to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.monitored_users, f, indent=2)
        except Exception as e:
            print(f"Error saving monitored users: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages and replace if user is being tracked"""
        # Ignore bot messages and commands
        if message.author.bot:
            return
            
        # Check if user is monitored in this guild
        guild_id = message.guild.id if message.guild else None
        if not guild_id or guild_id not in self.monitored_users:
            return
            
        user_id = message.author.id
        if user_id not in self.monitored_users[guild_id]:
            return
            
        # Check if monitoring applies to this channel
        monitor_data = self.monitored_users[guild_id][user_id]
        if monitor_data != 'all' and monitor_data != message.channel.id:
            return
            
        # Replace the message with empty content
        try:
            # Small delay to ensure message is fully sent
            await asyncio.sleep(0.1)
            
            # Create webhook to send replacement
            webhook = await message.channel.create_webhook(name="DeliriumDenAutoReplacer")
            
            # Send empty message with invisible character
            invisible_char = "​"  # Zero-width space
            await webhook.send(
                content=invisible_char,
                username=message.author.display_name,
                avatar_url=message.author.avatar.url if message.author.avatar else None
            )
            
            # Delete the original message
            await message.delete()
            
            # Clean up webhook
            await webhook.delete()
            
        except discord.Forbidden:
            print(f"Missing permissions to replace message in {message.guild.name}")
        except Exception as e:
            print(f"Error replacing message: {e}")

    @commands.command(name='monitor_empty', aliases=['monitor', 'auto_empty'])
    @commands.has_permissions(manage_messages=True)
    async def monitor_user_empty(self, ctx, user: discord.Member, scope: str = "channel"):
        """
        Monitor a user and automatically replace all their future messages with empty ones.
        Usage: !monitor_empty @user [channel/server]
        - channel: Only monitor in current channel (default)
        - server: Monitor in entire server
        """
        guild_id = ctx.guild.id
        user_id = user.id
        
        if guild_id not in self.monitored_users:
            self.monitored_users[guild_id] = {}
        
        if scope.lower() in ['server', 'guild', 'all']:
            self.monitored_users[guild_id][user_id] = 'all'
            scope_text = "entire server"
        else:
            self.monitored_users[guild_id][user_id] = ctx.channel.id
            scope_text = f"#{ctx.channel.name}"
        
        self.save_data()
        
        embed = discord.Embed(
            title="👻 User Monitoring Enabled",
            description=f"Now monitoring **{user.display_name}** in {scope_text}.\nAll their future messages will be replaced with empty messages.",
            color=0x2ecc71,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Target", value=user.mention, inline=True)
        embed.add_field(name="Scope", value=scope_text, inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.set_footer(
            text="Delirium Den • Message Monitoring",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete(delay=1)

    @commands.command(name='unmonitor', aliases=['stop_monitor', 'stop_empty'])
    @commands.has_permissions(manage_messages=True)
    async def unmonitor_user(self, ctx, user: discord.Member):
        """
        Stop monitoring a user's messages.
        Usage: !unmonitor @user
        """
        guild_id = ctx.guild.id
        user_id = user.id
        
        if (guild_id in self.monitored_users and 
            user_id in self.monitored_users[guild_id]):
            
            del self.monitored_users[guild_id][user_id]
            
            # Clean up empty guild entries
            if not self.monitored_users[guild_id]:
                del self.monitored_users[guild_id]
            
            self.save_data()
            
            embed = discord.Embed(
                title="✅ Monitoring Stopped",
                description=f"No longer monitoring **{user.display_name}**.\nTheir messages will appear normally.",
                color=0xe74c3c,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Stopped By", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text="Delirium Den • Message Monitoring",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed, delete_after=8)
        else:
            error_embed = discord.Embed(
                title="❌ User Not Monitored",
                description=f"{user.mention} is not currently being monitored.",
                color=0x95a5a6,
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Message Monitoring",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=5)
        
        await ctx.message.delete(delay=1)

    @commands.command(name='monitored_list', aliases=['list_monitored', 'empty_list'])
    @commands.has_permissions(manage_messages=True)
    async def list_monitored(self, ctx):
        """
        Show all users currently being monitored in this server.
        """
        guild_id = ctx.guild.id
        
        if guild_id not in self.monitored_users or not self.monitored_users[guild_id]:
            embed = discord.Embed(
                title="📋 Monitored Users",
                description="No users are currently being monitored in this server.",
                color=0x95a5a6,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(
                text="Delirium Den • Message Monitoring",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed, delete_after=8)
            await ctx.message.delete(delay=1)
            return
        
        embed = discord.Embed(
            title="📋 Monitored Users",
            description="Users whose messages are being replaced with empty messages:",
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )
        
        for user_id, scope in self.monitored_users[guild_id].items():
            try:
                user = ctx.guild.get_member(user_id)
                if user:
                    scope_text = "Entire Server" if scope == 'all' else f"<#{scope}>"
                    embed.add_field(
                        name=f"👻 {user.display_name}",
                        value=f"**Scope:** {scope_text}",
                        inline=False
                    )
                else:
                    # User left the server, clean up
                    del self.monitored_users[guild_id][user_id]
            except Exception:
                continue
        
        embed.set_footer(
            text="Delirium Den • Message Monitoring",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        self.save_data()
        await ctx.send(embed=embed, delete_after=15)
        await ctx.message.delete(delay=1)

    @commands.command(name='clear_monitors', aliases=['clear_all_monitors'])
    @commands.has_permissions(administrator=True)
    async def clear_all_monitors(self, ctx):
        """
        Clear all monitored users in this server. (Admin only)
        """
        guild_id = ctx.guild.id
        
        if guild_id in self.monitored_users:
            count = len(self.monitored_users[guild_id])
            del self.monitored_users[guild_id]
            self.save_data()
            
            embed = discord.Embed(
                title="🗑️ All Monitors Cleared",
                description=f"Cleared monitoring for {count} user(s).\nAll messages will now appear normally.",
                color=0xe67e22,
                timestamp=discord.utils.utcnow()
            )
        else:
            embed = discord.Embed(
                title="🗑️ No Monitors to Clear", 
                description="No users were being monitored in this server.",
                color=0x95a5a6,
                timestamp=discord.utils.utcnow()
            )
        
        embed.add_field(name="Cleared By", value=ctx.author.mention, inline=True)
        embed.set_footer(
            text="Delirium Den • Message Monitoring",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=embed, delete_after=8)
        await ctx.message.delete(delay=1)

    # Keep the original one-time commands as well
    @commands.command(name='empty', aliases=['clear_once', 'invisible'])
    @commands.has_permissions(manage_messages=True)
    async def empty_message(self, ctx, *, target_content=None):
        """
        Replace a single user message with empty/invisible content.
        Usage: !empty [message_content_to_find]
        If no content specified, it will target the message above the command.
        """
        try:
            await ctx.message.delete()
            
            messages = []
            async for message in ctx.channel.history(limit=50):
                messages.append(message)
            
            target_message = None
            
            if target_content:
                for msg in messages:
                    if (target_content.lower() in msg.content.lower() and 
                        msg.author != self.bot.user and 
                        not msg.content.startswith(ctx.prefix)):
                        target_message = msg
                        break
            else:
                for msg in messages:
                    if (msg.author != self.bot.user and 
                        not msg.content.startswith(ctx.prefix)):
                        target_message = msg
                        break
            
            if target_message:
                webhook = await ctx.channel.create_webhook(name="DeliriumDenEmptyReplacer")
                
                invisible_char = "​"
                await webhook.send(
                    content=invisible_char,
                    username=target_message.author.display_name,
                    avatar_url=target_message.author.avatar.url if target_message.author.avatar else None
                )
                
                await target_message.delete()
                await webhook.delete()
                
            else:
                error_embed = discord.Embed(
                    title="❌ Target Not Found",
                    description="Could not find target message to replace.",
                    color=0xe74c3c,
                    timestamp=discord.utils.utcnow()
                )
                error_embed.set_footer(
                    text="Delirium Den • Message Replacement",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                error_msg = await ctx.send(embed=error_embed)
                await error_msg.delete(delay=3)
                
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Denied",
                description="I don't have permission to manage messages or webhooks.",
                color=0xe74c3c,
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Message Replacement",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            error_msg = await ctx.send(embed=error_embed)
            await error_msg.delete(delay=5)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error Occurred",
                description=f"An unexpected error occurred: {str(e)}",
                color=0xe74c3c,
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Message Replacement",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            error_msg = await ctx.send(embed=error_embed)
            await error_msg.delete(delay=5)

    @commands.command(name='empty_help', aliases=['monitor_help'])
    @commands.has_permissions(manage_messages=True)
    async def empty_help(self, ctx):
        """Show help for empty message commands"""
        help_embed = discord.Embed(
            title="👻 Empty Message Commands Help",
            description="Commands for monitoring users and replacing their messages with empty content.",
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )
        
        help_embed.add_field(
            name="📡 Monitoring Commands",
            value="```!monitor_empty @user [channel/server]\n!unmonitor @user\n!monitored_list\n!clear_monitors```",
            inline=False
        )
        
        help_embed.add_field(
            name="🎯 One-Time Commands",
            value="```!empty [message_content]\n!invisible [message_content]\n!clear_once [message_content]```",
            inline=False
        )
        
        help_embed.add_field(
            name="📋 Command Descriptions",
            value="• **monitor_empty** - Start monitoring a user's messages\n• **unmonitor** - Stop monitoring a user\n• **monitored_list** - Show all monitored users\n• **clear_monitors** - Clear all monitors (Admin only)\n• **empty** - Replace a single message with empty content",
            inline=False
        )
        
        help_embed.add_field(
            name="⚙️ Monitoring Scopes",
            value="• **channel** - Monitor only in current channel (default)\n• **server** - Monitor in entire server",
            inline=False
        )
        
        help_embed.add_field(
            name="ℹ️ Important Notes",
            value="• Requires 'Manage Messages' permission\n• Messages are replaced with invisible characters\n• Original message author's name and avatar are preserved\n• Monitoring persists between bot restarts",
            inline=False
        )
        
        help_embed.set_footer(
            text="Delirium Den • Message Monitoring Help",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=help_embed, delete_after=30)
        await ctx.message.delete(delay=2)

    @monitor_user_empty.error
    @unmonitor_user.error
    @list_monitored.error
    @empty_message.error
    @empty_help.error
    async def monitor_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            error_embed = discord.Embed(
                title="❌ Permission Required",
                description="You need 'Manage Messages' permission to use this command.",
                color=0xe74c3c,
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            error_msg = await ctx.send(embed=error_embed)
            await error_msg.delete(delay=5)
    
    @clear_all_monitors.error
    async def clear_monitors_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            error_embed = discord.Embed(
                title="❌ Administrator Required",
                description="You need 'Administrator' permission to use this command.",
                color=0xe74c3c,
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            error_msg = await ctx.send(embed=error_embed)
            await error_msg.delete(delay=5)

async def setup(bot):
    await bot.add_cog(EmptyMessageCog(bot))
    print("EmptyMessageCog loaded successfully with Delirium Den branding")