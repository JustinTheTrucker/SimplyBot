import discord
from discord.ext import commands
import json
from datetime import datetime
import os

class RoleUserExtractor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Your specified role IDs with hierarchy weights (lower number = higher rank)
        self.target_roles = [
            1374789771964059792,
            1294400888252796969,
            1295064164766584833,
            1294400444998877196,
            1295064503641182280,
            1294400316439134268,
            1294400210096885831,
            1295064684508221571,
            1295064730461016074,
            1294671778769141760
        ]
        
        # Role hierarchy weights (you can adjust these based on actual rank order)
        # Lower number = higher position in hierarchy
        self.role_hierarchy = {
            1374789771964059792: 1,  # Likely highest rank
            1294400888252796969: 2,
            1295064164766584833: 3,
            1294400444998877196: 4,
            1295064503641182280: 5,
            1294400316439134268: 6,
            1294400210096885831: 7,
            1295064684508221571: 8,
            1295064730461016074: 9,
            1294671778769141760: 10  # Likely lowest rank
        }

    @commands.command(name='extract_users')
    @commands.has_permissions(administrator=True)
    async def extract_users_from_roles(self, ctx, output_format: str = 'txt'):
        """
        Extract users from specified roles and save to file.
        Usage: !extract_users [txt|json|csv]
        """
        try:
            # Dictionary to store role data
            role_data = {}
            total_users = set()
            
            # Get guild
            guild = ctx.guild
            
            # Process each role
            for role_id in self.target_roles:
                role = guild.get_role(role_id)
                if role:
                    # Get members with this role
                    members = role.members
                    role_data[role.name] = {
                        'role_id': role_id,
                        'member_count': len(members),
                        'members': []
                    }
                    
                    # Add member data
                    for member in members:
                        member_info = {
                            'id': member.id,
                            'username': member.name,
                            'display_name': member.display_name,
                            'discriminator': member.discriminator,
                            'joined_at': member.joined_at.isoformat() if member.joined_at else None,
                            'created_at': member.created_at.isoformat()
                        }
                        role_data[role.name]['members'].append(member_info)
                        total_users.add(member.id)
                else:
                    role_data[f'Unknown Role ({role_id})'] = {
                        'role_id': role_id,
                        'member_count': 0,
                        'members': [],
                        'error': 'Role not found'
                    }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if output_format.lower() == 'json':
                filename = f'role_users_{timestamp}.json'
                await self._save_as_json(role_data, filename, total_users)
            elif output_format.lower() == 'csv':
                filename = f'role_users_{timestamp}.csv'
                await self._save_as_csv(role_data, filename)
            else:  # Default to txt
                filename = f'role_users_{timestamp}.txt'
                await self._save_as_txt(role_data, filename, total_users)
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Extraction Complete",
                description=f"Successfully extracted users from {len(self.target_roles)} roles.",
                color=discord.Color.green()
            )
            embed.add_field(name="Total Unique Users", value=len(total_users), inline=True)
            embed.add_field(name="Output File", value=filename, inline=True)
            embed.add_field(name="Format", value=output_format.upper(), inline=True)
            
            await ctx.send(embed=embed)
            
            # Send file if it exists and is small enough
            if os.path.exists(filename) and os.path.getsize(filename) < 8 * 1024 * 1024:  # 8MB limit
                with open(filename, 'rb') as f:
                    await ctx.send(file=discord.File(f, filename))
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    async def _save_as_txt(self, role_data, filename, total_users):
        """Save data as formatted text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== ROLE USERS EXTRACTION REPORT ===\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Unique Users: {len(total_users)}\n")
            f.write("=" * 50 + "\n\n")
            
            for role_name, data in role_data.items():
                f.write(f"ROLE: {role_name}\n")
                f.write(f"Role ID: {data['role_id']}\n")
                f.write(f"Member Count: {data['member_count']}\n")
                
                if 'error' in data:
                    f.write(f"Error: {data['error']}\n")
                else:
                    f.write("Members:\n")
                    for member in data['members']:
                        f.write(f"  - {member['display_name']} ({member['username']}#{member['discriminator']})\n")
                        f.write(f"    ID: {member['id']}\n")
                        f.write(f"    Joined: {member['joined_at']}\n")
                
                f.write("\n" + "-" * 30 + "\n\n")

    async def _save_as_json(self, role_data, filename, total_users):
        """Save data as JSON file"""
        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_unique_users': len(total_users),
                'total_roles_processed': len(self.target_roles)
            },
            'roles': role_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    async def _save_as_csv(self, role_data, filename):
        """Save data as CSV file"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['Role Name', 'Role ID', 'User ID', 'Username', 'Display Name', 'Discriminator', 'Joined At', 'Created At'])
            
            # Data rows
            for role_name, data in role_data.items():
                if 'error' not in data:
                    for member in data['members']:
                        writer.writerow([
                            role_name,
                            data['role_id'],
                            member['id'],
                            member['username'],
                            member['display_name'],
                            member['discriminator'],
                            member['joined_at'],
                            member['created_at']
                        ])

    @commands.command(name='stafflist')
    async def staff_list(self, ctx, detailed: bool = False):
        """
        Display staff members organized by role hierarchy without cross-posting.
        Usage: !stafflist [True for detailed view]
        """
        try:
            guild = ctx.guild
            staff_data = {}
            already_listed = set()  # Track users who have already been listed
            
            # Collect data for each role
            for role_id in self.target_roles:
                role = guild.get_role(role_id)
                if role and role.members:
                    staff_data[role_id] = {
                        'role': role,
                        'members': role.members,
                        'hierarchy_weight': self.role_hierarchy.get(role_id, 999)
                    }
            
            # Sort roles by hierarchy weight (highest rank first)
            sorted_roles = sorted(staff_data.items(), key=lambda x: x[1]['hierarchy_weight'])
            
            if not sorted_roles:
                embed = discord.Embed(
                    title="📋 Staff List",
                    description="No staff members found in the specified roles.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
            
            # Create main embed
            embed = discord.Embed(
                title="👥 Server Staff Hierarchy",
                description="Current staff members organized by rank (highest role only)",
                color=discord.Color.blue()
            )
            
            total_staff = 0
            
            # Add fields for each role in hierarchy order
            for role_id, data in sorted_roles:
                role = data['role']
                all_members = data['members']
                
                # Filter out users who have already been listed in higher roles
                unique_members = [member for member in all_members if member.id not in already_listed]
                
                if not unique_members:
                    continue
                
                # Add these users to the already_listed set
                for member in unique_members:
                    already_listed.add(member.id)
                
                total_staff += len(unique_members)
                
                # Create member list
                if detailed:
                    # Detailed view with user info
                    member_list = []
                    for member in unique_members[:10]:  # Limit to prevent embed size issues
                        status_emoji = self._get_status_emoji(member.status)
                        member_list.append(f"{status_emoji} {member.display_name}")
                    
                    if len(unique_members) > 10:
                        member_list.append(f"... and {len(unique_members) - 10} more")
                    
                    member_text = "\n".join(member_list) if member_list else "No unique members"
                else:
                    # Simple view with just names
                    member_names = [member.display_name for member in unique_members[:15]]
                    if len(unique_members) > 15:
                        member_names.append(f"... +{len(unique_members) - 15} more")
                    member_text = ", ".join(member_names) if member_names else "No unique members"
                
                embed.add_field(
                    name=f"{role.name} ({len(unique_members)})",
                    value=member_text,
                    inline=False
                )
            
            # Add footer with total count
            embed.set_footer(text=f"Total Unique Staff Members: {total_staff}")
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while generating staff list: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    @commands.command(name='stafflist_compact')
    async def staff_list_compact(self, ctx):
        """
        Display a compact staff list with just role names and unique counts.
        """
        try:
            guild = ctx.guild
            staff_data = {}
            already_counted = set()  # Track users who have already been counted
            
            # Collect data for each role
            for role_id in self.target_roles:
                role = guild.get_role(role_id)
                if role:
                    staff_data[role_id] = {
                        'role': role,
                        'all_members': role.members,
                        'hierarchy_weight': self.role_hierarchy.get(role_id, 999)
                    }
            
            # Sort roles by hierarchy weight
            sorted_roles = sorted(staff_data.items(), key=lambda x: x[1]['hierarchy_weight'])
            
            # Create compact embed
            embed = discord.Embed(
                title="📊 Staff Overview",
                description="Staff counts by role (unique members only)",
                color=discord.Color.green()
            )
            
            total_staff = 0
            role_info = []
            
            for role_id, data in sorted_roles:
                role = data['role']
                all_members = data['all_members']
                
                # Count only unique members (not already counted in higher roles)
                unique_members = [member for member in all_members if member.id not in already_counted]
                unique_count = len(unique_members)
                
                # Add these users to the already_counted set
                for member in unique_members:
                    already_counted.add(member.id)
                
                total_staff += unique_count
                
                # Add role info (show both total and unique counts)
                total_count = len(all_members)
                if unique_count != total_count:
                    role_info.append(f"**{role.name}**: {unique_count} unique ({total_count} total)")
                else:
                    role_info.append(f"**{role.name}**: {unique_count} members")
            
            embed.description = "\n".join(role_info) if role_info else "No staff roles found."
            embed.set_footer(text=f"Total Unique Staff: {total_staff} members")
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    @commands.command(name='list_target_roles')
    @commands.has_permissions(administrator=True)
    async def list_target_roles(self, ctx):
        """List all target roles and their current member counts"""
        guild = ctx.guild
        embed = discord.Embed(
            title="🎭 Target Roles Status",
            description="Current status of all target roles:",
            color=discord.Color.blue()
        )
        
        for role_id in self.target_roles:
            role = guild.get_role(role_id)
            if role:
                embed.add_field(
                    name=f"{role.name}",
                    value=f"ID: {role_id}\nMembers: {len(role.members)}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="❌ Role Not Found",
                    value=f"ID: {role_id}",
                    inline=True
                )
        
        await ctx.send(embed=embed)

    @commands.command(name='update_hierarchy')
    @commands.has_permissions(administrator=True)
    async def update_hierarchy(self, ctx, role_id: int, weight: int):
        """
        Update the hierarchy weight of a role.
        Usage: !update_hierarchy <role_id> <weight>
        Lower weight = higher in hierarchy
        """
        if role_id in self.target_roles:
            self.role_hierarchy[role_id] = weight
            role = ctx.guild.get_role(role_id)
            role_name = role.name if role else f"Role {role_id}"
            
            embed = discord.Embed(
                title="✅ Hierarchy Updated",
                description=f"Updated {role_name} hierarchy weight to {weight}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Role ID not found in target roles list.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    def _get_status_emoji(self, status):
        """Get emoji for user status"""
        status_emojis = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        return status_emojis.get(status, "⚫")

    # Error handlers
    @extract_users_from_roles.error
    @list_target_roles.error
    @update_hierarchy.error
    async def admin_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command.")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")

    @staff_list.error
    @staff_list_compact.error
    async def general_command_error(self, ctx, error):
        await ctx.send(f"❌ An error occurred: {str(error)}")

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(RoleUserExtractor(bot))