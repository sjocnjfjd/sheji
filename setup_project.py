import os
import shutil

def setup_project():
    # 1. 创建目录结构
    directories = [
        'static/css',
        'static/js',
        'static/images',
        'static/sounds',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

    # 2. 创建并写入所有文件
    files = {
        'app.py': app_code,
        'static/css/style.css': css_content,
        'static/js/game.js': js_content,
        'templates/base.html': base_html,
        'templates/game.html': game_html,
        'requirements.txt': requirements,
        'Dockerfile': dockerfile,
        '.gitignore': gitignore,
        'Procfile': 'web: gunicorn --worker-class eventlet -w 1 app:app'
    }
    
    for file_path, content in files.items():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created file: {file_path}")

    # 3. 复制资源文件
    try:
        # 复制图片文件
        source_images = '../images'
        if os.path.exists(source_images):
            for file in os.listdir(source_images):
                if file.endswith(('.png', '.bmp')):
                    shutil.copy2(
                        os.path.join(source_images, file),
                        'static/images/'
                    )
                    print(f"Copied image: {file}")
        else:
            print("Warning: Images directory not found")

        # 复制音效文件
        source_sounds = '../yinxiao'
        if os.path.exists(source_sounds):
            for file in os.listdir(source_sounds):
                if file.endswith('.wav'):
                    shutil.copy2(
                        os.path.join(source_sounds, file),
                        'static/sounds/'
                    )
                    print(f"Copied sound: {file}")
        else:
            print("Warning: Sounds directory not found")

    except Exception as e:
        print(f"Error copying assets: {e}")

    print("\nProject setup completed!")
    print("\nNext steps:")
    print("1. Check if all files were created correctly")
    print("2. Initialize git repository")
    print("3. Make initial commit")
    print("4. Push to GitHub")

# 文件内容定义
app_code = '''from flask import Flask, render_template, jsonify, request
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
    socketio.run(app, debug=True)'''

css_content = '''body {
    margin: 0;
    padding: 0;
    background: #1a1a1a;
    color: white;
    font-family: Arial, sans-serif;
}

.game-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    min-height: 100vh;
}

#gameCanvas {
    border: 2px solid #333;
    background: #000;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
    margin-bottom: 20px;
}

.controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 15px;
}

.mode-buttons {
    display: flex;
    gap: 15px;
}

button {
    padding: 12px 24px;
    font-size: 16px;
    cursor: pointer;
    border: none;
    border-radius: 5px;
    transition: all 0.3s ease;
    text-transform: uppercase;
    font-weight: bold;
}

#startButton {
    background: #4CAF50;
    color: white;
}

#endlessMode {
    background: #2196F3;
    color: white;
}

#featureMode {
    background: #FF9800;
    color: white;
}

#twoPlayerMode {
    background: #E91E63;
    color: white;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

button:active {
    transform: translateY(0);
}

.game-over {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.9);
    padding: 30px;
    border-radius: 10px;
    text-align: center;
    display: none;
}

.game-over.show {
    display: block;
}'''

js_content = '''class Game {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = 1200;
        this.canvas.height = 800;
        
        this.socket = io();
        this.playerId = null;
        this.gameState = null;
        this.images = {};
        
        this.keys = {
            ArrowLeft: false,
            ArrowRight: false,
            ArrowUp: false,
            ArrowDown: false,
            Space: false
        };
        
        this.setupSocketEvents();
        this.setupControls();
        this.loadAssets();
    }

    loadAssets() {
        const imageFiles = {
            ship: 'ship.png',
            alien1: 'guaiwu1.png',
            alien2: 'guaiwu2.png',
            alien3: 'guaiwu3.png',
            bullet: 'xiaozidan.png',
            explosion: 'baozha.png',
            powerup1: 'zidan.png',
            powerup2: 'jiasu.png',
            powerup3: 'hudun.png'
        };
        
        Object.entries(imageFiles).forEach(([key, file]) => {
            const img = new Image();
            img.src = `/static/images/${file}`;
            img.onload = () => {
                this.images[key] = img;
            };
        });
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('gameStarted', (data) => {
            this.playerId = data.playerId;
            this.gameMode = data.mode;
            console.log('Game started:', data);
        });

        this.socket.on('gameState', (state) => {
            this.gameState = state;
            this.render();
        });

        this.socket.on('gameOver', (data) => {
            this.handleGameOver(data);
        });
    }

    setupControls() {
        document.addEventListener('keydown', (e) => {
            if (this.keys.hasOwnProperty(e.code)) {
                this.keys[e.code] = true;
                this.sendPlayerMove();
            }
            if (e.code === 'Space') {
                this.socket.emit('playerShoot');
            }
        });

        document.addEventListener('keyup', (e) => {
            if (this.keys.hasOwnProperty(e.code)) {
                this.keys[e.code] = false;
                this.sendPlayerMove();
            }
        });

        // 设置游戏模式按钮
        ['endlessMode', 'featureMode', 'twoPlayerMode'].forEach(mode => {
            document.getElementById(mode).addEventListener('click', () => {
                this.socket.emit('startGame', { mode: mode.replace('Mode', '') });
            });
        });
    }

    sendPlayerMove() {
        if (!this.gameState?.ships?.[this.playerId]) return;
        
        const ship = this.gameState.ships[this.playerId];
        let x = ship.x;
        let y = ship.y;
        
        if (this.keys.ArrowLeft) x -= 5;
        if (this.keys.ArrowRight) x += 5;
        if (this.keys.ArrowUp) y -= 5;
        if (this.keys.ArrowDown) y += 5;
        
        // 边界检查
        x = Math.max(0, Math.min(x, this.canvas.width - 50));
        y = Math.max(0, Math.min(y, this.canvas.height - 50));
        
        this.socket.emit('playerMove', { x, y });
    }

    render() {
        if (!this.gameState) return;
        
        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制所有游戏元素
        this.drawShips();
        this.drawAliens();
        this.drawBullets();
        this.drawPowerUps();
        this.drawUI();
    }

    drawShips() {
        const shipImg = this.images.ship;
        if (!shipImg) return;
        
        Object.entries(this.gameState.ships).forEach(([id, ship]) => {
            this.ctx.drawImage(shipImg, ship.x, ship.y, 50, 50);
            this.drawHealthBar(ship);
        });
    }

    drawAliens() {
        this.gameState.aliens.forEach(alien => {
            const alienImg = this.images[`alien${alien.type}`];
            if (alienImg) {
                this.ctx.drawImage(alienImg, alien.x, alien.y, 50, 50);
                this.drawHealthBar(alien);
            }
        });
    }

    drawBullets() {
        const bulletImg = this.images.bullet;
        if (!bulletImg) return;
        
        this.gameState.bullets.forEach(bullet => {
            this.ctx.drawImage(bulletImg, bullet.x, bullet.y, 10, 20);
        });
    }

    drawPowerUps() {
        this.gameState.power_ups.forEach(powerup => {
            const powerupImg = this.images[`powerup${powerup.type}`];
            if (powerupImg) {
                this.ctx.drawImage(powerupImg, powerup.x, powerup.y, 30, 30);
            }
        });
    }

    drawHealthBar(entity) {
        const width = 50;
        const height = 5;
        const x = entity.x;
        const y = entity.y - 10;
        
        // 背景
        this.ctx.fillStyle = 'red';
        this.ctx.fillRect(x, y, width, height);
        
        // 血量
        const healthPercent = entity.health / (entity.maxHealth || 3);
        this.ctx.fillStyle = 'green';
        this.ctx.fillRect(x, y, width * healthPercent, height);
    }

    drawUI() {
        // 分数
        this.ctx.fillStyle = 'white';
        this.ctx.font = '24px Arial';
        Object.entries(this.gameState.scores).forEach(([id, score], index) => {
            const text = id === this.playerId ? `Your Score: ${score}` : `Player ${index + 1}: ${score}`;
            this.ctx.fillText(text, 10, 30 + index * 30);
        });
    }

    handleGameOver(data) {
        const isWinner = data.winner === this.playerId;
        
        // 显示游戏结束对话框
        const message = isWinner ? 'You Win!' : 'Game Over';
        const scoreText = Object.entries(data.scores)
            .map(([id, score]) => `${id === this.playerId ? 'You' : 'Player'}: ${score}`)
            .join('\\n');
            
        alert(`${message}\\n\\n${scoreText}`);
        
        // 重置游戏状态
        this.gameState = null;
        this.playerId = null;
    }
}

// 初始化游戏
window.onload = () => {
    const game = new Game();
};'''

base_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Alien Invasion</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    {% block content %}{% endblock %}
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="{{ url_for('static', filename='js/game.js') }}"></script>
</body>
</html>'''

game_html = '''{% extends "base.html" %}

{% block content %}
<div class="game-container">
    <canvas id="gameCanvas"></canvas>
    <div class="controls">
        <button id="startButton">Start Game</button>
        <div class="mode-buttons">
            <button id="endlessMode">Endless Mode</button>
            <button id="featureMode">Feature Mode</button>
            <button id="twoPlayerMode">Two Player Mode</button>
        </div>
    </div>
</div>
{% endblock %}'''

requirements = '''Flask==2.0.1
Flask-SocketIO==5.1.1
python-socketio==5.3.0
python-engineio==4.2.1
gunicorn==20.1.0
eventlet==0.33.0
Werkzeug==2.0.1'''

dockerfile = '''FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD gunicorn --worker-class eventlet -w 1 app:app'''

gitignore = '''__pycache__/
*.pyc
venv/
.env'''

if __name__ == '__main__':
    setup_project() 