import discord
from discord.ext import commands
from discord import app_commands
import asyncio


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
        self.unverified_role_id = 1296917049435492432
        self.verified_role_ids = [
            1295852195585069137,
            1368628647304368238,
            1296454440286556200
        ]

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, emoji="✅", custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle verification button click"""
        try:
            # Get the unverified role
            unverified_role = interaction.guild.get_role(self.unverified_role_id)
            
            if not unverified_role:
                await interaction.response.send_message("❌ Verification role not found. Please contact an administrator.", ephemeral=True)
                return
            
            # Check if user has the unverified role
            if unverified_role not in interaction.user.roles:
                await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
                return
            
            # Remove the unverified role
            await interaction.user.remove_roles(unverified_role, reason="User completed verification")
            
            # Add the verified roles
            roles_to_add = []
            for role_id in self.verified_role_ids:
                role = interaction.guild.get_role(role_id)
                if role and role not in interaction.user.roles:
                    roles_to_add.append(role)
            
            if roles_to_add:
                await interaction.user.add_roles(*roles_to_add, reason="User completed verification")
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Verification Complete!",
                description=f"Welcome to {interaction.guild.name}! You now have access to all channels.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🎉 What's Next?",
                value="• Explore the server channels\n• Read the rules if you haven't already\n• Introduce yourself to the community!",
                inline=False
            )
            embed.set_footer(
                text=f"Verified: {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log the verification (optional)
            print(f"✅ {interaction.user.name} ({interaction.user.id}) completed verification in {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to remove roles. Please contact an administrator.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ An error occurred during verification: {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("❌ An unexpected error occurred. Please try again or contact an administrator.", ephemeral=True)
            print(f"❌ Verification error: {e}")


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.unverified_role_id = 1296917049435492432
        self.verified_role_ids = [
            1295852195585069137,
            1368628647304368238,
            1296454440286556200
        ]

    async def cog_load(self):
        """Add the persistent view when the cog loads"""
        self.bot.add_view(VerificationView())

    @app_commands.command(name="setup_verification", description="Set up the verification message")
    @app_commands.describe(
        channel="Channel to send verification message to (optional, uses current channel if not specified)"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_verification(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Set up the verification message with button"""
        
        if channel is None:
            channel = interaction.channel
        
        # Check if bot has required permissions
        permissions = channel.permissions_for(interaction.guild.me)
        if not permissions.send_messages:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
            return
        
        if not permissions.manage_roles:
            await interaction.response.send_message("❌ I need the 'Manage Roles' permission to remove verification roles.", ephemeral=True)
            return
        
        # Check if the unverified role exists
        unverified_role = interaction.guild.get_role(self.unverified_role_id)
        if not unverified_role:
            await interaction.response.send_message(f"❌ Unverified role with ID `{self.unverified_role_id}` not found in this server.", ephemeral=True)
            return
        
        # Create verification embed
        embed = discord.Embed(
            title="🔐 Server Verification",
            description=f"Welcome to **{interaction.guild.name}**!\n\n"
                       "To gain access to all channels and features, please click the **Verify** button below.\n\n"
                       "This helps us maintain a safe and welcoming community for everyone.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 What happens when you verify?",
            value="• You'll gain access to all server channels\n• You'll receive member roles automatically\n• You can participate in discussions\n• You'll be able to see member-only content",
            inline=False
        )
        
        embed.add_field(
            name="🤖 Having trouble?",
            value="If the verification button doesn't work, please contact a staff member for assistance.",
            inline=False
        )
        
        embed.set_footer(
            text=f"Click the button below to verify • {interaction.guild.name}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        # Create view with verification button
        view = VerificationView()
        
        try:
            # Send the verification message
            await channel.send(embed=embed, view=view)
            
            # Confirm to admin
            await interaction.response.send_message(f"✅ Verification message sent to {channel.mention}!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sending verification message: {e}", ephemeral=True)

    @app_commands.command(name="verify_user", description="Manually verify a user (remove unverified role)")
    @app_commands.describe(user="The user to verify")
    @app_commands.default_permissions(moderate_members=True)
    async def verify_user(self, interaction: discord.Interaction, user: discord.Member):
        """Manually verify a user (Moderator only)"""
        
        unverified_role = interaction.guild.get_role(self.unverified_role_id)
        
        if not unverified_role:
            await interaction.response.send_message(f"❌ Unverified role not found.", ephemeral=True)
            return
        
        if unverified_role not in user.roles:
            await interaction.response.send_message(f"✅ {user.mention} is already verified!", ephemeral=True)
            return
        
        try:
            await user.remove_roles(unverified_role, reason=f"Manually verified by {interaction.user}")
            
            # Add the verified roles
            roles_to_add = []
            for role_id in self.verified_role_ids:
                role = interaction.guild.get_role(role_id)
                if role and role not in user.roles:
                    roles_to_add.append(role)
            
            if roles_to_add:
                await user.add_roles(*roles_to_add, reason=f"Manually verified by {interaction.user}")
            
            embed = discord.Embed(
                title="✅ User Verified",
                description=f"{user.mention} has been manually verified by {interaction.user.mention}",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Try to notify the user
            try:
                dm_embed = discord.Embed(
                    title="✅ Verification Complete!",
                    description=f"You have been manually verified in **{interaction.guild.name}** by a staff member.\n\n"
                               "You now have access to all channels!",
                    color=discord.Color.green()
                )
                await user.send(embed=dm_embed)
            except:
                pass  # Ignore if we can't DM them
                
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage roles.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error verifying user: {e}", ephemeral=True)

    @app_commands.command(name="verification_stats", description="Show verification statistics")
    @app_commands.default_permissions(moderate_members=True)
    async def verification_stats(self, interaction: discord.Interaction):
        """Show verification statistics"""
        
        unverified_role = interaction.guild.get_role(self.unverified_role_id)
        
        if not unverified_role:
            await interaction.response.send_message(f"❌ Unverified role not found.", ephemeral=True)
            return
        
        # Count members
        total_members = len([m for m in interaction.guild.members if not m.bot])
        unverified_members = len(unverified_role.members)
        verified_members = total_members - unverified_members
        
        embed = discord.Embed(
            title="📊 Verification Statistics",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👥 Total Members",
            value=f"`{total_members:,}`",
            inline=True
        )
        
        embed.add_field(
            name="✅ Verified Members",
            value=f"`{verified_members:,}`",
            inline=True
        )
        
        embed.add_field(
            name="🔒 Unverified Members",
            value=f"`{unverified_members:,}`",
            inline=True
        )
        
        if total_members > 0:
            verification_rate = (verified_members / total_members) * 100
            embed.add_field(
                name="📈 Verification Rate",
                value=f"`{verification_rate:.1f}%`",
                inline=False
            )
        
        # Show some unverified members (up to 10)
        if unverified_members > 0:
            unverified_list = [m.mention for m in unverified_role.members[:10]]
            if len(unverified_role.members) > 10:
                unverified_list.append(f"... and {len(unverified_role.members) - 10} more")
            
            embed.add_field(
                name="🔒 Unverified Members",
                value="\n".join(unverified_list) if unverified_list else "None",
                inline=False
            )
        
        embed.set_footer(
            text=f"Unverified Role: {unverified_role.name}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Automatically assign the unverified role to new members"""
        if member.bot:
            return
        
        unverified_role = member.guild.get_role(self.unverified_role_id)
        
        if unverified_role:
            try:
                await member.add_roles(unverified_role, reason="Auto-assigned unverified role to new member")
                print(f"✅ Assigned unverified role to {member.name} in {member.guild.name}")
            except discord.Forbidden:
                print(f"❌ Missing permissions to assign unverified role to {member.name}")
            except Exception as e:
                print(f"❌ Error assigning unverified role to {member.name}: {e}")


async def setup(bot):
    await bot.add_cog(Verification(bot))