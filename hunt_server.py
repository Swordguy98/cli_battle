import socket
import threading
import json
import random

class GameServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.players = {}
        self.grid_size = 20
        self.game_state = {
            'player1': {'x': 0, 'y': 0, 'direction': 'right'},
            'player2': {'x': 19, 'y': 19, 'direction': 'left'}
        }
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(2)
        print(f"Server started on port {self.port}")
        
        while len(self.players) < 2:
            conn, addr = server.accept()
            player_id = f"player{len(self.players) + 1}"
            self.players[player_id] = conn
            threading.Thread(target=self.handle_player, args=(conn, player_id)).start()
            
    def handle_player(self, conn, player_id):
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                    
                command = data.lower()
                pos = self.game_state[player_id]
                
                # Handle movement
                if command == 'w' and pos['y'] > 0:
                    pos['y'] -= 1
                    pos['direction'] = 'up'
                elif command == 's' and pos['y'] < self.grid_size - 1:
                    pos['y'] += 1
                    pos['direction'] = 'down'
                elif command == 'a' and pos['x'] > 0:
                    pos['x'] -= 1
                    pos['direction'] = 'left'
                elif command == 'd' and pos['x'] < self.grid_size - 1:
                    pos['x'] += 1
                    pos['direction'] = 'right'
                elif command == 'space':  # Shooting
                    if self.handle_shot(player_id):
                        self.broadcast(f"{player_id} wins!")
                        break
                
                # Check for collision
                other_player = 'player2' if player_id == 'player1' else 'player1'
                if (pos['x'] == self.game_state[other_player]['x'] and 
                    pos['y'] == self.game_state[other_player]['y']):
                    self.broadcast(f"{player_id} wins!")
                    break
                
                self.broadcast_state()
                
        except:
            pass
        finally:
            conn.close()
            del self.players[player_id]
            
    def handle_shot(self, player_id):
        pos = self.game_state[player_id].copy()
        direction = pos['direction']
        other_player = 'player2' if player_id == 'player1' else 'player1'
        
        # Calculate shot trajectory
        while True:
            if direction == 'up':
                pos['y'] -= 1
            elif direction == 'down':
                pos['y'] += 1
            elif direction == 'left':
                pos['x'] -= 1
            elif direction == 'right':
                pos['x'] += 1
                
            # Check if shot is out of bounds
            if (pos['x'] < 0 or pos['x'] >= self.grid_size or 
                pos['y'] < 0 or pos['y'] >= self.grid_size):
                return False
                
            # Check if shot hits other player
            if (pos['x'] == self.game_state[other_player]['x'] and 
                pos['y'] == self.game_state[other_player]['y']):
                return True
                
    def broadcast_state(self):
        for player_id, conn in self.players.items():
            try:
                conn.send(json.dumps(self.game_state).encode())
            except:
                pass
                
    def broadcast(self, message):
        for conn in self.players.values():
            try:
                conn.send(message.encode())
            except:
                pass

if __name__ == '__main__':
    server = GameServer()
    server.start() 