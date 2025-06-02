import discord
from discord.ext import commands
import asyncio
from datetime import datetime

class StaffRules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="createstaffrules")
    @commands.has_permissions(administrator=True)
    async def create_staff_rules(self, ctx, skip_confirmation=False):
        """Creates a staff rules channel with formatted embeds"""
        
        # Track the status message
        status_message = None
        
        if not skip_confirmation:
            # Ask for confirmation
            confirmation_embed = discord.Embed(
                title="📝 Staff Rules Channel Creation",
                description="This will create a new channel named `staff-rules` with formatted rule embeds.\n\n"
                           "Do you want to proceed?",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            try:
                status_message = await ctx.send(embed=confirmation_embed)
                
                # Add reaction buttons
                await status_message.add_reaction("✅")
                await status_message.add_reaction("❌")
                
                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == status_message.id
                
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == "❌":
                        try:
                            await status_message.edit(embed=discord.Embed(
                                title="❌ Operation Cancelled",
                                description="Staff rules channel creation was cancelled.",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow()
                            ))
                        except discord.NotFound:
                            await ctx.send(embed=discord.Embed(
                                title="❌ Operation Cancelled",
                                description="Staff rules channel creation was cancelled.",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow()
                            ))
                        return
                    
                except asyncio.TimeoutError:
                    try:
                        await status_message.edit(embed=discord.Embed(
                            title="⏱️ Timed Out",
                            description="No response received. Staff rules channel creation was cancelled.",
                            color=discord.Color.grey(),
                            timestamp=datetime.utcnow()
                        ))
                    except discord.NotFound:
                        await ctx.send(embed=discord.Embed(
                            title="⏱️ Timed Out",
                            description="No response received. Staff rules channel creation was cancelled.",
                            color=discord.Color.grey(),
                            timestamp=datetime.utcnow()
                        ))
                    return
                
                # Operation confirmed, update status message
                try:
                    await status_message.edit(embed=discord.Embed(
                        title="🔄 Creating Staff Rules Channel",
                        description="Please wait while I set everything up...",
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow()
                    ))
                except discord.NotFound:
                    # Message was deleted, create a new status message
                    status_message = await ctx.send(embed=discord.Embed(
                        title="🔄 Creating Staff Rules Channel",
                        description="Please wait while I set everything up...",
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow()
                    ))
            except Exception as e:
                await ctx.send(f"Error during confirmation: {e}")
                # Continue with the process even if confirmation fails
                pass
        
        # Check if staff-rules channel already exists
        existing_channel = discord.utils.get(ctx.guild.text_channels, name="staff-rules")
        if existing_channel:
            confirmation_embed = discord.Embed(
                title="⚠️ Channel Already Exists",
                description=f"A channel named `staff-rules` already exists: {existing_channel.mention}\n\n"
                           f"Would you like to replace its contents? (This will not delete the channel)",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            
            # Send a new message instead of trying to edit
            if status_message:
                try:
                    await status_message.delete()
                except discord.NotFound:
                    pass
            
            status_message = await ctx.send(embed=confirmation_embed)
            
            await status_message.add_reaction("✅")
            await status_message.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == status_message.id
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    try:
                        await status_message.edit(embed=discord.Embed(
                            title="❌ Operation Cancelled",
                            description="Staff rules update was cancelled.",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                    except discord.NotFound:
                        await ctx.send(embed=discord.Embed(
                            title="❌ Operation Cancelled",
                            description="Staff rules update was cancelled.",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                    return
                
                # If confirmed, clear the existing channel
                await existing_channel.purge(limit=100)
                staff_rules_channel = existing_channel
                
            except asyncio.TimeoutError:
                try:
                    await status_message.edit(embed=discord.Embed(
                        title="⏱️ Timed Out",
                        description="No response received. Staff rules update was cancelled.",
                        color=discord.Color.grey(),
                        timestamp=datetime.utcnow()
                    ))
                except discord.NotFound:
                    await ctx.send(embed=discord.Embed(
                        title="⏱️ Timed Out",
                        description="No response received. Staff rules update was cancelled.",
                        color=discord.Color.grey(),
                        timestamp=datetime.utcnow()
                    ))
                return
        else:
            # Create a new channel
            # First, try to find a "staff" category
            staff_category = None
            for category in ctx.guild.categories:
                if "staff" in category.name.lower() or "mod" in category.name.lower() or "admin" in category.name.lower():
                    staff_category = category
                    break
            
            # Create permissions for the channel (only visible to staff roles)
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True, embed_links=True)
            }
            
            # Add permissions for roles with "mod", "admin", "staff" in their names
            for role in ctx.guild.roles:
                role_name = role.name.lower()
                if "mod" in role_name or "admin" in role_name or "staff" in role_name or "owner" in role_name or "manager" in role_name:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
            
            # Create the channel
            try:
                staff_rules_channel = await ctx.guild.create_text_channel(
                    name="staff-rules",
                    category=staff_category,
                    overwrites=overwrites,
                    topic="Official staff rules and guidelines for the Delirium Den moderation team.",
                    reason=f"Staff rules channel created by {ctx.author}"
                )
            except Exception as e:
                await ctx.send(f"Error creating channel: {e}")
                return
        
        # Now the channel exists and is empty, add the rule embeds
        # Send a new progress message instead of editing
        if status_message:
            try:
                await status_message.delete()
            except discord.NotFound:
                pass
        
        status_message = await ctx.send(embed=discord.Embed(
            title="✅ Staff Rules Channel Created",
            description=f"Successfully created {staff_rules_channel.mention}. Adding rules...",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        ))
        
        # Send welcome header
        welcome_embed = discord.Embed(
            title="📋 Staff Rules & Guidelines",
            description="Welcome to the Delirium Den staff team! This channel outlines the expectations and responsibilities for each staff role in our Discord community.\n\n**Staff Hierarchy:**\n`Moderator → Admin → Manager → Owner`\n\nAs a staff member, you represent our community and must uphold our values at all times. Your role is to foster a positive, welcoming environment for all members.",
            color=0x7B68EE,  # Medium slate blue (matching delirium theme)
            timestamp=datetime.utcnow()
        )
        welcome_embed.set_footer(text="Last Updated", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        # Create a text-based banner that will always work
        welcome_text = "```\n" + \
                      "╔═══════════════════════════════════════════════════════════╗\n" + \
                      "║                                                           ║\n" + \
                      "║                  DELIRIUM DEN STAFF                       ║\n" + \
                      "║                                                           ║\n" + \
                      "║              Mod → Admin → Manager → Owner                ║\n" + \
                      "║                                                           ║\n" + \
                      "║                  Community Guidelines                     ║\n" + \
                      "║                                                           ║\n" + \
                      "╚═══════════════════════════════════════════════════════════╝\n" + \
                      "```"
        
        # Send the text banner first
        await staff_rules_channel.send(welcome_text)
        # Then send the welcome embed
        await staff_rules_channel.send(embed=welcome_embed)
        
        # Send general conduct section
        conduct_embed = discord.Embed(
            title="🌟 General Staff Conduct",
            description="As a staff member, you are expected to exemplify the highest standards of behavior.",
            color=0x7B68EE,
            timestamp=datetime.utcnow()
        )
        
        conduct_embed.add_field(
            name="1.1 Lead by Example",
            value="Always follow all server rules yourself. You cannot enforce rules you don't follow.",
            inline=False
        )
        
        conduct_embed.add_field(
            name="1.2 Professionalism",
            value="Maintain professionalism when dealing with members. Stay calm and respectful, even when dealing with difficult situations.",
            inline=False
        )
        
        conduct_embed.add_field(
            name="1.3 Active Presence",
            value="Regular activity is expected on Discord. If you need to be absent for an extended period, please inform the admin team.",
            inline=False
        )
        
        conduct_embed.add_field(
            name="1.4 Confidentiality",
            value="Staff discussions, decisions, and member issues must remain confidential. Never share screenshots or details from staff channels.",
            inline=False
        )
        
        conduct_embed.add_field(
            name="1.5 Teamwork",
            value="Work cooperatively with other staff members. If you have an issue with another staff member, address it privately or with a higher-up.",
            inline=False
        )
        
        conduct_embed.set_footer(text="Section 1: General Conduct", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await staff_rules_channel.send(embed=conduct_embed)
        
        # Send moderation guidelines
        moderation_embed = discord.Embed(
            title="🛡️ Moderation Guidelines",
            description="Consistent and fair moderation is crucial to maintaining a healthy community.",
            color=0x7B68EE,
            timestamp=datetime.utcnow()
        )
        
        moderation_embed.add_field(
            name="2.1 Fairness",
            value="Treat all members equally regardless of their status, how well you know them, or personal feelings.",
            inline=False
        )
        
        moderation_embed.add_field(
            name="2.2 Escalation Path",
            value="```\n• Warning: For minor first offenses\n• Timeout: For repeated minor offenses or moderate violations\n• Kick: For serious offenses from new members\n• Ban: For severe rule violations or repeated offenses```\n\n**Staff Escalation Structure:**\n`Moderator → Admin → Manager → Owner`\n\nEscalate issues to the next higher rank if you are unable to resolve them with your current authority.",
            inline=False
        )
        
        moderation_embed.add_field(
            name="2.3 Documentation",
            value="Always document moderation actions in `#mod-logs`. Include the member's name, offense, action taken, and any relevant context or evidence.",
            inline=False
        )
        
        moderation_embed.add_field(
            name="2.4 Conflict Resolution",
            value="When in doubt about how to handle a situation, consult with other staff members before taking action. De-escalation should always be the first approach.",
            inline=False
        )
        
        moderation_embed.add_field(
            name="2.5 Appeals",
            value="All members have the right to appeal moderation decisions. Direct appeals to the designated admin team and handle them fairly and promptly.",
            inline=False
        )
        
        moderation_embed.add_field(
            name="2.6 Chat Moderation Specifics",
            value="• Monitor for spam, inappropriate content, and rule violations\n• Keep conversations on-topic in designated channels\n• Handle heated discussions before they become arguments\n• Be mindful of cultural differences and promote inclusivity\n• Watch for potential raids or coordinated disruptions",
            inline=False
        )
        
        moderation_embed.set_footer(text="Section 2: Moderation Guidelines", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await staff_rules_channel.send(embed=moderation_embed)
        
        # Send communication guidelines
        communication_embed = discord.Embed(
            title="💬 Staff Communication",
            description="Clear communication among staff is essential for effective community management.",
            color=0x7B68EE,
            timestamp=datetime.utcnow()
        )
        
        communication_embed.add_field(
            name="3.1 Staff Channels",
            value="Use the appropriate staff channels for different types of discussions:\n• `#staff-chat`: General staff discussion and coordination\n• `#mod-logs`: Documentation of moderation actions\n• `#management`: Higher staff coordination and sensitive matters",
            inline=False
        )
        
        communication_embed.add_field(
            name="3.2 Mentioning Higher Staff",
            value="Only mention admins, managers, or owners for urgent matters that require immediate attention. Respect their time and availability.",
            inline=False
        )
        
        communication_embed.add_field(
            name="3.3 Disagreements",
            value="If you disagree with another staff member's decision, discuss it privately or in staff channels. Never contradict another staff member publicly.",
            inline=False
        )
        
        communication_embed.add_field(
            name="3.4 Public Communication",
            value="When speaking as staff in public channels, maintain a helpful and friendly tone. Your words represent the entire team and community.",
            inline=False
        )
        
        communication_embed.add_field(
            name="3.5 Community Engagement",
            value="Actively participate in community discussions and events. Be approachable and help create a welcoming atmosphere for all members.",
            inline=False
        )
        
        communication_embed.set_footer(text="Section 3: Communication Guidelines", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await staff_rules_channel.send(embed=communication_embed)
        
        # Send role-specific duties
        duties_embed = discord.Embed(
            title="📋 Role-Specific Responsibilities",
            description="Different staff roles have different responsibilities and authorities.",
            color=0x7B68EE,
            timestamp=datetime.utcnow()
        )
        
        duties_embed.add_field(
            name="4.1 Moderator",
            value="• Monitor all chat channels for rule violations and inappropriate content\n• Issue warnings, timeouts, and mutes as appropriate\n• Welcome new members and help them integrate into the community\n• Answer questions about server rules and features\n• Report serious issues or repeat offenders to Admins\n• Participate in community events and discussions\n• Document all moderation actions in mod-logs",
            inline=False
        )
        
        duties_embed.add_field(
            name="4.2 Admin",
            value="• All moderator duties with extended authority\n• Handle complex disputes and serious rule violations\n• Review and approve permanent bans\n• Manage server roles and permissions as needed\n• Coordinate community events and activities\n• Train and mentor new moderators\n• Make decisions on appeals and complex moderation cases\n• Implement policy changes and rule updates",
            inline=False
        )
        
        duties_embed.add_field(
            name="4.3 Manager",
            value="• Oversee all staff operations and community management\n• Develop policies and guidelines for the community\n• Handle high-level disputes and administrative decisions\n• Coordinate with the Owner on server direction and vision\n• Manage staff recruitment, training, and performance\n• Plan and execute major community initiatives\n• Handle external partnerships and collaborations\n• Direct liaison between Owner and staff team",
            inline=False
        )
        
        duties_embed.add_field(
            name="4.4 Owner",
            value="• Final authority on all Discord community matters\n• Makes decisions on server direction, vision, and major policies\n• Manages server infrastructure and bot configurations\n• Appoints and removes Manager and Admin positions\n• Oversees all aspects of the community\n• Handles critical situations and major decisions\n• Represents the community in external matters",
            inline=False
        )
        
        duties_embed.set_footer(text="Section 4: Role Responsibilities", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await staff_rules_channel.send(embed=duties_embed)
        
        # Send termination guidelines
        termination_embed = discord.Embed(
            title="⚠️ Staff Removal Guidelines",
            description="Staff members who fail to uphold these standards may be removed from the team.",
            color=0xFF0000,  # Red
            timestamp=datetime.utcnow()
        )
        
        termination_embed.add_field(
            name="5.1 Minor Violations",
            value="Minor violations will result in a private warning from the admin team and additional training if needed.",
            inline=False
        )
        
        termination_embed.add_field(
            name="5.2 Serious Violations",
            value="Serious violations may result in demotion or immediate removal from the staff team.",
            inline=False
        )
        
        termination_embed.add_field(
            name="5.3 Grounds for Removal",
            value="• Abuse of staff powers or privileges\n• Sharing confidential staff information\n• Disrespecting members or other staff\n• Extended inactivity without notice\n• Deliberately violating server rules\n• Creating drama or disruption within the team\n• Harassment or discrimination of any kind",
            inline=False
        )
        
        termination_embed.set_footer(text="Section 5: Removal Policy", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await staff_rules_channel.send(embed=termination_embed)
        
        # Send acknowledgment message
        ack_embed = discord.Embed(
            title="✅ Acknowledgment",
            description="By accepting a staff role, you agree to follow these guidelines and understand the consequences of failing to do so. Thank you for your dedication to helping make Delirium Den a welcoming and positive community for everyone!",
            color=0x7B68EE,
            timestamp=datetime.utcnow()
        )
        
        ack_embed.set_footer(text="Delirium Den Staff Guidelines", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await staff_rules_channel.send(embed=ack_embed)
        
        # Notify completion - send a new message instead of editing
        if status_message:
            try:
                await status_message.delete()
            except discord.NotFound:
                pass
        
        final_embed = discord.Embed(
            title="✅ Staff Rules Created Successfully",
            description=f"The staff rules channel has been set up at {staff_rules_channel.mention}.\n\n"
                       f"• Added 6 detailed rule sections\n"
                       f"• Configured proper permissions\n"
                       f"• Channel is ready for use",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        await ctx.send(embed=final_embed)
    
    @commands.command(name="updatestaffrules")
    @commands.has_permissions(administrator=True)
    async def update_staff_rules(self, ctx):
        """Updates the staff rules in an existing staff-rules channel"""
        # Check if staff-rules channel exists
        staff_rules_channel = discord.utils.get(ctx.guild.text_channels, name="staff-rules")
        if not staff_rules_channel:
            await ctx.send(embed=discord.Embed(
                title="❌ Channel Not Found",
                description="No `staff-rules` channel found. Please use `!createstaffrules` to create one first.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            ))
            return
        
        # Ask for confirmation
        confirmation_embed = discord.Embed(
            title="🔄 Update Staff Rules",
            description=f"This will clear and update all content in {staff_rules_channel.mention}.\n\n"
                       "Do you want to proceed?",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        status_message = await ctx.send(embed=confirmation_embed)
        
        # Add reaction buttons
        await status_message.add_reaction("✅")
        await status_message.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == status_message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "❌":
                try:
                    await status_message.edit(embed=discord.Embed(
                        title="❌ Operation Cancelled",
                        description="Staff rules update was cancelled.",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    ))
                except discord.NotFound:
                    await ctx.send(embed=discord.Embed(
                        title="❌ Operation Cancelled",
                        description="Staff rules update was cancelled.",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    ))
                return
            
        except asyncio.TimeoutError:
            try:
                await status_message.edit(embed=discord.Embed(
                    title="⏱️ Timed Out",
                    description="No response received. Staff rules update was cancelled.",
                    color=discord.Color.grey(),
                    timestamp=datetime.utcnow()
                ))
            except discord.NotFound:
                await ctx.send(embed=discord.Embed(
                    title="⏱️ Timed Out",
                    description="No response received. Staff rules update was cancelled.",
                    color=discord.Color.grey(),
                    timestamp=datetime.utcnow()
                ))
            return
        
        # Operation confirmed
        try:
            await status_message.delete()
        except discord.NotFound:
            pass
            
        # Clear the channel
        await staff_rules_channel.purge(limit=100)
        
        # Use the createstaffrules function directly with skip_confirmation=True
        ctx.channel = staff_rules_channel  # Temporarily change the context channel
        await self.create_staff_rules(ctx, skip_confirmation=True)
        
        # Send final confirmation in the original channel
        await ctx.send(embed=discord.Embed(
            title="✅ Staff Rules Updated Successfully",
            description=f"The staff rules have been updated in {staff_rules_channel.mention}.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        ))

# Make sure the cog is properly registered
async def setup(bot):
    """Add the StaffRules cog to the bot"""
    await bot.add_cog(StaffRules(bot))
    print("StaffRules cog loaded successfully")