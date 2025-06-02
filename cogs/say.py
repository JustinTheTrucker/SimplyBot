import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime

class SayCommand(commands.Cog):
    """A cog that allows sending messages as the bot with Delirium Den branding"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event"""
        print("🎭 Delirium Den Say Command cog loaded successfully")
    
    @commands.command(name='say', aliases=['speak', 'echo'])
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message):
        """
        Send a message as the bot
        Usage: !say <message>
        """
        try:
            # Delete the original command message
            await ctx.message.delete()
            
            # Send the message as the bot
            await ctx.send(message)
            
            # Send confirmation to user via DM
            try:
                confirm_embed = discord.Embed(
                    title="✅ Message Sent",
                    description=f"Your message was sent to {ctx.channel.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                confirm_embed.add_field(
                    name="Message Content",
                    value=f"```{message[:1000]}{'...' if len(message) > 1000 else ''}```",
                    inline=False
                )
                confirm_embed.set_footer(
                    text="Delirium Den • Say Command",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await ctx.author.send(embed=confirm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to delete messages in this channel.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=10)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • System Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=10)
    
    @commands.command(name='sayto', aliases=['sendto'])
    @commands.has_permissions(manage_messages=True)
    async def say_to(self, ctx, channel: discord.TextChannel, *, message):
        """
        Send a message as the bot to a specific channel
        Usage: !sayto #channel <message>
        """
        try:
            # Delete the original command message
            await ctx.message.delete()
            
            # Send the message to the specified channel
            await channel.send(message)
            
            # Send confirmation to the user
            confirm_embed = discord.Embed(
                title="✅ Message Sent to Channel",
                description=f"Your message was successfully sent to {channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            confirm_embed.add_field(
                name="Target Channel",
                value=channel.mention,
                inline=True
            )
            confirm_embed.add_field(
                name="Sent By",
                value=ctx.author.mention,
                inline=True
            )
            confirm_embed.add_field(
                name="Message Content",
                value=f"```{message[:1000]}{'...' if len(message) > 1000 else ''}```",
                inline=False
            )
            confirm_embed.set_footer(
                text="Delirium Den • Cross-Channel Message",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            try:
                await ctx.author.send(embed=confirm_embed)
            except discord.Forbidden:
                # If DMs are disabled, send to original channel and delete after delay
                temp_msg = await ctx.send(embed=confirm_embed)
                await asyncio.sleep(10)
                try:
                    await temp_msg.delete()
                except:
                    pass
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to send messages to that channel or delete your message.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Required Permissions",
                value="• Send Messages (target channel)\n• Manage Messages (current channel)",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=15)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • System Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=10)
    
    @commands.command(name='embed')
    @commands.has_permissions(manage_messages=True)
    async def say_embed(self, ctx, title, *, description):
        """
        Send an embed message as the bot
        Usage: !embed "Title Here" Description here
        """
        try:
            # Delete the original command message
            await ctx.message.delete()
            
            # Create and send embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(
                text=f"Delirium Den • Requested by {ctx.author.display_name}",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await ctx.send(embed=embed)
            
            # Send confirmation to user
            try:
                confirm_embed = discord.Embed(
                    title="✅ Embed Sent",
                    description=f"Your embed was sent to {ctx.channel.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                confirm_embed.add_field(
                    name="Embed Title",
                    value=title,
                    inline=False
                )
                confirm_embed.add_field(
                    name="Embed Description",
                    value=f"```{description[:500]}{'...' if len(description) > 500 else ''}```",
                    inline=False
                )
                confirm_embed.set_footer(
                    text="Delirium Den • Embed Command",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await ctx.author.send(embed=confirm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to delete messages in this channel.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=10)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • System Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=10)
    
    @commands.command(name='embedto')
    @commands.has_permissions(manage_messages=True)
    async def embed_to(self, ctx, channel: discord.TextChannel, title, *, description):
        """
        Send an embed message as the bot to a specific channel
        Usage: !embedto #channel "Title Here" Description here
        """
        try:
            # Delete the original command message
            await ctx.message.delete()
            
            # Create and send embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(
                text=f"Delirium Den • Requested by {ctx.author.display_name}",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await channel.send(embed=embed)
            
            # Send confirmation to user
            confirm_embed = discord.Embed(
                title="✅ Embed Sent to Channel",
                description=f"Your embed was successfully sent to {channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            confirm_embed.add_field(
                name="Target Channel",
                value=channel.mention,
                inline=True
            )
            confirm_embed.add_field(
                name="Sent By",
                value=ctx.author.mention,
                inline=True
            )
            confirm_embed.add_field(
                name="Embed Title",
                value=title,
                inline=False
            )
            confirm_embed.add_field(
                name="Embed Description",
                value=f"```{description[:500]}{'...' if len(description) > 500 else ''}```",
                inline=False
            )
            confirm_embed.set_footer(
                text="Delirium Den • Cross-Channel Embed",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            try:
                await ctx.author.send(embed=confirm_embed)
            except discord.Forbidden:
                # If DMs are disabled, send to original channel and delete after delay
                temp_msg = await ctx.send(embed=confirm_embed)
                await asyncio.sleep(15)
                try:
                    await temp_msg.delete()
                except:
                    pass
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to send embeds to that channel or delete your message.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Required Permissions",
                value="• Send Messages (target channel)\n• Embed Links (target channel)\n• Manage Messages (current channel)",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=15)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • System Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=10)
    
    @commands.command(name='announce')
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message):
        """
        Send an announcement embed as the bot to a specific channel
        Usage: !announce #channel Your announcement message here
        Requires Administrator permission
        """
        try:
            # Delete the original command message
            await ctx.message.delete()
            
            # Create announcement embed
            embed = discord.Embed(
                title="📢 Delirium Den Announcement",
                description=message,
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(
                text=f"Delirium Den • Announced by {ctx.author.display_name}",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await channel.send(embed=embed)
            
            # Send confirmation to user
            confirm_embed = discord.Embed(
                title="📢 Announcement Sent",
                description=f"Your announcement was successfully sent to {channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            confirm_embed.add_field(
                name="Target Channel",
                value=channel.mention,
                inline=True
            )
            confirm_embed.add_field(
                name="Announced By",
                value=ctx.author.mention,
                inline=True
            )
            confirm_embed.add_field(
                name="Message Content",
                value=f"```{message[:800]}{'...' if len(message) > 800 else ''}```",
                inline=False
            )
            confirm_embed.set_footer(
                text="Delirium Den • Announcement System",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            try:
                await ctx.author.send(embed=confirm_embed)
            except discord.Forbidden:
                # If DMs are disabled, send to original channel and delete after delay
                temp_msg = await ctx.send(embed=confirm_embed)
                await asyncio.sleep(15)
                try:
                    await temp_msg.delete()
                except:
                    pass
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to send announcements to that channel or delete your message.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=15)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • System Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=10)
    
    @commands.command(name='sayhelp', aliases=['say_help'])
    @commands.has_permissions(manage_messages=True)
    async def say_help(self, ctx):
        """Show help for say commands"""
        help_embed = discord.Embed(
            title="🎭 Delirium Den Say Commands",
            description="Commands for sending messages as the bot.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        help_embed.add_field(
            name="💬 Basic Commands",
            value="```!say <message>\n!sayto #channel <message>\n!speak <message>\n!echo <message>```",
            inline=False
        )
        
        help_embed.add_field(
            name="🎨 Embed Commands",
            value="```!embed \"Title\" Description\n!embedto #channel \"Title\" Description```",
            inline=False
        )
        
        help_embed.add_field(
            name="📢 Announcement Commands (Admin Only)",
            value="```!announce #channel <message>```",
            inline=False
        )
        
        help_embed.add_field(
            name="🔧 Command Details",
            value="• **say** - Send a message in current channel\n• **sayto** - Send a message to specific channel\n• **embed** - Send an embed in current channel\n• **embedto** - Send an embed to specific channel\n• **announce** - Send a special announcement embed\n• **sayhelp** - Show this help message",
            inline=False
        )
        
        help_embed.add_field(
            name="⚠️ Permissions Required",
            value="• **Manage Messages** - For basic say/embed commands\n• **Administrator** - For announcement commands\n• Bot needs Send Messages & Embed Links permissions",
            inline=False
        )
        
        help_embed.add_field(
            name="💡 Tips",
            value="• Original command messages are automatically deleted\n• Confirmations are sent via DM when possible\n• Use quotes around embed titles: `\"Like This\"`\n• All sent messages include Delirium Den branding",
            inline=False
        )
        
        help_embed.set_footer(
            text="Delirium Den • Say Commands Help",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=help_embed, delete_after=60)
    
    # Error handlers for all commands
    @say.error
    @say_to.error
    @say_embed.error
    @embed_to.error
    @announce.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            if ctx.command.name == 'announce':
                perm_text = "You need **Administrator** permission to use announcement commands."
            else:
                perm_text = "You need **Manage Messages** permission to use this command."
            
            error_embed = discord.Embed(
                title="❌ Missing Permissions",
                description=perm_text,
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Command Used",
                value=f"`{ctx.command.name}`",
                inline=True
            )
            error_embed.add_field(
                name="Your Permissions",
                value="Insufficient",
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=15)
            
        elif isinstance(error, commands.MissingRequiredArgument):
            usage_examples = {
                'say': "`!say Hello everyone!`",
                'sayto': "`!sayto #general Hello everyone!`",
                'embed': "`!embed \"Announcement\" This is important info`",
                'embedto': "`!embedto #announcements \"Title\" Description here`",
                'announce': "`!announce #general Important server announcement`"
            }
            
            error_embed = discord.Embed(
                title="❌ Missing Arguments",
                description=f"Please provide the required arguments for the `{ctx.command.name}` command.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Correct Usage",
                value=usage_examples.get(ctx.command.name, "Check `!sayhelp` for usage examples"),
                inline=False
            )
            error_embed.add_field(
                name="💡 Need Help?",
                value="Use `!sayhelp` to see all available commands and examples.",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Usage Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=20)
            
        elif isinstance(error, commands.ChannelNotFound):
            error_embed = discord.Embed(
                title="❌ Channel Not Found",
                description="The channel you specified could not be found.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="💡 Tips",
                value="• Make sure to mention the channel with #\n• Ensure the channel exists in this server\n• Check that you have permission to view the channel",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Channel Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=15)
            
        else:
            error_embed = discord.Embed(
                title="❌ Command Error",
                description=f"An unexpected error occurred: {str(error)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Command",
                value=f"`{ctx.command.name}`",
                inline=True
            )
            error_embed.add_field(
                name="User",
                value=ctx.author.mention,
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • System Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed, delete_after=15)

# Function to add the cog to your bot
async def setup(bot):
    await bot.add_cog(SayCommand(bot))