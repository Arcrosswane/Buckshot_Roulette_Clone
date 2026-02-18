from flask import Flask, render_template, jsonify, request
from game_engine import CasinoGameEngine, ITEM_STEAL, ITEM_DIAMOND

app = Flask(__name__)

# Global state
game = None
lobby = [] # List of player names
game_started = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/join', methods=['POST'])
def join_lobby():
    global lobby, game_started
    if game_started:
        return jsonify({"error": "Game already in progress"}), 400
    
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"error": "Name required"}), 400
    
    if len(lobby) >= 8:
        return jsonify({"error": "Lobby full (max 8)"}), 400
        
    if name in lobby:
        # Check if rejoining? Just return success
        return jsonify({"message": "Joined", "name": name, "lobby": lobby}) 
        
    lobby.append(name)
    return jsonify({"message": "Joined", "name": name, "lobby": lobby})

@app.route('/api/lobby')
def get_lobby():
    return jsonify({"lobby": lobby, "started": game_started})

@app.route('/api/start', methods=['POST'])
def start_game():
    global game, game_started, lobby
    if len(lobby) < 2:
        return jsonify({"error": "Need at least 2 players"}), 400
        
    game = CasinoGameEngine(lobby)
    game_started = True
    return jsonify({"status": "started", "message": "Game initialized"})

@app.route('/api/reset', methods=['POST'])
def reset_game():
    global game, game_started, lobby
    game = None
    game_started = False
    lobby = []
    # Could imply we want to restart completely.
    return jsonify({"status": "reset"})

@app.route('/api/next_round', methods=['POST'])
def next_round():
    global game
    if not game:
        return jsonify({"error": "No game"}), 404
    
    success = game.start_next_round()
    if success:
         return jsonify({"status": "next_round", "round": game.round_num})
    else:
         return jsonify({"status": "game_over", "winner": game.alive[0] if game.alive else "Nobody"})

@app.route('/api/state')
def get_state():
    global game
    if not game:
        if game_started: # Should imply game exists, but maybe just started
             return jsonify({"error": "Game loading..."}), 202
        return jsonify({"error": "No game running"}), 404
    
    player_name = request.args.get('player') # For private logs
    
    # State filtered for this player
    state = game.get_state(requesting_player=player_name)
    
    state["turn_player"] = game.current()
    state["is_my_turn"] = (game.current() == player_name)
    
    return jsonify(state)

@app.route('/api/action', methods=['POST'])
def perform_action():
    global game
    if not game:
        return jsonify({"error": "No game running"}), 404
    
    data = request.json
    action_type = data.get('type')
    
    player = game.current()
    if not player:
        return jsonify({"status": "game_over"}), 400

    if action_type == 'draw':
        target = data.get('target')
        mode = data.get('mode', 'safe')
        game.run_draw(target, mode)
    
    elif action_type == 'use':
        item = data.get('item')
        target = data.get('target')
        item_to_steal = data.get('steal_item')
        game.run_use(item, target, item_to_steal)

    return jsonify({"status": "success", "state": game.get_state()})

@app.route('/api/ai', methods=['POST'])
def trigger_ai():
    global game
    if not game: return jsonify({"error": "No game"}), 404
    
    current = game.current()
    # Simple check if current player name contains "Auto" or "Bot"
    if "Auto" in current or "Bot" in current:
        game.ai_turn(current)
        return jsonify({"status": "ai_moved"})
    
    return jsonify({"status": "waiting_for_human"})

if __name__ == '__main__':
    # Host 0.0.0.0 for LAN access
    app.run(debug=True, host='0.0.0.0', port=5000)
