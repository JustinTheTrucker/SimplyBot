import discord
from discord.ext import commands
import asyncio
import re


class Archive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Regex pattern to identify category header channels
        self.category_pattern = re.compile(r"^📂 (.+?) 📂$")

    @commands.command(name="archive")
    @commands.has_permissions(administrator=True)
    async def archive(self, ctx):
        """
        Archives the entire server structure into an 'archived' category 
        and makes it invisible to everyone while preserving layout
        """
        
        # Send initial message
        status_msg = await ctx.send("📦 Starting archival process...")
        
        # Create the main archive category
        archive_category = await ctx.guild.create_category(
            name="archived",
            reason="Archival requested by " + str(ctx.author)
        )
        
        # Set default permissions for the archive category - invisible to everyone
        everyone_role = ctx.guild.default_role
        await archive_category.set_permissions(
            everyone_role, 
            view_channel=False,    # No one can see the archived content
            send_messages=False,   # No one can send new messages
            connect=False,         # No one can connect to voice channels
            speak=False            # No one can speak in voice channels
        )
        
        await status_msg.edit(
            content="📦 Archive category created with no permissions (hidden from everyone). Beginning channel migration..."
        )
        
        # Get all categories in the guild
        categories = ctx.guild.categories
        
        # Skip the newly created archive category
        categories = [category for category in categories if category.id != archive_category.id]
        
        for category in categories:
            # Create a text channel with the category name in the archive category as a separator
            category_header = await ctx.guild.create_text_channel(
                name=f"📂 {category.name.upper()} 📂",  # Using folder emoji and uppercase to clearly identify as category header
                category=archive_category,
                reason="Category header - preserving original layout"
            )
            
            # Make the category header read-only for everyone
            await category_header.edit(sync_permissions=True)
            await category_header.set_permissions(
                ctx.guild.default_role,
                send_messages=False,
                add_reactions=False
            )
            
            # Send an information message in the category header
            try:
                await category_header.send(
                    f"**CATEGORY: {category.name}**\n─────────────────────\nThis channel represents the original category structure."
                )
            except:
                pass
            
            # Process text channels in this category
            for text_channel in category.text_channels:
                try:
                    # Move the existing text channel to archive category
                    await text_channel.edit(
                        category=archive_category,
                        position=category_header.position + 1,  # Position right after the category header
                        reason="Channel archival - preserving message history and layout"
                    )
                    # Reset permissions to inherit from parent category
                    await text_channel.edit(sync_permissions=True)
                except discord.Forbidden:
                    await ctx.send(f"⚠️ Warning: Couldn't move text channel {text_channel.name}")
            
            # Process voice channels in this category
            for voice_channel in category.voice_channels:
                try:
                    # Move the existing voice channel to archive category
                    await voice_channel.edit(
                        category=archive_category,
                        reason="Channel archival - preserving all settings and layout"
                    )
                    # Reset permissions to inherit from parent category
                    await voice_channel.edit(sync_permissions=True)
                except discord.Forbidden:
                    await ctx.send(f"⚠️ Warning: Couldn't move voice channel {voice_channel.name}")
                    
            await status_msg.edit(content=f"📦 Archived category: {category.name}")
            
            # Delete the now-empty category
            try:
                await category.delete(reason="Category archived to 'archived' category")
            except discord.Forbidden:
                await ctx.send(f"⚠️ Warning: Couldn't delete empty category {category.name}")
            
        # Process uncategorized channels
        uncategorized = [
            c for c in ctx.guild.channels 
            if c.category is None and not isinstance(c, discord.CategoryChannel)
        ]
        
        if uncategorized:
            # Create a text channel to represent uncategorized section
            uncategorized_header = await ctx.guild.create_text_channel(
                name="📂 UNCATEGORIZED 📂",
                category=archive_category,
                reason="Uncategorized header - preserving original layout"
            )
            
            # Make the uncategorized header read-only for everyone
            await uncategorized_header.edit(sync_permissions=True)
            await uncategorized_header.set_permissions(
                ctx.guild.default_role,
                send_messages=False,
                add_reactions=False
            )
            
            # Send an information message in the uncategorized header
            try:
                await uncategorized_header.send(
                    "**UNCATEGORIZED CHANNELS**\n─────────────────────\nThis channel represents channels that were not in any category."
                )
            except:
                pass
            
            # Process all uncategorized channels
            for channel in uncategorized:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel)):
                    try:
                        # Move the existing channel to archive category
                        await channel.edit(
                            category=archive_category,
                            position=uncategorized_header.position + 1,  # Position right after the header
                            reason="Channel archival - preserving history, settings, and layout"
                        )
                        # Reset permissions to inherit from parent category
                        await channel.edit(sync_permissions=True)
                    except discord.Forbidden:
                        await ctx.send(f"⚠️ Warning: Couldn't move channel {channel.name}")
            
            await status_msg.edit(content="📦 Archived uncategorized channels")
        
        # Add permissions for the command executor to still see the archived content
        try:
            await archive_category.set_permissions(
                ctx.author,
                view_channel=True,    # Command executor can still see everything
                send_messages=True,   # And can send messages if needed
                connect=True,         # And can connect to voice channels
                speak=True            # And can speak in voice channels
            )
            # Let the user know they still have access
            note = "\n\nNote: You (the command executor) have been granted permission to view and manage the archived content."
        except:
            note = ""
            
        await status_msg.edit(
            content=f"✅ Archival process complete! All channels have been moved to the 'archived' category which is hidden from everyone. Original layout has been preserved using text channel headers.{note}"
        )

    @commands.command(name="unarchive")
    @commands.has_permissions(administrator=True)
    async def unarchive(self, ctx):
        """Restores the server structure from an 'archived' category"""
        
        # Send initial message
        status_msg = await ctx.send("🔄 Starting unarchival process...")
        
        # Find the archive category
        archive_category = discord.utils.get(ctx.guild.categories, name="archived")
        
        if not archive_category:
            return await status_msg.edit(
                content="❌ No 'archived' category found. Nothing to unarchive."
            )
        
        # Initialize a dictionary to keep track of category groupings
        categories = {}
        current_category = None
        
        # Get all channels in the archive category
        channels = archive_category.channels
        channels.sort(key=lambda c: c.position)  # Sort by position to maintain order
        
        # First pass: Identify category headers and group channels
        for channel in channels:
            # Check if this is a category header channel
            match = self.category_pattern.match(channel.name)
            
            if match and isinstance(channel, discord.TextChannel):
                # This is a category header, extract the original category name
                category_name = match.group(1).title()  # Convert back to title case
                
                if category_name == "UNCATEGORIZED":
                    current_category = None
                else:
                    # Create a new category with the original name
                    try:
                        new_category = await ctx.guild.create_category(
                            name=category_name,
                            reason="Unarchival process - restoring server structure"
                        )
                        current_category = new_category
                        await status_msg.edit(content=f"🔄 Restored category: {category_name}")
                    except:
                        await ctx.send(f"⚠️ Warning: Couldn't create category {category_name}")
                        current_category = None
                
                # Store the header to delete later
                categories[category_name] = {
                    'category': current_category,
                    'header': channel,
                    'channels': []
                }
            elif current_category is not None or (match and match.group(1) == "UNCATEGORIZED"):
                # This is a channel belonging to the current category or an uncategorized channel
                if current_category is None:
                    # This belongs to uncategorized
                    category_name = "UNCATEGORIZED"
                else:
                    # This belongs to current category
                    category_name = current_category.name
                
                # Add it to the group
                categories[category_name]['channels'].append(channel)
        
        # Second pass: Move channels to their respective categories
        for category_name, data in categories.items():
            category = data['category']
            header = data['header']
            
            for channel in data['channels']:
                try:
                    if category:
                        # Move channel to its proper category
                        await channel.edit(
                            category=category,
                            reason="Unarchival process - restoring channel to original category"
                        )
                    else:
                        # This channel belongs to uncategorized, so remove its category
                        await channel.edit(
                            category=None,
                            reason="Unarchival process - restoring channel to uncategorized"
                        )
                except discord.Forbidden:
                    await ctx.send(f"⚠️ Warning: Couldn't move channel {channel.name}")
            
            # Delete the category header channel
            try:
                await header.delete(reason="Unarchival process - removing category header")
            except:
                await ctx.send(f"⚠️ Warning: Couldn't delete header channel for {category_name}")
        
        # Finally, delete the archive category
        try:
            await archive_category.delete(reason="Unarchival process complete - removing archive category")
            await status_msg.edit(content="✅ Unarchival process complete! The server structure has been restored.")
        except:
            await status_msg.edit(
                content="⚠️ Unarchival partially complete. Could not delete the archive category, but channels have been restored."
            )


async def setup(bot):
    await bot.add_cog(Archive(bot))