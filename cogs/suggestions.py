import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'suggestions_data.json'
        self.suggestions_data = self.load_data()
        self.next_suggestion_id = self.get_next_id()
        
        # Default settings - can be customized per server
        self.default_settings = {
            'suggestions_channel': None,
            'use_threads': False,  # Use threads for suggestions
            'use_forum': False,    # Use forum channel for suggestions
            'anonymous_allowed': True,
            'auto_reactions': True
        }
        
    def load_data(self):
        """Load suggestions data from JSON file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {
            'suggestions': {},
            'settings': {}
        }
    
    def save_data(self):
        """Save suggestions data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.suggestions_data, f, indent=4)
    
    def get_next_id(self):
        """Get the next suggestion ID"""
        if not self.suggestions_data['suggestions']:
            return 1
        return max(int(sid) for sid in self.suggestions_data['suggestions'].keys()) + 1
    
    def get_server_settings(self, guild_id):
        """Get settings for a specific server"""
        guild_str = str(guild_id)
        if guild_str not in self.suggestions_data['settings']:
            self.suggestions_data['settings'][guild_str] = self.default_settings.copy()
            self.save_data()
        return self.suggestions_data['settings'][guild_str]
    
    @app_commands.command(name="suggest", description="Submit a suggestion")
    async def suggest_slash(self, interaction: discord.Interaction, suggestion: str, anonymous: bool = False):
        """Submit a suggestion via slash command"""
        await self.create_suggestion(interaction, suggestion, anonymous, is_slash=True)
    
    @commands.command(name="suggest")
    async def suggest_prefix(self, ctx, *, suggestion: str = None):
        """Submit a suggestion via prefix command"""
        if not suggestion:
            embed = discord.Embed(
                title="💡 How to Submit a Suggestion",
                description="**Usage:**\n`!suggest Your suggestion here`\n`!suggest -anon Your anonymous suggestion`\n\n**Examples:**\n• `!suggest Add more music bots`\n• `!suggest -anon The server needs better moderation`",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Cephalo • Suggestions Help", icon_url="https://i.imgur.com/pKBQZJE.png")
            temp_msg = await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
            await temp_msg.delete(delay=15)
            return
        
        anonymous = False
        if suggestion.startswith('-anon '):
            anonymous = True
            suggestion = suggestion[6:]  # Remove '-anon ' prefix
        
        await self.create_suggestion(ctx, suggestion, anonymous, is_slash=False)
    
    async def create_suggestion(self, ctx_or_interaction, suggestion: str, anonymous: bool, is_slash: bool):
        """Create a new suggestion"""
        if is_slash:
            guild = ctx_or_interaction.guild
            user = ctx_or_interaction.user
        else:
            guild = ctx_or_interaction.guild
            user = ctx_or_interaction.author
        
        settings = self.get_server_settings(guild.id)
        
        # Check if suggestions channel is set
        if not settings['suggestions_channel']:
            embed = discord.Embed(
                title="❌ Suggestions Not Set Up",
                description="The suggestions system hasn't been configured yet.\n\nAsk an administrator to:\n• Run `!setup_suggestions #channel` for regular channel\n• Run `!setup_suggestions #forum` for forum channel\n• Run `!setup_suggestions #channel threads` for threaded suggestions",
                color=discord.Color.red()
            )
            embed.set_footer(text="Cephalo • Setup Required", icon_url="https://i.imgur.com/pKBQZJE.png")
            if is_slash:
                await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=embed)
            return
        
        suggestions_channel = guild.get_channel(settings['suggestions_channel'])
        if not suggestions_channel:
            embed = discord.Embed(
                title="❌ Suggestions Channel Not Found",
                description="The suggestions channel no longer exists. Please ask an administrator to reconfigure it with `!setup_suggestions`.",
                color=discord.Color.red()
            )
            if is_slash:
                await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=embed)
            return
        
        # Create suggestion
        suggestion_id = self.next_suggestion_id
        self.next_suggestion_id += 1
        
        # Store suggestion data
        self.suggestions_data['suggestions'][str(suggestion_id)] = {
            'id': suggestion_id,
            'author_id': user.id,
            'author_name': str(user),
            'content': suggestion,
            'anonymous': anonymous,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'guild_id': guild.id
        }
        
        self.save_data()
        
        # Create embed
        embed = discord.Embed(
            description=f"## 💡 {suggestion}",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        if not anonymous:
            embed.set_author(name=f"Suggestion #{suggestion_id} by {user.display_name}", icon_url=user.display_avatar.url)
        else:
            embed.set_author(name=f"Suggestion #{suggestion_id} (Anonymous)", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        
        embed.add_field(
            name="🗳️ How to Vote", 
            value="👍 **Upvote** • 👎 **Downvote**", 
            inline=True
        )
        embed.add_field(
            name="💬 Discussion", 
            value="Use the thread below to discuss!", 
            inline=True
        )
        embed.set_footer(
            text="Cephalo • Vote with reactions above", 
            icon_url="https://i.imgur.com/pKBQZJE.png"
        )
        
        # Handle different channel types
        suggestion_message = None
        
        if settings['use_forum'] and suggestions_channel.type == discord.ChannelType.forum:
            # Create forum post
            try:
                thread = await suggestions_channel.create_thread(
                    name=f"💡 Suggestion #{suggestion_id}: {suggestion[:50]}{'...' if len(suggestion) > 50 else ''}",
                    content=f"**Suggestion #{suggestion_id}**\n\n{suggestion}\n\n*Submitted by: {'Anonymous' if anonymous else user.mention}*\n\n**Vote by reacting below!**"
                )
                suggestion_message = thread.message
                
                # Store thread info
                self.suggestions_data['suggestions'][str(suggestion_id)]['thread_id'] = thread.id
                
            except Exception as e:
                embed_error = discord.Embed(
                    title="❌ Failed to Create Forum Post",
                    description=f"Error: {str(e)}",
                    color=discord.Color.red()
                )
                if is_slash:
                    await ctx_or_interaction.response.send_message(embed=embed_error, ephemeral=True)
                else:
                    await ctx_or_interaction.send(embed=embed_error)
                return
                
        elif settings['use_threads']:
            # Create thread from message
            suggestion_message = await suggestions_channel.send(embed=embed)
            try:
                thread = await suggestion_message.create_thread(
                    name=f"💬 Suggestion #{suggestion_id} Discussion",
                    auto_archive_duration=10080  # 7 days
                )
                # Send a welcoming message in the thread
                welcome_embed = discord.Embed(
                    title="💬 Discussion Thread",
                    description=f"**Original Suggestion:** {suggestion}\n\n{'*Submitted anonymously*' if anonymous else f'*Submitted by {user.mention}*'}\n\nShare your thoughts, ask questions, or provide feedback about this suggestion!",
                    color=discord.Color.blue()
                )
                welcome_embed.set_footer(text="Cephalo • Keep discussions respectful and constructive", icon_url="https://i.imgur.com/pKBQZJE.png")
                await thread.send(embed=welcome_embed)
                
                # Store thread info
                self.suggestions_data['suggestions'][str(suggestion_id)]['thread_id'] = thread.id
            except Exception as e:
                print(f"Failed to create thread: {e}")
        else:
            # Regular channel message
            suggestion_message = await suggestions_channel.send(embed=embed)
        
        # Add reactions for voting
        if suggestion_message:
            await suggestion_message.add_reaction('👍')
            await suggestion_message.add_reaction('👎')
            
            # Store message ID
            self.suggestions_data['suggestions'][str(suggestion_id)]['message_id'] = suggestion_message.id
            self.save_data()
        
        # Confirm to user (temporary message)
        if settings['use_forum']:
            confirm_text = f"Your suggestion has been posted as a **forum thread** in {suggestions_channel.mention}"
        elif settings['use_threads']:
            confirm_text = f"Your suggestion has been posted in {suggestions_channel.mention} with a **discussion thread**"
        else:
            confirm_text = f"Your suggestion has been posted in {suggestions_channel.mention}"
        
        confirm_embed = discord.Embed(
            title="✅ Suggestion Submitted Successfully!",
            description=f"{confirm_text}\n\n**Suggestion ID:** #{suggestion_id}\n**Content:** {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}",
            color=discord.Color.green()
        )
        confirm_embed.add_field(
            name="🗳️ Voting", 
            value="Others can vote with 👍 👎 reactions", 
            inline=True
        )
        confirm_embed.add_field(
            name="🗑️ Delete", 
            value="`!delete_my_suggestion " + str(suggestion_id) + "`", 
            inline=True
        )
        confirm_embed.set_footer(text="This message will disappear in 15 seconds", icon_url="https://i.imgur.com/pKBQZJE.png")
        
        if is_slash:
            await ctx_or_interaction.response.send_message(embed=confirm_embed, ephemeral=True)
        else:
            # For prefix commands, delete the original command message and send a temporary confirmation
            try:
                await ctx_or_interaction.message.delete()
            except:
                pass
            
            temp_message = await ctx_or_interaction.send(embed=confirm_embed)
            await temp_message.delete(delay=15)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_suggestions(self, ctx, suggestions_channel: discord.abc.GuildChannel = None, mode: str = "normal"):
        """Set up the suggestions system
        
        Usage:
        !setup_suggestions #channel - Regular suggestions
        !setup_suggestions #channel threads - With discussion threads
        !setup_suggestions #forum - Forum channel (for forum channels only)
        """
        if suggestions_channel is None:
            embed = discord.Embed(
                title="🐙 Suggestions System Setup",
                description="**Choose your setup method:**\n\n`!setup_suggestions #channel` - Regular suggestions channel\n`!setup_suggestions #channel threads` - Suggestions with discussion threads\n`!setup_suggestions #forum` - Forum channel (forum channels only)\n\n**Examples:**\n• `!setup_suggestions #suggestions`\n• `!setup_suggestions #suggestions threads`\n• `!setup_suggestions #suggestion-forum`",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Cephalo • Setup Help", icon_url="https://i.imgur.com/pKBQZJE.png")
            await ctx.send(embed=embed)
            return
        
        # Check if channel is valid for suggestions
        if not isinstance(suggestions_channel, (discord.TextChannel, discord.ForumChannel)):
            embed = discord.Embed(
                title="❌ Invalid Channel Type",
                description="Please use a text channel or forum channel for suggestions.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        settings = self.get_server_settings(ctx.guild.id)
        settings['suggestions_channel'] = suggestions_channel.id
        settings['use_threads'] = mode.lower() == "threads"
        settings['use_forum'] = mode.lower() == "forum" or suggestions_channel.type == discord.ChannelType.forum
        
        self.save_data()
        
        # Determine setup type
        if settings['use_forum']:
            setup_type = "**Forum Channel** - Each suggestion gets its own thread"
            usage_text = "Users submit suggestions that become individual forum posts with voting and discussion!"
        elif settings['use_threads']:
            setup_type = "**Threaded Channel** - Each suggestion gets a discussion thread"
            usage_text = "Users submit suggestions with automatic discussion threads for community feedback!"
        else:
            setup_type = "**Regular Channel** - Simple suggestion posts"
            usage_text = "Users submit suggestions as embed messages with reaction voting!"
        
        embed = discord.Embed(
            title="🐙 Suggestions System Setup Complete!",
            description=f"Suggestions will now be posted in {suggestions_channel.mention}\n\n**Mode:** {setup_type}\n\n{usage_text}",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="📝 How to Submit",
            value="• `/suggest Your idea here`\n• `!suggest Your idea here`\n• `!suggest -anon Anonymous idea`",
            inline=True
        )
        embed.add_field(
            name="🗳️ How to Vote",
            value="React with 👍 or 👎 on suggestions to vote!",
            inline=True
        )
        embed.set_footer(text="Cephalo • Suggestions System", icon_url="https://i.imgur.com/pKBQZJE.png")
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def suggestion_status(self, ctx, suggestion_id: int, *, status: str):
        """Update a suggestion's status (approved, denied, implemented, etc.)"""
        suggestion_str = str(suggestion_id)
        
        if suggestion_str not in self.suggestions_data['suggestions']:
            await ctx.send("❌ Suggestion not found!")
            return
        
        suggestion = self.suggestions_data['suggestions'][suggestion_str]
        
        # Update status
        suggestion['status'] = status.lower()
        self.save_data()
        
        # Status emojis and colors
        status_map = {
            'approved': ('✅', discord.Color.green()),
            'denied': ('❌', discord.Color.red()),
            'implemented': ('🚀', discord.Color.blue()),
            'under review': ('🔍', discord.Color.orange()),
            'pending': ('🟡', discord.Color.yellow())
        }
        
        emoji, color = status_map.get(status.lower(), ('📝', discord.Color.purple()))
        
        embed = discord.Embed(
            title=f"📋 Suggestion #{suggestion_id} Status Updated",
            description=f"Status changed to: {emoji} **{status.title()}**\n\n*Original suggestion: {suggestion['content'][:100]}{'...' if len(suggestion['content']) > 100 else ''}*",
            color=color
        )
        embed.set_footer(text="Cephalo • Status Update", icon_url="https://i.imgur.com/pKBQZJE.png")
        await ctx.send(embed=embed)
    
    @commands.command()
    async def suggestion_info(self, ctx, suggestion_id: int):
        """Get detailed info about a suggestion"""
        suggestion_str = str(suggestion_id)
        
        if suggestion_str not in self.suggestions_data['suggestions']:
            embed = discord.Embed(
                title="❌ Suggestion Not Found",
                description=f"Suggestion #{suggestion_id} doesn't exist.\n\nUse `!suggest` to submit a new suggestion!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        suggestion = self.suggestions_data['suggestions'][suggestion_str]
        
        embed = discord.Embed(
            title=f"💡 Suggestion #{suggestion_id} Details",
            description=suggestion['content'],
            color=discord.Color.purple(),
            timestamp=datetime.fromisoformat(suggestion['timestamp'])
        )
        
        if not suggestion['anonymous']:
            embed.add_field(name="👤 Author", value=f"<@{suggestion['author_id']}>", inline=True)
        else:
            embed.add_field(name="👤 Author", value="Anonymous", inline=True)
        
        embed.add_field(name="📅 Status", value=suggestion['status'].title(), inline=True)
        embed.add_field(name="🗳️ Voting", value="Check reactions on the original message", inline=True)
        
        embed.set_footer(text="Cephalo • Suggestion Info", icon_url="https://i.imgur.com/pKBQZJE.png")
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def remove_suggestion(self, ctx, suggestion_id: int):
        """Remove a suggestion completely (moderators only)"""
        suggestion_str = str(suggestion_id)
        
        if suggestion_str not in self.suggestions_data['suggestions']:
            embed = discord.Embed(
                title="❌ Suggestion Not Found",
                description=f"Suggestion #{suggestion_id} doesn't exist.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        suggestion = self.suggestions_data['suggestions'][suggestion_str]
        
        # Try to delete the message/thread from Discord
        success = await self._delete_suggestion_content(ctx.guild, suggestion)
        
        # Remove from data
        del self.suggestions_data['suggestions'][suggestion_str]
        self.save_data()
        
        embed = discord.Embed(
            title="🗑️ Suggestion Removed",
            description=f"Suggestion #{suggestion_id} has been permanently deleted.",
            color=discord.Color.red()
        )
        if not success:
            embed.add_field(name="⚠️ Note", value="Couldn't delete the original message/thread (may already be deleted)", inline=False)
        
        embed.set_footer(text="Cephalo • Suggestion Removed", icon_url="https://i.imgur.com/pKBQZJE.png")
        await ctx.send(embed=embed)
    
    @commands.command()
    async def delete_my_suggestion(self, ctx, suggestion_id: int):
        """Delete your own suggestion"""
        suggestion_str = str(suggestion_id)
        
        if suggestion_str not in self.suggestions_data['suggestions']:
            embed = discord.Embed(
                title="❌ Suggestion Not Found",
                description=f"Suggestion #{suggestion_id} doesn't exist.",
                color=discord.Color.red()
            )
            temp_msg = await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
            await temp_msg.delete(delay=10)
            return
        
        suggestion = self.suggestions_data['suggestions'][suggestion_str]
        
        # Check if user owns this suggestion
        if suggestion['author_id'] != ctx.author.id:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You can only delete your own suggestions.",
                color=discord.Color.red()
            )
            temp_msg = await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
            await temp_msg.delete(delay=10)
            return
        
        # Try to delete the message/thread from Discord
        await self._delete_suggestion_content(ctx.guild, suggestion)
        
        # Remove from data
        del self.suggestions_data['suggestions'][suggestion_str]
        self.save_data()
        
        embed = discord.Embed(
            title="🗑️ Your Suggestion Deleted",
            description=f"Your suggestion #{suggestion_id} has been deleted.",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Cephalo • Suggestion Deleted", icon_url="https://i.imgur.com/pKBQZJE.png")
        temp_message = await ctx.send(embed=embed)
        
        # Delete the command message and confirmation after a delay
        try:
            await ctx.message.delete()
        except:
            pass
        await temp_message.delete(delay=10)
    
    async def _delete_suggestion_content(self, guild, suggestion):
        """Helper method to delete suggestion content from Discord"""
        try:
            settings = self.get_server_settings(guild.id)
            if settings['suggestions_channel']:
                channel = guild.get_channel(settings['suggestions_channel'])
                if channel:
                    # Try to delete thread if it exists
                    if 'thread_id' in suggestion:
                        thread = guild.get_thread(suggestion['thread_id'])
                        if thread:
                            await thread.delete()
                            return True
                    
                    # Try to delete message
                    if 'message_id' in suggestion:
                        message = await channel.fetch_message(suggestion['message_id'])
                        await message.delete()
                        return True
        except:
            pass
        return False

async def setup(bot):
    cog = Suggestions(bot)
    await bot.add_cog(cog)