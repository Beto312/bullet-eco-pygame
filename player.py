"""
Módulo Player — define o personagem controlado pelo jogador no jogo Pygame.

Responsabilidades:
- Movimento via teclado (WASD) com colisão contra paredes.
- Rotação em direção ao cursor do mouse.
- Disparo de projéteis e sistema de munição/recarga.
- Upgrades de atributos (velocidade, dano, HP, munição).
- Efeitos de knockback (impulsos) e resistência (armadura).
- Renderização com sprite (imagem) ou fallback vetorial.

Depende de:
- constants.py (PLAYER_SPEED, PLAYER_HP, FIRE_RATE etc.)
- bullets.Bullet para criar projéteis.
"""

import pygame
import math
from constants import *


class Player:
    """Classe que representa o jogador, controlando movimento, combate e upgrades."""

    def __init__(self, x: float, y: float):
        """
        Inicializa o jogador na posição (x, y) e carrega seus parâmetros iniciais.

        Args:
            x, y (float): coordenadas iniciais do jogador.
        """
        self.x = x
        self.y = y
        self.angle = 0
        self.hp = PLAYER_HP
        self.max_hp = PLAYER_HP
        self.rect = pygame.Rect(int(x - PLAYER_SIZE//2), int(y - PLAYER_SIZE//2), PLAYER_SIZE, PLAYER_SIZE)

        # Atributos base
        self.speed = PLAYER_SPEED
        self.bullet_damage = BULLET_DAMAGE
        self.bullet_speed = BULLET_SPEED
        self.bullet_range = BULLET_RANGE
        self.bullet_size = BULLET_SIZE
        self.armor = 0
        self.fire_rate = FIRE_RATE
        self.last_shot_time = -self.fire_rate

        # Sistema de munição
        self.max_ammo = 30
        self.current_ammo = self.max_ammo
        self.is_reloading = False
        self.reload_time = 2.0
        self.reload_start = 0

        # Contadores de upgrades
        self.speed_level = 0
        self.damage_level = 0

        # Impulsos (knockback)
        self.impulse_x = 0.0
        self.impulse_y = 0.0
        self.impulse_decay = 9.0  # amortecimento do impulso

        # Carregar sprite com fallback
        self.image_available = True
        original = pygame.image.load("bolinha.png").convert_alpha()
        self.original_image = pygame.transform.smoothscale(original, (PLAYER_SIZE, PLAYER_SIZE))

    def _candidate_rect(self, dx: float, dy: float) -> pygame.Rect:
        """
        Retorna um retângulo hipotético (rect) após movimento, usado para prever colisões.

        Args:
            dx, dy (float): deslocamento proposto.

        Returns:
            pygame.Rect: rect ajustado para verificar colisão antes do movimento real.
        """
        cand = self.rect.copy()
        cand.centerx = int(self.x + dx)
        cand.centery = int(self.y + dy)
        return cand

    def apply_impulse(self, ix: float, iy: float):
        """
        Aplica um impulso (knockback) instantâneo no jogador.

        Args:
            ix, iy (float): componentes do impulso em cada eixo.
        """
        self.impulse_x += ix
        self.impulse_y += iy

    def _resolve_collisions(self, walls):
        """
        Corrige penetrações após colisão empurrando o jogador para fora da parede.

        Args:
            walls (list[pygame.Rect]): lista de paredes.
        """
        for w in walls:
            if self.rect.colliderect(w):
                left_overlap = self.rect.right - w.left
                right_overlap = w.right - self.rect.left
                top_overlap = self.rect.bottom - w.top
                bottom_overlap = w.bottom - self.rect.top

                min_overlap = min(left_overlap, right_overlap, top_overlap, bottom_overlap)

                if min_overlap == left_overlap:
                    self.rect.right = w.left
                elif min_overlap == right_overlap:
                    self.rect.left = w.right
                elif min_overlap == top_overlap:
                    self.rect.bottom = w.top
                else:
                    self.rect.top = w.bottom

                self.x = float(self.rect.centerx)
                self.y = float(self.rect.centery)

    def update(self, dt: float, keys, walls):
        """
        Atualiza a posição e o estado do jogador com base no teclado e física.

        Args:
            dt (float): delta de tempo entre frames.
            keys: estado das teclas (pygame.key.get_pressed()).
            walls (list[pygame.Rect]): obstáculos.
        """
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1

        # Normaliza a velocidade em diagonais
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Movimento base + impulso
        move_x = dx * self.speed * dt + self.impulse_x * dt
        move_y = dy * self.speed * dt + self.impulse_y * dt

        # Amortecer impulso
        self.impulse_x -= self.impulse_x * self.impulse_decay * dt
        self.impulse_y -= self.impulse_y * self.impulse_decay * dt

        # Movimento eixo X
        if move_x != 0:
            cand = self._candidate_rect(move_x, 0)
            if not any(cand.colliderect(w) for w in walls):
                self.x += move_x
                self.rect.centerx = int(self.x)

        # Movimento eixo Y
        if move_y != 0:
            cand = self._candidate_rect(0, move_y)
            if not any(cand.colliderect(w) for w in walls):
                self.y += move_y
                self.rect.centery = int(self.y)

        # Corrigir penetração
        self.rect.center = (int(self.x), int(self.y))
        self._resolve_collisions(walls)

    def rotate_to_mouse(self, mouse_pos):
        """
        Atualiza o ângulo do jogador para mirar em direção ao mouse.

        Args:
            mouse_pos (tuple[int,int]): posição do cursor.
        """
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        self.angle = math.atan2(dy, dx)

    def shoot(self, current_time: float):
        """
        Dispara uma bala, respeitando o cooldown e a munição disponível.

        Args:
            current_time (float): tempo atual do jogo (segundos).

        Returns:
            Bullet | None: objeto Bullet se o disparo for possível, None caso contrário.
        """
        from bullets import Bullet
        if current_time - self.last_shot_time < self.fire_rate:
            return None
        if self.is_reloading:
            return None
        if self.current_ammo <= 0:
            self.start_reload(current_time)
            return None
        self.current_ammo -= 1
        self.last_shot_time = current_time
        return Bullet(self.x, self.y, self.angle, self.bullet_damage, self.bullet_speed, self.bullet_range, self.bullet_size)

    def take_damage(self, damage: int):
        """
        Aplica dano ao jogador, levando em conta armadura.

        Args:
            damage (int): quantidade de dano recebida.
        """
        if self.armor > 0:
            damage = max(1, damage // 2)
            self.armor -= 1
        self.hp = max(0, self.hp - damage)

    def upgrade_speed(self):
        """Aumenta a velocidade de movimento do jogador."""
        self.speed_level += 1
        self.speed += 50
        return True

    def upgrade_damage(self):
        """Aumenta o dano das balas."""
        self.damage_level += 1
        self.bullet_damage += 15
        return True

    def upgrade_max_hp(self):
        """Aumenta o HP máximo e atual do jogador."""
        self.max_hp += 25
        self.hp += 25
        return True

    def upgrade_ammo_capacity(self):
        """Aumenta a capacidade máxima de munição."""
        self.max_ammo += 5
        if self.current_ammo >= self.max_ammo - 5:
            self.current_ammo = self.max_ammo
        return True

    def start_reload(self, current_time: float):
        """
        Inicia o processo de recarregar munição.

        Args:
            current_time (float): tempo atual do jogo (segundos).
        """
        if not self.is_reloading and self.current_ammo < self.max_ammo:
            self.is_reloading = True
            self.reload_start = current_time
            return True
        return False

    def update_reload(self, current_time: float):
        """
        Atualiza o progresso da recarga e conclui quando o tempo necessário passa.

        Args:
            current_time (float): tempo atual.

        Returns:
            bool: True se a recarga foi concluída neste frame.
        """
        if self.is_reloading:
            if (current_time - self.reload_start) >= self.reload_time:
                self.current_ammo = self.max_ammo
                self.is_reloading = False
                return True
        return False

    def draw(self, screen):
        """
        Renderiza o jogador na tela:
        - Sprite rotacionado ou círculo genérico.
        - Linha representando o cano da arma.
        """
        if self.image_available and self.original_image is not None:
            rotated_image = pygame.transform.rotate(self.original_image, -math.degrees(self.angle))
            rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(rotated_image, rect)
        else:
            pygame.draw.circle(screen, (200, 200, 255), (int(self.x), int(self.y)), PLAYER_SIZE//2)

        # Arma (linha apontando na direção do mouse)
        gun_length = 25
        gun_x = self.x + math.cos(self.angle) * (PLAYER_SIZE//2 + 5)
        gun_y = self.y + math.sin(self.angle) * (PLAYER_SIZE//2 + 5)
        pygame.draw.line(screen, DARK_GRAY, (self.x, self.y), (gun_x, gun_y), 3)