import discord
from discord.ext import commands
import json
import os
from typing import Dict, List, Optional

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "reaction_roles.json"
        self.reaction_roles = self.load_data()
    
    def load_data(self) -> Dict:
        """Load reaction roles data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_data(self):
        """Save reaction roles data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.reaction_roles, f, indent=4)
    
    def get_emoji_name(self, emoji) -> str:
        """Get the name/id of an emoji for storage"""
        if isinstance(emoji, str):
            return emoji
        else:
            return str(emoji.id) if emoji.id else emoji.name
    
    @commands.group(name='reactionroles', aliases=['rr'], invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def reaction_roles(self, ctx):
        """Main reaction roles command group"""
        embed = discord.Embed(
            title="🎭 Reaction Roles Commands",
            description="Manage reaction roles for your server",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Setup Commands",
            value="`rr add <message_id> <emoji> <role>` - Add a reaction role\n"
                  "`rr remove <message_id> <emoji>` - Remove a reaction role\n"
                  "`rr create <channel> <title> <description>` - Create a new reaction role message",
            inline=False
        )
        embed.add_field(
            name="Management Commands",
            value="`rr list` - List all reaction roles\n"
                  "`rr clear <message_id>` - Clear all reactions from a message\n"
                  "`rr panel <channel>` - Create an interactive setup panel",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @reaction_roles.command(name='add')
    @commands.has_permissions(manage_roles=True)
    async def add_reaction_role(self, ctx, message_id: int, emoji, *, role: discord.Role):
        """Add a reaction role to a message"""
        try:
            # Find the message
            message = None
            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel):
                    try:
                        message = await channel.fetch_message(message_id)
                        break
                    except (discord.NotFound, discord.Forbidden):
                        continue
            
            if not message:
                await ctx.send("❌ Message not found!")
                return
            
            # Check if bot can manage the role
            if role >= ctx.guild.me.top_role:
                await ctx.send("❌ I cannot manage this role as it's higher than my highest role!")
                return
            
            # Add the reaction to the message
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                await ctx.send("❌ Failed to add reaction. Make sure the emoji is valid!")
                return
            
            # Store the reaction role data
            message_key = str(message_id)
            emoji_key = self.get_emoji_name(emoji)
            
            if message_key not in self.reaction_roles:
                self.reaction_roles[message_key] = {}
            
            self.reaction_roles[message_key][emoji_key] = {
                'role_id': role.id,
                'guild_id': ctx.guild.id,
                'channel_id': message.channel.id
            }
            
            self.save_data()
            
            embed = discord.Embed(
                title="✅ Reaction Role Added",
                description=f"Successfully added reaction role!",
                color=discord.Color.green()
            )
            embed.add_field(name="Message ID", value=message_id, inline=True)
            embed.add_field(name="Emoji", value=emoji, inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @reaction_roles.command(name='remove')
    @commands.has_permissions(manage_roles=True)
    async def remove_reaction_role(self, ctx, message_id: int, emoji):
        """Remove a reaction role from a message"""
        message_key = str(message_id)
        emoji_key = self.get_emoji_name(emoji)
        
        if message_key not in self.reaction_roles or emoji_key not in self.reaction_roles[message_key]:
            await ctx.send("❌ Reaction role not found!")
            return
        
        # Remove from data
        del self.reaction_roles[message_key][emoji_key]
        
        # Clean up empty message entries
        if not self.reaction_roles[message_key]:
            del self.reaction_roles[message_key]
        
        self.save_data()
        
        # Try to remove the reaction from the message
        try:
            message = None
            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel):
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.clear_reaction(emoji)
                        break
                    except (discord.NotFound, discord.Forbidden):
                        continue
        except:
            pass  # Ignore if we can't remove the reaction
        
        embed = discord.Embed(
            title="✅ Reaction Role Removed",
            description=f"Successfully removed reaction role for {emoji}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @reaction_roles.command(name='list')
    @commands.has_permissions(manage_roles=True)
    async def list_reaction_roles(self, ctx):
        """List all reaction roles in the server"""
        server_roles = {}
        
        for message_id, reactions in self.reaction_roles.items():
            for emoji, data in reactions.items():
                if data['guild_id'] == ctx.guild.id:
                    if message_id not in server_roles:
                        server_roles[message_id] = []
                    
                    role = ctx.guild.get_role(data['role_id'])
                    channel = ctx.guild.get_channel(data['channel_id'])
                    
                    server_roles[message_id].append({
                        'emoji': emoji,
                        'role': role.name if role else "Deleted Role",
                        'channel': channel.name if channel else "Unknown Channel"
                    })
        
        if not server_roles:
            await ctx.send("❌ No reaction roles found in this server!")
            return
        
        embed = discord.Embed(
            title="🎭 Reaction Roles List",
            color=discord.Color.blue()
        )
        
        for message_id, roles in server_roles.items():
            role_list = []
            channel_name = roles[0]['channel'] if roles else "Unknown"
            
            for role_data in roles:
                emoji_display = role_data['emoji']
                # Handle custom emoji display
                if role_data['emoji'].isdigit():
                    custom_emoji = self.bot.get_emoji(int(role_data['emoji']))
                    if custom_emoji:
                        emoji_display = str(custom_emoji)
                
                role_list.append(f"{emoji_display} → {role_data['role']}")
            
            embed.add_field(
                name=f"Message ID: {message_id} (#{channel_name})",
                value="\n".join(role_list),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @reaction_roles.command(name='create')
    @commands.has_permissions(manage_roles=True)
    async def create_reaction_message(self, ctx, channel: discord.TextChannel, title, *, description):
        """Create a new message for reaction roles"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="React below to get roles!")
        
        try:
            message = await channel.send(embed=embed)
            
            embed = discord.Embed(
                title="✅ Reaction Role Message Created",
                description=f"Message created in {channel.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Message ID", value=str(message.id), inline=False)
            embed.add_field(name="Next Step", value=f"Use `{ctx.prefix}rr add {message.id} <emoji> <role>` to add reaction roles", inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to send messages in that channel!")
    
    @reaction_roles.command(name='clear')
    @commands.has_permissions(manage_roles=True)
    async def clear_reactions(self, ctx, message_id: int):
        """Clear all reaction roles from a message"""
        message_key = str(message_id)
        
        if message_key not in self.reaction_roles:
            await ctx.send("❌ No reaction roles found for this message!")
            return
        
        # Remove all reaction roles for this message
        del self.reaction_roles[message_key]
        self.save_data()
        
        # Try to clear all reactions from the message
        try:
            message = None
            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel):
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.clear_reactions()
                        break
                    except (discord.NotFound, discord.Forbidden):
                        continue
        except:
            pass
        
        await ctx.send("✅ All reaction roles cleared from the message!")
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle when someone adds a reaction"""
        if payload.user_id == self.bot.user.id:
            return
        
        message_key = str(payload.message_id)
        emoji_key = self.get_emoji_name(payload.emoji)
        
        if message_key not in self.reaction_roles or emoji_key not in self.reaction_roles[message_key]:
            return
        
        role_data = self.reaction_roles[message_key][emoji_key]
        
        if role_data['guild_id'] != payload.guild_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        role = guild.get_role(role_data['role_id'])
        if not role:
            return
        
        try:
            await member.add_roles(role, reason="Reaction role")
            
            # Send DM notification (optional)
            try:
                embed = discord.Embed(
                    title="✅ Role Added",
                    description=f"You have been given the **{role.name}** role in **{guild.name}**!",
                    color=discord.Color.green()
                )
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
                
        except discord.Forbidden:
            pass  # Bot doesn't have permission to add roles
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle when someone removes a reaction"""
        if payload.user_id == self.bot.user.id:
            return
        
        message_key = str(payload.message_id)
        emoji_key = self.get_emoji_name(payload.emoji)
        
        if message_key not in self.reaction_roles or emoji_key not in self.reaction_roles[message_key]:
            return
        
        role_data = self.reaction_roles[message_key][emoji_key]
        
        if role_data['guild_id'] != payload.guild_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        role = guild.get_role(role_data['role_id'])
        if not role:
            return
        
        try:
            await member.remove_roles(role, reason="Reaction role removed")
            
            # Send DM notification (optional)
            try:
                embed = discord.Embed(
                    title="➖ Role Removed",
                    description=f"The **{role.name}** role has been removed from you in **{guild.name}**.",
                    color=discord.Color.orange()
                )
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
                
        except discord.Forbidden:
            pass  # Bot doesn't have permission to remove roles

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))