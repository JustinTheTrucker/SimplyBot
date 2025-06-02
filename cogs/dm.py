# dm.py - DM command cog for Discord bot
# Usage: !dm @user your message here
import discord
from discord.ext import commands

class DMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='dm')
    async def dm_command(self, ctx, target: discord.Member, *, message_content):
        """Send a DM to a user. Usage: !dm @user your message here"""
        
        # Check permissions (optional - uncomment if you want to restrict this)
        # if not ctx.author.guild_permissions.moderate_members:
        #     await ctx.reply("❌ You don't have permission to use this command!")
        #     return
        
        try:
            # Send the DM with warning message
            dm_message = f"{message_content}\n\n⚠️ **These messages aren't checked. Do not reply.**"
            await target.send(dm_message)
            
            # Confirm in the channel
            await ctx.reply(f"✅ DM sent to {target.mention}!")
            
            # Optional: Delete the original command message for privacy
            # await ctx.message.delete()
            
        except discord.Forbidden:
            await ctx.reply('❌ Cannot send DM to that user - they might have DMs disabled!')
        except discord.HTTPException:
            await ctx.reply('❌ Failed to send DM. Please try again later.')
        except Exception as e:
            print(f'Error sending DM: {e}')
            await ctx.reply('❌ An unexpected error occurred.')

    @commands.command(name='dm_embed')
    async def dm_embed_command(self, ctx, target: discord.Member, *, message_content):
        """Send a fancy embed DM to a user. Usage: !dm_embed @user your message here"""
        
        try:
            # Create embed for the DM
            dm_embed = discord.Embed(
                title='📨 New Message',
                description=message_content,
                color=0x5865F2,
                timestamp=ctx.message.created_at
            )
            dm_embed.set_footer(
                text="Anonymous Message",
                icon_url=None
            )
            
            # Add warning field to embed
            dm_embed.add_field(
                name="⚠️ Important",
                value="These messages aren't checked. Do not reply.",
                inline=False
            )
            
            await target.send(embed=dm_embed)
            await ctx.reply(f'✅ Fancy DM sent to {target.mention}!')
            
        except discord.Forbidden:
            await ctx.reply('❌ Cannot send DM to that user - they might have DMs disabled!')
        except discord.HTTPException:
            await ctx.reply('❌ Failed to send DM. Please try again later.')
        except Exception as e:
            print(f'Error sending DM: {e}')
            await ctx.reply('❌ An unexpected error occurred.')

# Required setup function for cogs
async def setup(bot):
    await bot.add_cog(DMCog(bot))