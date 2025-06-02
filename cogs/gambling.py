import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import asyncio
from typing import Optional, List, Dict, Any


class Card:
    """Represents a playing card"""
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.value = self._get_value()
    
    def _get_value(self) -> int:
        """Get the base value of the card (Ace = 11 initially)"""
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)
    
    def __str__(self):
        return f"{self.rank}{self.suit}"


class Deck:
    """Represents a deck of playing cards"""
    suits = ['♠', '♣', '♦', '♥']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        """Reset and shuffle the deck"""
        self.cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.cards)
    
    def draw(self) -> Card:
        """Draw a card from the deck"""
        if not self.cards:
            self.reset()
        return self.cards.pop()


class BlackjackHand:
    """Represents a blackjack hand"""
    def __init__(self):
        self.cards: List[Card] = []
        self.bet = 0
        self.doubled = False
        self.split = False
    
    def add_card(self, card: Card):
        """Add a card to the hand"""
        self.cards.append(card)
    
    def get_value(self) -> int:
        """Calculate the best value of the hand"""
        total = sum(card.value for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 'A')
        
        # Adjust for aces
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def is_bust(self) -> bool:
        """Check if hand is bust"""
        return self.get_value() > 21
    
    def is_blackjack(self) -> bool:
        """Check if hand is blackjack"""
        return len(self.cards) == 2 and self.get_value() == 21
    
    def can_double(self) -> bool:
        """Check if hand can be doubled"""
        return len(self.cards) == 2 and not self.doubled
    
    def can_split(self) -> bool:
        """Check if hand can be split"""
        return (len(self.cards) == 2 and 
                self.cards[0].rank == self.cards[1].rank and 
                not self.split)
    
    def __str__(self):
        return ' '.join(str(card) for card in self.cards)


class BlackjackView(discord.ui.View):
    """View for blackjack game controls"""
    
    def __init__(self, gambling_cog, user_id: int):
        super().__init__(timeout=300)
        self.gambling_cog = gambling_cog
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🎯")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hit button - draw another card"""
        if self.user_id not in self.gambling_cog.blackjack_games:
            return await interaction.response.send_message("❌ Game not found!", ephemeral=True)
        
        game = self.gambling_cog.blackjack_games[self.user_id]
        current_hand_idx = game["current_hand"]
        current_hand = game["player_hands"][current_hand_idx]
        
        # Draw card
        current_hand.add_card(game["deck"].draw())
        
        if current_hand.is_bust():
            # Move to next hand or end game
            if current_hand_idx + 1 < len(game["player_hands"]):
                game["current_hand"] += 1
                embed = self.gambling_cog.create_blackjack_embed(self.user_id, "🎯 Next hand!")
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                # All hands done
                result_text = self.gambling_cog.finish_blackjack_game(self.user_id)
                embed = self.gambling_cog.create_blackjack_embed(self.user_id, f"🎲 Game Over!\n{result_text}", discord.Color.orange())
                del self.gambling_cog.blackjack_games[self.user_id]
                await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = self.gambling_cog.create_blackjack_embed(self.user_id, "🎯 Your turn!")
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stand button - keep current hand"""
        if self.user_id not in self.gambling_cog.blackjack_games:
            return await interaction.response.send_message("❌ Game not found!", ephemeral=True)
        
        game = self.gambling_cog.blackjack_games[self.user_id]
        current_hand_idx = game["current_hand"]
        
        # Move to next hand or end game
        if current_hand_idx + 1 < len(game["player_hands"]):
            game["current_hand"] += 1
            embed = self.gambling_cog.create_blackjack_embed(self.user_id, "🎯 Next hand!")
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # All hands done
            result_text = self.gambling_cog.finish_blackjack_game(self.user_id)
            embed = self.gambling_cog.create_blackjack_embed(self.user_id, f"🎲 Game Over!\n{result_text}", discord.Color.orange())
            del self.gambling_cog.blackjack_games[self.user_id]
            await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Double Down", style=discord.ButtonStyle.success, emoji="💰")
    async def double_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Double down button - double bet and draw one card"""
        if self.user_id not in self.gambling_cog.blackjack_games:
            return await interaction.response.send_message("❌ Game not found!", ephemeral=True)
        
        game = self.gambling_cog.blackjack_games[self.user_id]
        current_hand_idx = game["current_hand"]
        current_hand = game["player_hands"][current_hand_idx]
        
        if not current_hand.can_double():
            return await interaction.response.send_message("❌ You can't double down now!", ephemeral=True)
        
        # Check if user has enough credits
        if current_hand.bet > self.gambling_cog.get_user_credits(self.user_id):
            return await interaction.response.send_message("❌ Not enough credits to double down!", ephemeral=True)
        
        # Double the bet
        self.gambling_cog.update_user_credits(self.user_id, -current_hand.bet)
        current_hand.bet *= 2
        current_hand.doubled = True
        
        # Draw one card
        current_hand.add_card(game["deck"].draw())
        
        # Move to next hand or end game
        if current_hand_idx + 1 < len(game["player_hands"]):
            game["current_hand"] += 1
            embed = self.gambling_cog.create_blackjack_embed(self.user_id, "🎯 Next hand!")
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # All hands done
            result_text = self.gambling_cog.finish_blackjack_game(self.user_id)
            embed = self.gambling_cog.create_blackjack_embed(self.user_id, f"🎲 Game Over!\n{result_text}", discord.Color.orange())
            del self.gambling_cog.blackjack_games[self.user_id]
            await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        """Handle view timeout"""
        if self.user_id in self.gambling_cog.blackjack_games:
            # Auto-stand and finish game
            result_text = self.gambling_cog.finish_blackjack_game(self.user_id)
            del self.gambling_cog.blackjack_games[self.user_id]


