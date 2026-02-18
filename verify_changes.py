import sys
import io

# Fix Windows encoding issues for verification script output
# (Handled by Buck_roulette import)

from Buck_roulette import CasinoGame, ITEM_DIAMOND, ITEM_HEAL, MODE_SAFE

def test_changes():
    print("--- Starting Verification ---")
    game = CasinoGame(["Tester", "Dummy"])
    
    # 1. Test Safeshot Self-Targeting
    p1 = game.players[0]
    p2 = game.players[1]
    
    # Ensure p1 is current
    game.turn = 0 
    
    initial_health = game.health[p1]
    print(f"\n[Test 1] Safeshot Self-Targeting")
    print(f"Initial Health: {initial_health}")
    
    # Force a SAFE card at top of deck to avoid round passing if empty
    game.deck.insert(0, "Blank round")
    
    # Execute draw safe on self
    game.draw(p1, MODE_SAFE)
    
    if game.health[p1] == initial_health - 1:
        print("PASS: Player took 1 damage from self-shot.")
    else:
        print(f"FAIL: Health is {game.health[p1]}, expected {initial_health - 1}")

    # 2. Test Diamond Item
    print(f"\n[Test 2] Diamond Item Logic")
    
    # Setup inventories
    game.items[p1] = [ITEM_DIAMOND]
    game.items[p2] = [ITEM_HEAL, ITEM_HEAL, "Soda"]
    
    print(f"{p1} items: {game.items[p1]}")
    print(f"{p2} items: {game.items[p2]}")
    
    # Use Diamond to get Cigarette (ITEM_HEAL)
    # The use signature for Diamond expects target to be the desired item name
    game.turn = 0 # Ensure it's p1's turn
    game.use(ITEM_DIAMOND, ITEM_HEAL)
    
    print(f"--- After Use ---")
    print(f"{p1} items: {game.items[p1]}")
    print(f"{p2} items: {game.items[p2]}")
    
    if ITEM_HEAL in game.items[p1] and ITEM_HEAL not in game.items[p2]:
        print("PASS: Obtained item and wiped from opponent.")
    else:
        print("FAIL: Item logic incorrect.")

if __name__ == "__main__":
    test_changes()
