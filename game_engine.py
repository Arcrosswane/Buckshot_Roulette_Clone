import random
import time

# =========================
# CONSTANTS & CONFIG
# =========================
SAFE = "Blank round"
BUST = "Live round"
MAGIC_BULLET = "Sudden Death" # Acts as BUST but 999 DMG & Hidden
DECK = "Gun"
HEALTH_NAME = "Health"

# Item Names
ITEM_STEAL = "Injection"
ITEM_SKIP = "Handcuffs"
ITEM_PEEK_RANDOM = "Phone"
ITEM_HEAL = "Cigarette"
ITEM_DOUBLE = "Knife"
ITEM_DISCARD = "Soda"
ITEM_LENS = "Lens"
ITEM_DIAMOND = "Diamond"
ITEM_INVERTER = "Inverter"
ITEM_MYSTERY_BOX = "Mystery Box"

ALL_ITEMS = [
    ITEM_STEAL,
    ITEM_SKIP,
    ITEM_PEEK_RANDOM,
    ITEM_HEAL,
    ITEM_DOUBLE,
    ITEM_DISCARD,
    ITEM_LENS,
    ITEM_INVERTER,
    ITEM_MYSTERY_BOX,
]
# DIAMOND removed from ALL_ITEMS to make it ultra rare (5%)

# Character Classes
CLASS_TANK = "Tank"
CLASS_SNIPER = "Sniper"
CLASS_GAMBLER = "Gambler"
PLAYER_CLASSES = [CLASS_TANK, CLASS_SNIPER, CLASS_GAMBLER]

# Gambler: "rare" items get higher weight. DIAMOND removed from here too.
RARE_ITEMS = [ITEM_LENS, ITEM_STEAL, ITEM_DOUBLE, ITEM_INVERTER, ITEM_MYSTERY_BOX]

# Draw Modes
MODE_SAFE = "safe"
MODE_RISK = "risk"

# Modifiers
MOD_DOUBLE_TROUBLE = "DOUBLE TROUBLE" # 2x Damage
MOD_VAMPIRISM = "VAMPIRISM" # Life steal on hit
# MOD_ITEM_RAIN Removed per user request

ROUND_MODIFIERS = [MOD_DOUBLE_TROUBLE, MOD_VAMPIRISM]

# Cinematic Messages
CINEMATIC_HIT = [
    "💥 BLAST! {0} staggers back!",
    "🔥 IMPACT! {0} reels from the shot!",
    "💀 STRIKE! {0} takes the hit!",
    "⚡ CRACK! {0} stumbles!",
]
CINEMATIC_DEATH = [
    "💀 {0} falls! OUT!",
    "☠️ {0} is down! OUT!",
]

