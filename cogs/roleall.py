import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal

class ConfirmView(discord.ui.View):
    def __init__(self, role, members_count, action):
        super().__init__(timeout=30)
        self.role = role
        self.members_count = members_count
        self.action = action
        self.confirmed = False

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        embed = discord.Embed(
            title="✅ Confirmed",
            description=f"Processing role {self.action} for {self.members_count} members...",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(
            text="Delirium Den • Role Management",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        embed = discord.Embed(
            title="❌ Cancelled",
            description=f"Role {self.action} operation has been cancelled.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(
            text="Delirium Den • Role Management",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class RoleAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="roleall", description="Add or remove a role from every member in the server")
    async def roleall_slash(self, interaction: discord.Interaction, role: discord.Role, action: Literal["add", "remove"]):
        """Add or remove a role from all members in the server."""
        
        # Check if bot has permissions
        if not interaction.guild.me.guild_permissions.manage_roles:
            error_embed = discord.Embed(
                title="❌ Missing Permissions",
                description="I need the 'Manage Roles' permission to manage roles.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return
        
        # Ensure the role is lower than the bot's role in the hierarchy
        if role.position >= interaction.guild.me.top_role.position:
            error_embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="I cannot manage a role higher than or equal to my own in the role hierarchy.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            error_embed.add_field(
                name="My Highest Role",
                value=interaction.guild.me.top_role.mention,
                inline=True
            )
            error_embed.add_field(
                name="Target Role",
                value=role.mention,
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Role Hierarchy Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return
        
        # Get all members in the guild excluding bots
        members = [member for member in interaction.guild.members if not member.bot]
        
        # Filter members based on action
        if action == "add":
            target_members = [member for member in members if role not in member.roles]
            action_text = "assign"
            action_past = "assigned"
            action_emoji = "➕"
        else:  # remove
            target_members = [member for member in members if role in member.roles]
            action_text = "remove"
            action_past = "removed"
            action_emoji = "➖"
        
        if not target_members:
            info_embed = discord.Embed(
                title="ℹ️ No Action Needed",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            if action == "add":
                info_embed.description = f"All members already have the **{role.name}** role!"
            else:
                info_embed.description = f"No members have the **{role.name}** role to remove!"
            
            info_embed.add_field(
                name="Role",
                value=role.mention,
                inline=True
            )
            info_embed.add_field(
                name="Total Members",
                value=len(members),
                inline=True
            )
            info_embed.set_footer(
                text="Delirium Den • Role Management",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=info_embed, ephemeral=True)
            return
        
        # Create confirmation view
        view = ConfirmView(role, len(target_members), action)
        embed = discord.Embed(
            title=f"{action_emoji} Role {action.title()} Confirmation",
            description=f"Are you sure you want to **{action_text}** the **{role.name}** role {'to' if action == 'add' else 'from'} **{len(target_members)}** members?",
            color=role.color or discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="🎭 Role",
            value=role.mention,
            inline=True
        )
        embed.add_field(
            name="👥 Target Members",
            value=len(target_members),
            inline=True
        )
        embed.add_field(
            name="⚡ Action",
            value=action.title(),
            inline=True
        )
        
        if action == "add":
            embed.add_field(
                name="ℹ️ Note",
                value="This will not remove any existing roles from members.",
                inline=False
            )
        
        embed.add_field(
            name="⏱️ Timeout",
            value="You have 30 seconds to confirm this action.",
            inline=False
        )
        
        embed.set_footer(
            text="Delirium Den • Role Management Confirmation",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        # Wait for user response
        await view.wait()
        
        if not view.confirmed:
            return  # Already handled in the view
        
        # Process the role assignment/removal
        processing_embed = discord.Embed(
            title="⚙️ Processing...",
            description=f"Please wait while I {action_text} the **{role.name}** role {'to' if action == 'add' else 'from'} {len(target_members)} members.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        processing_embed.set_footer(
            text="Delirium Den • Processing Role Changes",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.followup.send(embed=processing_embed, ephemeral=True)
        
        # Add or remove the role
        failed_members = []
        success_count = 0
        
        for member in target_members:
            try:
                if action == "add":
                    await member.add_roles(role, reason=f"Bulk role assignment by {interaction.user}")
                else:
                    await member.remove_roles(role, reason=f"Bulk role removal by {interaction.user}")
                success_count += 1
            except discord.Forbidden:
                failed_members.append(member.name)
            except discord.HTTPException:
                failed_members.append(member.name)
        
        # Send final result
        result_embed = discord.Embed(
            title=f"✅ Role {action.title()} Complete",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        if failed_members:
            result_embed.description = f"Successfully {action_past} the **{role.name}** role {'to' if action == 'add' else 'from'} **{success_count}** members!"
            
            failed_list = ', '.join(failed_members[:10])
            if len(failed_members) > 10:
                failed_list += f"... and {len(failed_members) - 10} more"
            
            result_embed.add_field(
                name="❌ Failed Members",
                value=failed_list,
                inline=False
            )
        else:
            result_embed.description = f"Successfully {action_past} the **{role.name}** role {'to' if action == 'add' else 'from'} all **{success_count}** members!"
        
        result_embed.add_field(
            name="📊 Statistics",
            value=f"**Success:** {success_count}\n**Failed:** {len(failed_members)}\n**Total Processed:** {len(target_members)}",
            inline=True
        )
        
        result_embed.add_field(
            name="🎭 Role",
            value=role.mention,
            inline=True
        )
        
        result_embed.add_field(
            name="👤 Performed By",
            value=interaction.user.mention,
            inline=True
        )
        
        result_embed.set_footer(
            text="Delirium Den • Role Management Complete",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.followup.send(embed=result_embed, ephemeral=True)
    
    @commands.command(name="roleall")
    @commands.has_permissions(manage_roles=True)
    async def roleall_prefix(self, ctx, action: str, role: discord.Role):
        """Add or remove a role from all members in the server using prefix command.
        
        Usage: !roleall add @RoleName or !roleall remove @RoleName
        """
        
        # Validate action parameter
        if action.lower() not in ["add", "remove"]:
            error_embed = discord.Embed(
                title="❌ Invalid Action",
                description="Invalid action! Use `add` or `remove`.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            error_embed.add_field(
                name="Correct Usage",
                value="```!roleall add @RoleName\n!roleall remove @RoleName```",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Command Usage Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed)
            return
        
        action = action.lower()
        
        # Check if bot has permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            error_embed = discord.Embed(
                title="❌ Missing Permissions",
                description="I need the 'Manage Roles' permission to manage roles.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed)
            return
        
        # Ensure the role is lower than the bot's role in the hierarchy
        if role.position >= ctx.guild.me.top_role.position:
            error_embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description="I cannot manage a role higher than or equal to my own in the role hierarchy.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            error_embed.add_field(
                name="My Highest Role",
                value=ctx.guild.me.top_role.mention,
                inline=True
            )
            error_embed.add_field(
                name="Target Role",
                value=role.mention,
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Role Hierarchy Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed)
            return
        
        # Get all members in the guild excluding bots
        members = [member for member in ctx.guild.members if not member.bot]
        
        # Filter members based on action
        if action == "add":
            target_members = [member for member in members if role not in member.roles]
            action_text = "assign"
            action_past = "assigned"
            action_emoji = "➕"
        else:  # remove
            target_members = [member for member in members if role in member.roles]
            action_text = "remove"
            action_past = "removed"
            action_emoji = "➖"
        
        if not target_members:
            info_embed = discord.Embed(
                title="ℹ️ No Action Needed",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            if action == "add":
                info_embed.description = f"All members already have the **{role.name}** role!"
            else:
                info_embed.description = f"No members have the **{role.name}** role to remove!"
            
            info_embed.add_field(
                name="Role",
                value=role.mention,
                inline=True
            )
            info_embed.add_field(
                name="Total Members",
                value=len(members),
                inline=True
            )
            info_embed.set_footer(
                text="Delirium Den • Role Management",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=info_embed)
            return
        
        # Ask for confirmation
        confirm_embed = discord.Embed(
            title=f"{action_emoji} Role {action.title()} Confirmation",
            description=f"Are you sure you want to **{action_text}** the **{role.name}** role {'to' if action == 'add' else 'from'} **{len(target_members)}** members?",
            color=role.color or discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        confirm_embed.add_field(
            name="🎭 Role",
            value=role.mention,
            inline=True
        )
        confirm_embed.add_field(
            name="👥 Target Members",
            value=len(target_members),
            inline=True
        )
        confirm_embed.add_field(
            name="⚡ Action",
            value=action.title(),
            inline=True
        )
        
        confirm_embed.add_field(
            name="📝 Instructions",
            value="React with ✅ to confirm or ❌ to cancel.\nYou have 30 seconds to respond.",
            inline=False
        )
        
        confirm_embed.set_footer(
            text="Delirium Den • Role Management Confirmation",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        confirm_msg = await ctx.send(embed=confirm_embed)
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except:
            timeout_embed = discord.Embed(
                title="⏰ Confirmation Timed Out",
                description=f"Role {action} operation has been cancelled due to timeout.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            timeout_embed.set_footer(
                text="Delirium Den • Timeout",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=timeout_embed)
            return
        
        if str(reaction.emoji) == "❌":
            cancelled_embed = discord.Embed(
                title="❌ Operation Cancelled",
                description=f"Role {action} operation has been cancelled.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            cancelled_embed.set_footer(
                text="Delirium Den • Cancelled",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=cancelled_embed)
            return
        
        # Send processing message
        processing_embed = discord.Embed(
            title="⚙️ Processing...",
            description=f"Please wait while I {action_text} the **{role.name}** role {'to' if action == 'add' else 'from'} {len(target_members)} members.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        processing_embed.set_footer(
            text="Delirium Den • Processing Role Changes",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        message = await ctx.send(embed=processing_embed)
        
        # Add or remove the role
        failed_members = []
        success_count = 0
        
        for member in target_members:
            try:
                if action == "add":
                    await member.add_roles(role, reason=f"Bulk role assignment by {ctx.author}")
                else:
                    await member.remove_roles(role, reason=f"Bulk role removal by {ctx.author}")
                success_count += 1
            except discord.Forbidden:
                failed_members.append(member.name)
            except discord.HTTPException:
                failed_members.append(member.name)
        
        # Send final result
        result_embed = discord.Embed(
            title=f"✅ Role {action.title()} Complete",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        if failed_members:
            result_embed.description = f"Successfully {action_past} the **{role.name}** role {'to' if action == 'add' else 'from'} **{success_count}** members!"
            
            failed_list = ', '.join(failed_members[:10])
            if len(failed_members) > 10:
                failed_list += f"... and {len(failed_members) - 10} more"
            
            result_embed.add_field(
                name="❌ Failed Members",
                value=failed_list,
                inline=False
            )
        else:
            result_embed.description = f"Successfully {action_past} the **{role.name}** role {'to' if action == 'add' else 'from'} all **{success_count}** members!"
        
        result_embed.add_field(
            name="📊 Statistics",
            value=f"**Success:** {success_count}\n**Failed:** {len(failed_members)}\n**Total Processed:** {len(target_members)}",
            inline=True
        )
        
        result_embed.add_field(
            name="🎭 Role",
            value=role.mention,
            inline=True
        )
        
        result_embed.add_field(
            name="👤 Performed By",
            value=ctx.author.mention,
            inline=True
        )
        
        result_embed.set_footer(
            text="Delirium Den • Role Management Complete",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await message.edit(embed=result_embed)

    @commands.command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def addrole_prefix(self, ctx, role: discord.Role):
        """Add a role to all members in the server (shortcut command)."""
        await self.roleall_prefix(ctx, "add", role)
    
    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def removerole_prefix(self, ctx, role: discord.Role):
        """Remove a role from all members in the server (shortcut command)."""
        await self.roleall_prefix(ctx, "remove", role)
    
    @commands.command(name="roleall_help", aliases=["rolehelp"])
    @commands.has_permissions(manage_roles=True)
    async def roleall_help(self, ctx):
        """Show help for role management commands"""
        help_embed = discord.Embed(
            title="🎭 Role Management Commands Help",
            description="Commands for bulk role management across all server members.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        help_embed.add_field(
            name="📋 Available Commands",
            value="```/roleall <add/remove> @role\n!roleall <add/remove> @role\n!addrole @role\n!removerole @role```",
            inline=False
        )
        
        help_embed.add_field(
            name="⚡ Slash Commands",
            value="• `/roleall add @role` - Add role to all members\n• `/roleall remove @role` - Remove role from all members",
            inline=False
        )
        
        help_embed.add_field(
            name="🔧 Prefix Commands",
            value="• `!roleall add @role` - Add role to all members\n• `!roleall remove @role` - Remove role from all members\n• `!addrole @role` - Shortcut for adding roles\n• `!removerole @role` - Shortcut for removing roles",
            inline=False
        )
        
        help_embed.add_field(
            name="⚠️ Important Notes",
            value="• Requires 'Manage Roles' permission\n• Cannot manage roles higher than the bot's role\n• Bots are excluded from bulk operations\n• All actions require confirmation\n• Operations include audit log reasons",
            inline=False
        )
        
        help_embed.add_field(
            name="🔒 Safety Features",
            value="• 30-second confirmation timeout\n• Detailed progress reporting\n• Error handling for failed operations\n• Statistics on successful/failed changes",
            inline=False
        )
        
        help_embed.set_footer(
            text="Delirium Den • Role Management Help",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await ctx.send(embed=help_embed)

async def setup(bot):
    await bot.add_cog(RoleAll(bot))
    print("RoleAll cog loaded successfully with Delirium Den branding")