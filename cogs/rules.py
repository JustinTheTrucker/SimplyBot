# cogs/rules.py
import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules_channel_id = int(os.getenv('RULES_CHANNEL_ID', 0))
        
        # Default server rules
        self.discord_rules = {
            "title": "🎭 DELIRIUM DEN RULES",
            "sections": [
                {
                    "name": "1. Follow Discord TOS",
                    "rules": [
                        "If Discord says not to do it, don't do it"
                    ]
                },
                {
                    "name": "2. Just generally don't be a dick man, not that hard",
                    "rules": [
                        "Just be decent to people, don't make people uncomfortable or anything",
                        "Most of the rules tie into this one"
                    ]
                },
                {
                    "name": "3. No bigotry in any form",
                    "rules": [
                        "Bigotry is prejudice against a person or people on the basis of their membership of a particular group",
                        "You will almost always get banned"
                    ]
                },
                {
                    "name": "4. No NSFW or acting overly sexual at ALL",
                    "rules": [
                        "This includes NSFW jokes, innuendos, or anything that's even a tad bit too sexual"
                    ]
                },
                {
                    "name": "5. No excessive trash talk, death threats, or any other form of extreme disrespect",
                    "rules": [
                        "Playful teasing is fine, but don't take it too far",
                        "Even as a joke"
                    ]
                },
                {
                    "name": "6. Try to take major disputes/debates to DMs, and remember to follow rule 5",
                    "rules": [
                        "Just to keep things civil in the server, keep arguments out of here"
                    ]
                },
                {
                    "name": "7. No slurs or excessive swearing",
                    "rules": [
                        "Some swearing is fine and expected, but don't go over the top",
                        "Slurs will almost ALWAYS get you banned"
                    ]
                },
                {
                    "name": "8. No doxxing, sending images of someone's face without consent, or anything like that",
                    "rules": [
                        "Don't share anyone's private info, ever"
                    ]
                },
                {
                    "name": "9. No self-promotion outside of designated spaces",
                    "rules": [
                        "Don't drop your socials outside of the self promo channel",
                        "Don't share discord links ever except for partners"
                    ]
                },
                {
                    "name": "10. No spamming",
                    "rules": [
                        "Especially mentions, but all spam is unwelcome here"
                    ]
                },
                {
                    "name": "11. Keep things in the right channels",
                    "rules": [
                        "Don't send images in general unless they directly contribute to the conversation (you WILL be muted)",
                        "Don't put stuff in a place that it doesn't belong"
                    ]
                },
                {
                    "name": "12. English only",
                    "rules": [
                        "Unless a staff member gives you permission, keep the chat English only"
                    ]
                },
                {
                    "name": "13. No controversial/offensive topics",
                    "rules": [
                        "Avoid politics, religion, or other controversial topics"
                    ]
                },
                {
                    "name": "14. Staff members can interpret this list of rules however they'd like",
                    "rules": [
                        "Staff can punish you for things not on this list if it makes members uncomfortable",
                        "If you think you've been unfairly punished by a staff member, please contact one of their higher-ups"
                    ]
                },
                {
                    "name": "⚠️ Warn/Strike System",
                    "rules": [
                        "**1 Warn** - 1 hour timeout",
                        "**2 Warns** - 1 day timeout", 
                        "**3 Warns** - 3 day timeout",
                        "**4 Warns** - 1 week ban",
                        "**5 Warns** - 2 week ban",
                        "**6 Warns** - 1 month ban",
                        "**7 Warns** - Permaban"
                    ]
                }
            ]
        }
        
        self.minecraft_rules = {
            "title": "⛏️ DELIRIUM DEN MINECRAFT SERVER RULES",
            "description": "**Welcome to the Delirium Den Survival Multiplayer Server!**\n\nOur SMP is designed to provide a fun, collaborative Minecraft experience. To ensure everyone enjoys their time in our chaotic world, please follow these guidelines:",
            "sections": [
                {
                    "name": "1. Gameplay Rules",
                    "rules": [
                        "No griefing or destroying other players' builds",
                        "No stealing items from other players' chests/bases",
                        "No cheating, hacking, or using unapproved mods/clients",
                        "PvP is allowed only with mutual consent"
                    ]
                },
                {
                    "name": "2. Building Guidelines",
                    "rules": [
                        "Maintain a reasonable distance from other players' bases",
                        "Clean up floating trees and creeper holes",
                        "No excessive redstone that causes server lag",
                        "No claiming massive areas without actively building"
                    ]
                },
                {
                    "name": "3. Community & Resources",
                    "rules": [
                        "Respect community areas and public farms",
                        "Don't harvest other players' crops without replanting",
                        "Leave some resources in public mining areas",
                        "Contribute to community projects when possible"
                    ]
                },
                {
                    "name": "4. Technical Rules",
                    "rules": [
                        "No lag machines or contraptions that impact server performance",
                        "Report bugs to staff instead of exploiting them",
                        "AFK responsibly and avoid overloading mob farms",
                        "Follow staff directions regarding technical limitations"
                    ]
                },
                {
                    "name": "5. Delirium Den Specific Guidelines",
                    "rules": [
                        "Embrace the chaos, but don't create chaos for others",
                        "Creative pranks are welcome if they don't cause permanent damage",
                        "Help newcomers navigate the madness",
                        "Document your wildest builds for the community to admire"
                    ]
                }
            ],
            "footer_text": "Remember: This is the Delirium Den community server! Be respectful, embrace the madness, and help create an awesome SMP experience for everyone in our den of chaos."
        }

    @commands.Cog.listener()
    async def on_ready(self):
        """Set up rules message when bot is ready"""
        print("🎭 Delirium Den Rules cog loaded successfully")
        await self.setup_rules()

    async def setup_rules(self):
        """Set up the rules message"""
        if not self.rules_channel_id:
            print("Rules channel ID not set in .env")
            return
            
        channel = self.bot.get_channel(self.rules_channel_id)
        if not channel:
            print(f"Rules channel not found: {self.rules_channel_id}")
            return

        # Check if rules message already exists
        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.embeds:
                if len(message.embeds) > 0 and message.embeds[0].title == self.discord_rules["title"]:
                    print("Rules message already exists")
                    return

        # Create Discord rules embed
        discord_rules_embed = discord.Embed(
            title=self.discord_rules["title"],
            color=discord.Color.purple(),
            description="Welcome to the Delirium Den! These rules apply to all Discord channels and voice chats. Please read them carefully and follow them to maintain our chaotic but respectful community.",
            timestamp=datetime.utcnow()
        )
        
        # Add each rule section
        for section in self.discord_rules["sections"]:
            rules_text = "\n".join([f"• {rule}" for rule in section["rules"]])
            discord_rules_embed.add_field(
                name=section["name"],
                value=rules_text,
                inline=False
            )
        
        # Add additional info
        discord_rules_embed.add_field(
            name="📞 Need Help?",
            value="If you have questions about the rules or need staff assistance, don't hesitate to reach out to our moderation team!",
            inline=False
        )
        
        discord_rules_embed.set_footer(
            text="Delirium Den • Discord Community Guidelines",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await channel.send(embed=discord_rules_embed)

        # Create Minecraft SMP rules embed
        minecraft_embed = discord.Embed(
            title=self.minecraft_rules["title"],
            description=self.minecraft_rules["description"],
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        # Add each rule section
        for section in self.minecraft_rules["sections"]:
            rules_text = "\n".join([f"• {rule}" for rule in section["rules"]])
            minecraft_embed.add_field(
                name=section["name"],
                value=rules_text,
                inline=False
            )
        
        # Add the footer text as a field
        minecraft_embed.add_field(
            name="🎭 Final Note",
            value=self.minecraft_rules["footer_text"],
            inline=False
        )
        
        minecraft_embed.set_footer(
            text="Delirium Den • Minecraft SMP Guidelines",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await channel.send(embed=minecraft_embed)
        print("🎭 Delirium Den rules setup complete")

    @app_commands.command(name="rules_setup", description="Set up the rules message")
    @app_commands.checks.has_permissions(administrator=True)
    async def rules_setup(self, interaction: discord.Interaction):
        """Manually set up the rules message"""
        await self.setup_rules()
        
        success_embed = discord.Embed(
            title="✅ Rules Setup Complete",
            description="The Delirium Den rules have been successfully posted to the rules channel!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(
            name="Channel",
            value=f"<#{self.rules_channel_id}>",
            inline=True
        )
        success_embed.add_field(
            name="Setup By",
            value=interaction.user.mention,
            inline=True
        )
        success_embed.set_footer(
            text="Delirium Den • Rules Management",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @app_commands.command(name="rules_edit", description="Edit a specific rule section")
    @app_commands.checks.has_permissions(administrator=True)
    async def rules_edit(self, interaction: discord.Interaction, section: int, rule_number: int, new_rule: str):
        """Edit a specific rule"""
        if 0 <= section < len(self.discord_rules["sections"]) and 0 <= rule_number < len(self.discord_rules["sections"][section]["rules"]):
            old_rule = self.discord_rules["sections"][section]["rules"][rule_number]
            self.discord_rules["sections"][section]["rules"][rule_number] = new_rule
            
            success_embed = discord.Embed(
                title="✅ Rule Updated Successfully",
                description=f"Rule has been updated in section {section + 1}.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            success_embed.add_field(
                name="Section",
                value=self.discord_rules["sections"][section]["name"],
                inline=False
            )
            success_embed.add_field(
                name="Old Rule",
                value=f"```{old_rule}```",
                inline=False
            )
            success_embed.add_field(
                name="New Rule",
                value=f"```{new_rule}```",
                inline=False
            )
            success_embed.add_field(
                name="Updated By",
                value=interaction.user.mention,
                inline=True
            )
            success_embed.add_field(
                name="💡 Note",
                value="Use `/rules_refresh` to update the rules display in the channel.",
                inline=False
            )
            success_embed.set_footer(
                text="Delirium Den • Rules Management",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        else:
            error_embed = discord.Embed(
                title="❌ Invalid Parameters",
                description="The section or rule number you specified is invalid.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Valid Sections",
                value=f"0 - {len(self.discord_rules['sections']) - 1}",
                inline=True
            )
            error_embed.add_field(
                name="Your Input",
                value=f"Section: {section}, Rule: {rule_number}",
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Rules Management Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="rules_add", description="Add a new rule to a section")
    @app_commands.checks.has_permissions(administrator=True)
    async def rules_add(self, interaction: discord.Interaction, section: int, new_rule: str):
        """Add a new rule to a section"""
        if 0 <= section < len(self.discord_rules["sections"]):
            self.discord_rules["sections"][section]["rules"].append(new_rule)
            
            success_embed = discord.Embed(
                title="✅ Rule Added Successfully",
                description=f"A new rule has been added to section {section + 1}.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            success_embed.add_field(
                name="Section",
                value=self.discord_rules["sections"][section]["name"],
                inline=False
            )
            success_embed.add_field(
                name="New Rule",
                value=f"```{new_rule}```",
                inline=False
            )
            success_embed.add_field(
                name="Added By",
                value=interaction.user.mention,
                inline=True
            )
            success_embed.add_field(
                name="Rule Position",
                value=f"#{len(self.discord_rules['sections'][section]['rules'])}",
                inline=True
            )
            success_embed.add_field(
                name="💡 Note",
                value="Use `/rules_refresh` to update the rules display in the channel.",
                inline=False
            )
            success_embed.set_footer(
                text="Delirium Den • Rules Management",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        else:
            error_embed = discord.Embed(
                title="❌ Invalid Section",
                description="The section number you specified is invalid.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Valid Sections",
                value=f"0 - {len(self.discord_rules['sections']) - 1}",
                inline=True
            )
            error_embed.add_field(
                name="Your Input",
                value=f"Section: {section}",
                inline=True
            )
            error_embed.set_footer(
                text="Delirium Den • Rules Management Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="rules_refresh", description="Refresh the rules display")
    @app_commands.checks.has_permissions(administrator=True)
    async def rules_refresh(self, interaction: discord.Interaction):
        """Refresh the rules display"""
        if not self.rules_channel_id:
            error_embed = discord.Embed(
                title="❌ Configuration Error",
                description="Rules channel ID is not set in the bot configuration.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Solution",
                value="Please set the `RULES_CHANNEL_ID` environment variable.",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Configuration Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return
            
        channel = self.bot.get_channel(self.rules_channel_id)
        if not channel:
            error_embed = discord.Embed(
                title="❌ Channel Not Found",
                description=f"Could not find the rules channel with ID `{self.rules_channel_id}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Possible Issues",
                value="• Channel was deleted\n• Bot doesn't have access to the channel\n• Incorrect channel ID in configuration",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Channel Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        # Send initial response
        processing_embed = discord.Embed(
            title="⚙️ Refreshing Rules...",
            description="Clearing old rules and posting updated versions...",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        processing_embed.set_footer(
            text="Delirium Den • Processing",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        await interaction.response.send_message(embed=processing_embed, ephemeral=True)

        try:
            # Clear the channel
            await channel.purge(limit=100)
            
            # Re-setup the rules
            await self.setup_rules()
            
            success_embed = discord.Embed(
                title="✅ Rules Refreshed Successfully",
                description="The rules have been updated and reposted to the rules channel!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            success_embed.add_field(
                name="Channel",
                value=channel.mention,
                inline=True
            )
            success_embed.add_field(
                name="Refreshed By",
                value=interaction.user.mention,
                inline=True
            )
            success_embed.add_field(
                name="Messages Cleared",
                value="Up to 100 previous messages",
                inline=True
            )
            success_embed.set_footer(
                text="Delirium Den • Rules Management",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to manage messages in the rules channel.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Required Permissions",
                value="• Manage Messages\n• Send Messages\n• Embed Links",
                inline=False
            )
            error_embed.set_footer(
                text="Delirium Den • Permission Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An error occurred while refreshing the rules: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.set_footer(
                text="Delirium Den • System Error",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="rules_info", description="Get information about the rules system")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def rules_info(self, interaction: discord.Interaction):
        """Get information about the rules system"""
        info_embed = discord.Embed(
            title="🎭 Delirium Den Rules System",
            description="Information about the server rules management system.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        info_embed.add_field(
            name="📋 Discord Rules",
            value=f"**Sections:** {len(self.discord_rules['sections'])}\n**Total Rules:** {sum(len(section['rules']) for section in self.discord_rules['sections'])}",
            inline=True
        )
        
        info_embed.add_field(
            name="⛏️ Minecraft Rules",
            value=f"**Sections:** {len(self.minecraft_rules['sections'])}\n**Total Rules:** {sum(len(section['rules']) for section in self.minecraft_rules['sections'])}",
            inline=True
        )
        
        info_embed.add_field(
            name="📍 Rules Channel",
            value=f"<#{self.rules_channel_id}>" if self.rules_channel_id else "Not configured",
            inline=True
        )
        
        info_embed.add_field(
            name="🔧 Management Commands",
            value="• `/rules_setup` - Post rules to channel\n• `/rules_refresh` - Update rules display\n• `/rules_edit` - Edit existing rules\n• `/rules_add` - Add new rules\n• `/rules_info` - Show this information",
            inline=False
        )
        
        info_embed.add_field(
            name="⚠️ Warning System",
            value="Progressive punishment system from 1 hour timeout to permanent ban after 7 warnings.",
            inline=False
        )
        
        info_embed.set_footer(
            text="Delirium Den • Rules System Information",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=info_embed, ephemeral=True)

    @app_commands.command(name="rules_help", description="Get help with rules management commands")
    @app_commands.checks.has_permissions(administrator=True)
    async def rules_help(self, interaction: discord.Interaction):
        """Get help with rules management commands"""
        help_embed = discord.Embed(
            title="🎭 Rules Management Help",
            description="Comprehensive guide to managing Delirium Den rules.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        help_embed.add_field(
            name="📝 Setup Commands",
            value="```/rules_setup - Post rules to the configured channel\n/rules_refresh - Clear and repost all rules```",
            inline=False
        )
        
        help_embed.add_field(
            name="✏️ Editing Commands",
            value="```/rules_edit <section> <rule_number> <new_rule>\n/rules_add <section> <new_rule>```",
            inline=False
        )
        
        help_embed.add_field(
            name="📊 Information Commands",
            value="```/rules_info - View rules system statistics\n/rules_help - Show this help message```",
            inline=False
        )
        
        help_embed.add_field(
            name="🔢 Section Numbers",
            value="Section numbers start from **0**. Use `/rules_info` to see total sections available.",
            inline=False
        )
        
        help_embed.add_field(
            name="⚙️ Configuration",
            value="Set `RULES_CHANNEL_ID` in your environment variables to specify where rules should be posted.",
            inline=False
        )
        
        help_embed.add_field(
            name="💡 Tips",
            value="• Always use `/rules_refresh` after editing rules\n• Rule changes are temporary until bot restart\n• Section and rule numbers start from 0\n• Use clear, concise language for rules",
            inline=False
        )
        
        help_embed.set_footer(
            text="Delirium Den • Rules Management Help",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Rules(bot))