class CasinoGameEngine:
    def __init__(self, players):
        self.original_players = players[:]
        self.players = players
        self.alive = players[:]
        self.turn = 0
        self.base_max_health = 4
        self.round_num = 1
        self.max_rounds = 3
        self.round_winner = None
        self.current_modifier = None
        self.bounty = None # { "assassin": p1, "target": p2 }
        
        # Match Stats
        self.stats = {p: {
            "dmg_dealt": 0,
            "dmg_taken": 0,
            "kills": 0,
            "deaths": 0,
            "self_harm": 0,
            "lucky_saves": 0, # Blanks shot at self
            "items_used": 0
        } for p in players}
        self.prize_pool = 100000 # Base $100,000
        
        # Logs structure: { "text": "...", "visible_to": None (all) or [names] }
        self.logs = [] 
        # Events structure: { "id": int, "type": "...", "data": {...} }
        self.events = []
        self.event_counter = 0

        self.player_classes = {}
        for p in players:
            self.player_classes[p] = random.choice(PLAYER_CLASSES)
        
        self.player_max_health = {}
        self.health = {}
        self.items = {p: [] for p in players}
        
        self._init_health()

        self.skip = {p: False for p in players}
        self.blocked = {p: False for p in players}
        self.double = None
        self.blackout_for = None
        self._blackout_announced = set()
        self.deck = []

        self.custom_log(f"--- ROUND {self.round_num} START ---")
        self.custom_log(f"Players: {', '.join(players)}")
        self.new_round_deck() 

    def _init_health(self):
        for p in self.original_players:
            if self.round_num == 1:
                base = 4
            else:
                base = random.randint(4, 8)
            
            bonus = 2 if self.player_classes[p] == CLASS_TANK else 0
            self.player_max_health[p] = base + bonus
            self.health[p] = self.player_max_health[p]

    def custom_log(self, message, visible_to=None):
        self.logs.append({
            "text": message,
            "visible_to": visible_to
        })

    def _trigger_event(self, event_type, **kwargs):
        """Register a persistent event for frontend visuals."""
        self.event_counter += 1
        self.events.append({
            "id": self.event_counter,
            "type": event_type,
            "data": kwargs,
            "timestamp": time.time()
        })
        # Keep last 30 events to ensure all clients catch up
        if len(self.events) > 30:
            self.events.pop(0)

    def new_round_deck(self):
        total = random.randint(4, 8)
        bust = random.randint(1, total - 1)
        safe = total - bust

        self.deck = [BUST] * bust + [SAFE] * safe
        
        # Round 3 Sudden Death: Replace one BUST with MAGIC_BULLET if possible
        if self.round_num == 3 and bust > 0:
            self.deck[0] = MAGIC_BULLET # We shuffle next anyway
            self.custom_log("💀 A SUDDEN DEATH BULLET has been loaded...")
            self._trigger_event("sudden_death_loaded")

        random.shuffle(self.deck)

        self.custom_log(f"🔫 Reloading... {bust} Live / {safe} Blank")
        self._trigger_event("reload", live=bust, blank=safe)
        
        # Bounty Expiration (User Request: "it should 'NOT' be like if deck is going to end it still asks me to kill")
        if self.bounty:
            a = self.bounty['assassin']
            self.custom_log(f"❌ Contract EXPIRED due to reshuffle.", visible_to=[a])
            self.bounty = None

        self.give_items()

    def give_items(self):
        for p in self.alive:
            if self.player_classes.get(p) == CLASS_GAMBLER:
                # Gambler diamond chance reduced to 25% as requested
                if random.random() < 0.25:
                    self.items[p].append(ITEM_DIAMOND)
                for _ in range(3):
                    self.items[p].append(random.choice(RARE_ITEMS + ALL_ITEMS))
            else:
                for _ in range(4):
                    if random.random() < 0.05: # Ultra Rare 5%
                        self.items[p].append(ITEM_DIAMOND)
                    else:
                        self.items[p].append(random.choice(ALL_ITEMS))

    def current(self):
        if not self.alive: return None
        return self.alive[self.turn % len(self.alive)]

    def next_turn(self):
        if len(self.alive) <= 1:
            self._check_round_over()
            return

        self.turn = (self.turn + 1) % len(self.alive)
        
        next_p = self.current()
        
        # Modifier: Item Rain
        if self.current_modifier == MOD_ITEM_RAIN:
            gift = random.choice(ALL_ITEMS)
            self.items[next_p].append(gift)
            self.custom_log(f"☔ Item Rain! {next_p} got a {gift}")
            self._trigger_event("item_rain", player=next_p, item=gift)

        if self.skip.get(next_p):
            self.custom_log(f"{next_p} was locked and loses turn!")
            self._trigger_event("skip", player=next_p)
            self.skip[next_p] = False
            self.next_turn()

    def _apply_damage(self, victim, dmg, source_player=None):
        # Modifier: Double Trouble
        if self.current_modifier == MOD_DOUBLE_TROUBLE:
            dmg *= 2
            self.custom_log(f"💀 Double Trouble! Damage x2!")

        self.health[victim] -= dmg
        if source_player and source_player in self.stats:
            if source_player != victim:
                self.stats[source_player]["dmg_dealt"] += dmg
            else:
                self.stats[source_player]["self_harm"] += dmg
        
        if victim in self.stats:
            self.stats[victim]["dmg_taken"] += dmg

        self.custom_log(random.choice(CINEMATIC_HIT).format(victim) + f" (-{dmg} {HEALTH_NAME})")
        
        # Determine if kill shot for event flavor
        is_kill = self.health[victim] <= 0
        if is_kill and victim in self.stats:
            self.stats[victim]["deaths"] += 1
        if is_kill and source_player and source_player != victim and source_player in self.stats:
            self.stats[source_player]["kills"] += 1

        self._trigger_event("damage", target=victim, amount=dmg, source=source_player, is_kill=is_kill)

        # Bounty Check
        if is_kill and self.bounty and source_player and source_player == self.bounty['assassin'] and victim == self.bounty['target']:
            self.custom_log(f"🎯 CONTRACT COMPLETE! {source_player} eliminated {victim}!")
            self._trigger_event("bounty_complete", assassin=source_player)
            self.round_winner = source_player
            self.custom_log(f"🏆 {source_player} wins by contract!")
            self._trigger_event("round_over", winner=source_player, is_grand=(self.round_num >= self.max_rounds))
            return True
        if self.current_modifier == MOD_VAMPIRISM and source_player and source_player != victim and source_player in self.alive:
            heal_amt = 1
            if self.health[source_player] < self.player_max_health[source_player]:
                self.health[source_player] += heal_amt
                self.custom_log(f"🧛 Vampirism! {source_player} drains life!")
                self._trigger_event("heal", target=source_player, amount=heal_amt, is_vampire=True)

        if is_kill:
            self.custom_log(random.choice(CINEMATIC_DEATH).format(victim))
            if victim in self.alive:
                self.alive.remove(victim)
            self._trigger_event("death", player=victim)
            self._check_round_over()
            return True
        return False
    
    def _check_round_over(self):
        if len(self.alive) == 1:
            winner = self.alive[0]
            if self.round_num < self.max_rounds:
                self.round_winner = winner
                self.custom_log(f"🏆 {winner} wins Round {self.round_num}!")
                self.custom_log("Next round starting...")
            else:
                self.custom_log(f"👑 GRAND WINNER: {winner}!")
            self._trigger_event("round_over", winner=winner, is_grand=(self.round_num >= self.max_rounds))

    def start_next_round(self):
        if self.round_num >= self.max_rounds:
            return False 
        
        self.round_num += 1
        self.round_winner = None
        self.alive = self.original_players[:]
        self.turn = 0 
        
        self._init_health()
        self.items = {p: [] for p in self.original_players}
        self.skip = {p: False for p in self.original_players}
        self.blocked = {p: False for p in self.original_players}
        self.double = None
        self.blackout_for = None
        self.bounty = None
        self.events = [] # Clear events on new round start? Or just let them roll off.
        self.event_counter = 0 # Reset counter or keep going? Better to keep going to avoid confusion, but round reset makes sense.
        # Impl: Resetting ensures a clean slate.
        
        # Select Round Modifier
        if self.round_num > 1:
            self.current_modifier = random.choice(ROUND_MODIFIERS)
            
            # Bounty Chance (30%) if enough players
            if len(self.alive) >= 2 and random.random() < 0.30:
                assassin = random.choice(self.alive)
                targets = [p for p in self.alive if p != assassin]
                if targets:
                    target = random.choice(targets)
                    self.bounty = {"assassin": assassin, "target": target}
                    self.custom_log(f"🎯 CONTRACT: Kill {target} to win the round!", visible_to=[assassin])
                    self.custom_log(f"🤫 You have received a secret contract...", visible_to=[assassin])
        else:
            self.current_modifier = None 

        self.custom_log(f"--- ROUND {self.round_num} START ---")
        self.prize_pool += 50000 # Increase prize pool per round
        if self.current_modifier:
            self.custom_log(f"⚠️ ROUND MODIFIER ACTIVE: {self.current_modifier} ⚠️")
            self._trigger_event("modifier_active", modifier=self.current_modifier)

        self.new_round_deck()
        return True

    def _sniper_bonus(self, player, base_dmg):
        if self.player_classes.get(player) == CLASS_SNIPER and random.random() < 0.10:
            self.custom_log(f"🎯 Sniper Critical Hit!")
            self._trigger_event("crit", player=player)
            return base_dmg + 1
        return base_dmg

    def _maybe_trigger_blackout(self):
        if len(self.alive) < 2: return
        if random.random() < 0.25:
            self.blackout_for = self.current()
            self._blackout_announced = set()
            self.custom_log(f"🌑 BLACKOUT triggered! {self.blackout_for}'s next draw will have target chosen at random.")
            self._trigger_event("blackout", active_player=self.blackout_for)

    def run_draw(self, target, mode=None):
        if self.round_winner: return 

        if mode is None or mode != MODE_RISK:
            mode = MODE_SAFE

        player = self.current()
        if not player: return

        if target not in self.alive:
            self.custom_log("Invalid target", visible_to=[player])
            return

        is_blackout_turn = self.blackout_for == player
        if is_blackout_turn:
            self.blackout_for = None
            opponents = [p for p in self.alive if p != player]
            if not opponents:
                self.custom_log("No valid opponents for Blackout.")
                return
            target = random.choice(opponents)
            self.custom_log(f"🌑 Blackout → target forced to {target}")

        if not self.deck:
            self.custom_log("⏹ Empty chamber. Reloading.")
            self.new_round_deck()

        card = self.deck.pop(0)
        is_live = (card == BUST or card == MAGIC_BULLET)
        is_magic = (card == MAGIC_BULLET)
        
        has_double = self.double == player
        if has_double:
            self.double = None
        
        self._trigger_event("shot_fired", player=player, target=target, is_live=is_live, is_magic=is_magic, mode=mode)

        if mode == MODE_SAFE:
            self.custom_log(f"🎯 {player} Safe Shot → {target}")
            
            if is_live:
                if is_magic:
                    dmg = 999
                    self.custom_log(f"💀 SUDDEN DEATH! {target} was obliterated!")
                else:
                    base_dmg = 2 if has_double else 1
                    dmg = self._sniper_bonus(player, base_dmg)
                
                self._apply_damage(target, dmg, source_player=player)
                self.next_turn()
                self._maybe_trigger_blackout()
            else:
                self.custom_log(f"Click! {SAFE}. No damage.")
                self._trigger_event("click", target=target)
                if target == player:
                    self.custom_log(f"{player} survives the blank and keeps the turn!")
                    if player in self.stats:
                        self.stats[player]["lucky_saves"] += 1
                else:
                    self.next_turn()
            return

        if mode == MODE_RISK:
            if is_blackout_turn:
                actual_target = target
                if is_live:
                    base_dmg = 3
                    dmg = self._sniper_bonus(player, base_dmg)
                    self.custom_log(f"🎯 {player} Risk Shot (blackout) → {actual_target}")
                    self._apply_damage(actual_target, dmg, source_player=player)
                else:
                    self.custom_log(f"🎯 {player} Risk Shot (blackout) → {actual_target} ... Click! {SAFE}.")
                    self._trigger_event("click", target=actual_target)
            else:
                hit_self = random.random() < 0.60
                actual_target = player if hit_self else target
                
                self.custom_log(f"🎯 {player} Risk Shot...")
                
                if is_live:
                    if hit_self:
                        self.custom_log(f"🔥 BACKFIRE! The gun snaps to {player}!")
                    else:
                        self.custom_log(f"🔫 The gun stays steady on {target}!")
                    
                    if is_magic:
                        dmg = 999
                        self.custom_log("💀 SUDDEN DEATH! INSTANT KILL!")
                    else:
                        base_dmg = 3
                        dmg = self._sniper_bonus(player, base_dmg)
                    
                    self._apply_damage(actual_target, dmg, source_player=player)
                else:
                    self.custom_log(f"Aimed at {actual_target}... Click! {SAFE}.")
                    self._trigger_event("click", target=actual_target)

            self.next_turn()
            self._maybe_trigger_blackout()

    def run_use(self, item, target=None, item_to_steal=None):
        if self.round_winner: return 

        player = self.current()
        if not player: return

        if self.blocked[player]:
            self.custom_log(f"{player} is jammed and can't use items!", visible_to=[player])
            self.blocked[player] = False
            return

        if item not in self.items[player]:
            self.custom_log("Item not owned", visible_to=[player])
            return

        self.items[player].remove(item)
        if player in self.stats:
            self.stats[player]["items_used"] += 1
        self._trigger_event("use_item", player=player, item=item, target=target)

        opponents = [p for p in self.alive if p != player]
        if not target and len(opponents) == 1 and item not in [ITEM_DIAMOND, ITEM_PEEK_RANDOM, ITEM_LENS, ITEM_DISCARD, ITEM_HEAL, ITEM_DOUBLE, ITEM_INVERTER, ITEM_MYSTERY_BOX]:
             target = opponents[0]

        # LOGIC
        if item == ITEM_STEAL:
             if not target or target == player or target not in self.alive:
                 self.custom_log("Steal failed: Invalid target", visible_to=[player])
                 self.items[player].append(item)
                 return
             
             if not self.items[target]:
                 self.custom_log(f"{target} has no items to steal", visible_to=[player])
                 self.items[player].append(item)
                 return
                 
             if not item_to_steal:
                 item_to_steal = random.choice(self.items[target])
             
             if item_to_steal not in self.items[target]:
                  self.custom_log(f"{target} does not have {item_to_steal}", visible_to=[player])
                  self.items[player].append(item)
                  return

             self.items[target].remove(item_to_steal)
             self.items[player].append(item_to_steal)
             self.custom_log(f"💉 {player} stole {item_to_steal} from {target}!")
             self.run_use(item_to_steal, target) # Auto-use stolen item

        elif item == ITEM_SKIP:
            if not target or target not in self.alive:
                self.custom_log("Skip failed: Invalid target", visible_to=[player])
                self.items[player].append(item)
                return
            self.skip[target] = True
            self.custom_log(f"⛓️ {target} is handcuffed! They will miss their next turn.")
            self._trigger_event("handcuffed", player=target)

        elif item == ITEM_PEEK_RANDOM:
            if self.deck:
                i = random.randrange(len(self.deck))
                peek_card = self.deck[i]
                
                msg = peek_card
                if peek_card == MAGIC_BULLET:
                    msg = "💀 SUDDEN DEATH BULLET"
                
                self.custom_log(f"🤫 Peek → shell {i + 1} is {msg}", visible_to=[player])
                self.custom_log(f"{player} checks a random shell phone...", visible_to=None) 

        elif item == ITEM_HEAL:
            max_hp = self.player_max_health[player]
            if self.health[player] < max_hp:
                self.health[player] += 1
                self.custom_log(f"{player} gains 1 {HEALTH_NAME}")
                self._trigger_event("heal", target=player, amount=1)
            else:
                self.custom_log(f"{player} is already at full health", visible_to=[player])
                self.items[player].append(item) 
                return

        elif item == ITEM_DOUBLE:
            self.double = player
            self.custom_log(f"{player} saws off the barrel! Next hit deals DOUBLE damage.")

        elif item == ITEM_DISCARD:
            if self.deck:
                gone = self.deck.pop(0)
                self.custom_log(f"Discarded {gone}")

        elif item == ITEM_LENS:
            if self.deck:
                peek_card = self.deck[0]
                # Disguise logic: Magic Bullet looks like LIVE round
                if peek_card == MAGIC_BULLET:
                    peek_card = BUST
                
                self.custom_log(f"🔍 Current shell is: {peek_card}", visible_to=[player])
                self.custom_log(f"{player} inspects the chamber...", visible_to=None) 
        
        elif item == ITEM_DIAMOND:
            if not target: 
                self.custom_log("Diamond failed: No item specified", visible_to=[player])
                self.items[player].append(item)
                return
            
            desired_item = target
            valid_items = ALL_ITEMS + RARE_ITEMS

            if desired_item not in valid_items:
                self.custom_log(f"Diamond failed: Invalid item {desired_item}", visible_to=[player])
                self.items[player].append(item)
                return

            self.items[player].append(desired_item)
            self.custom_log(f"💎 {player} wishes for a {desired_item}!")
            
            wiped_count = 0
            for p in self.alive:
                if p != player and desired_item in self.items[p]:
                    matches = [i for i in self.items[p] if i == desired_item]
                    wiped_count += len(matches)
                    self.items[p] = [i for i in self.items[p] if i != desired_item]
            
            if wiped_count > 0:
                self.custom_log(f"✨ The wish ripples out... {wiped_count} {desired_item}(s) vanished from opponents!")
        
        elif item == ITEM_INVERTER:
            if self.deck:
                current_shell = self.deck[0]
                # Inverter logic with Magic Bullet? 
                # If Magic, act as Live -> invert to Blank? Or invert to Live?
                # Let's say it breaks the Inverter or just acts as Live.
                # Logic: If Magic, it's "Live". Inverting "Live" -> "Blank". 
                # So Magic Bullet becomes Safe. That's a good counterplay.
                
                new_shell = BUST if current_shell == SAFE else SAFE
                if current_shell == MAGIC_BULLET:
                     new_shell = SAFE # Neutralized!
                     self.custom_log(f"⚡ {player} neutralized the anomaly! It's now Blank!")
                
                self.deck[0] = new_shell
                self.custom_log(f"⚡ {player} inverted the polarity! The shell is now {new_shell}!")
                self._trigger_event("inverse", player=player)
            else:
                self.custom_log("Inverter failed: Gun is empty", visible_to=[player])
                self.items[player].append(item)
        
        elif item == ITEM_MYSTERY_BOX:
            # Random effect
            outcomes = ["HEAL", "HURT", "LOOT", "RELOAD"]
            outcome = random.choice(outcomes)
            self.custom_log(f"❓ {player} opens the Mystery Box...")
            
            if outcome == "HEAL":
                self.health[player] += 2
                self.custom_log(f"💖 Miracle! +2 HP!")
                self._trigger_event("heal", target=player, amount=2)
            elif outcome == "HURT":
                self.health[player] -= 1
                self.custom_log(f"💥 Trap! -1 HP!")
                self._trigger_event("damage", target=player, amount=1, source=player)
                if self.health[player] <= 0:
                     self.custom_log(random.choice(CINEMATIC_DEATH).format(player))
                     self.alive.remove(player)
                     self._trigger_event("death", player=player)
                     self._check_round_over()
            elif outcome == "LOOT":
                loot = [random.choice(ALL_ITEMS) for _ in range(2)]
                self.items[player].extend(loot)
                self.custom_log(f"🎁 Jackpot! Found {loot}!")
            elif outcome == "RELOAD":
                self.custom_log(f"🔄 The box contained... a new gun?")
                self.new_round_deck()


    def get_state(self, requesting_player=None):
        visible_logs = []
        for log in self.logs:
            if log['visible_to'] is None:
                visible_logs.append(log['text'])
            elif requesting_player and requesting_player in log['visible_to']:
                visible_logs.append(log['text'])
        
        visible_logs = visible_logs[-20:]

        live_count = self.deck.count(BUST)
        blank_count = self.deck.count(SAFE)

        return {
            "players": self.alive,
            "current_player": self.current(),
            "health": self.health,
            "max_health": self.player_max_health,
            "items": self.items,
            "classes": self.player_classes,
            "logs": visible_logs,
            "game_over": len(self.alive) <= 1 and self.round_num >= self.max_rounds,
            "round_winner": self.round_winner,
            "winner": self.alive[0] if len(self.alive) == 1 else None,
            "deck_count": len(self.deck),
            "live_count": live_count,
            "blank_count": blank_count,
            "round": self.round_num,
            "max_rounds": self.max_rounds,
            "blackout_next": self.blackout_for,
            "modifier": self.current_modifier,
            "events": self.events,
            "stats": self.stats if len(self.alive) <= 1 and self.round_num >= self.max_rounds else None,
            "prize_pool": self.prize_pool
        }

