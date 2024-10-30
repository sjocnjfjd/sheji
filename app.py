from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import os
import json
import random
import time
from dataclasses import dataclass, asdict
from typing import List, Dict

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
socketio = SocketIO(app)

# 游戏状态类
@dataclass
class GameState:
    ships: Dict = None  # 存储所有玩家的飞船
    aliens: List = None  # 外星人列表 
    bullets: List = None  # 子弹列表
    power_ups: List = None  # 道具列表
    scores: Dict = None  # 玩家分数
    game_active: bool = False
    game_mode: str = None
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.ships = {}
        self.aliens = []
        self.bullets = []
        self.power_ups = []
        self.scores = {}
        self.game_active = False
        self.game_mode = None

# 全局游戏状态
game_state = GameState()

@app.route('/')
def index():
    return render_template('game.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('gameState', asdict(game_state))

@socketio.on('startGame')
def handle_start_game(data):
    mode = data.get('mode', 'endless')
    game_state.game_mode = mode
    game_state.game_active = True
    game_state.reset()
    
    # 初始化玩家飞船
    player_id = request.sid
    game_state.ships[player_id] = {
        'x': 600,
        'y': 700,
        'health': 3,
        'power_ups': {}
    }
    game_state.scores[player_id] = 0
    
    emit('gameStarted', {'mode': mode, 'playerId': player_id}, broadcast=True)
    start_game_loop()

@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    if player_id in game_state.ships:
        del game_state.ships[player_id]
    if player_id in game_state.scores:
        del game_state.scores[player_id]

@socketio.on('playerMove')
def handle_player_move(data):
    player_id = request.sid
    if player_id in game_state.ships:
        ship = game_state.ships[player_id]
        ship['x'] = data['x']
        ship['y'] = data['y']
        emit('gameState', asdict(game_state), broadcast=True)

@socketio.on('playerShoot')
def handle_player_shoot():
    player_id = request.sid
    if player_id in game_state.ships:
        ship = game_state.ships[player_id]
        bullet = {
            'x': ship['x'],
            'y': ship['y'] - 20,
            'player_id': player_id
        }
        game_state.bullets.append(bullet)
        emit('gameState', asdict(game_state), broadcast=True)

def start_game_loop():
    """启动游戏主循环"""
    def game_loop():
        while game_state.game_active:
            update_game_state()
            emit('gameState', asdict(game_state), broadcast=True)
            socketio.sleep(0.016)  # ~60 FPS
    
    socketio.start_background_task(game_loop)

def update_game_state():
    """更新游戏状态"""
    # 更新子弹位置
    for bullet in game_state.bullets[:]:
        bullet['y'] -= 5
        if bullet['y'] < 0:
            game_state.bullets.remove(bullet)
    
    # 生成新的外星人
    if random.random() < 0.02:  # 2%概率生成新外星人
        alien = {
            'x': random.randint(0, 1150),
            'y': -50,
            'health': random.randint(2, 4),
            'type': random.randint(1, 3)
        }
        game_state.aliens.append(alien)
    
    # 更新外星人位置
    for alien in game_state.aliens[:]:
        alien['y'] += 2
        if alien['y'] > 800:
            game_state.aliens.remove(alien)
    
    # 检测碰撞
    check_collisions()

def check_collisions():
    """检查所有碰撞"""
    # 子弹与外星人的碰撞
    for bullet in game_state.bullets[:]:
        for alien in game_state.aliens[:]:
            if check_collision(bullet, alien):
                alien['health'] -= 1
                if alien['health'] <= 0:
                    game_state.aliens.remove(alien)
                    if bullet['player_id'] in game_state.scores:
                        game_state.scores[bullet['player_id']] += 50
                game_state.bullets.remove(bullet)
                break

    # 外星人与飞船的碰撞
    for alien in game_state.aliens[:]:
        for player_id, ship in game_state.ships.items():
            if check_collision(alien, ship):
                ship['health'] -= 1
                game_state.aliens.remove(alien)
                if ship['health'] <= 0:
                    end_game(player_id)
                break

def check_collision(obj1, obj2):
    """简单的矩形碰撞检测"""
    return (abs(obj1['x'] - obj2['x']) < 40 and 
            abs(obj1['y'] - obj2['y']) < 40)

def end_game(player_id):
    """结束游戏"""
    game_state.game_active = False
    emit('gameOver', {
        'scores': game_state.scores,
        'winner': max(game_state.scores.items(), key=lambda x: x[1])[0]
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)