class HighLowView(discord.ui.View):
    """View for high-low game controls"""
    
    def __init__(self, gambling_cog, user_id: int):
        super().__init__(timeout=300)
        self.gambling_cog = gambling_cog
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Higher", style=discord.ButtonStyle.success, emoji="⬆️")
    async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Guess higher"""
        await self.make_guess(interaction, "higher")

    @discord.ui.button(label="Lower", style=discord.ButtonStyle.danger, emoji="⬇️")
    async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Guess lower"""
        await self.make_guess(interaction, "lower")

    @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.secondary, emoji="💸")
    async def cash_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cash out current winnings"""
        if self.user_id not in self.gambling_cog.highlow_games:
            return await interaction.response.send_message("❌ Game not found!", ephemeral=True)
        
        game = self.gambling_cog.highlow_games[self.user_id]
        streak = game["streak"]
        total_bet = game["total_bet"]
        
        if streak == 0:
            return await interaction.response.send_message("❌ You need at least one correct guess to cash out!", ephemeral=True)
        
        # Calculate winnings
        multiplier = self.gambling_cog.highlow_multipliers.get(streak, 1.0)
        winnings = int(total_bet * multiplier)
        
        # Give winnings
        new_balance = self.gambling_cog.update_user_credits(self.user_id, winnings)
        
        embed = discord.Embed(
            title="💸 Cashed Out!",
            description=f"You cashed out with a streak of `{streak}`!\n\n"
                       f"💰 **Winnings:** `{winnings:,}` credits\n"
                       f"💳 **New Balance:** `{new_balance:,}` credits",
            color=discord.Color.green()
        )
        
        embed.set_footer(
            text="Delirium Den • High-Low",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        del self.gambling_cog.highlow_games[self.user_id]
        await interaction.response.edit_message(embed=embed, view=None)

    async def make_guess(self, interaction: discord.Interaction, guess: str):
        """Make a guess in the high-low game"""
        if self.user_id not in self.gambling_cog.highlow_games:
            return await interaction.response.send_message("❌ Game not found!", ephemeral=True)
        
        game = self.gambling_cog.highlow_games[self.user_id]
        current_card = game["current_card"]
        deck = game["deck"]
        
        # Draw new card
        new_card = deck.draw()
        
        # Check if guess is correct
        if guess == "higher":
            correct = new_card.value > current_card.value
        else:  # lower
            correct = new_card.value < current_card.value
        
        # Handle ties (count as incorrect)
        if new_card.value == current_card.value:
            correct = False
        
        if correct:
            # Correct guess - continue game
            game["current_card"] = new_card
            game["streak"] += 1
            
            embed = self.gambling_cog.create_highlow_embed(
                self.user_id, 
                f"✅ Correct! The card was {new_card} (Value: {new_card.value})",
                discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # Wrong guess - game over
            embed = discord.Embed(
                title="❌ Wrong Guess - Game Over!",
                description=f"The card was **{new_card}** (Value: {new_card.value})\n"
                           f"You guessed **{guess}** but it was **{'higher' if new_card.value > current_card.value else 'lower' if new_card.value < current_card.value else 'equal'}**!\n\n"
                           f"🔥 **Streak:** `{game['streak']}`\n"
                           f"💸 **Lost:** `{game['total_bet']:,}` credits",
                color=discord.Color.red()
            )
            
            balance = self.gambling_cog.get_user_credits(self.user_id)
            embed.add_field(
                name="💳 Balance",
                value=f"`{balance:,}` credits",
                inline=True
            )
            
            embed.set_footer(
                text="Delirium Den • High-Low",
                icon_url="https://i.imgur.com/RzksmKL.png"
            )
            
            del self.gambling_cog.highlow_games[self.user_id]
            await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        """Handle view timeout"""
        if self.user_id in self.gambling_cog.highlow_games:
            del self.gambling_cog.highlow_games[self.user_id]


class DiceGameView(discord.ui.View):
    """View for dice game number selection"""
    
    def __init__(self, gambling_cog, user_id: int, bet: int, balance: int):
        super().__init__(timeout=60)
        self.gambling_cog = gambling_cog
        self.user_id = user_id
        self.bet = bet
        self.balance = balance
        
        # Add number buttons (2-12) in rows
        # Row 1: 2-6
        for i in range(2, 7):
            button = discord.ui.Button(
                label=str(i),
                style=discord.ButtonStyle.secondary,
                row=0
            )
            button.callback = self.make_number_callback(i)
            self.add_item(button)
        
        # Row 2: 7-12
        for i in range(7, 13):
            button = discord.ui.Button(
                label=str(i),
                style=discord.ButtonStyle.secondary,
                row=1
            )
            button.callback = self.make_number_callback(i)
            self.add_item(button)

    def make_number_callback(self, number: int):
        """Create callback for number button"""
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            
            # Roll two dice
            die1 = random.randint(1, 6)
            die2 = random.randint(1, 6)
            total = die1 + die2
            
            # Check if they won
            won = total == number
            
            if won:
                # Calculate winnings based on probability
                # Probability decreases towards edges (2 and 12 are hardest)
                prob_map = {2: 36, 3: 18, 4: 12, 5: 9, 6: 7.2, 7: 6, 
                           8: 7.2, 9: 9, 10: 12, 11: 18, 12: 36}
                multiplier = prob_map[number]
                winnings = int(self.bet * multiplier)
                new_balance = self.gambling_cog.update_user_credits(self.user_id, winnings)
                
                embed = discord.Embed(
                    title="🎲 Dice Roll - You Won!",
                    description=f"🎯 You picked `{number}` and rolled `{total}`!\n\n"
                               f"🎲 **Roll:** {die1} + {die2} = {total}\n"
                               f"💰 **Winnings:** `{winnings:,}` credits (x{multiplier})\n"
                               f"💳 **Balance:** `{new_balance:,}` credits",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="🎲 Dice Roll - You Lost!",
                    description=f"💔 You picked `{number}` but rolled `{total}`\n\n"
                               f"🎲 **Roll:** {die1} + {die2} = {total}\n"
                               f"💸 **Lost:** `{self.bet:,}` credits\n"
                               f"💳 **Balance:** `{self.balance:,}` credits",
                    color=discord.Color.red()
                )
            
            await interaction.response.edit_message(embed=embed, view=None)
        
        return callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return False
        return True


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "levels_data.json"
        
        # Active games tracking
        self.blackjack_games: Dict[int, Dict[str, Any]] = {}
        self.highlow_games: Dict[int, Dict[str, Any]] = {}
        
        # Game settings
        self.min_bet = 10
        self.max_bet = 10000
        self.blackjack_payout = 1.5  # 3:2 payout for blackjack
        
        # High-low settings
        self.highlow_multipliers = {
            1: 1.1,   # Very easy
            2: 1.25,  # Easy  
            3: 1.5,   # Medium
            4: 2.0,   # Hard
            5: 3.0,   # Very hard
            6: 5.0,   # Extreme
        }

    def load_data(self) -> Dict[str, Any]:
        """Load user data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self, data: Dict[str, Any]):
        """Save user data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_credits(self, user_id: int) -> int:
        """Get user's credit balance"""
        data = self.load_data()
        user_data = data.get(str(user_id), {})
        return user_data.get("credits", 0)

    def update_user_credits(self, user_id: int, amount: int) -> int:
        """Update user's credits and return new balance"""
        data = self.load_data()
        user_id_str = str(user_id)
        
        if user_id_str not in data:
            data[user_id_str] = {
                "xp": 0,
                "level": 0,
                "credits": 100,
                "reputation": 0,
                "voice_time": 0,
                "messages_sent": 0,
                "last_daily": 0,
                "profile_bg": "default",
                "rank_bg": "default",
                "description": "No description set."
            }
        
        data[user_id_str]["credits"] += amount
        new_balance = data[user_id_str]["credits"]
        self.save_data(data)
        return new_balance

    def validate_bet(self, user_id: int, bet: int) -> tuple[bool, str]:
        """Validate if user can make the bet"""
        if bet < self.min_bet:
            return False, f"Minimum bet is `{self.min_bet}` credits!"
        
        if bet > self.max_bet:
            return False, f"Maximum bet is `{self.max_bet:,}` credits!"
        
        credits = self.get_user_credits(user_id)
        if bet > credits:
            return False, f"You only have `{credits:,}` credits!"
        
        return True, ""

    # Coinflip Command
    @app_commands.command(name="coinflip", description="Flip a coin and bet on heads or tails")
    @app_commands.describe(
        choice="Choose heads or tails",
        bet="Amount to bet"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, choice: str, bet: int):
        """Coinflip gambling game"""
        # Validate bet
        valid, error_msg = self.validate_bet(interaction.user.id, bet)
        if not valid:
            return await interaction.response.send_message(f"❌ {error_msg}", ephemeral=True)
        
        # Deduct bet
        old_balance = self.update_user_credits(interaction.user.id, -bet)
        new_balance = old_balance - bet
        
        # Flip coin
        result = random.choice(["heads", "tails"])
        won = result == choice.lower()
        
        # Create animated embed
        embed = discord.Embed(
            title="🪙 Coinflip",
            description="Flipping coin...",
            color=discord.Color.yellow()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Simulate coin flip animation
        await asyncio.sleep(1)
        embed.description = "🌀 Spinning..."
        await interaction.edit_original_response(embed=embed)
        
        await asyncio.sleep(1)
        
        # Show result
        if won:
            winnings = bet * 2
            new_balance = self.update_user_credits(interaction.user.id, winnings)
            
            embed = discord.Embed(
                title="🪙 Coinflip - You Won!",
                description=f"The coin landed on **{result.title()}**!\n\n"
                           f"💰 **Winnings:** `{winnings:,}` credits\n"
                           f"💳 **Balance:** `{new_balance:,}` credits",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="🪙 Coinflip - You Lost!",
                description=f"The coin landed on **{result.title()}**!\n\n"
                           f"💸 **Lost:** `{bet:,}` credits\n"
                           f"💳 **Balance:** `{new_balance:,}` credits",
                color=discord.Color.red()
            )
        
        coin_emoji = "🔘" if result == "heads" else "⚪"
        embed.add_field(
            name="Result",
            value=f"{coin_emoji} **{result.title()}**",
            inline=True
        )
        
        embed.set_footer(
            text=f"Delirium Den • You chose {choice.title()}",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.edit_original_response(embed=embed)

    # Blackjack Commands
    @app_commands.command(name="blackjack", description="Play a game of blackjack")
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        """Start a blackjack game"""
        user_id = interaction.user.id
        
        # Check if user already has a game
        if user_id in self.blackjack_games:
            return await interaction.response.send_message("❌ You already have a blackjack game in progress!", ephemeral=True)
        
        # Validate bet
        valid, error_msg = self.validate_bet(user_id, bet)
        if not valid:
            return await interaction.response.send_message(f"❌ {error_msg}", ephemeral=True)
        
        # Deduct bet
        self.update_user_credits(user_id, -bet)
        
        # Initialize game
        deck = Deck()
        player_hand = BlackjackHand()
        dealer_hand = BlackjackHand()
        
        # Deal initial cards
        player_hand.add_card(deck.draw())
        dealer_hand.add_card(deck.draw())
        player_hand.add_card(deck.draw())
        dealer_hand.add_card(deck.draw())
        
        player_hand.bet = bet
        
        # Store game
        self.blackjack_games[user_id] = {
            "deck": deck,
            "player_hands": [player_hand],
            "dealer_hand": dealer_hand,
            "current_hand": 0,
            "game_over": False
        }
        
        # Check for immediate blackjack
        if player_hand.is_blackjack():
            if dealer_hand.is_blackjack():
                # Push
                self.update_user_credits(user_id, bet)
                result_embed = self.create_blackjack_embed(user_id, "🤝 Push - Both Blackjack!", discord.Color.yellow())
            else:
                # Player blackjack wins
                winnings = int(bet * (1 + self.blackjack_payout))
                self.update_user_credits(user_id, winnings)
                result_embed = self.create_blackjack_embed(user_id, f"🎉 Blackjack! You won `{winnings:,}` credits!", discord.Color.green())
            
            del self.blackjack_games[user_id]
            return await interaction.response.send_message(embed=result_embed)
        
        # Show initial game state
        embed = self.create_blackjack_embed(user_id, "🃏 Your turn!")
        view = BlackjackView(self, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    def create_blackjack_embed(self, user_id: int, title: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
        """Create blackjack game embed"""
        if user_id not in self.blackjack_games:
            return discord.Embed(title="❌ Game not found", color=discord.Color.red())
        
        game = self.blackjack_games[user_id]
        player_hands = game["player_hands"]
        dealer_hand = game["dealer_hand"]
        current_hand = game["current_hand"]
        
        embed = discord.Embed(title=title, color=color)
        
        # Dealer's hand (hide hole card if game not over)
        if game["game_over"]:
            dealer_cards = str(dealer_hand)
            dealer_value = dealer_hand.get_value()
            dealer_text = f"{dealer_cards} (Value: {dealer_value})"
        else:
            visible_card = str(dealer_hand.cards[0])
            dealer_text = f"{visible_card} 🂠 (Value: ?)"
        
        embed.add_field(
            name="🏠 Dealer",
            value=dealer_text,
            inline=False
        )
        
        # Player's hands
        for i, hand in enumerate(player_hands):
            hand_status = ""
            if hand.is_bust():
                hand_status = " (BUST)"
            elif hand.is_blackjack():
                hand_status = " (BLACKJACK)"
            elif len(player_hands) > 1 and i == current_hand:
                hand_status = " ← Current"
            
            embed.add_field(
                name=f"👤 Your Hand{f' #{i+1}' if len(player_hands) > 1 else ''}{hand_status}",
                value=f"{hand} (Value: {hand.get_value()}) | Bet: `{hand.bet:,}`",
                inline=False
            )
        
        # Show balance
        balance = self.get_user_credits(user_id)
        embed.add_field(
            name="💳 Balance",
            value=f"`{balance:,}` credits",
            inline=True
        )
        
        embed.set_footer(
            text="Delirium Den • Blackjack",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        return embed

    def finish_blackjack_game(self, user_id: int) -> str:
        """Finish blackjack game and calculate winnings"""
        if user_id not in self.blackjack_games:
            return "Game not found!"
        
        game = self.blackjack_games[user_id]
        player_hands = game["player_hands"]
        dealer_hand = game["dealer_hand"]
        deck = game["deck"]
        
        # Dealer plays
        while dealer_hand.get_value() < 17:
            dealer_hand.add_card(deck.draw())
        
        game["game_over"] = True
        
        # Calculate results for each hand
        total_winnings = 0
        results = []
        
        for i, hand in enumerate(player_hands):
            if hand.is_bust():
                results.append(f"Hand {i+1 if len(player_hands) > 1 else ''}: Lost `{hand.bet:,}` (Bust)")
                continue
            
            dealer_value = dealer_hand.get_value()
            player_value = hand.get_value()
            
            if dealer_hand.is_bust() or player_value > dealer_value:
                if hand.is_blackjack():
                    winnings = int(hand.bet * (1 + self.blackjack_payout))
                else:
                    winnings = hand.bet * 2
                total_winnings += winnings
                results.append(f"Hand {i+1 if len(player_hands) > 1 else ''}: Won `{winnings:,}`")
            elif player_value < dealer_value:
                results.append(f"Hand {i+1 if len(player_hands) > 1 else ''}: Lost `{hand.bet:,}`")
            else:
                # Push
                total_winnings += hand.bet
                results.append(f"Hand {i+1 if len(player_hands) > 1 else ''}: Push `{hand.bet:,}`")
        
        # Update balance
        if total_winnings > 0:
            self.update_user_credits(user_id, total_winnings)
        
        result_text = "\n".join(results)
        return result_text

    # High-Low Game
    @app_commands.command(name="highlow", description="Guess if the next card will be higher or lower")
    @app_commands.describe(bet="Amount to bet")
    async def highlow(self, interaction: discord.Interaction, bet: int):
        """Start a high-low game"""
        user_id = interaction.user.id
        
        # Check if user already has a game
        if user_id in self.highlow_games:
            return await interaction.response.send_message("❌ You already have a high-low game in progress!", ephemeral=True)
        
        # Validate bet
        valid, error_msg = self.validate_bet(user_id, bet)
        if not valid:
            return await interaction.response.send_message(f"❌ {error_msg}", ephemeral=True)
        
        # Deduct bet
        self.update_user_credits(user_id, -bet)
        
        # Initialize game
        deck = Deck()
        current_card = deck.draw()
        
        self.highlow_games[user_id] = {
            "deck": deck,
            "current_card": current_card,
            "streak": 0,
            "total_bet": bet,
            "last_bet": bet
        }
        
        embed = self.create_highlow_embed(user_id, "🎴 High-Low Game Started!")
        view = HighLowView(self, user_id)
        await interaction.response.send_message(embed=embed, view=view)

    def create_highlow_embed(self, user_id: int, title: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
        """Create high-low game embed"""
        if user_id not in self.highlow_games:
            return discord.Embed(title="❌ Game not found", color=discord.Color.red())
        
        game = self.highlow_games[user_id]
        current_card = game["current_card"]
        streak = game["streak"]
        total_bet = game["total_bet"]
        
        embed = discord.Embed(title=title, color=color)
        
        embed.add_field(
            name="🎴 Current Card",
            value=f"**{current_card}** (Value: {current_card.value})",
            inline=True
        )
        
        embed.add_field(
            name="🔥 Streak",
            value=f"`{streak}`",
            inline=True
        )
        
        # Calculate potential winnings
        multiplier = self.highlow_multipliers.get(streak + 1, 1.0)
        potential_winnings = int(total_bet * multiplier)
        
        embed.add_field(
            name="💰 Potential Winnings",
            value=f"`{potential_winnings:,}` credits (x{multiplier})",
            inline=True
        )
        
        balance = self.get_user_credits(user_id)
        embed.add_field(
            name="💳 Balance",
            value=f"`{balance:,}` credits",
            inline=True
        )
        
        # Show streak bonuses
        bonus_text = []
        for level, mult in self.highlow_multipliers.items():
            status = "✅" if streak >= level else "⬜"
            bonus_text.append(f"{status} Streak {level}: x{mult}")
        
        embed.add_field(
            name="🎯 Streak Bonuses",
            value="\n".join(bonus_text),
            inline=False
        )
        
        embed.set_footer(
            text="Delirium Den • High-Low | Will the next card be higher or lower?",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        return embed

    @app_commands.command(name="gamble", description="Quick gambling with various games")
    @app_commands.describe(
        game="Choose a quick game",
        bet="Amount to bet"
    )
    @app_commands.choices(game=[
        app_commands.Choice(name="Dice Roll (2-12)", value="dice"),
        app_commands.Choice(name="Lucky Number (1-100)", value="lucky"),
        app_commands.Choice(name="Color Wheel", value="color")
    ])
    async def quick_gamble(self, interaction: discord.Interaction, game: str, bet: int):
        """Quick gambling games"""
        # Validate bet
        valid, error_msg = self.validate_bet(interaction.user.id, bet)
        if not valid:
            return await interaction.response.send_message(f"❌ {error_msg}", ephemeral=True)
        
        # Deduct bet
        old_balance = self.update_user_credits(interaction.user.id, -bet)
        new_balance = old_balance - bet
        
        if game == "dice":
            await self.dice_game(interaction, bet, new_balance)
        elif game == "lucky":
            await self.lucky_number_game(interaction, bet, new_balance)
        elif game == "color":
            await self.color_wheel_game(interaction, bet, new_balance)

    async def dice_game(self, interaction: discord.Interaction, bet: int, balance: int):
        """Dice rolling game"""
        # Player picks a number (2-12)
        embed = discord.Embed(
            title="🎲 Dice Roll Game",
            description="Pick a number from 2-12!\nIf you roll it exactly, you win big!",
            color=discord.Color.blue()
        )
        
        view = DiceGameView(self, interaction.user.id, bet, balance)
        await interaction.response.send_message(embed=embed, view=view)

    async def lucky_number_game(self, interaction: discord.Interaction, bet: int, balance: int):
        """Lucky number guessing game"""
        # Generate random number 1-100
        lucky_number = random.randint(1, 100)
        player_guess = random.randint(1, 100)  # For now, random guess
        
        # Calculate how close they were
        difference = abs(lucky_number - player_guess)
        
        # Determine winnings based on closeness
        if difference == 0:
            multiplier = 50  # Exact match
            result = "🎯 BULLSEYE!"
        elif difference <= 5:
            multiplier = 10  # Very close
            result = "🔥 Very Close!"
        elif difference <= 10:
            multiplier = 5   # Close
            result = "✨ Close!"
        elif difference <= 20:
            multiplier = 2   # Decent
            result = "👍 Not bad!"
        else:
            multiplier = 0   # Too far
            result = "💔 Too far..."
        
        if multiplier > 0:
            winnings = bet * multiplier
            new_balance = self.update_user_credits(interaction.user.id, winnings)
            color = discord.Color.green()
        else:
            winnings = 0
            new_balance = balance
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🔮 Lucky Number Results",
            description=f"{result}\n\n"
                       f"🎯 **Lucky Number:** `{lucky_number}`\n"
                       f"🎲 **Your Guess:** `{player_guess}`\n"
                       f"📏 **Difference:** `{difference}`\n\n"
                       f"💰 **Winnings:** `{winnings:,}` credits (x{multiplier})\n"
                       f"💳 **Balance:** `{new_balance:,}` credits",
            color=color
        )
        
        await interaction.response.send_message(embed=embed)

    async def color_wheel_game(self, interaction: discord.Interaction, bet: int, balance: int):
        """Color wheel spinning game"""
        colors = {
            "🔴": {"name": "Red", "chance": 0.4, "multiplier": 2},
            "🟡": {"name": "Yellow", "chance": 0.3, "multiplier": 3},
            "🟢": {"name": "Green", "chance": 0.2, "multiplier": 4},
            "🔵": {"name": "Blue", "chance": 0.08, "multiplier": 10},
            "🟣": {"name": "Purple", "chance": 0.02, "multiplier": 50}
        }
        
        # Spin the wheel
        rand = random.random()
        cumulative = 0
        result_color = None
        
        for emoji, data in colors.items():
            cumulative += data["chance"]
            if rand <= cumulative:
                result_color = emoji
                result_data = data
                break
        
        # Calculate winnings
        winnings = int(bet * result_data["multiplier"])
        new_balance = self.update_user_credits(interaction.user.id, winnings)
        
        embed = discord.Embed(
            title="🎡 Color Wheel Results",
            description=f"The wheel landed on {result_color} **{result_data['name']}**!\n\n"
                       f"💰 **Winnings:** `{winnings:,}` credits (x{result_data['multiplier']})\n"
                       f"💳 **Balance:** `{new_balance:,}` credits",
            color=discord.Color.gold()
        )
        
        # Show all probabilities
        prob_text = []
        for emoji, data in colors.items():
            prob_text.append(f"{emoji} {data['name']}: {data['chance']*100}% (x{data['multiplier']})")
        
        embed.add_field(
            name="🎯 Probabilities",
            value="\n".join(prob_text),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gambling-stats", description="View your gambling statistics")
    async def gambling_stats(self, interaction: discord.Interaction, user: discord.Member = None):
        """Show gambling statistics"""
        target_user = user or interaction.user
        credits = self.get_user_credits(target_user.id)
        
        embed = discord.Embed(
            title=f"🎰 {target_user.display_name}'s Gambling Stats",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="💳 Current Balance",
            value=f"`{credits:,}` credits",
            inline=True
        )
        
        # Check if user has active games
        active_games = []
        if target_user.id in self.blackjack_games:
            active_games.append("🃏 Blackjack")
        if target_user.id in self.highlow_games:
            active_games.append("🎴 High-Low")
        
        embed.add_field(
            name="🎮 Active Games",
            value="\n".join(active_games) if active_games else "None",
            inline=True
        )
        
        embed.add_field(
            name="🎲 Available Games",
            value="• `/coinflip` - 50/50 chance\n"
                  "• `/blackjack` - Classic card game\n"
                  "• `/highlow` - Streak-based guessing\n"
                  "• `/gamble` - Quick mini-games",
            inline=False
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(
            text="Delirium Den • Gambling Hub",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gambling-help", description="Learn how to play the gambling games")
    async def gambling_help(self, interaction: discord.Interaction):
        """Show gambling help"""
        embed = discord.Embed(
            title="🎰 Gambling Help",
            description="Learn how to play all the gambling games!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🪙 Coinflip",
            value="Simple 50/50 game. Pick heads or tails and double your bet if correct!",
            inline=False
        )
        
        embed.add_field(
            name="🃏 Blackjack",
            value="Get as close to 21 as possible without going over.\n"
                  "• **Hit:** Draw another card\n"
                  "• **Stand:** Keep your current total\n"
                  "• **Double Down:** Double bet and draw one card\n"
                  "• **Blackjack:** 21 with 2 cards (1.5x payout)",
            inline=False
        )
        
        embed.add_field(
            name="🎴 High-Low",
            value="Guess if the next card will be higher or lower.\n"
                  "Build up streaks for bigger multipliers!\n"
                  "• Streak 1: x1.1\n• Streak 3: x1.5\n• Streak 6: x5.0\n"
                  "Cash out anytime to secure your winnings!",
            inline=False
        )
        
        embed.add_field(
            name="🎲 Quick Games (/gamble)",
            value="• **Dice:** Pick a number 2-12 and roll dice\n"
                  "• **Lucky Number:** Get close to the lucky number\n"
                  "• **Color Wheel:** Spin for different multipliers",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value=f"• Minimum bet: `{self.min_bet}` credits\n"
                  f"• Maximum bet: `{self.max_bet:,}` credits\n"
                  "• Get daily credits with `/daily`\n"
                  "• Games time out after 5 minutes",
            inline=False
        )
        
        embed.set_footer(
            text="Delirium Den • Gamble Responsibly!",
            icon_url="https://i.imgur.com/RzksmKL.png"
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Gambling(bot))