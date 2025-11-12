"""
Efeitos climáticos utilizados nas telas do jogo.

O módulo define:
- Snowflake: partículas individuais que caem com leve deslocamento de vento.
- WindOverlay: névoa translúcida composta por rajadas horizontais.
"""

import math
import random
import pygame
from constants import SCREEN_W, SCREEN_H

class Snowflake:
    """Representa um floco de neve que cai com leve efeito de vento."""
    def __init__(self):
        self.x = random.uniform(0, SCREEN_W)
        self.y = random.uniform(-SCREEN_H, 0)
        self.size = random.randint(2, 5)
        self.speed = random.uniform(40, 120)
        self.wind = random.uniform(-20, 20)  # deslocamento horizontal leve

    def update(self, dt):
        """Atualiza a posição com base no tempo e vento."""
        self.y += self.speed * dt
        self.x += self.wind * dt

        # Oscilação leve (simula vento turbulento)
        self.x += 15 * dt * random.uniform(-1, 1)

        # reaparecer no topo quando sair da tela
        if self.y > SCREEN_H:
            self.y = random.uniform(-20, -5)
            self.x = random.uniform(0, SCREEN_W)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size)

class WindOverlay:
    """Névoa translúcida em movimento lateral simulando vento."""
    def __init__(self):
        self.surface = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.gusts = [self._create_gust() for _ in range(12)]

    def _create_gust(self):
        width = random.randint(220, 360)
        height = random.randint(50, 100)
        base_alpha = random.randint(28, 58)
        gust_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        # Desenha elipses concêntricas para um gradiente suave
        for i in range(4):
            shrink = i * 6
            alpha = max(6, base_alpha - i * 6)
            pygame.draw.ellipse(
                gust_surface,
                (220, 230, 255, alpha),
                (shrink, shrink, width - shrink * 2, height - shrink * 2)
            )
        return {
            "x": random.uniform(-SCREEN_W, SCREEN_W),
            "base_y": random.uniform(60, SCREEN_H - 60),
            "y": 0.0,
            "width": width,
            "height": height,
            "speed": random.uniform(60, 140),
            "amplitude": random.uniform(10, 30),
            "sway_speed": random.uniform(0.8, 1.6),
            "sway_phase": random.uniform(0, math.tau),
            "surface": gust_surface,
        }

    def update(self, dt):
        for gust in self.gusts:
            gust["x"] += gust["speed"] * dt
            gust["sway_phase"] += gust["sway_speed"] * dt
            gust["y"] = gust["base_y"] + math.sin(gust["sway_phase"]) * gust["amplitude"]
            if gust["x"] - gust["width"] > SCREEN_W:
                gust["x"] = -gust["width"] - random.uniform(0, SCREEN_W * 0.3)
                gust["base_y"] = random.uniform(60, SCREEN_H - 60)
                gust["sway_phase"] = random.uniform(0, math.tau)

    def draw(self, screen):
        self.surface.fill((0, 0, 0, 0))
        for gust in self.gusts:
            self.surface.blit(gust["surface"], (gust["x"], gust["y"] - gust["height"] // 2))
        screen.blit(self.surface, (0, 0))
