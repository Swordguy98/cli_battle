import socket
import json
import sys
import termios
import tty
import threading

class GameClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            print("Connected to server!")
            return True
        except:
            print("Couldn't connect to server")
            return False
            
    def get_char(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
        
    def receive_updates(self):
        while self.running:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                    
                try:
                    game_state = json.loads(data)
                    self.draw_game(game_state)
                except json.JSONDecodeError:
                    print("\n" + data)  # Print server messages (like win notifications)
                    self.running = False
                    break
            except:
                break
                
    def draw_game(self, game_state):
        # Clear screen (works on Unix-like systems)
        print("\033[H\033[J")
        
        player_pos = None
        other_pos = None
        
        # Determine which player we are
        if self.socket.getsockname() < self.socket.getpeername():
            player_pos = game_state['player1']
            other_pos = game_state['player2']
        else:
            player_pos = game_state['player2']
            other_pos = game_state['player1']
            
        # Draw only visible area (5x5 grid around player)
        visible_range = 2
        
        for y in range(max(0, player_pos['y'] - visible_range),
                      min(20, player_pos['y'] + visible_range + 1)):
            for x in range(max(0, player_pos['x'] - visible_range),
                         min(20, player_pos['x'] + visible_range + 1)):
                if x == player_pos['x'] and y == player_pos['y']:
                    # Show direction with arrows
                    direction_chars = {
                        'up': '↑', 'down': '↓',
                        'left': '←', 'right': '→'
                    }
                    print(direction_chars[player_pos['direction']], end=' ')
                elif x == other_pos['x'] and y == other_pos['y']:
                    print('E', end=' ')
                else:
                    print('.', end=' ')
            print()
            
        print("\nUse WASD to move. SPACE to shoot. Q to quit.")
        
    def start(self):
        if not self.connect():
            return
            
        # Start receive thread
        threading.Thread(target=self.receive_updates).start()
        
        # Main game loop
        while self.running:
            char = self.get_char()
            if char.lower() == 'q':
                break
            if char.lower() in ['w', 'a', 's', 'd']:
                self.socket.send(char.encode())
            elif char == ' ':  # Space key
                self.socket.send('space'.encode())
                
        self.running = False
        self.socket.close()

if __name__ == '__main__':
    client = GameClient()
    client.start() 