"""
Módulo de projéteis para um jogo em Pygame.

Classes:
- Bullet: projétil padrão do jogador com alcance finito baseado em tempo de vida.
- BossBullet: projétil simples usado por bosses; desaparece ao colidir com paredes ou sair da tela.
- SplitterBullet: projétil grande que percorre uma distância e então se divide em 5 BossBullets.

Constantes esperadas de `constants`:
- SCREEN_W, SCREEN_H e cores (YELLOW, PURPLE, ORANGE), entre outras.
"""

import pygame
import math
from constants import *
from typing import Optional


class Bullet:
    """Projétil básico do jogador, com dano, velocidade e tempo de vida (alcance) derivado de range/speed."""

    def __init__(self, x: float, y: float, angle: float, damage: int, speed: float, range_val: float, size: int):
        """
        Inicializa um projétil.

        Args:
            x, y (float): posição inicial do centro.
            angle (float): ângulo do disparo (radianos).
            damage (int): dano causado ao acertar.
            speed (float): velocidade escalar do projétil (px/s).
            range_val (float): alcance em pixels; usado para derivar o tempo de vida.
            size (int): diâmetro para colisão/desenho.
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 0.0
        self.max_life = range_val / speed
        self.rect = pygame.Rect(int(x - size//2), int(y - size//2), size, size)
        self.size = size

    def update(self, dt: float, walls):
        """
        Avança a posição pelo vetor velocidade, acumula tempo de vida e verifica colisão com paredes.

        Args:
            dt (float): delta de tempo.
            walls (Iterable[pygame.Rect]): retângulos de colisão.

        Returns:
            bool: True se ainda está ativo (não colidiu e não expirou); False caso contrário.
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life += dt
        self.rect.center = (int(self.x), int(self.y))

        for wall in walls:
            if self.rect.colliderect(wall):
                return False
        return self.life < self.max_life

    def draw(self, screen):
        """
        Desenha o projétil como um círculo amarelo.

        Args:
            screen (pygame.Surface): superfície de destino.
        """
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.size//2)


class BossBullet:
    """Projétil simples disparado por chefes; some ao colidir com paredes ou ao sair da área de jogo (+50px de margem)."""

    def __init__(self, x, y, angle, speed=500, damage=25, size=8):
        """
        Inicializa o projétil do boss.

        Args:
            x, y (float): posição inicial.
            angle (float): direção do disparo (radianos).
            speed (float): velocidade (px/s).
            damage (int): dano causado ao atingir o jogador.
            size (int): diâmetro usado na colisão/desenho.
        """
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = size
        self.rect = pygame.Rect(int(x - size//2), int(y - size//2), size, size)
        self.damage = damage

    def update(self, dt, walls):
        """
        Atualiza posição, checa colisões e descarte fora da tela.

        Args:
            dt (float): delta de tempo.
            walls (Iterable[pygame.Rect]): paredes para colisão.

        Returns:
            bool: True se continua ativo; False se colidiu ou saiu dos limites.
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))
        for w in walls:
            if self.rect.colliderect(w):
                return False
        if self.x < -50 or self.x > SCREEN_W + 50 or self.y < -50 or self.y > SCREEN_H + 50:
            return False
        return True

    def draw(self, screen):
        """
        Desenha o projétil do boss como um círculo roxo.

        Args:
            screen (pygame.Surface): superfície de destino.
        """
        pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y)), self.size//2)


class SplitterBullet:
    """Bala grande que se divide em 5 balas menores após uma certa distância."""

    def __init__(self, x, y, angle, speed=400, damage=25, size=16, split_distance=300):
        """
        Inicializa o projétil divisor.

        Args:
            x, y (float): posição inicial.
            angle (float): ângulo do disparo (radianos).
            speed (float): velocidade do projétil grande.
            damage (int): dano base (cada bala filha usará metade).
            size (int): diâmetro do projétil grande.
            split_distance (float): distância a percorrer antes de dividir.
        """
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = size
        self.rect = pygame.Rect(int(x - size//2), int(y - size//2), size, size)
        self.damage = damage
        self.split_distance = split_distance
        self.distance_traveled = 0.0
        self.has_split = False

    def update(self, dt, walls):
        """
        Avança, mede a distância percorrida e divide-se em 5 `BossBullet` quando atingir `split_distance`.

        Args:
            dt (float): delta de tempo.
            walls (Iterable[pygame.Rect]): paredes para colisão.

        Returns:
            tuple[bool, list[BossBullet]]:
                - bool: True se ainda ativo; False se deve ser removido.
                - list: lista de balas-filhas geradas no instante da divisão (ou vazia).
        """
        if self.has_split:
            return False, []  # Já dividiu, não precisa mais atualizar
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))
        
        # Calcula distância percorrida
        dx = self.x - self.start_x
        dy = self.y - self.start_y
        self.distance_traveled = math.hypot(dx, dy)
        
        # Verifica colisão com paredes
        for w in walls:
            if self.rect.colliderect(w):
                return False, []
        
        # Verifica se saiu da tela
        if self.x < -50 or self.x > SCREEN_W + 50 or self.y < -50 or self.y > SCREEN_H + 50:
            return False, []
        
        # Verifica se deve dividir
        if self.distance_traveled >= self.split_distance and not self.has_split:
            self.has_split = True
            # Cria 5 balas menores em diferentes ângulos
            split_bullets = []
            base_angle = self.angle
            spread_angle = math.pi / 3  # 60 graus de spread total
            for i in range(5):
                # Distribui os ângulos: -60, -30, 0, 30, 60 graus em relação ao ângulo original
                offset = (i - 2) * (spread_angle / 4)
                new_angle = base_angle + offset
                split_bullets.append(BossBullet(self.x, self.y, new_angle, speed=450, damage=self.damage // 2, size=8))
            return False, split_bullets
        
        return True, []

    def draw(self, screen):
        """
        Desenha a bala grande com dois círculos concêntricos (laranja/amarelo) para destacá-la.

        Args:
            screen (pygame.Surface): superfície de destino.
        """
        # Desenha a bala grande em laranja/amarelo para diferenciá-la
        pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.size//2)
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.size//2 - 2)