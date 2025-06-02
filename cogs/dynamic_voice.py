import discord
from discord.ext import commands
import asyncio
import time

class DynamicVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = {}  # Dictionary to track temporary channels {channel_id: creator_id}
        self.user_cooldowns = {}  # Dictionary to track user cooldowns {user_id: last_channel_creation_time}
        self.cooldown_period = 30  # Cooldown in seconds to prevent spam
        self.pending_deletes = set()  # Set to track channels pending deletion
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Handles dynamic voice channel creation and deletion
        Works alongside the Logging cog's voice state listener
        Implements anti-spam measures
        """
        # Skip bot users
        if member.bot:
            return
            
        # CHANNEL CREATION LOGIC
        if after.channel and after.channel.name.lower() == "🐙 create voice channel":
            # Check if user is on cooldown
            current_time = time.time()
            last_creation = self.user_cooldowns.get(member.id, 0)
            
            if current_time - last_creation < self.cooldown_period:
                # User is on cooldown, move them back to their previous channel if possible
                if before.channel and before.channel.id != after.channel.id:
                    try:
                        await member.move_to(before.channel)
                        # Don't log anything to avoid spam
                    except:
                        pass
                return
                
            # Set cooldown
            self.user_cooldowns[member.id] = current_time
            
            # Create a new voice channel in the same category or guild if no category
            try:
                if after.channel.category:
                    category = after.channel.category
                    new_channel = await category.create_voice_channel(
                        name=f"🌊 {member.display_name}'s Den",
                        bitrate=96000,
                        user_limit=99
                    )
                else:
                    # Create in guild directly if no category
                    new_channel = await member.guild.create_voice_channel(
                        name=f"🌊 {member.display_name}'s Den",
                        bitrate=96000,
                        user_limit=99
                    )
                
                # Store the channel in our dictionary
                self.temp_channels[new_channel.id] = member.id
                
                # Move the member to the new channel
                await member.move_to(new_channel)
                
                # Log the creation (to console only)
                print(f"🐙 Cephalo: Created temporary voice channel {new_channel.name} for {member.display_name}")
            except Exception as e:
                print(f"🐙 Cephalo: Error creating voice channel: {e}")
        
        # CHANNEL DELETION LOGIC
        if before.channel and before.channel.id in self.temp_channels:
            # Check if the channel is empty
            if len(before.channel.members) == 0:
                # Avoid duplicate deletion attempts
                if before.channel.id in self.pending_deletes:
                    return
                    
                self.pending_deletes.add(before.channel.id)
                
                # Use a delay to prevent deletion if someone joins quickly
                await asyncio.sleep(3)
                
                # Check if the channel is still empty (someone might have joined)
                channel = self.bot.get_channel(before.channel.id)
                if channel and len(channel.members) == 0:
                    try:
                        # Delete the channel
                        await channel.delete()
                        # Remove from our tracking dictionary
                        if channel.id in self.temp_channels:
                            del self.temp_channels[channel.id]
                        # Log the deletion (to console only)
                        print(f"🐙 Cephalo: Deleted empty temporary voice channel {channel.name}")
                    except Exception as e:
                        print(f"🐙 Cephalo: Error deleting voice channel: {e}")
                
                # Remove from pending deletes
                self.pending_deletes.discard(before.channel.id)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_voice(self, ctx):
        """Creates the '🐙 Create Voice Channel' channel"""
        # Create the special channel that users join to create their own channel
        try:
            category = ctx.channel.category
            if category is None:
                # If the command was used in a channel without a category, create in the guild directly
                create_channel = await ctx.guild.create_voice_channel(name="🐙 Create Voice Channel")
            else:
                # Create in the same category as the command channel
                create_channel = await category.create_voice_channel(name="🐙 Create Voice Channel")
            
            embed = discord.Embed(
                title="🐙 Dynamic Voice System Setup Complete!",
                description=f"Join {create_channel.mention} to create your own temporary voice channel.\n\nUsers will get their own **🌊 [Name]'s Den** when they join!",
                color=discord.Color.purple()
            )
            embed.set_footer(
                text="Cephalo • Dynamic Voice System",
                icon_url="https://i.imgur.com/pKBQZJE.png"
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Setup Error",
                description=f"Error setting up voice channel system: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def cleanup_voice(self, ctx):
        """Cleans up all temporary voice channels"""
        count = 0
        errors = 0
        for channel_id in list(self.temp_channels.keys()):
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.delete()
                    del self.temp_channels[channel_id]
                    count += 1
            except Exception as e:
                print(f"🐙 Cephalo: Error cleaning up voice channel {channel_id}: {e}")
                errors += 1
        
        embed = discord.Embed(
            title="🧹 Voice Channel Cleanup Complete",
            color=discord.Color.green() if errors == 0 else discord.Color.orange()
        )
        
        if errors > 0:
            embed.description = f"Cleaned up **{count}** temporary voice channels.\nFailed to clean up **{errors}** channels."
        else:
            embed.description = f"Successfully cleaned up **{count}** temporary voice channels."
        
        embed.set_footer(
            text="Cephalo • Voice Cleanup",
            icon_url="https://i.imgur.com/pKBQZJE.png"
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_voice_cooldown(self, ctx, seconds: int):
        """Sets the cooldown period for creating voice channels"""
        if seconds < 0:
            embed = discord.Embed(
                title="❌ Invalid Cooldown",
                description="Cooldown must be a positive number of seconds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        self.cooldown_period = seconds
        embed = discord.Embed(
            title="⏱️ Cooldown Updated",
            description=f"Voice channel creation cooldown set to **{seconds} seconds**.",
            color=discord.Color.blue()
        )
        embed.set_footer(
            text="Cephalo • Voice Settings",
            icon_url="https://i.imgur.com/pKBQZJE.png"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DynamicVoice(bot))