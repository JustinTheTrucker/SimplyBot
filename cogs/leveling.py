import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import asyncio
import time
import random
import math
import re


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "levels_data.json"
        self.voice_sessions = {}  # Track voice channel time
        self.message_cooldowns = {}  # Prevent XP spam
        self.voice_xp_task.start()
        
        # Load data on startup
        self.load_data()
        
        # XP Configuration - More balanced rates
        self.text_xp_min = 5
        self.text_xp_max = 15
        self.voice_xp_per_minute = 3
        self.message_cooldown = 60
        
        # Level rewards (role IDs to give at certain levels)
        self.level_rewards = {
            2: 1295852195585069137,   # [Levels 0-4] - middle level 2
            7: 1295852430566752390,   # [Levels 5-9] - middle level 7
            12: 1295852596732493924,  # [Levels 10-14] - middle level 12
            17: 1295852714051244123,  # [Levels 15-19] - middle level 17
            25: 1295852823241687051,  # [Levels 20-29] - middle level 25
            35: 1295852968960196681,  # [Levels 30-39] - middle level 35
            40: 1295853145095667763,  # [Levels 40+] - level 40
        }

    def load_data(self):
        """Load user data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                self.users_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.users_data = {}

    def save_data(self):
        """Save user data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.users_data, f, indent=4)

    def get_user_data(self, user_id):
        """Get or create user data"""
        user_id = str(user_id)
        if user_id not in self.users_data:
            self.users_data[user_id] = {
                "xp": 0,
                "level": 0,
                "credits": 100,  # Starting credits
                "reputation": 0,
                "voice_time": 0,  # Total voice time in minutes
                "messages_sent": 0,
                "last_daily": 0,
                "profile_bg": "default",
                "rank_bg": "default",
                "description": "No description set."
            }
        return self.users_data[user_id]

    def calculate_level(self, xp):
        """Calculate level from XP using the new formula"""
        if xp < 0:
            return 0
            
        level = 0
        xp_used = 0
        
        while True:
            # XP needed for the NEXT level (starting from level 1)
            xp_needed_for_next = int(150 * (level + 1) ** 1.5)
            
            # If we don't have enough XP for the next level, stay at current level
            if xp_used + xp_needed_for_next > xp:
                break
                
            xp_used += xp_needed_for_next
            level += 1
            
        return level

    def xp_for_level(self, target_level):
        """Calculate total XP needed to reach a specific level"""
        if target_level <= 0:
            return 0
            
        total_xp = 0
        for level in range(1, target_level + 1):
            xp_for_this_level = int(150 * level ** 1.5)
            total_xp += xp_for_this_level
            
        return total_xp

    def xp_for_next_level(self, current_level):
        """Calculate XP needed for the next level from current level"""
        return int(150 * (current_level + 1) ** 1.5)

    def xp_progress_for_current_level(self, xp, current_level):
        """Calculate how much XP progress toward the next level"""
        if current_level == 0:
            return xp
        
        # XP needed to reach current level
        xp_for_current_level = self.xp_for_level(current_level)
        
        # Progress toward next level
        return xp - xp_for_current_level

    async def level_up_check(self, user_id, channel):
        """Check if user leveled up and handle rewards"""
        user_data = self.get_user_data(user_id)
        current_level = user_data["level"]
        new_level = self.calculate_level(user_data["xp"])
        
        if new_level > current_level:
            user_data["level"] = new_level
            self.save_data()
            
            # Send level up message
            user = self.bot.get_user(int(user_id))
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{user.mention} reached level **{new_level}**!",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="XP Progress",
                value=f"`{user_data['xp']:,}` total XP",
                inline=True
            )
            
            # Check for role rewards
            if new_level in self.level_rewards and self.level_rewards[new_level]:
                try:
                    guild = channel.guild
                    member = guild.get_member(int(user_id))
                    role = guild.get_role(self.level_rewards[new_level])
                    if role and member:
                        await member.add_roles(role)
                        embed.add_field(
                            name="🎁 Reward Unlocked!",
                            value=f"You received the **{role.name}** role!",
                            inline=False
                        )
                except:
                    pass
            
            try:
                await channel.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle XP gain from messages"""
        if message.author.bot or not message.guild:
            return
        
        user_id = str(message.author.id)
        current_time = time.time()
        
        # Check message cooldown
        if user_id in self.message_cooldowns:
            if current_time - self.message_cooldowns[user_id] < self.message_cooldown:
                return
        
        # Update cooldown
        self.message_cooldowns[user_id] = current_time
        
        # Give XP
        user_data = self.get_user_data(user_id)
        xp_gain = random.randint(self.text_xp_min, self.text_xp_max)
        user_data["xp"] += xp_gain
        user_data["messages_sent"] += 1
        
        # Check for level up
        await self.level_up_check(user_id, message.channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice channel time"""
        user_id = str(member.id)
        current_time = time.time()
        
        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            self.voice_sessions[user_id] = current_time
        
        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            if user_id in self.voice_sessions:
                session_time = current_time - self.voice_sessions[user_id]
                minutes = int(session_time // 60)
                
                if minutes > 0:  # Only give XP for full minutes
                    user_data = self.get_user_data(user_id)
                    user_data["voice_time"] += minutes
                    user_data["xp"] += minutes * self.voice_xp_per_minute
                    
                    # Check for level up (use general channel if available)
                    channel = discord.utils.get(member.guild.text_channels, name="general")
                    if not channel:
                        channel = member.guild.text_channels[0]
                    await self.level_up_check(user_id, channel)
                
                del self.voice_sessions[user_id]

    @tasks.loop(minutes=1)
    async def voice_xp_task(self):
        """Give XP to users currently in voice channels"""
        current_time = time.time()
        for user_id in list(self.voice_sessions.keys()):
            # Get member from all guilds the bot is in
            member = None
            for guild in self.bot.guilds:
                member = guild.get_member(int(user_id))
                if member and member.voice and member.voice.channel:
                    # User is still in voice in this guild
                    user_data = self.get_user_data(user_id)
                    user_data["xp"] += self.voice_xp_per_minute
                    user_data["voice_time"] += 1
                    break
            
            # If we didn't find the user in any voice channel, clean up
            if not member or not member.voice or not member.voice.channel:
                if user_id in self.voice_sessions:
                    del self.voice_sessions[user_id]

    @voice_xp_task.before_loop
    async def before_voice_xp_task(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="rank", description="Show your or another user's rank and XP")
    @app_commands.describe(user="The user to check (optional)")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        """Show user's rank and XP"""
        if user is None:
            user = interaction.user
        
        user_data = self.get_user_data(user.id)
        current_level = user_data["level"]
        current_xp = user_data["xp"]
        
        # Recalculate level to make sure it's accurate
        actual_level = self.calculate_level(current_xp)
        if actual_level != current_level:
            user_data["level"] = actual_level
            current_level = actual_level
            self.save_data()
        
        # Calculate XP progress for current level
        xp_for_next = self.xp_for_next_level(current_level)
        xp_progress = self.xp_progress_for_current_level(current_xp, current_level)
        
        # Calculate server rank
        all_users = [(uid, data["xp"]) for uid, data in self.users_data.items() 
                     if int(uid) in [m.id for m in interaction.guild.members]]
        all_users.sort(key=lambda x: x[1], reverse=True)
        rank = next((i + 1 for i, (uid, _) in enumerate(all_users) if uid == str(user.id)), 0)
        
        embed = discord.Embed(
            title=f"📊 {user.display_name}'s Rank",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="Level",
            value=f"`{current_level}`",
            inline=True
        )
        
        embed.add_field(
            name="Server Rank",
            value=f"`#{rank}`",
            inline=True
        )
        
        embed.add_field(
            name="Total XP",
            value=f"`{current_xp:,}`",
            inline=True
        )
        
        embed.add_field(
            name="Level Progress",
            value=f"`{xp_progress:,}` / `{xp_for_next:,}` XP",
            inline=False
        )
        
        embed.add_field(
            name="📈 Stats",
            value=f"Messages: `{user_data['messages_sent']:,}`\n"
                  f"Voice Time: `{user_data['voice_time']:,}` minutes\n"
                  f"Credits: `{user_data['credits']:,}`\n"
                  f"Reputation: `{user_data['reputation']:,}`",
            inline=False
        )
        
        # Progress bar (make sure we don't divide by zero)
        if xp_for_next > 0:
            progress_percent = max(0, min(100, int((xp_progress / xp_for_next) * 100)))
            progress_bars = int((progress_percent / 100) * 20)
            bar = "█" * progress_bars + "░" * (20 - progress_bars)
            embed.add_field(
                name="Progress",
                value=f"`{bar}` {progress_percent}%",
                inline=False
            )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Delirium Den • {user_data['description']}", 
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the server leaderboard")
    @app_commands.describe(page="Page number to view (default: 1)")
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Show server leaderboard"""
        # Get all users in the server
        guild_members = [str(m.id) for m in interaction.guild.members if not m.bot]
        guild_users = [(uid, data) for uid, data in self.users_data.items() 
                       if uid in guild_members]
        guild_users.sort(key=lambda x: x[1]["xp"], reverse=True)
        
        # Pagination
        per_page = 10
        total_pages = math.ceil(len(guild_users) / per_page)
        page = max(1, min(page, total_pages))
        
        start = (page - 1) * per_page
        end = start + per_page
        
        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} Leaderboard",
            description=f"Page {page}/{total_pages}",
            color=discord.Color.gold()
        )
        
        leaderboard_text = ""
        for i, (user_id, user_data) in enumerate(guild_users[start:end], start + 1):
            user = self.bot.get_user(int(user_id))
            if user:
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                medal = medals.get(i, f"`#{i}`")
                leaderboard_text += f"{medal} **{user.display_name}**\n"
                leaderboard_text += f"    Level `{user_data['level']}` • `{user_data['xp']:,}` XP\n\n"
        
        embed.description = leaderboard_text or "No users found."
        embed.set_footer(
            text=f"Delirium Den • Your rank: #{next((i + 1 for i, (uid, _) in enumerate(guild_users) if uid == str(interaction.user.id)), 'N/A')}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily credits")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily credits"""
        user_data = self.get_user_data(interaction.user.id)
        current_time = time.time()
        last_daily = user_data["last_daily"]
        
        # Check if 24 hours have passed
        if current_time - last_daily < 86400:  # 24 hours in seconds
            time_left = 86400 - (current_time - last_daily)
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            embed = discord.Embed(
                title="⏰ Daily Cooldown",
                description=f"You can claim your daily credits in `{hours}h {minutes}m`",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Give daily credits
        daily_amount = random.randint(50, 100)
        user_data["credits"] += daily_amount
        user_data["last_daily"] = current_time
        self.save_data()
        
        embed = discord.Embed(
            title="💰 Daily Credits Claimed!",
            description=f"You received `{daily_amount}` credits!\n"
                       f"New balance: `{user_data['credits']:,}` credits",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reputation", description="Give reputation to another user")
    @app_commands.describe(user="The user to give reputation to")
    async def reputation(self, interaction: discord.Interaction, user: discord.Member):
        """Give reputation to another user"""
        if user.bot:
            return await interaction.response.send_message("❌ You can't give reputation to bots!", ephemeral=True)
        
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You can't give reputation to yourself!", ephemeral=True)
        
        giver_data = self.get_user_data(interaction.user.id)
        current_time = time.time()
        
        # Check cooldown (24 hours)
        if "last_rep" in giver_data:
            if current_time - giver_data["last_rep"] < 86400:
                time_left = 86400 - (current_time - giver_data["last_rep"])
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                
                return await interaction.response.send_message(f"⏰ You can give reputation again in `{hours}h {minutes}m`", ephemeral=True)
        
        # Give reputation
        receiver_data = self.get_user_data(user.id)
        receiver_data["reputation"] += 1
        giver_data["last_rep"] = current_time
        self.save_data()
        
        embed = discord.Embed(
            title="⭐ Reputation Given!",
            description=f"{interaction.user.mention} gave reputation to {user.mention}!\n"
                       f"{user.display_name} now has `{receiver_data['reputation']}` reputation.",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your or another user's profile")
    @app_commands.describe(user="The user to view (optional)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        """View user profile"""
        if user is None:
            user = interaction.user
        
        user_data = self.get_user_data(user.id)
        
        embed = discord.Embed(
            title=f"👤 {user.display_name}'s Profile",
            description=user_data["description"],
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="📊 Level",
            value=f"`{user_data['level']}`",
            inline=True
        )
        
        embed.add_field(
            name="💰 Credits",
            value=f"`{user_data['credits']:,}`",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Reputation",
            value=f"`{user_data['reputation']}`",
            inline=True
        )
        
        embed.add_field(
            name="📈 Activity",
            value=f"Messages: `{user_data['messages_sent']:,}`\n"
                  f"Voice Time: `{user_data['voice_time']:,}` minutes",
            inline=False
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Delirium Den • User ID: {user.id}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setdesc", description="Set your profile description")
    @app_commands.describe(description="Your new profile description (max 100 characters)")
    async def set_description(self, interaction: discord.Interaction, description: str):
        """Set your profile description"""
        if len(description) > 100:
            return await interaction.response.send_message("❌ Description must be 100 characters or less!", ephemeral=True)
        
        user_data = self.get_user_data(interaction.user.id)
        user_data["description"] = description
        self.save_data()
        
        await interaction.response.send_message(f"✅ Your description has been updated to: `{description}`", ephemeral=True)

    @app_commands.command(name="scanroles", description="Scan server for Japanese quote format level roles")
    @app_commands.default_permissions(administrator=True)
    async def scan_roles(self, interaction: discord.Interaction):
        """Scan server for Japanese quote format level roles"""
        await interaction.response.send_message("🔍 Scanning server roles...")
        
        level_roles = []
        other_roles = []
        all_roles_info = []
        
        # Scan all roles
        for role in interaction.guild.roles:
            if role.name == '@everyone':
                continue
                
            member_count = len(role.members)
            all_roles_info.append(f"`{role.name}` ({member_count} members)")
            
            if member_count == 0:
                continue
                
            # Check for Japanese quote format: 「Levels X-Y」
            japanese_pattern = re.search(r'「Levels? (\d+)-(\d+)」', role.name, re.IGNORECASE)
            
            if japanese_pattern:
                start_num = int(japanese_pattern.group(1))
                end_num = int(japanese_pattern.group(2))
                middle_level = (start_num + end_num) // 2
                
                level_roles.append({
                    'role': role,
                    'members': member_count,
                    'start': start_num,
                    'end': end_num,
                    'middle': middle_level
                })
            else:
                # Check for other level-related keywords
                role_lower = role.name.lower()
                has_level_keyword = any(word in role_lower for word in 
                                      ['level', 'lvl', 'rank', 'tier', 'grade'])
                
                if has_level_keyword:
                    other_roles.append({
                        'role': role,
                        'members': member_count
                    })
        
        # Sort results
        level_roles.sort(key=lambda x: x['start'])
        other_roles.sort(key=lambda x: x['members'])
        
        # Create response embed
        embed = discord.Embed(
            title="🔍 Role Scan Results",
            description=f"Scanned {len(all_roles_info)} total roles",
            color=discord.Color.blue()
        )
        
        # Show debug info
        debug_text = "\n".join(all_roles_info[:15])
        if len(all_roles_info) > 15:
            debug_text += f"\n... and {len(all_roles_info) - 15} more roles"
            
        embed.add_field(
            name="🔧 All Roles (Debug)",
            value=debug_text if debug_text else "No roles found",
            inline=False
        )
        
        # Show Japanese format roles
        if level_roles:
            role_text = []
            config_lines = []
            
            for data in level_roles:
                role = data['role']
                role_text.append(f"`{role.name}` - {data['members']} members (ID: {role.id})")
                config_lines.append(f"    {data['middle']}: {role.id},  # {role.name}")
            
            embed.add_field(
                name="✅ Japanese Format Roles Found",
                value="\n".join(role_text),
                inline=False
            )
            
            embed.add_field(
                name="💻 Configuration Code",
                value=f"```python\nself.level_rewards = {{\n" + "\n".join(config_lines) + "\n}}```",
                inline=False
            )
        else:
            embed.add_field(
                name="❌ No Japanese Format Roles",
                value="No roles matching 「Levels X-Y」 pattern found",
                inline=False
            )
        
        # Show other potential roles
        if other_roles:
            other_text = []
            for data in other_roles[:5]:
                role = data['role']
                other_text.append(f"`{role.name}` - {data['members']} members")
            
            if other_text:
                embed.add_field(
                    name="🤔 Other Level-Related Roles",
                    value="\n".join(other_text),
                    inline=False
                )
        
        embed.set_footer(
            text="Delirium Den • Role Scanner",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="importroles", description="Import existing level roles and assign appropriate XP/levels")
    @app_commands.default_permissions(administrator=True)
    async def import_roles(self, interaction: discord.Interaction):
        """Import existing level roles and assign appropriate XP/levels"""
        # Create a mapping of role IDs to level ranges
        role_to_level_range = {
            1295852195585069137: (0, 4),    # 「Levels 0-4」
            1295852430566752390: (5, 9),    # 「Levels 5-9」
            1295852596732493924: (10, 14),  # 「Levels 10-14」
            1295852714051244123: (15, 19),  # 「Levels 15-19」
            1295852823241687051: (20, 29),  # 「Levels 20-29」
            1295852968960196681: (30, 39),  # 「Levels 30-39」
            1295853145095667763: (40, 50),  # 「Levels 40+」 - assume max 50
        }
        
        # Send confirmation message
        role_list = []
        for role_id, (min_lvl, max_lvl) in role_to_level_range.items():
            role = interaction.guild.get_role(role_id)
            if role:
                role_list.append(f"Levels {min_lvl}-{max_lvl}: {role.name}")
        
        embed = discord.Embed(
            title="⚠️ Confirm Role Import",
            description="This will scan all members and assign levels based on their highest level role.\n\n"
                       f"**Configured Level Roles:**\n" + "\n".join(role_list) + "\n\n"
                       "React with ✅ to proceed.",
            color=discord.Color.orange()
        )
        
        msg = await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) != "✅":
                return await interaction.edit_original_response(embed=discord.Embed(title="❌ Import Cancelled", color=discord.Color.red()))
        except asyncio.TimeoutError:
            return await interaction.edit_original_response(embed=discord.Embed(title="⏰ Import Timed Out", color=discord.Color.red()))
        
        # Start the import process
        await interaction.edit_original_response(embed=discord.Embed(title="🔄 Importing roles...", description="This may take a moment...", color=discord.Color.blue()))
        
        imported_count = 0
        skipped_count = 0
        
        for member in interaction.guild.members:
            if member.bot:
                continue
            
            # Find the highest level role this member has
            highest_level = 0
            for role in member.roles:
                if role.id in role_to_level_range:
                    min_lvl, max_lvl = role_to_level_range[role.id]
                    # Use the maximum level of the range for import
                    if max_lvl > highest_level:
                        highest_level = max_lvl
            
            if highest_level > 0:
                # Get or create user data
                user_data = self.get_user_data(member.id)
                
                # Only import if they don't already have a higher level
                if user_data["level"] < highest_level:
                    # Calculate minimum XP needed for this level
                    min_xp_for_level = self.xp_for_level(highest_level)
                    
                    # Set their XP to the minimum needed for their level
                    user_data["xp"] = min_xp_for_level
                    user_data["level"] = highest_level
                    imported_count += 1
                else:
                    skipped_count += 1
        
        # Save all changes
        self.save_data()
        
        # Send completion message
        embed = discord.Embed(
            title="✅ Role Import Complete!",
            description=f"**Imported:** {imported_count} members\n"
                       f"**Skipped:** {skipped_count} members (already higher level)\n\n"
                       "All members with level roles have been assigned appropriate XP!",
            color=discord.Color.green()
        )
        
        await interaction.edit_original_response(embed=embed)

    # Admin commands
    @app_commands.command(name="givexp", description="Give XP to a user")
    @app_commands.describe(user="The user to give XP to", amount="Amount of XP to give")
    @app_commands.default_permissions(administrator=True)
    async def give_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Give XP to a user (Admin only)"""
        user_data = self.get_user_data(user.id)
        old_level = user_data["level"]
        user_data["xp"] += amount
        new_level = self.calculate_level(user_data["xp"])
        user_data["level"] = new_level
        self.save_data()
        
        embed = discord.Embed(
            title="✅ XP Given",
            description=f"Gave `{amount:,}` XP to {user.mention}\n"
                       f"Level: `{old_level}` → `{new_level}`",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetlevels", description="Reset levels for a user or entire server")
    @app_commands.describe(user="The user to reset (leave empty for server-wide reset)")
    @app_commands.default_permissions(administrator=True)
    async def reset_levels(self, interaction: discord.Interaction, user: discord.Member = None):
        """Reset levels for a user or entire server (Admin only)"""
        if user:
            # Reset specific user
            user_data = self.get_user_data(user.id)
            user_data["xp"] = 0
            user_data["level"] = 0
            self.save_data()
            await interaction.response.send_message(f"✅ Reset levels for {user.mention}")
        else:
            # Reset entire server (with confirmation)
            embed = discord.Embed(
                title="⚠️ Confirm Reset",
                description="This will reset ALL user levels in this server. React with ✅ to confirm.",
                color=discord.Color.red()
            )
            msg = await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            
            def check(reaction, user):
                return user == interaction.user and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                if str(reaction.emoji) == "✅":
                    # Reset all users in this server
                    guild_member_ids = [str(m.id) for m in interaction.guild.members]
                    for user_id in guild_member_ids:
                        if user_id in self.users_data:
                            self.users_data[user_id]["xp"] = 0
                            self.users_data[user_id]["level"] = 0
                    self.save_data()
                    await interaction.edit_original_response(embed=discord.Embed(title="✅ Server Levels Reset", color=discord.Color.green()))
                else:
                    await interaction.edit_original_response(embed=discord.Embed(title="❌ Reset Cancelled", color=discord.Color.red()))
            except asyncio.TimeoutError:
                await interaction.edit_original_response(embed=discord.Embed(title="⏰ Reset Timed Out", color=discord.Color.red()))

    @app_commands.command(name="xplevels", description="Show XP requirements for different levels")
    @app_commands.default_permissions(administrator=True)  
    async def xp_levels(self, interaction: discord.Interaction):
        """Show XP requirements for different levels (Admin only)"""
        embed = discord.Embed(
            title="📊 XP Level Requirements",
            description="Here are the XP requirements for each level:",
            color=discord.Color.blue()
        )
        
        # Show XP requirements for key levels
        key_levels = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        level_info = []
        
        for level in key_levels:
            total_xp = self.xp_for_level(level)
            if level > 0:
                xp_for_this_level = self.xp_for_next_level(level - 1)
                level_info.append(f"Level {level}: `{total_xp:,}` total XP (`{xp_for_this_level:,}` for this level)")
            else:
                level_info.append(f"Level {level}: `{total_xp:,}` total XP")
        
        embed.add_field(
            name="Level Progression",
            value="\n".join(level_info),
            inline=False
        )
        
        # Show your role rewards
        reward_info = []
        for level, role_id in self.level_rewards.items():
            role = interaction.guild.get_role(role_id)
            if role:
                total_xp = self.xp_for_level(level)
                reward_info.append(f"Level {level}: `{total_xp:,}` XP → {role.name}")
        
        if reward_info:
            embed.add_field(
                name="🎁 Role Rewards",
                value="\n".join(reward_info),
                inline=False
            )
        
        embed.add_field(
            name="💡 XP Rates",
            value=f"Messages: `{self.text_xp_min}-{self.text_xp_max}` XP (1min cooldown)\n"
                  f"Voice: `{self.voice_xp_per_minute}` XP per minute",
            inline=False
        )
        
        embed.set_footer(
            text="Delirium Den • XP Calculator",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Levels(bot))
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")