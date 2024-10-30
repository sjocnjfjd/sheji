class Game {
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
            .join('\n');
            
        alert(`${message}\n\n${scoreText}`);
        
        // 重置游戏状态
        this.gameState = null;
        this.playerId = null;
    }
}

// 初始化游戏
window.onload = () => {
    const game = new Game();
};