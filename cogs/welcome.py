import discord
from discord.ext import commands
import os
from datetime import datetime
import pytz


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = int(os.getenv('WELCOME_CHANNEL_ID'))
        self.unverified_role_id = 1296917049435492432  # Unverified role
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event"""
        print("🎭 Delirium Den Welcome cog loaded successfully")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message and assign unverified role when a member joins"""
        
        # Assign the unverified role
        try:
            role = member.guild.get_role(self.unverified_role_id)
            if role:
                await member.add_roles(role, reason="Auto-assigned unverified role to new member")
                print(f"🎭 ✅ Assigned unverified role '{role.name}' to {member.name}")
            else:
                print(f"🎭 ⚠️ Could not find unverified role with ID {self.unverified_role_id}")
        except discord.Forbidden:
            print(f"🎭 ❌ Missing permissions to assign unverified role to {member.name}")
        except discord.HTTPException as e:
            print(f"🎭 ❌ HTTP error assigning unverified role to {member.name}: {e}")
        except Exception as e:
            print(f"🎭 ❌ Unexpected error assigning unverified role to {member.name}: {e}")
        
        # Send welcome message
        channel = self.bot.get_channel(self.welcome_channel_id)
        if not channel:
            print(f"🎭 ❌ Welcome channel not found: {self.welcome_channel_id}")
            return
        
        # Get member count (excluding bots)
        member_count = len([m for m in member.guild.members if not m.bot])
        
        # Get current time in EST
        est = pytz.timezone('US/Eastern')
        current_time_est = datetime.now(est)
        
        # Create welcome embed
        embed = discord.Embed(
            title=f"🎭 Welcome to the Delirium Den! 🎭",
            description=f"Welcome {member.mention} to our friendly Discord community! We're glad you're here.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎪 Welcome to the Den",
            value=f"**Member #{member_count}** • Great to have you here!",
            inline=True
        )
        
        embed.add_field(
            name="📅 Account Age",
            value=f"Created: <t:{int(member.created_at.timestamp())}:R>",
            inline=True
        )
        
        embed.add_field(
            name="🎮 What Awaits You",
            value="🎭 **Discord Community**\n• Friendly and welcoming community\n• Creative discussions and events\n• Active and helpful staff team\n• Regular community activities",
            inline=False
        )
        
        embed.add_field(
            name="⛏️ **Minecraft Features**",
            value="• **Survival Multiplayer (SMP)** - Collaborative gameplay\n• **Creative Building** - Express your creativity\n• **Community Events** - Join the fun\n• **Dedicated Staff** - We're here to help",
            inline=False
        )
        
        embed.add_field(
            name="🚀 Getting Started",
            value=f"**1.** Complete verification to access all channels\n**2.** Read the rules in <#{os.getenv('RULES_CHANNEL_ID', '0')}>\n**3.** Introduce yourself and start chatting\n**4.** Need help? Create a ticket in <#{os.getenv('TICKETS_CHANNEL_ID', '0')}>",
            inline=False
        )
        
        embed.add_field(
            name="🎭 Community Guidelines",
            value="• **Be respectful** to all community members\n• **Be welcoming** to fellow members\n• **Follow the rules** - they help keep things friendly\n• **Have fun** - that's what we're here for!",
            inline=False
        )
        
        # Add user avatar as thumbnail
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Add server icon as image (if available)
        if member.guild.icon:
            embed.set_image(url=member.guild.icon.url)
        
        embed.set_footer(
            text=f"Delirium Den • Joined at {current_time_est.strftime('%m-%d-%Y %I:%M:%S %p')} EST",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        try:
            # Send welcome message
            welcome_msg = await channel.send(f"🎭 Everyone welcome {member.mention} to the Delirium Den! 🎭", embed=embed)
            
            # Add reactions to welcome message
            reactions = ["🎭", "👋", "🎉", "✨", "💜"]
            for reaction in reactions:
                try:
                    await welcome_msg.add_reaction(reaction)
                except:
                    pass  # Ignore reaction errors
                    
            print(f"🎭 ✅ Sent welcome message for {member.name}")
            
        except discord.Forbidden:
            print(f"🎭 ❌ Missing permissions to send welcome message for {member.name}")
        except Exception as e:
            print(f"🎭 ❌ Error sending welcome message for {member.name}: {e}")
        
        # Send a DM welcome message (optional)
        try:
            dm_embed = discord.Embed(
                title="🎭 Welcome to Delirium Den!",
                description="Thank you for joining our friendly community!",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            dm_embed.add_field(
                name="🚀 Quick Start Guide",
                value="1. **Read the rules** to understand our community\n3. **Introduce yourself** and start chatting\n4. **Join our Minecraft SMP** if you're interested!",
                inline=False
            )
            
            dm_embed.add_field(
                name="💬 Need Help?",
                value="Create a support ticket in the server or ask any staff member. We're here to help you get settled in!",
                inline=False
            )
            
            dm_embed.add_field(
                name="🎪 What Makes Us Special",
                value="We're a welcoming community that values creativity, friendship, and fun. Come as you are and make yourself at home!",
                inline=False
            )
            
            dm_embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
            dm_embed.set_footer(
                text="Delirium Den • Welcome Message",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await member.send(embed=dm_embed)
            print(f"🎭 ✅ Sent DM welcome message to {member.name}")
            
        except discord.Forbidden:
            print(f"🎭 ℹ️ Could not send DM to {member.name} (DMs disabled)")
        except Exception as e:
            print(f"🎭 ⚠️ Error sending DM welcome to {member.name}: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send goodbye message when a member leaves"""
        channel = self.bot.get_channel(self.welcome_channel_id)
        if not channel:
            return
        
        # Calculate how long they were in the server
        join_date = member.joined_at
        leave_date = datetime.utcnow()
        time_in_server = leave_date - join_date if join_date else None
        
        # Get current member count
        current_member_count = len([m for m in member.guild.members if not m.bot])
        
        embed = discord.Embed(
            title="👋 Farewell from the Den",
            description=f"**{member.name}** has left the Delirium Den. We'll miss them!",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎭 Departed Member",
            value=f"**Username:** {member.name}#{member.discriminator}\n**ID:** {member.id}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Server Stats",
            value=f"**Members Now:** {current_member_count}\n**Account Age:** <t:{int(member.created_at.timestamp())}:R>",
            inline=True
        )
        
        if time_in_server:
            days_in_server = time_in_server.days
            hours_in_server = time_in_server.seconds // 3600
            
            if days_in_server > 0:
                time_text = f"{days_in_server} days"
                if hours_in_server > 0:
                    time_text += f" and {hours_in_server} hours"
            else:
                time_text = f"{hours_in_server} hours" if hours_in_server > 0 else "Less than an hour"
                
            embed.add_field(
                name="⏰ Time in Den",
                value=time_text,
                inline=True
            )
        
        # Add some flavor text based on how long they stayed
        if time_in_server:
            if time_in_server.days > 30:
                flavor = "They were a valued member of our community. 🎭"
            elif time_in_server.days > 7:
                flavor = "They got to know our community well. 🎪"
            elif time_in_server.days > 1:
                flavor = "They spent some good time with us. ✨"
            else:
                flavor = "They briefly visited our community. 👻"
        else:
            flavor = "Their journey with us has ended. 🌙"
            
        embed.add_field(
            name="💭 Reflection",
            value=flavor,
            inline=False
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Delirium Den • Hope to see them again someday",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        try:
            goodbye_msg = await channel.send(embed=embed)
            
            # Add a farewell reaction
            try:
                await goodbye_msg.add_reaction("👋")
                await goodbye_msg.add_reaction("💔")
            except:
                pass
                
            print(f"🎭 ✅ Sent goodbye message for {member.name}")
            
        except discord.Forbidden:
            print(f"🎭 ❌ Missing permissions to send goodbye message for {member.name}")
        except Exception as e:
            print(f"🎭 ❌ Error sending goodbye message for {member.name}: {e}")
    
    @commands.command(name="welcome_test")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx, member: discord.Member = None):
        """Test the welcome message system"""
        if member is None:
            member = ctx.author
            
        # Manually trigger the welcome event
        await self.on_member_join(member)
        
        success_embed = discord.Embed(
            title="✅ Welcome Test Complete",
            description=f"Test welcome message sent for {member.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="Tested By",
            value=ctx.author.mention,
            inline=True
        )
        success_embed.add_field(
            name="Test Subject",
            value=member.mention,
            inline=True
        )
        success_embed.set_footer(
            text="Delirium Den • Welcome Test",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=success_embed, delete_after=10)
        
        # Clean up command message
        try:
            await ctx.message.delete()
        except:
            pass
    
    @commands.command(name="goodbye_test")
    @commands.has_permissions(administrator=True)
    async def test_goodbye(self, ctx, member: discord.Member = None):
        """Test the goodbye message system"""
        if member is None:
            member = ctx.author
            
        # Manually trigger the goodbye event
        await self.on_member_remove(member)
        
        success_embed = discord.Embed(
            title="✅ Goodbye Test Complete",
            description=f"Test goodbye message sent for {member.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="Tested By",
            value=ctx.author.mention,
            inline=True
        )
        success_embed.add_field(
            name="Test Subject",
            value=member.mention,
            inline=True
        )
        success_embed.set_footer(
            text="Delirium Den • Goodbye Test",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=success_embed, delete_after=10)
        
        # Clean up command message
        try:
            await ctx.message.delete()
        except:
            pass
    
    @commands.command(name="welcome_info")
    @commands.has_permissions(manage_guild=True)
    async def welcome_info(self, ctx):
        """Show information about the welcome system"""
        
        # Get channel info
        welcome_channel = self.bot.get_channel(self.welcome_channel_id)
        
        info_embed = discord.Embed(
            title="🎭 Delirium Den Welcome System",
            description="Information about the server welcome and goodbye system.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        info_embed.add_field(
            name="📍 Welcome Channel",
            value=welcome_channel.mention if welcome_channel else "❌ Not configured or not found",
            inline=True
        )
        
        info_embed.add_field(
            name="🔐 Unverified Role",
            value=unverified_role.mention if unverified_role else "❌ Not found",
            inline=True
        )
        
        info_embed.add_field(
            name="📊 Server Statistics",
            value=f"**Total Members:** {ctx.guild.member_count}\n**Humans:** {len([m for m in ctx.guild.members if not m.bot])}\n**Bots:** {len([m for m in ctx.guild.members if m.bot])}",
            inline=True
        )
        
        info_embed.add_field(
            name="🛠️ Features",
            value="• **Auto Role Assignment** - New members get unverified role\n• **Rich Welcome Messages** - Branded embeds with server info\n• **Goodbye Messages** - Track member departures\n• **DM Welcome** - Private welcome message\n• **Reaction Support** - Auto-reactions on messages",
            inline=False
        )
        
        info_embed.add_field(
            name="🔧 Test Commands",
            value="• `!welcome_test [@user]` - Test welcome message\n• `!goodbye_test [@user]` - Test goodbye message\n• `!welcome_info` - Show this information",
            inline=False
        )
        
        info_embed.add_field(
            name="⚙️ Configuration",
            value=f"**Welcome Channel ID:** `{self.welcome_channel_id}`\n**Unverified Role ID:** `{self.unverified_role_id}`",
            inline=False
        )
        
        info_embed.set_footer(
            text="Delirium Den • Welcome System Info",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=info_embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))