"""
Módulo Enemy — define a classe `Enemy` usada no jogo Pygame.

Funções principais:
- Movimento dos inimigos em direção ao jogador.
- Ataque corpo-a-corpo com cooldown.
- Recebimento de dano e knockback.
- Animação de morte com partículas e fade-out.
- Renderização com sprite (se disponível) ou fallback colorido com barra de HP.

Depende de:
- constantes.py (ENEMY_SIZE, ENEMY_SPEED, etc.)
- pygame.Rect, pygame.Surface
"""

import pygame
import math
import random
from constants import *
from typing import Optional


class Enemy:
    """
    Representa um inimigo comum no jogo.

    Cada inimigo persegue o jogador, causa dano ao se aproximar, 
    e produz um efeito de partículas quando morre. 
    Pode carregar um sprite (imagem) ou usar um círculo colorido como fallback.
    """

    def __init__(self, x: float, y: float, wave: int = 1):
        """
        Inicializa um inimigo na posição (x, y), ajustando HP e velocidade com base na wave atual.

        Args:
            x, y (float): coordenadas iniciais do inimigo.
            wave (int): número da wave, afeta HP e velocidade.
        """
        # Carregar imagem do inimigo (apenas uma vez para otimizar)
        if not hasattr(Enemy, "_image_loaded"):
            Enemy._image_loaded = False
            Enemy._image_surface = None
            loaded = pygame.image.load(ENEMY_IMAGE_FILE).convert_alpha()
            Enemy._image_surface = pygame.transform.smoothscale(loaded, (ENEMY_SIZE, ENEMY_SIZE))
            Enemy._image_loaded = True

        # Atributos principais
        self.x = x
        self.y = y
        self.max_hp = ENEMY_HP + (wave - 1) * 30
        self.hp = self.max_hp
        self.speed = ENEMY_SPEED + (wave - 1) * 5
        self.damage = ENEMY_DAMAGE
        self.last_attack = 0.0
        self.attack_cooldown = 1.0
        self.rect = pygame.Rect(int(x - ENEMY_SIZE//2), int(y - ENEMY_SIZE//2), ENEMY_SIZE, ENEMY_SIZE)

        # Estado de morte e partículas
        self.is_dead_flag = False
        self.death_timer = 0.0
        self.fade_duration = 0.8
        self.death_particles = []

        # Knockback (recuo após dano)
        self.knockback_x = 0.0
        self.knockback_y = 0.0
        self.knockback_decay = 8.0

        # Flag de imagem carregada
        self.image_available = getattr(Enemy, "_image_loaded", False)

    def update(self, dt: float, player, walls):
        """
        Atualiza posição e estado do inimigo.

        - Se morto, apenas acumula tempo de fade.
        - Caso vivo, move-se em direção ao jogador com checagem de colisão e aplica amortecimento de knockback.

        Args:
            dt (float): delta de tempo entre frames.
            player: objeto jogador com .x, .y.
            walls (list[pygame.Rect]): obstáculos no mapa.
        """
        if self.is_dead_flag:
            self.death_timer += dt
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            dx = (dx / dist) * self.speed * dt
            dy = (dy / dist) * self.speed * dt

            # Aplicar knockback residual
            dx += self.knockback_x * dt
            dy += self.knockback_y * dt
            self.knockback_x -= self.knockback_x * self.knockback_decay * dt
            self.knockback_y -= self.knockback_y * self.knockback_decay * dt

            new_x = self.x + dx
            new_y = self.y + dy

            new_rect = pygame.Rect(new_x - ENEMY_SIZE//2, new_y - ENEMY_SIZE//2, ENEMY_SIZE, ENEMY_SIZE)
            if not any(new_rect.colliderect(w) for w in walls):
                self.x = new_x
                self.y = new_y
                self.rect.center = (int(self.x), int(self.y))

    def attack(self, player, current_time: float):
        """
        Tenta atacar o jogador se estiver próximo e se o cooldown tiver acabado.

        Args:
            player: jogador com método take_damage().
            current_time (float): tempo atual do jogo (em segundos).
        """
        if self.is_dead_flag:
            return
        if math.hypot(player.x - self.x, player.y - self.y) <= 30 and (current_time - self.last_attack) >= self.attack_cooldown:
            player.take_damage(self.damage)
            self.last_attack = current_time

    def take_damage(self, damage: int, angle: Optional[float] = None):
        """
        Aplica dano ao inimigo, gera partículas e aplica knockback se um ângulo for informado.

        Args:
            damage (int): dano recebido.
            angle (float|None): ângulo (radianos) de onde veio o ataque.
        """
        if self.is_dead_flag:
            return
        self.hp = max(0, self.hp - damage)
        if angle is not None:
            self.knockback_x = math.cos(angle) * 300
            self.knockback_y = math.sin(angle) * 300

        # Partícula de impacto
        self.death_particles.append({"x": self.x, "y": self.y, "radius": 6, "life": 0.3, "color": (255, 255, 0)})

        if self.hp <= 0:
            self.die()

    def die(self):
        """
        Marca o inimigo como morto e gera partículas de explosão.

        - Define o início do fade-out.
        - Cria 10 partículas com movimento aleatório.
        """
        self.is_dead_flag = True
        self.death_timer = 0.0
        for _ in range(10):
            self.death_particles.append({
                "x": self.x, "y": self.y,
                "radius": random.randint(3, 6),
                "vx": random.uniform(-150, 150),
                "vy": random.uniform(-150, 150),
                "life": random.uniform(0.4, 0.8),
                "color": (255, random.randint(100, 200), 0)
            })

    def is_dead(self) -> bool:
        """
        Retorna True quando o inimigo já morreu e completou o tempo de fade.

        Returns:
            bool: True se o inimigo deve ser removido.
        """
        return self.is_dead_flag and self.death_timer >= self.fade_duration

    def draw(self, screen):
        """
        Renderiza o inimigo na tela.

        - Se morto, exibe partículas e efeito de fade-out.
        - Caso vivo, desenha sprite ou círculo colorido proporcional ao HP.
        - Inclui uma barra de HP acima do inimigo.
        """
        # Atualizar partículas
        for p in self.death_particles[:]:
            p["x"] += p.get("vx", 0) * 0.016
            p["y"] += p.get("vy", 0) * 0.016
            p["life"] -= 0.016
            if p["life"] <= 0:
                self.death_particles.remove(p)
            else:
                pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), max(1, int(p["radius"])))

        # Render de fade-out
        if self.is_dead_flag:
            alpha = max(0, 255 * (1 - self.death_timer / self.fade_duration))
            surface = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(surface, (255, 50, 0, int(alpha)), (ENEMY_SIZE//2, ENEMY_SIZE//2), ENEMY_SIZE//2)
            screen.blit(surface, (self.x - ENEMY_SIZE//2, self.y - ENEMY_SIZE//2))
            return

        # Sprite ou fallback colorido
        img = getattr(Enemy, "_image_surface", None)
        if self.image_available and img is not None:
            rect = img.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(img, rect)
        else:
            ratio = self.hp / self.max_hp
            color = (int(255 * (1 - ratio)), int(255 * ratio), 0)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), ENEMY_SIZE//2)

        # Barra de HP
        bar_w, bar_h = 30, 4
        bar_x = self.x - bar_w//2
        bar_y = self.y - ENEMY_SIZE//2 - 10
        pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        health_w = int((self.hp / self.max_hp) * bar_w)
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_w, bar_h))