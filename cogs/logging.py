import discord
from discord.ext import commands
from datetime import datetime, timedelta
import re
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WebhookLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Get webhook URL from environment variable
        self.webhook_url = os.getenv("WEBHOOK_URL")
        if not self.webhook_url:
            print("Warning: WEBHOOK_URL not found in environment variables")
        
        # Get staff server ID for context
        self.staff_server_id = int(os.getenv("STAFF_SERVER_ID", "0"))
        # Get the main server name for reference
        self.main_server_name = os.getenv("SERVER_NAME", "Delirium Den")

    def get_role_info(self, role, guild_id=None, staff_server_id=None):
        """Format role information based on whether it's from a different server"""
        different_server = guild_id is not None and staff_server_id is not None and guild_id != staff_server_id
        
        try:
            role_id = role.id
            role_name = role.name
            
            if different_server:
                return f"{role_name}"
            else:
                return f"<@&{role_id}>"
        except AttributeError:
            try:
                role_str = str(role)
                if role_str != "@unknown-role" and role_str != "Unknown Role":
                    return f"{role_str}"
            except:
                pass
                
            try:
                return f"Role ID: {role.id}"
            except:
                pass
                
            try:
                return f"{role}"
            except:
                return "Unknown Role"

    async def get_audit_log_entry(self, guild, action_type, target=None, limit=10):
        """Get the most recent audit log entry for a specific action and target"""
        if not guild.me.guild_permissions.view_audit_log:
            return None
            
        try:
            # Wait a short time to ensure the audit log entry has been created
            await asyncio.sleep(0.5)
            
            # Get audit logs with the specified action type
            async for entry in guild.audit_logs(limit=limit, action=action_type):
                # If target is provided, match it with the entry target
                if target is not None:
                    # Check if target is a member/user
                    if isinstance(target, (discord.Member, discord.User)):
                        if entry.target.id == target.id:
                            return entry
                    # Check if target is a message (match channel and user)
                    elif hasattr(target, 'author') and hasattr(target, 'channel'):
                        if entry.target.id == target.author.id and entry.extra.channel.id == target.channel.id:
                            return entry
                    # Check if target is a channel
                    elif isinstance(target, discord.abc.GuildChannel):
                        if entry.target.id == target.id:
                            return entry
                    # Check if target is a role
                    elif isinstance(target, discord.Role):
                        if entry.target.id == target.id:
                            return entry
                # If no target provided or target doesn't match any type above, return the most recent entry
                else:
                    return entry
                
            # If we went through all entries and didn't find a match, return None
            return None
        except Exception as e:
            print(f"Error getting audit log entry: {e}")
            return None

    async def send_webhook(self, embed, guild=None):
        """Send a log event via webhook"""
        if not self.webhook_url:
            print("Warning: No webhook URL configured, skipping log event")
            return
            
        try:
            # Add the server info to the footer if guild is provided
            footer_text = embed.footer.text
            icon_url = embed.footer.icon_url
            
            if guild and guild.id != self.staff_server_id:
                # If the footer text already exists, prepend the server name
                if footer_text:
                    embed.set_footer(
                        text=f"Server: {guild.name} • {footer_text}",
                        icon_url=icon_url
                    )
                else:
                    embed.set_footer(
                        text=f"Server: {guild.name}",
                        icon_url=icon_url
                    )
            
            # Convert embed to dict for webhook
            webhook_data = {
                "embeds": [embed.to_dict()]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=webhook_data) as response:
                    if response.status not in [200, 204]:
                        print(f"Webhook request failed with status {response.status}: {await response.text()}")
                        
        except Exception as e:
            print(f"Error sending webhook: {e}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log deleted messages"""
        if message.author.bot:
            return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Author", value=f"{message.author.mention} ({message.author})", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        
        # Extract content, up to 1024 characters
        content = message.content[:1024] if message.content else "No text content"
        embed.add_field(name="Content", value=content, inline=False)
        
        # Check for attachments
        if message.attachments:
            attachment_info = []
            for i, attachment in enumerate(message.attachments, 1):
                attachment_info.append(f"{i}. {attachment.filename} - {attachment.url}")
            
            embed.add_field(
                name=f"Attachments ({len(message.attachments)})",
                value="\n".join(attachment_info)[:1024],
                inline=False
            )
        
        # Check for links in the message
        urls = re.findall(r'(https?://\S+)', message.content)
        if urls:
            embed.add_field(
                name=f"Links ({len(urls)})",
                value="\n".join(urls)[:1024],
                inline=False
            )
        
        # Add created at time
        created_time = int(message.created_at.timestamp())
        time_diff = int(discord.utils.utcnow().timestamp()) - created_time
        time_text = f"<t:{created_time}:F> ({time_diff} seconds ago)"
        embed.add_field(name="Created", value=time_text, inline=True)
        
        # Add responsible user from audit log if available
        entry = await self.get_audit_log_entry(message.guild, discord.AuditLogAction.message_delete, message)
        if entry and entry.user:
            # Make sure it's a recent delete action (within last 5 seconds)
            entry_time = int((discord.utils.utcnow() - entry.created_at).total_seconds())
            if entry_time < 5:
                embed.add_field(
                    name="Deleted By",
                    value=f"{entry.user.mention} ({entry.user})",
                    inline=True
                )
                
                # Add reason if available
                if entry.reason:
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
        
        embed.set_footer(
            text=f"Delirium Den • Message ID: {message.id}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(embed, message.guild)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log edited messages"""
        if before.author.bot or before.content == after.content:
            return

        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Author", value=f"{before.author.mention} ({before.author})", inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=before.content[:1024] if before.content else "No text content", inline=False)
        embed.add_field(name="After", value=after.content[:1024] if after.content else "No text content", inline=False)
        
        # Add message link
        message_link = f"https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id}"
        embed.add_field(name="Message Link", value=f"[Jump to Message]({message_link})", inline=False)
        
        embed.set_footer(
            text=f"Delirium Den • Message ID: {before.id}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(embed, before.guild)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Log bulk message deletions"""
        if not messages:
            return
            
        # Get the channel where messages were deleted
        channel = messages[0].channel
        guild = messages[0].guild
        
        embed = discord.Embed(
            title="🗑️ Bulk Message Delete",
            description=f"**{len(messages)}** messages were deleted in {channel.mention}",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        
        # Count messages by author
        author_counts = {}
        for message in messages:
            author_name = str(message.author)
            if author_name in author_counts:
                author_counts[author_name] += 1
            else:
                author_counts[author_name] = 1
        
        # Format author counts
        author_text = "\n".join([f"**{author}**: {count} messages" for author, count in author_counts.items()])
        if len(author_text) > 1024:
            author_text = author_text[:1021] + "..."
            
        embed.add_field(name="Authors", value=author_text, inline=False)
        
        # Add responsible user from audit log if available
        entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.message_bulk_delete)
        if entry and entry.user:
            # Make sure it's a recent action (within last 10 seconds)
            entry_time = int((discord.utils.utcnow() - entry.created_at).total_seconds())
            if entry_time < 10:
                embed.add_field(
                    name="Deleted By",
                    value=f"{entry.user.mention} ({entry.user})",
                    inline=True
                )
                
                # Add reason if available
                if entry.reason:
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
        
        embed.set_footer(
            text=f"Delirium Den • Channel ID: {channel.id}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(embed, guild)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Log member bans"""
        embed = discord.Embed(
            title="🔨 Member Banned",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="User", value=f"{user.mention} ({user})", inline=True)
        embed.add_field(name="User ID", value=user.id, inline=True)
        
        # Add responsible user from audit log
        entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.ban, user)
        if entry and entry.user:
            embed.add_field(
                name="Banned By",
                value=f"{entry.user.mention} ({entry.user})",
                inline=True
            )
            
            # Add reason if available
            if entry.reason:
                embed.add_field(name="Reason", value=entry.reason, inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text="Delirium Den • Moderation Log",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(embed, guild)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Log member unbans"""
        embed = discord.Embed(
            title="🔓 Member Unbanned",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="User", value=f"{user.mention} ({user})", inline=True)
        embed.add_field(name="User ID", value=user.id, inline=True)
        
        # Add responsible user from audit log
        entry = await self.get_audit_log_entry(guild, discord.AuditLogAction.unban, user)
        if entry and entry.user:
            embed.add_field(
                name="Unbanned By",
                value=f"{entry.user.mention} ({entry.user})",
                inline=True
            )
            
            # Add reason if available
            if entry.reason:
                embed.add_field(name="Reason", value=entry.reason, inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text="Delirium Den • Moderation Log",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(embed, guild)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log member updates (roles, nickname, etc.)"""
        if before.display_name != after.display_name:
            embed = discord.Embed(
                title="📝 Nickname Changed",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="User", value=f"{after.mention} ({after})", inline=True)
            embed.add_field(name="Before", value=before.display_name, inline=True)
            embed.add_field(name="After", value=after.display_name, inline=True)
            
            # Add responsible user from audit log
            entry = await self.get_audit_log_entry(after.guild, discord.AuditLogAction.member_update, after)
            if entry and entry.user:
                # Verify it's actually a nickname change
                if hasattr(entry.changes.before, 'nick') or hasattr(entry.changes.after, 'nick'):
                    embed.add_field(
                        name="Changed By",
                        value=f"{entry.user.mention} ({entry.user})",
                        inline=True
                    )
                    
                    # Add reason if available
                    if entry.reason:
                        embed.add_field(name="Reason", value=entry.reason, inline=False)
            
            embed.set_footer(
                text="Delirium Den • Member Log",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await self.send_webhook(embed, after.guild)
        
        if before.roles != after.roles:
            embed = discord.Embed(
                title="🎭 Role Update",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="User", value=f"{after.mention} ({after})", inline=True)
            
            # Compare role IDs instead of role objects to avoid reference issues
            before_role_ids = {role.id for role in before.roles}
            after_role_ids = {role.id for role in after.roles}
            
            added_role_ids = after_role_ids - before_role_ids
            removed_role_ids = before_role_ids - after_role_ids
            
            # Get the actual role objects
            added_roles = [role for role in after.roles if role.id in added_role_ids]
            # For removed roles, we need to use before.roles since they might not be in after.roles
            removed_roles = [role for role in before.roles if role.id in removed_role_ids]
            
            if added_roles:
                # Format using get_role_info method for more reliable role reference
                added_role_text = []
                for role in added_roles:
                    role_info = self.get_role_info(role, after.guild.id, self.staff_server_id)
                    added_role_text.append(role_info)
                
                embed.add_field(name="Added Roles", value=", ".join(added_role_text), inline=False)
            
            if removed_roles:
                # Format using get_role_info method for more reliable role reference
                removed_role_text = []
                for role in removed_roles:
                    role_info = self.get_role_info(role, after.guild.id, self.staff_server_id)
                    removed_role_text.append(role_info)
                
                embed.add_field(name="Removed Roles", value=", ".join(removed_role_text), inline=False)
            
            # Add responsible user from audit log
            entry = await self.get_audit_log_entry(after.guild, discord.AuditLogAction.member_role_update, after)
            if entry and entry.user:
                embed.add_field(
                    name="Updated By",
                    value=f"{entry.user.mention} ({entry.user})",
                    inline=True
                )
                
                # Add reason if available
                if entry.reason:
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
            
            embed.set_footer(
                text="Delirium Den • Role Log",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await self.send_webhook(embed, after.guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Log voice channel changes"""
        if before.channel != after.channel:
            embed = discord.Embed(
                title="🔊 Voice State Update",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="User", value=f"{member.mention} ({member})", inline=True)
            
            if before.channel is None:
                embed.add_field(name="Action", value=f"Joined {after.channel.mention}", inline=False)
            elif after.channel is None:
                embed.add_field(name="Action", value=f"Left {before.channel.mention}", inline=False)
            else:
                embed.add_field(name="Action", value=f"Moved from {before.channel.mention} to {after.channel.mention}", inline=False)
            
            # Check if user was moved by someone else
            entry = await self.get_audit_log_entry(member.guild, discord.AuditLogAction.member_move, member)
            if entry and entry.user and entry.user.id != member.id:
                # Make sure it's a recent action (within last 5 seconds)
                entry_time = int((discord.utils.utcnow() - entry.created_at).total_seconds())
                if entry_time < 5:
                    embed.add_field(
                        name="Moved By",
                        value=f"{entry.user.mention} ({entry.user})",
                        inline=True
                    )
                    
                    # Add reason if available
                    if entry.reason:
                        embed.add_field(name="Reason", value=entry.reason, inline=False)
            
            embed.set_footer(
                text="Delirium Den • Voice Log",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await self.send_webhook(embed, member.guild)
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        embed = discord.Embed(
            title="📝 Channel Created",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Name", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        
        # Add responsible user from audit log
        entry = await self.get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_create)
        if entry and entry.user and entry.target.id == channel.id:
            embed.add_field(
                name="Created By",
                value=f"{entry.user.mention} ({entry.user})",
                inline=True
            )
            
            # Add reason if available
            if entry.reason:
                embed.add_field(name="Reason", value=entry.reason, inline=False)
        
        embed.set_footer(
            text="Delirium Den • Channel Log",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(embed, channel.guild)
        
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Name", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.add_field(name="Channel ID", value=channel.id, inline=True)
        
        # Add responsible user from audit log
        entry = await self.get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_delete)
        if entry and entry.user and entry.target.id == channel.id:
            embed.add_field(
                name="Deleted By",
                value=f"{entry.user.mention} ({entry.user})",
                inline=True
            )
            
            # Add reason if available
            if entry.reason:
                embed.add_field(name="Reason", value=entry.reason, inline=False)
        
        embed.set_footer(
            text="Delirium Den • Channel Log",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(embed, channel.guild)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwebhook(self, ctx, webhook_url: str = None):
        """Set the webhook URL for logging"""
        if webhook_url is None:
            await ctx.send("❌ Please provide a webhook URL.\n**Usage:** `!setwebhook <webhook_url>`")
            return
            
        # Basic validation
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            await ctx.send("❌ Invalid webhook URL. Make sure it starts with `https://discord.com/api/webhooks/`")
            return
            
        self.webhook_url = webhook_url
        
        # Store the webhook URL in environment (for runtime)
        os.environ["WEBHOOK_URL"] = webhook_url
        
        # Inform user that to make this permanent they should update their .env file
        await ctx.send(f"✅ Webhook URL has been set successfully!\n\n**Note:** To make this setting permanent, add the following line to your .env file:\n```\nWEBHOOK_URL={webhook_url}\n```")
        
        # Test webhook
        test_embed = discord.Embed(
            title="📝 Webhook Configured",
            description="This webhook has been successfully configured for logging.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        test_embed.set_footer(
            text="Delirium Den • Webhook Logging System",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(test_embed, ctx.guild)
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def testwebhook(self, ctx):
        """Test the webhook connection"""
        if not self.webhook_url:
            await ctx.send("❌ No webhook URL configured. Use `!setwebhook <url>` first.")
            return
            
        test_embed = discord.Embed(
            title="🧪 Webhook Test",
            description="This is a test message to verify the webhook is working correctly.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        test_embed.add_field(name="Triggered By", value=f"{ctx.author.mention} ({ctx.author})", inline=True)
        test_embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        test_embed.set_footer(
            text="Delirium Den • Webhook Test",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await self.send_webhook(test_embed, ctx.guild)
        await ctx.send("✅ Test webhook sent! Check your logging channel.")
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def invites(self, ctx):
        """Display all active invites for the server"""
        if not ctx.guild.me.guild_permissions.manage_guild:
            await ctx.send("❌ I need the `Manage Server` permission to see invites.")
            return
            
        try:
            guild_invites = await ctx.guild.invites()
            
            if not guild_invites:
                await ctx.send("📋 There are no active invites for this server.")
                return
                
            guild_invites.sort(key=lambda invite: invite.uses or 0, reverse=True)
            
            embed = discord.Embed(
                title=f"📨 Invite Links for {ctx.guild.name}",
                description=f"Total active invites: {len(guild_invites)}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            invites_by_creator = {}
            
            for invite in guild_invites:
                inviter_name = str(invite.inviter) if invite.inviter else "Unknown"
                inviter_id = invite.inviter.id if invite.inviter else 0
                
                if inviter_id not in invites_by_creator:
                    invites_by_creator[inviter_id] = {
                        "name": inviter_name,
                        "mention": invite.inviter.mention if invite.inviter else "Unknown",
                        "invites": []
                    }
                
                invite_info = f"Code: `{invite.code}` | Uses: {invite.uses} | Channel: {invite.channel.mention}"
                
                if invite.max_age > 0:
                    if hasattr(invite, 'created_at'):
                        expire_time = invite.created_at + timedelta(seconds=invite.max_age)
                        timestamp = int(expire_time.timestamp())
                        invite_info += f" | Expires: <t:{timestamp}:R>"
                    else:
                        invite_info += " | Temporary"
                
                if invite.max_uses > 0:
                    invite_info += f" | Max Uses: {invite.uses}/{invite.max_uses}"
                
                invites_by_creator[inviter_id]["invites"].append(invite_info)
            
            for creator_id, data in invites_by_creator.items():
                invites_text = "\n".join(data["invites"])
                
                if len(invites_text) > 1024:
                    invites_text = invites_text[:1021] + "..."
                
                embed.add_field(
                    name=f"Created by {data['name']}",
                    value=invites_text,
                    inline=False
                )
            
            if "VANITY_URL" in ctx.guild.features:
                try:
                    vanity = await ctx.guild.vanity_invite()
                    if vanity:
                        embed.add_field(
                            name="Vanity URL",
                            value=f"Code: `{vanity.code}` | Uses: {vanity.uses}",
                            inline=False
                        )
                except:
                    pass
            
            embed.set_footer(
                text="Delirium Den • Invite Management",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to view the server's invites.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")


async def setup(bot):
    await bot.add_cog(WebhookLogging(bot))