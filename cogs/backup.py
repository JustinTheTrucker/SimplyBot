import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Union

class ServerBackup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_dir = "backups"
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event"""
        print("🎭 Delirium Den Server Backup cog loaded successfully")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx):
        """Backup the current server structure (channels, categories, roles)"""
        # Check if bot has administrator permissions
        if not ctx.guild.me.guild_permissions.administrator:
            error_embed = discord.Embed(
                title="❌ Missing Permissions",
                description="I need Administrator permissions to create a backup.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Backup System",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            return await ctx.send(embed=error_embed)
        
        start_embed = discord.Embed(
            title="🎭 Starting Server Backup",
            description="Creating a complete backup of your server structure. This might take a moment...",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        start_embed.set_footer(
            text="Delirium Den • Backup System",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await ctx.send(embed=start_embed)
        
        guild = ctx.guild
        backup_data = {
            "name": guild.name,
            "icon_url": str(guild.icon.url) if guild.icon else None,
            "created_at": str(guild.created_at),
            "categories": [],
            "channels": [],
            "roles": [],
            "backup_date": str(datetime.utcnow()),
            "backed_up_by": f"{ctx.author.name}#{ctx.author.discriminator}",
            "server_id": guild.id,
            "member_count": guild.member_count
        }
        
        # Backup roles (reversed to maintain hierarchy)
        progress_embed = discord.Embed(
            title="⚙️ Backup in Progress",
            description="Backing up roles...",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        progress_embed.set_footer(
            text="Delirium Den • Backup Progress",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        progress_msg = await ctx.send(embed=progress_embed)
        
        roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        for role in roles:
            # Skip @everyone role as it can't be recreated
            if role.name == "@everyone":
                continue
                
            role_data = {
                "name": role.name,
                "color": role.color.value,
                "permissions": role.permissions.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "position": role.position,
                "managed": role.managed
            }
            backup_data["roles"].append(role_data)
        
        # Backup categories
        progress_embed.description = "Backing up categories..."
        await progress_msg.edit(embed=progress_embed)
        
        for category in guild.categories:
            category_data = {
                "name": category.name,
                "position": category.position,
                "overwrites": self._get_overwrites(category),
                "id": category.id  # Store ID for channel references
            }
            backup_data["categories"].append(category_data)
        
        # Backup channels
        progress_embed.description = "Backing up channels..."
        await progress_msg.edit(embed=progress_embed)
        
        for channel in guild.channels:
            # Skip categories as they're already backed up
            if isinstance(channel, discord.CategoryChannel):
                continue
                
            channel_data = {
                "name": channel.name,
                "type": str(channel.type),
                "position": channel.position,
                "category_id": channel.category_id,
                "overwrites": self._get_overwrites(channel),
                "slowmode_delay": getattr(channel, "slowmode_delay", 0),
                "nsfw": getattr(channel, "nsfw", False),
                "topic": getattr(channel, "topic", None)
            }
            backup_data["channels"].append(channel_data)
        
        # Save to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.backup_dir}/{guild.name}_{timestamp}.json"
        
        # Clean filename for filesystem compatibility
        safe_filename = "".join(c for c in backup_filename if c.isalnum() or c in (' ', '-', '_', '.', '/')).rstrip()
        
        with open(safe_filename, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=4)
        
        # Create completion embed
        complete_embed = discord.Embed(
            title="✅ Backup Complete",
            description=f"Successfully created backup for **{guild.name}**!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        complete_embed.add_field(
            name="📊 Backup Statistics",
            value=f"**Roles:** {len(backup_data['roles'])}\n**Categories:** {len(backup_data['categories'])}\n**Channels:** {len(backup_data['channels'])}",
            inline=True
        )
        
        complete_embed.add_field(
            name="📁 File Info",
            value=f"**Filename:** `{os.path.basename(safe_filename)}`\n**Size:** {os.path.getsize(safe_filename)} bytes",
            inline=True
        )
        
        complete_embed.add_field(
            name="📧 Delivery",
            value="Backup file will be sent via DM if possible",
            inline=False
        )
        
        complete_embed.set_footer(
            text="Delirium Den • Backup Complete",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await progress_msg.edit(embed=complete_embed)
        
        # Send backup file to user
        try:
            dm_embed = discord.Embed(
                title="🎭 Delirium Den Server Backup",
                description=f"Your backup for **{guild.name}** is ready!",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            dm_embed.add_field(
                name="📋 Backup Details",
                value=f"**Server:** {guild.name}\n**Created:** <t:{int(datetime.utcnow().timestamp())}:F>\n**Backed up by:** {ctx.author.mention}",
                inline=False
            )
            dm_embed.set_footer(
                text="Delirium Den • Server Backup",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            with open(safe_filename, "rb") as f:
                await ctx.author.send(embed=dm_embed, file=discord.File(f, filename=f"{guild.name}_backup.json"))
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send backup file via DM. Please check your privacy settings.")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def restore(self, ctx, backup_file: str = None):
        """Restore a server from backup by completely wiping it first"""
        # Check if bot has administrator permissions
        if not ctx.guild.me.guild_permissions.administrator:
            error_embed = discord.Embed(
                title="❌ Missing Permissions",
                description="I need Administrator permissions to restore a backup.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Restore System",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            return await ctx.send(embed=error_embed)
        
        # If no file specified, list available backups
        if not backup_file:
            files = [f for f in os.listdir(self.backup_dir) if f.endswith('.json')]
            if not files:
                no_backups_embed = discord.Embed(
                    title="📁 No Backups Found",
                    description="No backup files found. Use `!backup` to create one first.",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                no_backups_embed.set_footer(
                    text="Delirium Den • Restore System",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                return await ctx.send(embed=no_backups_embed)
            
            list_embed = discord.Embed(
                title="📋 Available Backups",
                description="Here are the available backup files:",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            file_list = "\n".join([f"• `{file}`" for file in files[:10]])  # Limit to 10 files
            if len(files) > 10:
                file_list += f"\n... and {len(files) - 10} more files"
                
            list_embed.add_field(
                name="Backup Files",
                value=file_list,
                inline=False
            )
            
            list_embed.add_field(
                name="Usage",
                value="Use `!restore filename.json` to restore a backup.",
                inline=False
            )
            
            list_embed.set_footer(
                text="Delirium Den • Available Backups",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            return await ctx.send(embed=list_embed)
        
        # Check if file exists
        backup_path = f"{self.backup_dir}/{backup_file}"
        if not os.path.isfile(backup_path):
            error_embed = discord.Embed(
                title="❌ File Not Found",
                description=f"Backup file `{backup_file}` not found.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • File Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            return await ctx.send(embed=error_embed)
        
        # Load backup data
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Invalid Backup File",
                description=f"Could not read backup file: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • File Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            return await ctx.send(embed=error_embed)
        
        # EXTREME WARNING for destructive operation
        warning_embed = discord.Embed(
            title="⚠️ DANGER: DESTRUCTIVE OPERATION ⚠️",
            description=(
                f"This will **DELETE ALL** existing channels, categories, and roles in **{ctx.guild.name}**, "
                "then recreate everything from the backup.\n\n"
                f"**This action cannot be undone!**"
            ),
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        warning_embed.add_field(
            name="📋 Backup Details",
            value=(
                f"**Source Server:** {backup_data['name']}\n"
                f"**Backup Date:** {backup_data['backup_date'][:19]}\n"
                f"**Contains:** {len(backup_data['roles'])} roles, "
                f"{len(backup_data['categories'])} categories, "
                f"{len(backup_data['channels'])} channels"
            ),
            inline=False
        )
        
        warning_embed.add_field(
            name="✅ Confirmation Required",
            value="To confirm this destructive action, type: `CONFIRM-WIPE-SERVER`\n*You have 60 seconds to respond.*",
            inline=False
        )
        
        warning_embed.set_footer(
            text="Delirium Den • Server Restore Warning",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=warning_embed)
        
        # Wait for text confirmation
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content == "CONFIRM-WIPE-SERVER"
        
        try:
            await self.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Operation Cancelled",
                description="Restoration cancelled due to timeout.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            timeout_embed.set_footer(
                text="Delirium Den • Operation Cancelled",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            return await ctx.send(embed=timeout_embed)
        
        # Create a temporary channel for logs
        temp_channel = None
        try:
            temp_channel = await ctx.guild.create_text_channel(
                "delirium-den-restore-logs",
                topic="Temporary channel for server restoration logs"
            )
            success_embed = discord.Embed(
                title="📝 Log Channel Created",
                description=f"Created temporary log channel {temp_channel.mention}. Restoration logs will be posted there.",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            success_embed.set_footer(
                text="Delirium Den • Restore System",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=success_embed)
        except Exception as e:
            await ctx.send(f"Could not create temporary log channel: {str(e)}")
            temp_channel = ctx.channel
        
        # Function to post status updates
        async def log_status(message, color=discord.Color.blue()):
            try:
                log_embed = discord.Embed(
                    description=message,
                    color=color,
                    timestamp=datetime.utcnow()
                )
                log_embed.set_footer(
                    text="Delirium Den • Restore Log",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await temp_channel.send(embed=log_embed)
            except:
                print(f"[RESTORE LOG] {message}")
        
        await log_status("⚠️ **SERVER WIPE AND RESTORE BEGINNING** ⚠️", discord.Color.red())
        await log_status(f"Starting restore of server from backup: {backup_file}")
        
        # Call the wipe function
        await self._wipe_server(ctx.guild, temp_channel, log_status)
        
        # STAGE 3: Recreate all roles
        await log_status("🔨 **PHASE 3: CREATING ROLES**", discord.Color.green())
        role_map = {}  # Maps role names to new role IDs
        
        # Map @everyone role
        role_map["@everyone"] = ctx.guild.default_role.id
        
        # Create roles in reverse order to maintain hierarchy
        for role_data in backup_data["roles"]:
            try:
                # Skip managed roles (bot roles, integration roles)
                if role_data.get("managed", False):
                    continue
                    
                # Skip problematic role names
                if role_data["name"].startswith(("@", "Dyno", "MEE6", "Ticket Tool")) or role_data["name"].lower().endswith(" bot"):
                    continue
                    
                # Create role
                new_role = await ctx.guild.create_role(
                    name=role_data["name"],
                    permissions=discord.Permissions(role_data["permissions"]),
                    color=discord.Color(role_data["color"]),
                    hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"]
                )
                
                # Store role mapping
                role_map[role_data["name"]] = new_role.id
                await log_status(f"✅ Created role: {new_role.name}")
                await asyncio.sleep(0.5)  # Rate limit prevention
            except Exception as e:
                await log_status(f"⚠️ Error creating role {role_data['name']}: {str(e)}", discord.Color.orange())
        
        # STAGE 4: Recreate categories
        await log_status("🔨 **PHASE 4: CREATING CATEGORIES**", discord.Color.green())
        category_map = {}  # Maps old category IDs to new ones
        
        for category_data in backup_data["categories"]:
            try:
                # Create permission overwrites
                overwrites = self._restore_overwrites(ctx.guild, category_data["overwrites"], role_map)
                
                # Create category
                new_category = await ctx.guild.create_category(
                    name=category_data["name"],
                    overwrites=overwrites
                )
                
                # Store category mapping
                category_map[category_data["id"]] = new_category.id
                await log_status(f"✅ Created category: {new_category.name}")
                await asyncio.sleep(0.5)  # Rate limit prevention
            except Exception as e:
                await log_status(f"⚠️ Error creating category {category_data['name']}: {str(e)}", discord.Color.orange())
        
        # STAGE 5: Recreate channels
        await log_status("🔨 **PHASE 5: CREATING CHANNELS**", discord.Color.green())
        
        # Sort channels by position for proper ordering
        sorted_channels = sorted(backup_data["channels"], key=lambda c: c["position"])
        
        for channel_data in sorted_channels:
            try:
                # Get category if it exists
                category = None
                if channel_data["category_id"] and channel_data["category_id"] in category_map:
                    category = ctx.guild.get_channel(category_map[channel_data["category_id"]])
                
                # Create permission overwrites
                overwrites = self._restore_overwrites(ctx.guild, channel_data["overwrites"], role_map)
                
                # Create channel based on type
                if channel_data["type"] == "text":
                    new_channel = await ctx.guild.create_text_channel(
                        name=channel_data["name"],
                        overwrites=overwrites,
                        category=category,
                        topic=channel_data["topic"],
                        slowmode_delay=channel_data["slowmode_delay"],
                        nsfw=channel_data["nsfw"]
                    )
                    await log_status(f"✅ Created text channel: {new_channel.name}")
                    
                elif channel_data["type"] == "voice":
                    new_channel = await ctx.guild.create_voice_channel(
                        name=channel_data["name"],
                        overwrites=overwrites,
                        category=category
                    )
                    await log_status(f"✅ Created voice channel: {new_channel.name}")
                    
                elif channel_data["type"] == "forum":
                    try:
                        new_channel = await ctx.guild.create_forum(
                            name=channel_data["name"],
                            overwrites=overwrites,
                            category=category
                        )
                        await log_status(f"✅ Created forum channel: {new_channel.name}")
                    except Exception as e:
                        await log_status(f"⚠️ Error creating forum channel {channel_data['name']}: {str(e)}", discord.Color.orange())
                
                await asyncio.sleep(0.5)  # Rate limit prevention
            except Exception as e:
                await log_status(f"⚠️ Error creating channel {channel_data['name']}: {str(e)}", discord.Color.orange())
        
        # Restoration complete
        await log_status("✅ **SERVER RESTORATION COMPLETE!**", discord.Color.green())
        await log_status(f"Successfully restored server layout from backup `{backup_file}`")
        await log_status("This channel will be deleted in 60 seconds...")
        
        # Clean up temporary channel
        if temp_channel != ctx.channel:
            await asyncio.sleep(60)
            try:
                await temp_channel.delete(reason="Restore operation completed")
            except:
                pass
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wipe(self, ctx):
        """Completely wipe the server (delete all channels, categories, and roles)"""
        # Check if bot has administrator permissions
        if not ctx.guild.me.guild_permissions.administrator:
            error_embed = discord.Embed(
                title="❌ Missing Permissions",
                description="I need Administrator permissions to wipe the server.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Wipe System",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            return await ctx.send(embed=error_embed)
        
        # EXTREME WARNING for destructive operation
        warning_embed = discord.Embed(
            title="⚠️ EXTREME DANGER: COMPLETE SERVER WIPE ⚠️",
            description=(
                f"This will **DELETE EVERYTHING** in **{ctx.guild.name}**, including:\n"
                "• All channels\n"
                "• All categories\n"
                "• All roles\n"
                "• All permission settings\n\n"
                f"**This action cannot be undone!**"
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        
        warning_embed.add_field(
            name="✅ Confirmation Required",
            value="To confirm this extremely destructive action, type: `CONFIRM-COMPLETE-WIPE`\n*You have 60 seconds to respond.*",
            inline=False
        )
        
        warning_embed.set_footer(
            text="Delirium Den • Server Wipe Warning",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=warning_embed)
        
        # Wait for text confirmation
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content == "CONFIRM-COMPLETE-WIPE"
        
        try:
            await self.bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Operation Cancelled",
                description="Wipe operation cancelled due to timeout.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            timeout_embed.set_footer(
                text="Delirium Den • Operation Cancelled",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            return await ctx.send(embed=timeout_embed)
        
        # Create a temporary channel for logs
        temp_channel = None
        try:
            temp_channel = await ctx.guild.create_text_channel(
                "delirium-den-wipe-logs",
                topic="Temporary channel for server wipe logs"
            )
            success_embed = discord.Embed(
                title="📝 Log Channel Created",
                description=f"Created temporary log channel {temp_channel.mention}. Wipe logs will be posted there.",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            success_embed.set_footer(
                text="Delirium Den • Wipe System",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=success_embed)
        except Exception as e:
            await ctx.send(f"Could not create temporary log channel: {str(e)}")
            temp_channel = ctx.channel
        
        # Function to post status updates
        async def log_status(message, color=discord.Color.blue()):
            try:
                log_embed = discord.Embed(
                    description=message,
                    color=color,
                    timestamp=datetime.utcnow()
                )
                log_embed.set_footer(
                    text="Delirium Den • Wipe Log",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await temp_channel.send(embed=log_embed)
            except:
                print(f"[WIPE LOG] {message}")
        
        await log_status("⚠️ **COMPLETE SERVER WIPE BEGINNING** ⚠️", discord.Color.red())
        
        # Call the wipe function
        await self._wipe_server(ctx.guild, temp_channel, log_status)
        
        # Wipe complete
        await log_status("✅ **SERVER WIPE COMPLETE!**", discord.Color.green())
        await log_status("All channels, categories, and roles have been deleted.")
        await log_status("This channel will be deleted in 60 seconds...")
        
        # Clean up temporary channel
        if temp_channel != ctx.channel:
            await asyncio.sleep(60)
            try:
                await temp_channel.delete(reason="Wipe operation completed")
            except:
                pass
    
    async def _wipe_server(self, guild, temp_channel, log_status):
        """Wipe the server (delete all channels, categories, and roles)"""
        # STAGE 1: Delete all channels except temp channel
        await log_status("🗑️ **PHASE 1: DELETING CHANNELS**", discord.Color.orange())
        deleted_count = 0
        
        for channel in guild.channels:
            if channel != temp_channel:
                try:
                    await channel.delete(reason="Server wipe operation")
                    deleted_count += 1
                    if deleted_count % 5 == 0:  # Log progress every 5 channels
                        await log_status(f"Deleted {deleted_count} channels so far...")
                    await asyncio.sleep(0.5)  # Rate limit prevention
                except Exception as e:
                    await log_status(f"⚠️ Error deleting channel {channel.name}: {str(e)}", discord.Color.orange())
        
        await log_status(f"✅ Deleted {deleted_count} channels")
        
        # STAGE 2: Delete all roles except @everyone and bot role
        await log_status("🗑️ **PHASE 2: DELETING ROLES**", discord.Color.orange())
        deleted_roles = 0
        
        bot_role = guild.me.top_role
        
        for role in reversed(guild.roles):  # Reverse to delete from bottom up
            # Skip @everyone, bot roles, and managed roles
            if role == guild.default_role or role == bot_role or role.managed:
                continue
                
            try:
                await role.delete(reason="Server wipe operation")
                deleted_roles += 1
                await asyncio.sleep(0.5)  # Rate limit prevention
            except Exception as e:
                await log_status(f"⚠️ Error deleting role {role.name}: {str(e)}", discord.Color.orange())
        
        await log_status(f"✅ Deleted {deleted_roles} roles")
        
        return True
    
    def _get_overwrites(self, channel):
        """Convert channel permission overwrites to serializable format"""
        overwrites = []
        for target, overwrite in channel.overwrites.items():
            target_type = "role" if isinstance(target, discord.Role) else "member"
            
            # Skip member overwrites for simplicity
            if target_type == "member":
                continue
                
            overwrite_dict = {
                "id": target.id,
                "type": target_type,
                "name": target.name,
                "allow": overwrite.pair()[0].value,
                "deny": overwrite.pair()[1].value
            }
            overwrites.append(overwrite_dict)
        return overwrites
    
    def _restore_overwrites(self, guild, overwrites_data, role_map):
        """Restore permission overwrites"""
        result = {}
        for overwrite in overwrites_data:
            # Skip members for now, just use roles
            if overwrite["type"] != "role":
                continue
            
            # Handle @everyone role
            if overwrite["name"] == "@everyone":
                target = guild.default_role
            else:
                # Get role ID from the mapping
                role_id = role_map.get(overwrite["name"])
                if not role_id:
                    continue
                    
                # Get the role object
                target = guild.get_role(role_id)
                if not target:
                    continue
            
            # Create permission objects
            allow = discord.Permissions(overwrite["allow"])
            deny = discord.Permissions(overwrite["deny"])
            
            # Set the overwrites
            result[target] = discord.PermissionOverwrite.from_pair(allow, deny)
        return result
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup_help(self, ctx):
        """Show help for backup system commands"""
        help_embed = discord.Embed(
            title="🎭 Delirium Den Backup System",
            description="Complete server backup and restore system for Delirium Den.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        help_embed.add_field(
            name="📋 Available Commands