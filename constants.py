"""
Módulo de constantes do jogo (Pygame).

Contém:
- Dimensões de tela, FPS e parâmetros do jogador.
- Parâmetros dos projéteis e inimigos.
- Paleta de cores RGB usada pelo render.
- Caminhos de áudio e imagens (sprites/power-ups).

Observação: este arquivo não tem lógica executável; serve apenas como
ponto único de configuração para balanceamento e assets.
"""

# CONSTANTES SIMPLIFICADAS
SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

# Jogador
PLAYER_SPEED = 200
PLAYER_SIZE = 30
PLAYER_HP = 100

# Projéteis
BULLET_SPEED = 400
BULLET_SIZE = 4
BULLET_DAMAGE = 25
BULLET_RANGE = 300
FIRE_RATE = 0.15

# Inimigos
ENEMY_SIZE = 25
ENEMY_SPEED = 80
ENEMY_HP = 50
ENEMY_DAMAGE = 20 
ENEMY_SPAWN_RATE = 1.0

# Cores (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
PURPLE = (160, 32, 240)
CYAN = (0, 200, 200)
ORANGE = (255, 140, 0)

# Áudio
"""
Caminhos de arquivos de áudio:
- POWER_UP_SOUND_FILE: sfx ao pegar power-up
- GUNSHOT_SOUND_FILE: sfx de disparo
- BACKGROUND_MUSIC_FILE: trilha sonora em loop
"""
POWER_UP_SOUND_FILE = "power-up-type-1-230548.mp3"
GUNSHOT_SOUND_FILE = "gunshot-352466.mp3"
BACKGROUND_MUSIC_FILE = "game-minecraft-gaming-background-music-402451.mp3"

# Imagens
"""
Sprites e ícones:
- ENEMY_IMAGE_FILE: sprite do inimigo comum.
- POWER_UP_IMAGE_FILES: dicionário que mapeia tipo de power-up -> arquivo PNG correspondente.
"""
ENEMY_IMAGE_FILE = "inimigo comum.png"
POWER_UP_IMAGE_FILES = {
    "health": "powerup_v4_health_boost_256.png",
    "armor": "powerup_v4_armour_256.png",
    "regen": "powerup_v4_health_recovery_256.png",
}