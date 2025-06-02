import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime, timedelta
import random

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "counting_data.json"
        self.counting_data = self.load_data()
        
        # Counting settings per guild - STRICT MODE
        self.default_settings = {
            "channel_id": None,
            "current_number": 0,
            "last_user": None,
            "highest_count": 0,
            "total_counts": 0,
            "enabled": False,
            "allow_same_user": False,  # STRICT: Never allow same user twice in a row
            "reset_on_mistake": True,  # STRICT: Always reset to 0 on wrong number
            "counting_role": None,     # Role to ping on milestones
            "save_progress": True,     # Save progress when reset
            "milestones": [100, 500, 1000, 2500, 5000, 10000],  # Celebration milestones
            "leaderboard": {},         # User count contributions
            "mistakes": 0,             # Total mistakes made
            "resets": 0,               # Total resets
            "last_reset": None,        # When last reset happened
            "streak_record": 0,        # Highest streak achieved
            "fun_mode": False,         # STRICT: No fun mode by default
            "auto_react": True,        # Auto react to correct counts
            "delete_wrong_messages": True,  # STRICT: Delete wrong numbers/non-numbers
            "strict_mode": True,       # STRICT: Enable all strict features
            "only_numbers": True,      # STRICT: Only allow pure numbers, no text
            "kick_on_spam": False,     # STRICT: Kick users who spam wrong numbers
            "spam_threshold": 3,       # How many wrong numbers before action
            "user_violations": {},     # Track user violations
            "mute_violators": True,    # STRICT: Temporarily mute repeat offenders
            "violation_timeout": 60,   # Timeout duration in seconds
        }
        
        # Fun messages for milestones
        self.milestone_messages = [
            "🎉 Amazing! You've reached {count}! Keep it up!",
            "🚀 Wow! {count} is incredible! You're all counting legends!",
            "🏆 Congratulations on reaching {count}! That's teamwork!",
            "✨ {count}! You're absolutely crushing it!",
            "🎊 What a milestone - {count}! This server can count!",
            "💯 {count} achieved! Math teachers everywhere are proud!",
            "🌟 {count}! Your counting skills are out of this world!",
            "🎈 Party time! You hit {count}! Time to celebrate!",
        ]
        
        # Fun reactions for correct counts
        self.count_reactions = [
            "✅", "👍", "🎯", "💯", "⚡", "🔥", "✨", "🌟", 
            "🎉", "👏", "💪", "🚀", "⭐", "💎", "🏆", "🎊"
        ]
        
        # Strict mode messages
        self.strict_messages = [
            "❌ **INCORRECT!** Expected {expected}, got {actual}. Count reset to 0.",
            "🚫 **WRONG NUMBER!** Should be {expected}, not {actual}. Starting over.",
            "⛔ **MISTAKE!** {actual} ≠ {expected}. Count reset. Be more careful!",
            "❌ **ERROR!** Expected {expected}. Count reset due to {actual}.",
            "🔴 **FAILED!** Wrong number {actual}. Expected {expected}. Reset to 0.",
        ]
        
        # Violation messages
        self.violation_messages = [
            "⚠️ **WARNING:** Multiple violations detected. Follow the rules!",
            "🚨 **VIOLATION:** Stop disrupting the count! Next violation = timeout.",
            "❌ **REPEATED OFFENSE:** You've been temporarily muted for violations.",
        ]

    def load_data(self):
        """Load counting data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def save_data(self):
        """Save counting data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.counting_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving counting data: {e}")

    def get_guild_data(self, guild_id):
        """Get or create guild counting data with migration"""
        guild_id_str = str(guild_id)
        
        if guild_id_str not in self.counting_data:
            self.counting_data[guild_id_str] = self.default_settings.copy()
            self.save_data()
        else:
            # Migrate old data to include new settings
            guild_data = self.counting_data[guild_id_str]
            updated = False
            
            # Add missing keys from default settings
            for key, default_value in self.default_settings.items():
                if key not in guild_data:
                    guild_data[key] = default_value
                    updated = True
            
            # Save if we added new keys
            if updated:
                self.save_data()
        
        return self.counting_data[guild_id_str]

    def update_leaderboard(self, guild_id, user_id):
        """Update user's count in leaderboard"""
        guild_data = self.get_guild_data(guild_id)
        user_id_str = str(user_id)
        
        if user_id_str not in guild_data["leaderboard"]:
            guild_data["leaderboard"][user_id_str] = 0
        
        guild_data["leaderboard"][user_id_str] += 1
        self.save_data()

    async def send_milestone_message(self, channel, count):
        """Send a celebration message for milestones"""
        message = random.choice(self.milestone_messages).format(count=count)
        
        embed = discord.Embed(
            title="🎊 Milestone Reached!",
            description=message,
            color=discord.Color.gold()
        )
        embed.add_field(name="Count", value=f"**{count}**", inline=True)
        embed.add_field(name="Keep Going!", value="Next milestone awaits! 🚀", inline=True)
        embed.set_footer(text=f"Milestone reached at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await channel.send(embed=embed)

    def update_violations(self, guild_id, user_id):
        """Track user violations for strict mode"""
        guild_data = self.get_guild_data(guild_id)
        user_id_str = str(user_id)
        
        if "user_violations" not in guild_data:
            guild_data["user_violations"] = {}
        
        if user_id_str not in guild_data["user_violations"]:
            guild_data["user_violations"][user_id_str] = {
                "count": 0,
                "last_violation": None
            }
        
        guild_data["user_violations"][user_id_str]["count"] += 1
        guild_data["user_violations"][user_id_str]["last_violation"] = datetime.now().isoformat()
        
        self.save_data()
        return guild_data["user_violations"][user_id_str]["count"]

    async def handle_violation(self, message, violation_count):
        """Handle user violations in strict mode"""
        guild_data = self.get_guild_data(message.guild.id)
        
        if violation_count >= guild_data["spam_threshold"]:
            # Mute the user
            if guild_data["mute_violators"]:
                try:
                    timeout_until = datetime.now() + timedelta(seconds=guild_data["violation_timeout"])
                    await message.author.timeout(timeout_until, reason="Counting violations")
                    
                    embed = discord.Embed(
                        title="🚨 USER MUTED",
                        description=f"{message.author.mention} has been muted for {guild_data['violation_timeout']} seconds due to repeated counting violations.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Violations", value=str(violation_count), inline=True)
                    embed.add_field(name="Duration", value=f"{guild_data['violation_timeout']} seconds", inline=True)
                    
                    await message.channel.send(embed=embed)
                    
                except discord.errors.Forbidden:
                    await message.channel.send(f"⚠️ {message.author.mention} has {violation_count} violations but I lack permission to timeout users.")
            
            # Reset violation count after punishment
            guild_data["user_violations"][str(message.author.id)]["count"] = 0
            self.save_data()
        
        elif violation_count == 2:
            # No warning message - silent enforcement
            pass

    async def reset_count(self, guild_id, channel, reason="mistake", user=None, expected=None, actual=None):
        """Reset the counting with strict messaging"""
        guild_data = self.get_guild_data(guild_id)
        
        # Save progress if enabled
        if guild_data["save_progress"] and guild_data["current_number"] > 0:
            if guild_data["current_number"] > guild_data["streak_record"]:
                guild_data["streak_record"] = guild_data["current_number"]
        
        old_count = guild_data["current_number"]
        guild_data["current_number"] = 0
        guild_data["last_user"] = None
        guild_data["mistakes"] += 1
        guild_data["resets"] += 1
        guild_data["last_reset"] = datetime.now().isoformat()
        
        self.save_data()
        
        if reason == "mistake" and guild_data["strict_mode"]:
            message = random.choice(self.strict_messages).format(
                expected=expected or "?", 
                actual=actual or "?"
            )
            
            embed = discord.Embed(
                title="🔴 COUNT RESET - STRICT MODE",
                description=message,
                color=discord.Color.red()
            )
            embed.add_field(name="Previous Count", value=str(old_count), inline=True)
            embed.add_field(name="Next Number", value="**1**", inline=True)
            
            if user:
                embed.add_field(name="Violator", value=user.mention, inline=True)
            
            embed.set_footer(text="STRICT MODE: Follow the rules precisely!")
            
            await channel.send(embed=embed)
        else:
            await channel.send(f"🔄 Count has been reset! Next number is **1**.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """STRICT counting message listener"""
        if message.author.bot:
            return
        
        guild_data = self.get_guild_data(message.guild.id)
        
        # Check if counting is enabled and in the right channel
        if (not guild_data["enabled"] or 
            guild_data["channel_id"] != message.channel.id):
            return
        
        expected_number = guild_data["current_number"] + 1
        
        # STRICT MODE: Only allow pure numbers
        if guild_data["only_numbers"]:
            content = message.content.strip()
            
            # Check if message contains ONLY a number
            try:
                number = int(content)
                if str(number) != content:  # Handles cases like "1.0" or "+1"
                    raise ValueError("Not a pure integer")
            except ValueError:
                # Not a pure number - delete and warn in strict mode
                if guild_data["delete_wrong_messages"]:
                    try:
                        await message.delete()
                    except discord.errors.Forbidden:
                        pass
                
                violation_count = self.update_violations(message.guild.id, message.author.id)
                
                embed = discord.Embed(
                    title="❌ INVALID MESSAGE",
                    description=f"{message.author.mention} Only pure numbers are allowed! Expected: **{expected_number}**",
                    color=discord.Color.red()
                )
                embed.add_field(name="Your Message", value=f"`{message.content[:50]}{'...' if len(message.content) > 50 else ''}`", inline=False)
                embed.add_field(name="Violations", value=str(violation_count), inline=True)
                embed.set_footer(text="STRICT MODE: Numbers only!")
                
                warning_msg = await message.channel.send(embed=embed, delete_after=10)
                
                await self.handle_violation(message, violation_count)
                return
        else:
            # Normal mode - try to extract number
            try:
                number = int(message.content.strip())
            except ValueError:
                # Not a number, ignore in normal mode
                return
        
        # Check if it's the correct number
        if number != expected_number:
            # Delete wrong message in strict mode
            if guild_data["delete_wrong_messages"]:
                try:
                    await message.delete()
                except discord.errors.Forbidden:
                    pass
            
            # Track violation
            violation_count = self.update_violations(message.guild.id, message.author.id)
            
            # Reset count
            await self.reset_count(
                message.guild.id, 
                message.channel, 
                "mistake", 
                message.author,
                expected_number,
                number
            )
            
            # Handle violations
            await self.handle_violation(message, violation_count)
            return
        
        # STRICT: Check same user rule (never allow in strict mode)
        if guild_data["last_user"] == message.author.id:
            # Delete message
            if guild_data["delete_wrong_messages"]:
                try:
                    await message.delete()
                except discord.errors.Forbidden:
                    pass
            
            violation_count = self.update_violations(message.guild.id, message.author.id)
            
            embed = discord.Embed(
                title="🚫 SAME USER VIOLATION",
                description=f"{message.author.mention} You cannot count twice in a row!",
                color=discord.Color.red()
            )
            embed.add_field(name="Rule", value="Someone else must count next", inline=True)
            embed.add_field(name="Violations", value=str(violation_count), inline=True)
            embed.set_footer(text="STRICT MODE: Wait for another user!")
            
            await message.channel.send(embed=embed, delete_after=8)
            await self.handle_violation(message, violation_count)
            return
        
        # Valid count! Update data
        guild_data["current_number"] = number
        guild_data["last_user"] = message.author.id
        guild_data["total_counts"] += 1
        
        # Update highest count
        if number > guild_data["highest_count"]:
            guild_data["highest_count"] = number
        
        # Update leaderboard
        self.update_leaderboard(message.guild.id, message.author.id)
        
        # Auto react if enabled
        if guild_data["auto_react"]:
            try:
                await message.add_reaction("✅")
            except discord.errors.Forbidden:
                pass
        
        # Check for milestones
        if number in guild_data["milestones"]:
            await self.send_milestone_message(message.channel, number)
        
        # Special milestone reactions
        if number % 100 == 0 and number > 0:  # Every 100
            try:
                await message.add_reaction("💯")
            except discord.errors.Forbidden:
                pass
        
        self.save_data()

    @commands.group(name="count", invoke_without_command=True)
    async def count_group(self, ctx):
        """Main counting command group"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        embed = discord.Embed(
            title="🔢 Counting Game Status",
            color=discord.Color.blue()
        )
        
        # Status
        status = "🟢 Enabled" if guild_data["enabled"] else "🔴 Disabled"
        embed.add_field(name="Status", value=status, inline=True)
        
        # Channel
        if guild_data["channel_id"]:
            channel = ctx.guild.get_channel(guild_data["channel_id"])
            channel_name = channel.mention if channel else "Deleted Channel"
        else:
            channel_name = "Not Set"
        embed.add_field(name="Channel", value=channel_name, inline=True)
        
        # Current stats
        embed.add_field(name="Current Number", value=str(guild_data["current_number"]), inline=True)
        embed.add_field(name="Highest Count", value=str(guild_data["highest_count"]), inline=True)
        embed.add_field(name="Total Counts", value=str(guild_data["total_counts"]), inline=True)
        embed.add_field(name="Violations", value=str(guild_data["mistakes"]), inline=True)
        
        # Next number
        next_num = guild_data["current_number"] + 1
        embed.add_field(name="Next Number", value=f"**{next_num}**", inline=True)
        
        # Settings preview
        settings = []
        if guild_data["strict_mode"]:
            settings.append("🔴 STRICT MODE")
        if guild_data["auto_react"]:
            settings.append("Auto reactions")
        if guild_data["delete_wrong_messages"]:
            settings.append("Delete violations")
        if guild_data["mute_violators"]:
            settings.append("Mute violators")
        
        if settings:
            embed.add_field(name="Settings", value=" • ".join(settings), inline=False)
        
        embed.set_footer(text="Use !count help for all commands")
        
        await ctx.send(embed=embed)

    @count_group.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def setup_counting(self, ctx, channel: discord.TextChannel = None):
        """Set up counting in a channel"""
        if not channel:
            channel = ctx.channel
        
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["channel_id"] = channel.id
        guild_data["enabled"] = True
        
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Counting Setup Complete!",
            description=f"Counting game is now active in {channel.mention}!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Next Number", value="**1**", inline=True)
        embed.add_field(name="How to Play", value="Simply type the next number! NO text, just the number!", inline=False)
        embed.add_field(name="STRICT RULES", value="• ONLY pure numbers allowed\n• NO same user twice in a row\n• Wrong number = instant reset\n• Violations are tracked and punished", inline=False)
        
        await ctx.send(embed=embed)
        
        # Send initial message to counting channel
        if channel != ctx.channel:
            start_embed = discord.Embed(
                title="🔢 STRICT COUNTING MODE ACTIVATED!",
                description="⚠️ **STRICT RULES IN EFFECT** ⚠️\n\nType **1** to begin! NUMBERS ONLY!",
                color=discord.Color.red()
            )
            start_embed.add_field(
                name="🚨 WARNING",
                value="• Only pure numbers allowed\n• No text, emojis, or symbols\n• Wrong numbers = instant reset\n• Violations = timeout punishment",
                inline=False
            )
            await channel.send(embed=start_embed)

    @count_group.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def disable_counting(self, ctx):
        """Disable the counting game"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["enabled"] = False
        self.save_data()
        
        await ctx.send("🔴 Counting game has been disabled.")

    @count_group.command(name="enable")
    @commands.has_permissions(manage_guild=True)
    async def enable_counting(self, ctx):
        """Enable the counting game"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if not guild_data["channel_id"]:
            return await ctx.send("❌ Please set up a counting channel first with `!count setup`")
        
        guild_data["enabled"] = True
        self.save_data()
        
        await ctx.send("🟢 Counting game has been enabled!")

    @count_group.command(name="reset")
    @commands.has_permissions(manage_guild=True)
    async def reset_counting(self, ctx):
        """Reset the current count to 0"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if guild_data["current_number"] == 0:
            return await ctx.send("Count is already at 0!")
        
        old_count = guild_data["current_number"]
        await self.reset_count(ctx.guild.id, ctx.channel, "admin", ctx.author)
        
        embed = discord.Embed(
            title="🔄 Count Reset by Admin",
            description=f"Count has been reset from {old_count} to 0.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Next Number", value="**1**", inline=True)
        embed.add_field(name="Reset by", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @count_group.command(name="stats")
    async def counting_stats(self, ctx, user: discord.Member = None):
        """Show counting statistics"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if user:
            # Individual user stats
            user_counts = guild_data["leaderboard"].get(str(user.id), 0)
            
            embed = discord.Embed(
                title=f"📊 Counting Stats for {user.display_name}",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="Numbers Counted", value=str(user_counts), inline=True)
            
            if guild_data["total_counts"] > 0:
                percentage = (user_counts / guild_data["total_counts"]) * 100
                embed.add_field(name="Contribution", value=f"{percentage:.1f}%", inline=True)
        
        else:
            # Server stats
            embed = discord.Embed(
                title="📊 Server Counting Statistics",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Current Count", value=str(guild_data["current_number"]), inline=True)
            embed.add_field(name="Highest Count Ever", value=str(guild_data["highest_count"]), inline=True)
            embed.add_field(name="Total Numbers Counted", value=str(guild_data["total_counts"]), inline=True)
            embed.add_field(name="Violations Made", value=str(guild_data["mistakes"]), inline=True)
            embed.add_field(name="Times Reset", value=str(guild_data["resets"]), inline=True)
            embed.add_field(name="Best Streak", value=str(guild_data["streak_record"]), inline=True)
            
            if guild_data["last_reset"]:
                try:
                    last_reset = datetime.fromisoformat(guild_data["last_reset"])
                    embed.add_field(name="Last Reset", value=f"<t:{int(last_reset.timestamp())}:R>", inline=True)
                except:
                    embed.add_field(name="Last Reset", value="Unknown", inline=True)
        
        await ctx.send(embed=embed)

    @count_group.command(name="leaderboard", aliases=["lb", "top"])
    async def counting_leaderboard(self, ctx):
        """Show counting leaderboard"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if not guild_data["leaderboard"]:
            return await ctx.send("No counting data yet! Start counting to see the leaderboard!")
        
        # Sort users by count
        sorted_users = sorted(guild_data["leaderboard"].items(), key=lambda x: x[1], reverse=True)[:10]
        
        embed = discord.Embed(
            title="🏆 Counting Leaderboard",
            description="Top counters in this server!",
            color=discord.Color.gold()
        )
        
        leaderboard_text = []
        for i, (user_id, count) in enumerate(sorted_users, 1):
            user = ctx.guild.get_member(int(user_id))
            if user:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text.append(f"{medal} {user.display_name} - **{count}** counts")
            else:
                leaderboard_text.append(f"{i}. Unknown User - **{count}** counts")
        
        embed.description = "\n".join(leaderboard_text)
        embed.set_footer(text=f"Total counts: {guild_data['total_counts']}")
        
        await ctx.send(embed=embed)

    @count_group.command(name="violations")
    async def show_violations(self, ctx, user: discord.Member = None):
        """Show violation statistics"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if user:
            # Individual user violations
            user_violations = guild_data.get("user_violations", {}).get(str(user.id), {"count": 0})
            
            embed = discord.Embed(
                title=f"⚠️ Violations for {user.display_name}",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="Total Violations", value=str(user_violations["count"]), inline=True)
            
            if user_violations.get("last_violation"):
                try:
                    last_violation = datetime.fromisoformat(user_violations["last_violation"])
                    embed.add_field(name="Last Violation", value=f"<t:{int(last_violation.timestamp())}:R>", inline=True)
                except:
                    pass
        else:
            # Server violation stats
            embed = discord.Embed(
                title="⚠️ Server Violation Statistics",
                color=discord.Color.orange()
            )
            
            total_violations = sum(data["count"] for data in guild_data.get("user_violations", {}).values())
            embed.add_field(name="Total Violations", value=str(total_violations), inline=True)
            embed.add_field(name="Total Resets", value=str(guild_data["resets"]), inline=True)
            
            # Top violators
            if guild_data.get("user_violations"):
                sorted_violators = sorted(
                    guild_data["user_violations"].items(), 
                    key=lambda x: x[1]["count"], 
                    reverse=True
                )[:5]
                
                violator_text = []
                for user_id, data in sorted_violators:
                    if data["count"] > 0:
                        user = ctx.guild.get_member(int(user_id))
                        name = user.display_name if user else "Unknown User"
                        violator_text.append(f"{name}: {data['count']} violations")
                
                if violator_text:
                    embed.add_field(name="Top Violators", value="\n".join(violator_text), inline=False)
        
        await ctx.send(embed=embed)

    @count_group.command(name="settings")
    @commands.has_permissions(manage_guild=True)
    async def counting_settings(self, ctx):
        """Show and manage counting settings"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        embed = discord.Embed(
            title="⚙️ STRICT COUNTING SETTINGS",
            description="🚨 **STRICT MODE ENABLED** - Enhanced rule enforcement",
            color=discord.Color.red()
        )
        
        # Current settings
        embed.add_field(name="Strict Mode", value="🔴 **ENABLED**", inline=True)
        embed.add_field(name="Only Pure Numbers", value="✅" if guild_data["only_numbers"] else "❌", inline=True)
        embed.add_field(name="Delete Wrong Messages", value="✅" if guild_data["delete_wrong_messages"] else "❌", inline=True)
        embed.add_field(name="Mute Violators", value="✅" if guild_data["mute_violators"] else "❌", inline=True)
        embed.add_field(name="Auto React", value="✅" if guild_data["auto_react"] else "❌", inline=True)
        embed.add_field(name="Violation Threshold", value=f"{guild_data['spam_threshold']} strikes", inline=True)
        embed.add_field(name="Mute Duration", value=f"{guild_data['violation_timeout']} seconds", inline=True)
        
        embed.add_field(
            name="📋 Strict Settings Commands",
            value="`!count setting delete_wrong_messages true/false`\n"
                  "`!count setting mute_violators true/false`\n"
                  "`!count setting violation_timeout <seconds>`\n"
                  "`!count setting spam_threshold <number>`",
            inline=False
        )
        
        embed.set_footer(text="⚠️ STRICT MODE: Zero tolerance for rule violations!")
        
        await ctx.send(embed=embed)

    @count_group.command(name="setting")
    @commands.has_permissions(manage_guild=True)
    async def change_setting(self, ctx, setting: str, value: str = None):
        """Change a counting setting"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        # Handle numeric settings
        if setting in ["violation_timeout", "spam_threshold"]:
            if not value or not value.isdigit():
                return await ctx.send(f"❌ {setting} requires a number value!")
            
            num_value = int(value)
            
            if setting == "violation_timeout":
                if num_value < 10 or num_value > 3600:  # 10 seconds to 1 hour
                    return await ctx.send("❌ Violation timeout must be between 10 and 3600 seconds!")
                guild_data[setting] = num_value
            elif setting == "spam_threshold":
                if num_value < 1 or num_value > 10:
                    return await ctx.send("❌ Spam threshold must be between 1 and 10!")
                guild_data[setting] = num_value
            
            self.save_data()
            
            embed = discord.Embed(
                title="✅ Setting Updated",
                description=f"**{setting.replace('_', ' ').title()}** set to **{num_value}**",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)
        
        # Handle boolean settings
        if not value:
            return await ctx.send("❌ Please provide a value (true/false)")
        
        # Convert value to boolean
        if value.lower() in ['true', 'yes', 'on', '1']:
            bool_value = True
        elif value.lower() in ['false', 'no', 'off', '0']:
            bool_value = False
        else:
            return await ctx.send("❌ Value must be `true` or `false`")
        
        # Check valid settings - STRICT MODE SETTINGS
        valid_settings = [
            "delete_wrong_messages", "mute_violators", "auto_react", 
            "save_progress", "only_numbers"
        ]
        
        # Some settings are locked in strict mode
        locked_settings = ["allow_same_user", "reset_on_mistake", "strict_mode"]
        
        if setting in locked_settings:
            return await ctx.send(f"🔒 **{setting}** is locked in STRICT MODE and cannot be changed!")
        
        if setting not in valid_settings:
            return await ctx.send(f"❌ Invalid setting! Available: {', '.join(valid_settings)}")
        
        guild_data[setting] = bool_value
        self.save_data()
        
        status = "enabled" if bool_value else "disabled"
        embed = discord.Embed(
            title="✅ Setting Updated",
            description=f"**{setting.replace('_', ' ').title()}** has been {status}!",
            color=discord.Color.green()
        )
        
        if setting == "delete_wrong_messages" and bool_value:
            embed.add_field(name="⚠️ Warning", value="Wrong messages will now be automatically deleted!", inline=False)
        elif setting == "mute_violators" and bool_value:
            embed.add_field(name="⚠️ Warning", value="Users with violations will now be temporarily muted!", inline=False)
        
        await ctx.send(embed=embed)

    @count_group.command(name="clearviolations")
    @commands.has_permissions(manage_guild=True)
    async def clear_violations(self, ctx, user: discord.Member = None):
        """Clear violation records"""
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if user:
            # Clear specific user's violations
            if "user_violations" in guild_data and str(user.id) in guild_data["user_violations"]:
                old_count = guild_data["user_violations"][str(user.id)]["count"]
                guild_data["user_violations"][str(user.id)] = {"count": 0, "last_violation": None}
                self.save_data()
                
                embed = discord.Embed(
                    title="✅ Violations Cleared",
                    description=f"Cleared {old_count} violations for {user.mention}",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="ℹ️ No Violations",
                    description=f"{user.mention} has no violations to clear",
                    color=discord.Color.blue()
                )
        else:
            # Clear all violations
            if "user_violations" in guild_data:
                total_cleared = sum(data["count"] for data in guild_data["user_violations"].values())
                guild_data["user_violations"] = {}
                self.save_data()
                
                embed = discord.Embed(
                    title="✅ All Violations Cleared",
                    description=f"Cleared {total_cleared} total violations for all users",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="ℹ️ No Violations",
                    description="No violations to clear",
                    color=discord.Color.blue()
                )
        
        await ctx.send(embed=embed)

    @count_group.command(name="help")
    async def counting_help(self, ctx):
        """Show counting help"""
        embed = discord.Embed(
            title="🔢 STRICT COUNTING GAME HELP",
            description="⚠️ **ZERO TOLERANCE COUNTING MODE** ⚠️",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🚨 STRICT RULES",
            value="• ONLY pure numbers allowed (1, 2, 3...)\n"
                  "• NO text, emojis, symbols, or extra characters\n"
                  "• One person CANNOT count twice in a row\n"
                  "• Wrong numbers = instant reset + violation\n"
                  "• 3 violations = automatic timeout\n"
                  "• Invalid messages are deleted immediately",
            inline=False
        )
        
        embed.add_field(
            name="👑 Admin Commands",
            value="`!count setup [channel]` - Setup strict counting\n"
                  "`!count reset` - Reset count to 0\n"
                  "`!count enable/disable` - Toggle counting\n"
                  "`!count settings` - View/change settings\n"
                  "`!count clearviolations [user]` - Clear violations",
            inline=True
        )
        
        embed.add_field(
            name="📊 Info Commands",
            value="`!count` - Show current status\n"
                  "`!count stats [user]` - Show statistics\n"
                  "`!count violations [user]` - Show violations\n"
                  "`!count leaderboard` - Top counters\n"
                  "`!count help` - This help message",
            inline=True
        )
        
        embed.add_field(
            name="⚠️ VIOLATIONS",
            value="• Wrong number posted\n"
                  "• Counting twice in a row\n"
                  "• Non-number messages\n"
                  "• Text mixed with numbers",
            inline=True
        )
        
        embed.add_field(
            name="🚨 PUNISHMENTS",
            value="• 1st-2nd violation: Warning\n"
                  "• 3rd violation: Timeout\n"
                  "• Messages auto-deleted\n"
                  "• Count always resets",
            inline=True
        )
        
        embed.set_footer(text="🔴 STRICT MODE: Follow the rules precisely or face consequences!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Load the Counting cog"""
    await bot.add_cog(Counting(bot))
    print("✅ Counting cog loaded successfully")