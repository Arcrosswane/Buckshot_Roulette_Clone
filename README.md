# 🎰 Buck Roulette - The High Stakes Casino

Welcome to **Buck Roulette**, a multi-player game of chance, strategy, and survival. Inspired by logic-based Russian Roulette games, this version adds complex character classes, chaotic items, and high-reward bounty contracts.

## 📝 The Core Rules

1. **The Goal**: Be the last player standing across 3 increasingly difficult rounds.
2. **The Gun**: Every round, a "Gun" is loaded with a random mix of **Live Rounds** 🔴 and **Blank Rounds** 🔵.
3. **The Shove**: On your turn, you must shoot.
   - **Safe Shot**: Aim at an opponent. If it's Live, they take damage. If it's Blank, nothing happens.
   - **Risk Shot**: Aim at yourself. If it's Blank, you **keep your turn**. If it's Live, you take damage and lose your turn.

## 🎭 Character Classes

Choose your survival strategy:

- **🛡️ Tank**: Starts with +2 Max Health. Harder to kill.
- **🎯 Sniper**: Deals +1 bonus damage when successfully hitting an opponent.
- **🎲 Gambler**: Has a higher chance (25%) to find the legendary **Diamond** and other rare items.

## 📦 Legendary Props (Items)

Use these to tilt the odds in your favor:

- **💉 Injection**: Steal an item from an opponent.
- **⛓️ Handcuffs**: Force an opponent to skip their next turn.
- **📱 Burner Phone**: Reveals a random shell's position in the gun (100% accurate).
- **🚬 Cigarette**: Restores 1 Health.
- **🔪 Knife**: Cuts the barrel! The next Live shot deals **2x Damage**.
- **🥤 Soda**: Safely ejects the current shell from the gun.
- **🔍 Lens**: Inspect the current shell (Note: Sudden Death bullets hide from this!).
- **⚡ Inverter**: Flips the current shell's polarity (Live ↔ Blank).
- **🎁 Mystery Box**: Triggers a random chaotic event (Heal, Harm, or Loot).
- **💎 Diamond**: The rarest item. Allows you to "Wish" for any item in the game and if any of it exists in the game (not including your) then it will be dissapeared now only you will have that thing.

## ⚠️ Chaos Mechanics

- **🎯 Secret Bounty**: In Rounds 2 & 3, you might get a secret contract to kill a specific player. Success results in an **Instant Round Win**.
- **💥 Round Modifiers**:
  - **Double Trouble**: All damage is doubled.
  - **Vampirism**: Healing 1 HP for every successful hit on an opponent.
- **💀 Sudden Death (Round 3)**: A special "Instant Kill" bullet is loaded into the gun. Only the **Phone** can detect it.

## 💰 Rewards & Stats

- **Match Prize**: Winners take home a massive cash prize starting at $100,000.
- **Match Stats**: After the game, view detailed stats on damage dealt, kills, and your "Luck Score" (survival streaks).

## 🚀 How to Run

1. Install Flask: `pip install flask`
2. Run the server: `python app.py`
3. Connect via browser using the Host IP displayed in the lobby.

---

_May the odds be ever in your favor._

