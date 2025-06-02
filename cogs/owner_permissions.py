import discord
from discord.ext import commands

class OwnerPermissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 267305778619088896  # Your user ID
    
    def is_owner(self, user_id):
        """Check if the user is the bot owner"""
        return user_id == self.owner_id
    
    async def cog_check(self, ctx):
        """Global check for this cog - only owner can use commands"""
        return self.is_owner(ctx.author.id)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event"""
        print(f"🎭 Delirium Den: Owner permissions loaded for user ID {self.owner_id}")
    
    @commands.command()
    async def grant_admin(self, ctx, member: discord.Member = None):
        """Grant administrator permissions to a member (or yourself)"""
        if member is None:
            member = ctx.author
        
        try:
            # Find or create an admin role
            admin_role = discord.utils.get(ctx.guild.roles, name="Delirium Den Admin")
            
            if not admin_role:
                # Create admin role with all permissions
                admin_role = await ctx.guild.create_role(
                    name="Delirium Den Admin",
                    permissions=discord.Permissions.all(),
                    color=discord.Color.purple(),
                    reason=f"Created by Delirium Den bot owner"
                )
                
                # Move role to near the top (just below bot's highest role)
                try:
                    bot_top_role = ctx.guild.me.top_role
                    await admin_role.edit(position=bot_top_role.position - 1)
                except:
                    pass
            
            # Add role to member
            await member.add_roles(admin_role, reason="Granted by bot owner")
            
            embed = discord.Embed(
                title="✅ Admin Permissions Granted",
                description=f"Successfully granted administrator permissions to {member.mention}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Role", value=admin_role.mention, inline=True)
            embed.add_field(name="Permissions", value="All permissions", inline=True)
            embed.add_field(name="Granted By", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text="Delirium Den • Owner Command", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Granting Permissions",
                description=f"Failed to grant admin permissions: {str(e)}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(
                text="Delirium Den • Error", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def revoke_admin(self, ctx, member: discord.Member):
        """Revoke administrator permissions from a member"""
        try:
            admin_role = discord.utils.get(ctx.guild.roles, name="Delirium Den Admin")
            
            if not admin_role:
                embed = discord.Embed(
                    title="❌ Role Not Found",
                    description="Delirium Den Admin role doesn't exist in this server.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(
                    text="Delirium Den • Error", 
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await ctx.send(embed=embed)
                return
            
            if admin_role not in member.roles:
                embed = discord.Embed(
                    title="❌ Member Doesn't Have Role",
                    description=f"{member.mention} doesn't have the Delirium Den Admin role.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(
                    text="Delirium Den • Error", 
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await ctx.send(embed=embed)
                return
            
            # Remove role from member
            await member.remove_roles(admin_role, reason="Revoked by bot owner")
            
            embed = discord.Embed(
                title="✅ Admin Permissions Revoked",
                description=f"Successfully revoked administrator permissions from {member.mention}",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Role Removed", value=admin_role.mention, inline=True)
            embed.add_field(name="Revoked By", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text="Delirium Den • Owner Command", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Revoking Permissions",
                description=f"Failed to revoke admin permissions: {str(e)}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(
                text="Delirium Den • Error", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def create_role(self, ctx, role_name: str, *, permissions: str = "basic"):
        """Create a custom role with specified permissions"""
        try:
            # Define permission presets
            permission_presets = {
                "basic": discord.Permissions(
                    send_messages=True, read_messages=True, connect=True, speak=True
                ),
                "moderator": discord.Permissions(
                    kick_members=True, ban_members=True, manage_messages=True,
                    manage_roles=True, manage_channels=True, mute_members=True,
                    deafen_members=True, move_members=True
                ),
                "admin": discord.Permissions.all(),
                "none": discord.Permissions.none()
            }
            
            # Get permissions
            if permissions.lower() in permission_presets:
                role_permissions = permission_presets[permissions.lower()]
            else:
                role_permissions = permission_presets["basic"]
            
            # Create role
            new_role = await ctx.guild.create_role(
                name=role_name,
                permissions=role_permissions,
                color=discord.Color.purple(),
                reason=f"Created by Delirium Den bot owner"
            )
            
            embed = discord.Embed(
                title="✅ Role Created",
                description=f"Successfully created role {new_role.mention}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Name", value=role_name, inline=True)
            embed.add_field(name="Permissions", value=permissions.title(), inline=True)
            embed.add_field(name="ID", value=new_role.id, inline=True)
            embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text="Delirium Den • Owner Command", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Creating Role",
                description=f"Failed to create role: {str(e)}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(
                text="Delirium Den • Error", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def give_role(self, ctx, member: discord.Member, role: discord.Role):
        """Give a role to a member"""
        try:
            await member.add_roles(role, reason="Added by bot owner")
            
            embed = discord.Embed(
                title="✅ Role Added",
                description=f"Successfully gave {role.mention} to {member.mention}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            embed.add_field(name="Added By", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text="Delirium Den • Owner Command", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Adding Role",
                description=f"Failed to add role: {str(e)}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(
                text="Delirium Den • Error", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
        """Remove a role from a member"""
        try:
            await member.remove_roles(role, reason="Removed by bot owner")
            
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"Successfully removed {role.mention} from {member.mention}",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            embed.add_field(name="Removed By", value=ctx.author.mention, inline=True)
            embed.set_footer(
                text="Delirium Den • Owner Command", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Removing Role",
                description=f"Failed to remove role: {str(e)}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(
                text="Delirium Den • Error", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def server_info(self, ctx):
        """Get detailed server information"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🎭 Server Information: {guild.name}",
            color=discord.Color.purple(),
            timestamp=guild.created_at
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Basic info
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        # Member counts
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="🤖 Bots", value=len([m for m in guild.members if m.bot]), inline=True)
        embed.add_field(name="👤 Humans", value=len([m for m in guild.members if not m.bot]), inline=True)
        
        # Channel counts
        embed.add_field(name="💬 Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="🔊 Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        
        # Server features
        if guild.features:
            features = ", ".join([feature.replace("_", " ").title() for feature in guild.features])
            embed.add_field(name="🌟 Features", value=features[:1024], inline=False)
        
        # Verification and content filter levels
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium", 
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        
        embed.add_field(
            name="🔒 Verification Level",
            value=verification_levels.get(guild.verification_level, "Unknown"),
            inline=True
        )
        
        embed.set_footer(
            text="Delirium Den • Owner Command", 
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def owner_help(self, ctx):
        """Show all owner commands"""
        embed = discord.Embed(
            title="🎭 Delirium Den Owner Commands",
            description="Commands only available to the bot owner",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        commands_list = [
            ("!grant_admin [@member]", "Grant admin permissions (creates Delirium Den Admin role)"),
            ("!revoke_admin @member", "Remove admin permissions"),
            ("!create_role \"Role Name\" [basic/moderator/admin]", "Create custom roles"),
            ("!give_role @member @role", "Give a role to someone"),
            ("!remove_role @member @role", "Remove a role from someone"),
            ("!server_info", "Get detailed server information"),
            ("!owner_help", "Show this help message"),
            ("!emergency_admin", "Emergency admin access (hidden command)")
        ]
        
        for command, description in commands_list:
            embed.add_field(name=command, value=description, inline=False)
        
        embed.add_field(
            name="ℹ️ Permission Presets",
            value="• **basic** - Send messages, read messages, connect, speak\n• **moderator** - Kick, ban, manage messages/roles/channels\n• **admin** - All permissions\n• **none** - No permissions",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Important Notes",
            value="• These commands only work for the bot owner\n• Admin roles are named 'Delirium Den Admin'\n• Emergency admin creates 'Emergency Admin' role\n• All actions are logged with reasons",
            inline=False
        )
        
        embed.set_footer(
            text="Delirium Den • Owner Only", 
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await ctx.send(embed=embed)
    
    @commands.command(hidden=True)
    async def emergency_admin(self, ctx):
        """Emergency command to grant yourself admin if something goes wrong"""
        if not self.is_owner(ctx.author.id):
            return
        
        try:
            # Grant all permissions directly to the owner
            admin_role = discord.utils.get(ctx.guild.roles, name="Emergency Admin")
            
            if not admin_role:
                admin_role = await ctx.guild.create_role(
                    name="Emergency Admin",
                    permissions=discord.Permissions.all(),
                    color=discord.Color.red(),
                    reason="Emergency admin access for Delirium Den bot owner"
                )
                
                # Try to move role near the top
                try:
                    bot_top_role = ctx.guild.me.top_role
                    await admin_role.edit(position=bot_top_role.position - 1)
                except:
                    pass
            
            await ctx.author.add_roles(admin_role)
            
            embed = discord.Embed(
                title="🚨 Emergency Admin Access Granted",
                description="You now have emergency administrator permissions.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Role", value=admin_role.mention, inline=True)
            embed.add_field(name="Granted To", value=ctx.author.mention, inline=True)
            embed.add_field(name="⚠️ Warning", value="This is an emergency override. Use responsibly.", inline=False)
            embed.set_footer(
                text="Delirium Den • Emergency Access", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Emergency Admin Failed",
                description=f"Failed to grant emergency access: {str(e)}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Emergency Error", 
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await ctx.send(embed=error_embed)
    
    @commands.command()
    async def list_admins(self, ctx):
        """List all members with Delirium Den Admin role"""
        admin_role = discord.utils.get(ctx.guild.roles, name="Delirium Den Admin")
        emergency_role = discord.utils.get(ctx.guild.roles, name="Emergency Admin")
        
        embed = discord.Embed(
            title="🎭 Admin Role Members",
            description="Members with Delirium Den administrative roles",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        # Delirium Den Admins
        if admin_role and admin_role.members:
            admin_list = "\n".join([f"• {member.mention} ({member.name}#{member.discriminator})" for member in admin_role.members])
            embed.add_field(
                name=f"🛡️ Delirium Den Admin ({len(admin_role.members)})",
                value=admin_list[:1024],
                inline=False
            )
        else:
            embed.add_field(
                name="🛡️ Delirium Den Admin (0)",
                value="No members have this role",
                inline=False
            )
        
        # Emergency Admins
        if emergency_role and emergency_role.members:
            emergency_list = "\n".join([f"• {member.mention} ({member.name}#{member.discriminator})" for member in emergency_role.members])
            embed.add_field(
                name=f"🚨 Emergency Admin ({len(emergency_role.members)})",
                value=emergency_list[:1024],
                inline=False
            )
        
        embed.set_footer(
            text="Delirium Den • Owner Command", 
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerPermissions(bot))
    print("OwnerPermissions cog loaded successfully with Delirium Den branding")