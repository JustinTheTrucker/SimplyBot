# cogs/tickets.py
import discord
from discord.ext import commands
from discord import app_commands
from discord import ui
import os
import json
import asyncio
from datetime import datetime

class TicketButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="Create Ticket",
            style=discord.ButtonStyle.green,
            custom_id="persistent_ticket_button",
            emoji="🎭"
        )

    async def callback(self, interaction: discord.Interaction):
        # Check if user already has an open ticket
        for channel in interaction.guild.text_channels:
            if channel.name == f"ticket-{interaction.user.name.lower()}":
                error_embed = discord.Embed(
                    title="❌ Ticket Already Exists",
                    description="You already have an open ticket! Please use your existing ticket or close it first.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                error_embed.add_field(
                    name="Existing Ticket",
                    value=channel.mention,
                    inline=True
                )
                error_embed.set_footer(
                    text="Delirium Den • Ticket System",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

        # Create ticket channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Add staff role permissions if exists
        staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = discord.utils.get(interaction.guild.categories, name="🎭 Delirium Den Tickets")
        if not category:
            category = await interaction.guild.create_category("🎭 Delirium Den Tickets")

        channel = await interaction.guild.create_text_channel(
            f"ticket-{interaction.user.name.lower()}",
            category=category,
            overwrites=overwrites,
            topic=f"Support ticket for {interaction.user.name} • Created {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # Send initial message
        embed = discord.Embed(
            title="🎭 Delirium Den Support Ticket",
            description=f"Welcome to the chaos, {interaction.user.mention}! Please describe your issue and our staff will assist you shortly.\n\nThis is your private support channel where you can discuss your concerns safely.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📋 Ticket Information",
            value=f"**Ticket Owner:** {interaction.user.mention}\n**Created:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** Open",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Available Commands",
            value="• `/ticket_close` - Close this ticket\n• `/ticket_add @user` - Add someone to the ticket\n• `/ticket_remove @user` - Remove someone from the ticket\n• `/ticket_claim` - Claim this ticket (Staff only)\n• `/ticket_rename <name>` - Rename the ticket channel",
            inline=False
        )
        
        embed.add_field(
            name="📞 Getting Help",
            value="Please provide as much detail as possible about your issue. Our staff will be with you shortly!",
            inline=False
        )
        
        embed.set_footer(
            text="Delirium Den • Support System",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )

        view = TicketControls()
        await channel.send(embed=embed, view=view)
        
        # Ping staff and ticket creator in a separate message
        if staff_role:
            # Create a notification embed with ticket information
            notification_embed = discord.Embed(
                title="🔔 New Support Ticket",
                description=f"A new support ticket has been created in the Delirium Den! Please respond as soon as possible.",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            notification_embed.add_field(
                name="🎭 Ticket Owner",
                value=f"{interaction.user.mention}\n`{interaction.user.name}` (ID: {interaction.user.id})",
                inline=True
            )
            
            notification_embed.add_field(
                name="📅 Created At",
                value=f"<t:{int(datetime.now().timestamp())}:F>",
                inline=True
            )
            
            notification_embed.add_field(
                name="📍 Channel",
                value=channel.mention,
                inline=True
            )
            
            notification_embed.add_field(
                name="⚡ Priority",
                value="Standard",
                inline=True
            )
            
            notification_embed.add_field(
                name="🎯 Status",
                value="Awaiting Staff Response",
                inline=True
            )
            
            notification_embed.set_footer(
                text="Delirium Den • Staff Notification",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            # Send ping with embed
            await channel.send(f"🎭 {interaction.user.mention} {staff_role.mention}", embed=notification_embed)
        else:
            await channel.send(f"🎭 {interaction.user.mention}")

        # Success response
        success_embed = discord.Embed(
            title="✅ Ticket Created Successfully",
            description=f"Your support ticket has been created: {channel.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="What's Next?",
            value="Head over to your ticket channel and describe your issue. Our staff will be with you shortly!",
            inline=False
        )
        success_embed.set_footer(
            text="Delirium Den • Ticket Created",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

class ClosureReasonModal(ui.Modal, title="🎭 Delirium Den Ticket Closure"):
    """Modal that pops up when closing a ticket to ask for a reason"""
    reason = ui.TextInput(
        label="Reason for Closing",
        placeholder="Please provide a detailed reason for closing this ticket...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # First, acknowledge the interaction
        await interaction.response.defer(ephemeral=True)
        
        # Check if this is a ticket channel
        if not (interaction.channel.name.startswith("ticket-") or interaction.channel.name.startswith("claimed-")):
            error_embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in ticket channels!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        # Send a message in the channel that we're closing the ticket
        closure_embed = discord.Embed(
            title="🔒 Closing Ticket",
            description="Creating transcript and preparing closure...",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        closure_embed.add_field(
            name="Closure Reason",
            value=self.reason.value,
            inline=False
        )
        closure_embed.add_field(
            name="Closed By",
            value=interaction.user.mention,
            inline=True
        )
        closure_embed.set_footer(
            text="Delirium Den • Ticket Closure",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.channel.send(embed=closure_embed)

        # Create transcript
        transcript = []
        transcript.append(f"=== DELIRIUM DEN TICKET TRANSCRIPT ===")
        transcript.append(f"Ticket: {interaction.channel.name}")
        transcript.append(f"Closed by: {interaction.user.name} ({interaction.user.id})")
        transcript.append(f"Closed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        transcript.append(f"Reason: {self.reason.value}")
        transcript.append(f"=" * 50)
        transcript.append("")
        
        async for message in interaction.channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
            author = f"{message.author.name}#{message.author.discriminator}"
            content = message.content if message.content else "[No text content]"
            
            if message.embeds:
                content += f" [Embed: {len(message.embeds)} embed(s)]"
            if message.attachments:
                content += f" [Attachments: {', '.join([att.filename for att in message.attachments])}]"
                
            transcript.append(f"[{timestamp}] {author}: {content}")

        # Save transcript
        transcript_text = "\n".join(transcript)
        filename = f"delirium-den-transcript-{interaction.channel.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        # Extract original ticket creator name (works for both "ticket-name" and "claimed-name" formats)
        ticket_creator_name = interaction.channel.name.split("-", 1)[1]
        members = interaction.guild.members
        ticket_creator = None
        
        # Try to find the ticket creator by username
        for member in members:
            if member.name.lower() == ticket_creator_name:
                ticket_creator = member
                break
        
        if ticket_creator:
            try:
                closure_dm_embed = discord.Embed(
                    title="🔒 Your Delirium Den Ticket Has Been Closed",
                    description="Your support ticket has been resolved and closed. A complete transcript is attached below for your records.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                
                closure_dm_embed.add_field(
                    name="📋 Closure Details",
                    value=f"**Reason:** {self.reason.value}\n**Closed By:** {interaction.user.name}\n**Closed At:** <t:{int(datetime.now().timestamp())}:F>",
                    inline=False
                )
                
                closure_dm_embed.add_field(
                    name="📄 Transcript",
                    value="A complete transcript of your ticket conversation is attached to this message.",
                    inline=False
                )
                
                closure_dm_embed.add_field(
                    name="💬 Need More Help?",
                    value="If you need further assistance, feel free to create a new ticket anytime!",
                    inline=False
                )
                
                closure_dm_embed.set_footer(
                    text="Delirium Den • Support System",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                
                await ticket_creator.send(
                    embed=closure_dm_embed,
                    file=discord.File(filename)
                )
            except Exception as e:
                error_embed = discord.Embed(
                    title="⚠️ Warning",
                    description=f"Failed to send transcript to user: {str(e)}",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                error_embed.set_footer(
                    text="Delirium Den • Warning",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        # Send confirmation to user who closed the ticket
        success_embed = discord.Embed(
            title="✅ Ticket Closed Successfully",
            description="The ticket has been closed and transcript created.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.set_footer(
            text="Delirium Den • Success",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)
        
        # Delete channel after a short delay
        countdown_embed = discord.Embed(
            title="⏰ Channel Deletion",
            description="This ticket channel will be deleted in 5 seconds...",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        countdown_embed.set_footer(
            text="Delirium Den • Cleanup",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.channel.send(embed=countdown_embed)
        await asyncio.sleep(5)
        
        try:
            await interaction.channel.delete()
            # Clean up transcript file after channel is deleted
            os.remove(filename)
        except Exception as e:
            print(f"Error deleting channel or cleaning up file: {str(e)}")

class CloseButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="Close Ticket", 
            style=discord.ButtonStyle.red, 
            emoji="🔒", 
            custom_id="close_ticket_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Show the closure reason modal
        await interaction.response.send_modal(ClosureReasonModal())

class ClaimButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="Claim Ticket", 
            style=discord.ButtonStyle.blurple, 
            emoji="✋", 
            custom_id="claim_ticket_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Acknowledge the interaction immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.channel.name.startswith("ticket-"):
            if interaction.channel.name.startswith("claimed-"):
                error_embed = discord.Embed(
                    title="❌ Already Claimed",
                    description="This ticket has already been claimed by another staff member!",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                error_embed.set_footer(
                    text="Delirium Den • Error",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
            
        # Check if user has staff role
        staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
        if staff_role not in interaction.user.roles:
            error_embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="Only staff members can claim tickets!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Required Role",
                value="Staff",
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
            
        # Get the ticket creator
        ticket_creator_name = interaction.channel.name.replace("ticket-", "")
        ticket_creator = None
        for member in interaction.guild.members:
            if member.name.lower() == ticket_creator_name:
                ticket_creator = member
                break
                
        # Update channel name to show it's claimed
        await interaction.channel.edit(
            name=f"claimed-{ticket_creator_name}",
            topic=f"Support ticket claimed by {interaction.user.name} • Originally created by {ticket_creator_name}"
        )
        
        # Send notification embed
        claim_embed = discord.Embed(
            title="✅ Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}.\nThey will be your dedicated support representative for this issue.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        claim_embed.add_field(
            name="🎭 Support Representative",
            value=f"{interaction.user.mention}\n`{interaction.user.name}`",
            inline=True
        )
        
        claim_embed.add_field(
            name="📅 Claimed At",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        claim_embed.add_field(
            name="💬 What This Means",
            value="Your ticket now has a dedicated staff member who will personally handle your issue from start to finish.",
            inline=False
        )
        
        claim_embed.set_footer(
            text="Delirium Den • Support System",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        # Disable the claim button after it's been used
        for item in self.view.children:
            if isinstance(item, ClaimButton):
                item.disabled = True
                item.label = "Claimed"
                item.style = discord.ButtonStyle.gray
                
        # Send followup to confirm action is complete
        success_embed = discord.Embed(
            title="✅ Ticket Claimed",
            description="You've successfully claimed this ticket!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.set_footer(
            text="Delirium Den • Success",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)
        
        # Send public message to channel
        await interaction.channel.send(embed=claim_embed)
        
        # Try to update the view with disabled button
        try:
            # Get the original message with the buttons
            async for message in interaction.channel.history(limit=20):
                if message.author == interaction.client.user and message.embeds:
                    if len(message.embeds) > 0 and "Delirium Den Support Ticket" in message.embeds[0].title:
                        await message.edit(view=self.view)
                        break
        except:
            pass # Ignore if we can't update the original message

class TicketControls(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Add buttons to the view
        self.add_item(ClaimButton())
        self.add_item(CloseButton())

class PersistentTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton())

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets_channel_id = int(os.getenv('TICKETS_CHANNEL_ID'))

    @commands.Cog.listener()
    async def on_ready(self):
        """Set up persistent views when bot is ready"""
        print("🎭 Delirium Den Tickets cog loaded successfully")
        
        # Add the persistent views
        self.bot.add_view(PersistentTicketView())
        self.bot.add_view(TicketControls())
        
        # Set up ticket panel
        await self.setup_ticket_panel()

    async def setup_ticket_panel(self):
        """Set up the ticket panel"""
        channel = self.bot.get_channel(self.tickets_channel_id)
        if not channel:
            print(f"Ticket channel not found: {self.tickets_channel_id}")
            return

        # Check if setup message already exists
        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.embeds:
                if len(message.embeds) > 0 and "🎭 Delirium Den Support" in message.embeds[0].title:
                    print("🎭 Delirium Den ticket panel already exists")
                    return

        # Create ticket panel
        embed = discord.Embed(
            title="🎭 Delirium Den Support System",
            description="Welcome to the Delirium Den support system! Need help navigating the chaos? Click the button below to create a private support ticket.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎪 How Our Support Works",
            value="1. **Click the button** below to create your ticket\n2. **Private channel** will be created just for you\n3. **Describe your issue** in detail\n4. **Staff notification** sent automatically\n5. **Get personalized help** from our team",
            inline=False
        )
        
        embed.add_field(
            name="📋 Ticket Guidelines",
            value="• **Be respectful** and patient with our staff\n• **Provide detailed information** about your issue\n• **One issue per ticket** - create separate tickets for different problems\n• **Don't ping staff** repeatedly - we'll respond as soon as possible\n• **Be honest** about any rule violations or issues",
            inline=False
        )
        
        embed.add_field(
            name="⚡ What to Expect",
            value="• **Fast Response** - Staff will be notified immediately\n• **Private Discussion** - Only you and staff can see your ticket\n• **Complete Transcript** - You'll receive a copy when closed\n• **Professional Support** - Our team is here to help!",
            inline=False
        )
        
        embed.add_field(
            name="🎭 Types of Support",
            value="• General questions about the server\n• Technical issues or bugs\n• Rule clarifications\n• Appeal requests\n• Reporting inappropriate behavior\n• Account or role issues",
            inline=False
        )
        
        embed.set_footer(
            text="Delirium Den • Support System",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )

        view = PersistentTicketView()
        
        await channel.send(embed=embed, view=view)
        print("🎭 Delirium Den ticket panel created successfully")

    @app_commands.command(name="ticket_setup", description="Set up the Delirium Den ticket panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        """Manually set up the ticket panel"""
        await self.setup_ticket_panel()
        
        success_embed = discord.Embed(
            title="✅ Ticket Panel Setup Complete",
            description="The Delirium Den ticket support system has been successfully configured!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="Setup By",
            value=interaction.user.mention,
            inline=True
        )
        success_embed.add_field(
            name="Channel",
            value=f"<#{self.tickets_channel_id}>",
            inline=True
        )
        success_embed.set_footer(
            text="Delirium Den • Setup Complete",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @app_commands.command(name="ticket_close", description="Close the current ticket with a reason")
    async def close(self, interaction: discord.Interaction):
        """Close a ticket"""
        # Send a modal to ask for the closure reason
        modal = ClosureReasonModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="ticket_add", description="Add a user to the current ticket")
    async def add(self, interaction: discord.Interaction, user: discord.Member):
        """Add a user to the ticket"""
        if not (interaction.channel.name.startswith("ticket-") or interaction.channel.name.startswith("claimed-")):
            error_embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in ticket channels!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)
        
        success_embed = discord.Embed(
            title="✅ User Added to Ticket",
            description=f"{user.mention} has been added to this ticket and can now participate in the conversation.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="Added User",
            value=f"{user.mention}\n`{user.name}`",
            inline=True
        )
        success_embed.add_field(
            name="Added By",
            value=interaction.user.mention,
            inline=True
        )
        success_embed.set_footer(
            text="Delirium Den • User Added",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=success_embed)

    @app_commands.command(name="ticket_remove", description="Remove a user from the current ticket")
    async def remove(self, interaction: discord.Interaction, user: discord.Member):
        """Remove a user from the ticket"""
        if not (interaction.channel.name.startswith("ticket-") or interaction.channel.name.startswith("claimed-")):
            error_embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in ticket channels!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        # Don't allow removing the ticket creator
        ticket_creator_name = interaction.channel.name.split("-", 1)[1]
        if user.name.lower() == ticket_creator_name:
            error_embed = discord.Embed(
                title="❌ Cannot Remove Ticket Owner",
                description="You cannot remove the ticket creator from their own ticket!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Ticket Owner",
                value=user.mention,
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        await interaction.channel.set_permissions(user, overwrite=None)
        
        success_embed = discord.Embed(
            title="✅ User Removed from Ticket",
            description=f"{user.mention} has been removed from this ticket and can no longer see or participate in the conversation.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="Removed User",
            value=f"{user.mention}\n`{user.name}`",
            inline=True
        )
        success_embed.add_field(
            name="Removed By",
            value=interaction.user.mention,
            inline=True
        )
        success_embed.set_footer(
            text="Delirium Den • User Removed",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=success_embed)

    @app_commands.command(name="ticket_rename", description="Rename the current ticket channel")
    async def rename(self, interaction: discord.Interaction, name: str):
        """Rename the ticket channel"""
        if not (interaction.channel.name.startswith("ticket-") or interaction.channel.name.startswith("claimed-")):
            error_embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in ticket channels!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        # Preserve the ticket status (claimed or not)
        prefix = "claimed" if interaction.channel.name.startswith("claimed-") else "ticket"
        old_name = interaction.channel.name
        new_name = f"{prefix}-{name}"
        
        await interaction.channel.edit(name=new_name)
        
        success_embed = discord.Embed(
            title="✅ Ticket Renamed",
            description="The ticket channel has been successfully renamed.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="Old Name",
            value=f"`{old_name}`",
            inline=True
        )
        success_embed.add_field(
            name="New Name",
            value=f"`{new_name}`",
            inline=True
        )
        success_embed.add_field(
            name="Renamed By",
            value=interaction.user.mention,
            inline=True
        )
        success_embed.set_footer(
            text="Delirium Den • Channel Renamed",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=success_embed)

    @app_commands.command(name="ticket_claim", description="Claim the current ticket as a staff member")
    async def claim(self, interaction: discord.Interaction):
        """Claim a ticket"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.channel.name.startswith("ticket-"):
            if interaction.channel.name.startswith("claimed-"):
                error_embed = discord.Embed(
                    title="❌ Already Claimed",
                    description="This ticket has already been claimed by another staff member!",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                error_embed.set_footer(
                    text="Delirium Den • Error",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                error_embed = discord.Embed(
                    title="❌ Invalid Channel",
                    description="This command can only be used in ticket channels!",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                error_embed.set_footer(
                    text="Delirium Den • Error",
                    icon_url="https://i.imgur.com/RzksmKL.png"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        # Check if user has staff role
        staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
        if staff_role not in interaction.user.roles:
            error_embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="Only staff members can claim tickets!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Required Role",
                value="Staff",
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        # Get the ticket creator name
        ticket_creator_name = interaction.channel.name.replace("ticket-", "")
        
        # Update channel name to show it's claimed
        await interaction.channel.edit(
            name=f"claimed-{ticket_creator_name}",
            topic=f"Support ticket claimed by {interaction.user.name} • Originally created by {ticket_creator_name}"
        )
        
        # Send notification embed
        claim_embed = discord.Embed(
            title="✅ Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}.\nThey will be your dedicated support representative for this issue.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        claim_embed.add_field(
            name="🎭 Support Representative",
            value=f"{interaction.user.mention}\n`{interaction.user.name}`",
            inline=True
        )
        
        claim_embed.add_field(
            name="📅 Claimed At",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        claim_embed.add_field(
            name="💬 What This Means",
            value="Your ticket now has a dedicated staff member who will personally handle your issue from start to finish.",
            inline=False
        )
        
        claim_embed.set_footer(
            text="Delirium Den • Support System",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        success_embed = discord.Embed(
            title="✅ Ticket Claimed",
            description="You've successfully claimed this ticket!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.set_footer(
            text="Delirium Den • Success",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.followup.send(embed=success_embed, ephemeral=True)
        await interaction.channel.send(embed=claim_embed)

    @app_commands.command(name="ticket_info", description="Get information about the current ticket")
    async def ticket_info(self, interaction: discord.Interaction):
        """Get information about the current ticket"""
        if not (interaction.channel.name.startswith("ticket-") or interaction.channel.name.startswith("claimed-")):
            error_embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in ticket channels!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        # Parse ticket information
        is_claimed = interaction.channel.name.startswith("claimed-")
        ticket_creator_name = interaction.channel.name.split("-", 1)[1]
        
        # Find ticket creator
        ticket_creator = None
        for member in interaction.guild.members:
            if member.name.lower() == ticket_creator_name:
                ticket_creator = member
                break

        # Get channel creation time
        channel_created = interaction.channel.created_at
        
        # Count messages
        message_count = 0
        async for message in interaction.channel.history(limit=None):
            message_count += 1

        info_embed = discord.Embed(
            title="🎭 Ticket Information",
            description=f"Detailed information about this Delirium Den support ticket.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        info_embed.add_field(
            name="📋 Basic Info",
            value=f"**Channel:** {interaction.channel.mention}\n**Status:** {'🔒 Claimed' if is_claimed else '🔓 Open'}\n**Created:** <t:{int(channel_created.timestamp())}:F>",
            inline=False
        )
        
        if ticket_creator:
            info_embed.add_field(
                name="👤 Ticket Owner",
                value=f"{ticket_creator.mention}\n`{ticket_creator.name}` (ID: {ticket_creator.id})",
                inline=True
            )
        else:
            info_embed.add_field(
                name="👤 Ticket Owner",
                value=f"User not found\n`{ticket_creator_name}` (User may have left)",
                inline=True
            )
            
        info_embed.add_field(
            name="📊 Statistics",
            value=f"**Messages:** {message_count}\n**Active For:** <t:{int(channel_created.timestamp())}:R>",
            inline=True
        )
        
        # Get channel permissions info
        permitted_users = []
        for member in interaction.guild.members:
            perms = interaction.channel.permissions_for(member)
            if perms.read_messages and not member.bot:
                permitted_users.append(member.name)
        
        if len(permitted_users) <= 10:
            users_list = ", ".join(permitted_users)
        else:
            users_list = ", ".join(permitted_users[:10]) + f"... and {len(permitted_users) - 10} more"
            
        info_embed.add_field(
            name="👥 Permitted Users",
            value=f"**Count:** {len(permitted_users)}\n**Users:** {users_list}",
            inline=False
        )
        
        info_embed.set_footer(
            text="Delirium Den • Ticket Information",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=info_embed, ephemeral=True)

    @app_commands.command(name="ticket_help", description="Get help with ticket system commands")
    async def ticket_help(self, interaction: discord.Interaction):
        """Get help with ticket system commands"""
        help_embed = discord.Embed(
            title="🎭 Delirium Den Ticket System Help",
            description="Complete guide to using the Delirium Den support ticket system.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        help_embed.add_field(
            name="🎫 Creating Tickets",
            value="Click the **Create Ticket** button in the support channel to create your private ticket. Only you and staff can see it!",
            inline=False
        )
        
        help_embed.add_field(
            name="🛠️ Ticket Commands",
            value="```/ticket_close - Close the current ticket\n/ticket_add @user - Add someone to ticket\n/ticket_remove @user - Remove someone from ticket\n/ticket_claim - Claim ticket (Staff only)\n/ticket_rename <name> - Rename the ticket\n/ticket_info - View ticket information```",
            inline=False
        )
        
        help_embed.add_field(
            name="👑 Admin Commands",
            value="```/ticket_setup - Setup the ticket panel```",
            inline=False
        )
        
        help_embed.add_field(
            name="🎯 Ticket Features",
            value="• **Private Channels** - Only you and staff can see your ticket\n• **Automatic Staff Notification** - Staff are pinged when you create a ticket\n• **Transcript Generation** - Complete conversation history sent to you when closed\n• **Claiming System** - Staff can claim tickets for dedicated support\n• **User Management** - Add/remove users from tickets as needed",
            inline=False
        )
        
        help_embed.add_field(
            name="📋 Best Practices",
            value="• **Be detailed** - Explain your issue clearly\n• **Be patient** - Staff will respond as soon as possible\n• **Stay respectful** - Follow server rules in tickets\n• **One issue per ticket** - Create separate tickets for different problems\n• **Provide context** - Include relevant screenshots or information",
            inline=False
        )
        
        help_embed.add_field(
            name="⚠️ Important Notes",
            value="• Tickets are logged and transcripts are saved\n• Staff can see all ticket activity\n• Abuse of the ticket system may result in restrictions\n• Closed tickets cannot be reopened - create a new one if needed",
            inline=False
        )
        
        help_embed.set_footer(
            text="Delirium Den • Ticket System Help",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))