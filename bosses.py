"""
Módulo de chefes (bosses) para um jogo em Pygame.

Classes:
- BossBase: base com HP, colisão, movimento e knockback.
- BossCharger: investida rápida com dano por contato.
- BossSummoner: kiteia e invoca minions periodicamente.
- BossShielded: alterna entre vulnerável/invulnerável.
- BossSniper: teleporta e dispara projéteis retos.
- BossSplitter: chefe final que combina as habilidades de todos e atira balas que se dividem.

O parâmetro `game` esperado em update() deve expor:
- game.player (x, y, rect, take_damage(...), apply_impulse(...))
- game.walls (lista de pygame.Rect)
- game.enemies (lista mutável)
- game.current_wave (int para escalar minions)
"""

import pygame
import math
import random
from constants import *
from typing import Optional
from enemy import Enemy
from bullets import BossBullet, SplitterBullet


class BossBase:
    """Classe base para bosses: vida, retângulo de colisão, movimento básico e knockback."""

    def __init__(self, x: float, y: float, size: int, hp: int, color=(255, 255, 255)):
        """
        Inicializa o boss base.

        Args:
            x, y (float): posição do centro.
            size (int): diâmetro do sprite/círculo.
            hp (int): vida máxima/inicial.
            color (tuple[int,int,int]): cor fallback para draw.
        """
        self.x = x
        self.y = y
        self.size = size
        self.max_hp = hp
        self.hp = hp
        self.color = color
        self.rect = pygame.Rect(int(x - size//2), int(y - size//2), size, size)
        self.speed = 120
        self.knockback_x = 0.0
        self.knockback_y = 0.0
        self.knockback_decay = 5.0
        self.is_dead_flag = False

    def take_damage(self, dmg: int, angle: Optional[float] = None):
        """
        Aplica dano e, opcionalmente, knockback na direção `angle`.

        Args:
            dmg (int): dano recebido.
            angle (float|None): ângulo em radianos para aplicar impulso de recuo.
        """
        if self.is_dead_flag:
            return
        self.hp = max(0, self.hp - dmg)
        if angle is not None:
            self.knockback_x = math.cos(angle) * 200
            self.knockback_y = math.sin(angle) * 200
        if self.hp <= 0:
            self.is_dead_flag = True

    def is_dead(self) -> bool:
        """Retorna True se o boss morreu (hp <= 0)."""
        return self.is_dead_flag

    def move_towards_player(self, dt: float, player, walls, speed=None):
        """
        Move-se em direção (ou afastando, se speed<0) ao player, com colisão e amortecimento do knockback.

        Args:
            dt (float): delta de tempo do frame.
            player: objeto com .x/.y/.rect.
            walls (list[pygame.Rect]): obstáculos.
            speed (float|None): velocidade a usar (default = self.speed).
        """
        if speed is None:
            speed = self.speed
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx = (dx / dist) * speed * dt
            dy = (dy / dist) * speed * dt

            dx += self.knockback_x * dt
            dy += self.knockback_y * dt
            self.knockback_x -= self.knockback_x * self.knockback_decay * dt
            self.knockback_y -= self.knockback_y * self.knockback_decay * dt

            new_x = self.x + dx
            new_y = self.y + dy
            new_rect = pygame.Rect(int(new_x - self.size//2), int(new_y - self.size//2), self.size, self.size)
            if not any(new_rect.colliderect(w) for w in walls):
                self.x, self.y = new_x, new_y
                self.rect.center = (int(self.x), int(self.y))

    def update(self, dt: float, game):
        """Hook para lógica por frame; classes filhas sobrescrevem."""
        pass

    def draw(self, screen):
        """Desenha um círculo fallback se não existir sprite específico."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size//2)


class BossCharger(BossBase):
    """Chefe que alterna entre idle e investida (charging), causando dano por contato e aplicando knockback no player."""

    def __init__(self, x, y):
        """
        Define parâmetros de investida e carrega sprites de idle/charging.
        """
        super().__init__(x, y, size=80, hp=3000, color=ORANGE)
        self.speed = 90
        self.charge_speed = 700
        self.charge_time = 0.5
        self.charge_cd = 2.8
        self.charge_timer = 0.0
        self.charge_dir = (0.0, 0.0)
        self.state = "idle"
        self._cd = 1.2
        self.contact_damage = 30
        self.knockback_power = 1200
        
        # Carregar imagens
        self.idle_image = pygame.image.load("chargeridle.png").convert_alpha()
        self.idle_image = pygame.transform.smoothscale(self.idle_image, (self.size, self.size))
        
        self.charging_image = pygame.image.load("chargercharging.png").convert_alpha()
        self.charging_image = pygame.transform.smoothscale(self.charging_image, (self.size, self.size))

    def update(self, dt, game):
        """
        Lida com timers, movimento e colisões da investida; em idle persegue e, no cooldown zerado, inicia charge.
        """
        if self.is_dead_flag:
            return

        self._cd -= dt
        if self.state == "charging":
            self.charge_timer -= dt

            vx = self.charge_dir[0] * self.charge_speed * dt
            vy = self.charge_dir[1] * self.charge_speed * dt
            new_x = self.x + vx
            new_y = self.y + vy
            new_rect = pygame.Rect(int(new_x - self.size//2), int(new_y - self.size//2), self.size, self.size)

            if any(new_rect.colliderect(w) for w in game.walls):
                self.state = "idle"
                self._cd = self.charge_cd
            else:
                self.x, self.y = new_x, new_y
                self.rect.center = (int(self.x), int(self.y))

                if self.rect.colliderect(game.player.rect):
                    kx = self.charge_dir[0] * self.knockback_power
                    ky = self.charge_dir[1] * self.knockback_power
                    game.player.apply_impulse(kx, ky)
                    game.player.take_damage(self.contact_damage)

                    self.state = "idle"
                    self._cd = self.charge_cd
                    self.charge_timer = 0.0

            if self.charge_timer <= 0 and self.state == "charging":
                self.state = "idle"
                self._cd = self.charge_cd

        else:
            self.move_towards_player(dt, game.player, game.walls, speed=self.speed)

            if self._cd <= 0:
                dx = game.player.x - self.x
                dy = game.player.y - self.y
                d = math.hypot(dx, dy) or 1.0
                self.charge_dir = (dx / d, dy / d)
                self.state = "charging"
                self.charge_timer = self.charge_time

    def draw(self, screen):
        """Desenha sprite de charging/idle; se faltarem imagens, usa círculo colorido com anel."""
        if self.state == "charging" and self.charging_image:
            rect = self.charging_image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.charging_image, rect)
        elif self.state == "idle" and self.idle_image:
            rect = self.idle_image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.idle_image, rect)
        else:
            # Fallback para desenho caso as imagens não carreguem
            base_color = ORANGE if self.state != "charging" else RED
            pygame.draw.circle(screen, base_color, (int(self.x), int(self.y)), self.size//2)
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.size//2 + 6, 2)


class BossSummoner(BossBase):
    """Chefe que mantém distância e invoca minions periodicamente ao redor de si."""

    def __init__(self, x, y):
        """
        Define timers de invocação e carrega sprite do summoner.
        """
        super().__init__(x, y, size=90, hp=4000, color=PURPLE)
        self.speed = 70
        self.summon_cd = 4.0
        self._cd = 2.0
        self.minions_per_cast = 5
        
        # Carregar imagem
        self.summoner_image = pygame.image.load("summoner.png").convert_alpha()
        self.summoner_image = pygame.transform.smoothscale(self.summoner_image, (self.size, self.size))

    def update(self, dt, game):
        """
        Kite quando o player está perto; caso contrário, deslocamento lateral.
        Quando o cooldown zera, invoca `minions_per_cast` minions, checando paredes.
        """
        if self.is_dead_flag: return
        self._cd -= dt
        dx = game.player.x - self.x
        dy = game.player.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 250:
            self.move_towards_player(dt, game.player, game.walls, speed=-self.speed)
        else:
            angle = math.atan2(dy, dx) + math.pi/2
            vx = math.cos(angle) * self.speed * dt
            vy = math.sin(angle) * self.speed * dt
            new_rect = pygame.Rect(int(self.x + vx - self.size//2), int(self.y + vy - self.size//2), self.size, self.size)
            if not any(new_rect.colliderect(w) for w in game.walls):
                self.x += vx
                self.y += vy
                self.rect.center = (int(self.x), int(self.y))
        if self._cd <= 0:
            self._cd = self.summon_cd
            for _ in range(self.minions_per_cast):
                ex = int(self.x + random.randint(-120, 120))
                ey = int(self.y + random.randint(-120, 120))
                enemy_rect = pygame.Rect(ex - ENEMY_SIZE//2, ey - ENEMY_SIZE//2, ENEMY_SIZE, ENEMY_SIZE)
                if not any(enemy_rect.colliderect(w) for w in game.walls):
                    game.enemies.append(Enemy(ex, ey, wave=max(1, game.current_wave)))
    
    def draw(self, screen):
        """Desenha o sprite do summoner; fallback: círculo roxo."""
        if self.summoner_image:
            rect = self.summoner_image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.summoner_image, rect)
        else:
            pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y)), self.size//2)


class BossShielded(BossBase):
    """Chefe que alterna entre invulnerável e vulnerável por timers, movendo mais rápido quando blindado."""

    def __init__(self, x, y):
        """
        Configura tempos de fase (vulnerável/invulnerável) e sprites de escudo.
        """
        super().__init__(x, y, size=100, hp=7000, color=CYAN)
        self.speed = 85
        self.vulnerable_time = 3.0
        self.invuln_time = 3.0
        self.timer = self.vulnerable_time
        self.invulnerable = False

        # Carregar imagens
        self.invulnerable_image = pygame.image.load("shieldactive.png").convert_alpha()
        self.invulnerable_image = pygame.transform.smoothscale(self.invulnerable_image, (self.size, self.size))

        self.shielded_image = pygame.image.load("shieldinactive.png").convert_alpha()
        self.shielded_image = pygame.transform.smoothscale(self.shielded_image, (self.size, self.size))

    def take_damage(self, dmg: int, angle: Optional[float] = None):
        """Ignora dano quando invulnerável; caso contrário, delega à base (aplica knockback se houver ângulo)."""
        if self.invulnerable:
            return
        super().take_damage(dmg, angle)

    def update(self, dt, game):
        """
        Alterna fase via timer: invulnerável -> vulnerável -> invulnerável …
        Move-se mais rápido quando invulnerável.
        """
        if self.is_dead_flag: return
        self.timer -= dt
        if self.invulnerable:
            self.move_towards_player(dt, game.player, game.walls, speed=self.speed+60)
            if self.timer <= 0:
                self.invulnerable = False
                self.timer = self.vulnerable_time
        else:
            self.move_towards_player(dt, game.player, game.walls, speed=self.speed)
            if self.timer <= 0:
                self.invulnerable = True
                self.timer = self.invuln_time

    def draw(self, screen):
        """Desenha sprite/efeito de escudo quando invulnerável; fallback com anel branco."""
        if self.invulnerable:
            if self.invulnerable_image:
                rect = self.invulnerable_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(self.invulnerable_image, rect)
            else:
                # Fallback quando invulnerável
                col = (100, 160, 255)
                pygame.draw.circle(screen, col, (int(self.x), int(self.y)), self.size//2)
                pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size//2 + 10, 3)
        else:
            if self.shielded_image:
                rect = self.shielded_image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(self.shielded_image, rect)
            else:
                # Fallback quando vulnerável
                col = (100, 255, 255)
                pygame.draw.circle(screen, col, (int(self.x), int(self.y)), self.size//2)


class BossSniper(BossBase):
    """Chefe que se move devagar, teleporta entre pontos predefinidos e dispara projéteis retos mirando o jogador."""

    def __init__(self, x, y):
        """
        Define timers de teleporte e de tiro; carrega sprite e inicializa lista de balas.
        """
        super().__init__(x, y, size=70, hp=4000, color=(220, 220, 255))
        self.speed = 60
        self.teleport_cd = 3.0
        self._tp_timer = 1.0
        self.shoot_cd = 1.2
        self._shoot_timer = 0.25
        self.bullets = []
        
        # Carregar imagem
        self.sniper_image = pygame.image.load("sniper.png").convert_alpha()
        self.sniper_image = pygame.transform.smoothscale(self.sniper_image, (self.size, self.size))

    def update(self, dt, game):
        """
        Move, atira periodicamente (BossBullet) e teleporta quando o timer zera.
        Remove balas ao colidir com paredes ou com o jogador (aplicando dano).
        """
        if self.is_dead_flag: return
        self._tp_timer -= dt
        self._shoot_timer -= dt

        self.move_towards_player(dt, game.player, game.walls, speed=self.speed)

        if self._shoot_timer <= 0:
            self._shoot_timer = self.shoot_cd
            ang = math.atan2(game.player.y - self.y, game.player.x - self.x)
            self.bullets.append(BossBullet(self.x, self.y, ang, speed=550, damage=50, size=8))

        for b in self.bullets[:]:
            if not b.update(dt, game.walls):
                self.bullets.remove(b)
            else:
                if b.rect.colliderect(game.player.rect):
                    game.player.take_damage(b.damage)
                    if b in self.bullets:
                        self.bullets.remove(b)

        if self._tp_timer <= 0:
            self._tp_timer = self.teleport_cd
            spots = [
                (100, 100), (SCREEN_W-100, 100),
                (100, SCREEN_H-100), (SCREEN_W-100, SCREEN_H-100),
                (SCREEN_W//2, 100), (SCREEN_W//2, SCREEN_H-100)
            ]
            tx, ty = random.choice(spots)
            r = pygame.Rect(tx - self.size//2, ty - self.size//2, self.size, self.size)
            if not any(r.colliderect(w) for w in game.walls):
                self.x, self.y = tx, ty
                self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen):
        """Desenha o sprite do sniper e suas balas; fallback: círculo azul-claro com contorno roxo."""
        if self.sniper_image:
            rect = self.sniper_image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sniper_image, rect)
        else:
            # Fallback caso a imagem não carregue
            pygame.draw.circle(screen, (220, 220, 255), (int(self.x), int(self.y)), self.size//2)
            pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y)), self.size//2 + 8, 2)
        for b in self.bullets:
            b.draw(screen)


class BossSplitter(BossBase):
    """Chefe final híbrido: investida, invocação de minions, escudo alternado, teleporte e projéteis que se dividem."""

    def __init__(self, x, y):
        """
        Combina timers e estados dos demais bosses e carrega sprites de estado (normal/charge/shield).
        """
        super().__init__(x, y, size=85, hp=10000, color=(255, 200, 120))
        self.speed = 100
        
        # Habilidade do BossCharger: Investida
        self.charge_speed = 700
        self.charge_time = 0.5
        self.charge_cd = 2.8
        self.charge_timer = 0.0
        self.charge_dir = (0.0, 0.0)
        self.state = "idle"
        self._charge_cd = 1.2
        self.contact_damage = 30
        self.knockback_power = 1200
        
        # Habilidade do BossSummoner: Invocação
        self.summon_cd = 4.0
        self._summon_timer = 2.0
        self.minions_per_cast = 5
        
        # Habilidade do BossShielded: Escudo
        self.vulnerable_time = 3.0
        self.invuln_time = 3.0
        self.shield_timer = self.vulnerable_time
        self.invulnerable = False
        
        # Habilidade do BossSniper: Teleporte
        self.teleport_cd = 3.0
        self._tp_timer = 1.0
        
        # Sistema de tiro (balas que se dividem)
        self.shoot_cd = 1.5
        self._shoot_timer = 0.5
        self.bullets = []
        
        # Carregar imagens
        self.finalboss_image = pygame.image.load("finalboss.png").convert_alpha()
        self.finalboss_image = pygame.transform.smoothscale(self.finalboss_image, (self.size, self.size))
        
        self.finalboss_charge_image = pygame.image.load("finalbosscharge.png").convert_alpha()
        self.finalboss_charge_image = pygame.transform.smoothscale(self.finalboss_charge_image, (self.size, self.size))
        
        self.finalboss_shield_image = pygame.image.load("finalbossshield.png").convert_alpha()
        self.finalboss_shield_image = pygame.transform.smoothscale(self.finalboss_shield_image, (self.size, self.size))

    def take_damage(self, dmg: int, angle: Optional[float] = None):
        """Ignora dano enquanto invulnerável; caso contrário, aplica dano/knockback via base."""
        if self.invulnerable:
            return
        super().take_damage(dmg, angle)

    def update(self, dt, game):
        """
        Atualiza todos os timers/estados (escudo, teleporte, investida, invocação e tiros divisores).
        Em 'charging', move fixo na charge_dir; em 'idle', kiteia se perto (<250) ou persegue (mais rápido quando invulnerável).
        """
        if self.is_dead_flag:
            return
        
        # Atualiza timers
        self._charge_cd -= dt
        self._summon_timer -= dt
        self._tp_timer -= dt
        self._shoot_timer -= dt
        self.shield_timer -= dt
        
        # Habilidade do BossShielded: Alterna entre vulnerável e invulnerável
        if self.invulnerable:
            if self.shield_timer <= 0:
                self.invulnerable = False
                self.shield_timer = self.vulnerable_time
        else:
            if self.shield_timer <= 0:
                self.invulnerable = True
                self.shield_timer = self.invuln_time
        
        # Habilidade do BossCharger: Investida
        if self.state == "charging":
            self.charge_timer -= dt
            
            vx = self.charge_dir[0] * self.charge_speed * dt
            vy = self.charge_dir[1] * self.charge_speed * dt
            new_x = self.x + vx
            new_y = self.y + vy
            new_rect = pygame.Rect(int(new_x - self.size//2), int(new_y - self.size//2), self.size, self.size)
            
            if any(new_rect.colliderect(w) for w in game.walls):
                self.state = "idle"
                self._charge_cd = self.charge_cd
            else:
                self.x, self.y = new_x, new_y
                self.rect.center = (int(self.x), int(self.y))
                
                if self.rect.colliderect(game.player.rect):
                    kx = self.charge_dir[0] * self.knockback_power
                    ky = self.charge_dir[1] * self.knockback_power
                    game.player.apply_impulse(kx, ky)
                    game.player.take_damage(self.contact_damage)
                    
                    self.state = "idle"
                    self._charge_cd = self.charge_cd
                    self.charge_timer = 0.0
            
            if self.charge_timer <= 0 and self.state == "charging":
                self.state = "idle"
                self._charge_cd = self.charge_cd
        
        elif self.state == "idle":
            # Habilidade do BossSniper: Teleporte
            if self._tp_timer <= 0:
                self._tp_timer = self.teleport_cd
                spots = [
                    (100, 100), (SCREEN_W-100, 100),
                    (100, SCREEN_H-100), (SCREEN_W-100, SCREEN_H-100),
                    (SCREEN_W//2, 100), (SCREEN_W//2, SCREEN_H-100)
                ]
                tx, ty = random.choice(spots)
                r = pygame.Rect(tx - self.size//2, ty - self.size//2, self.size, self.size)
                if not any(r.colliderect(w) for w in game.walls):
                    self.x, self.y = tx, ty
                    self.rect.center = (int(self.x), int(self.y))
            
            # Movimento normal ou kiting
            dx = game.player.x - self.x
            dy = game.player.y - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 250:
                self.move_towards_player(dt, game.player, game.walls, speed=-self.speed)
            else:
                move_speed = self.speed + 60 if self.invulnerable else self.speed
                self.move_towards_player(dt, game.player, game.walls, speed=move_speed)
            
            if self._charge_cd <= 0:
                dx = game.player.x - self.x
                dy = game.player.y - self.y
                d = math.hypot(dx, dy) or 1.0
                self.charge_dir = (dx / d, dy / d)
                self.state = "charging"
                self.charge_timer = self.charge_time
        
        # Habilidade do BossSummoner: Invoca minions
        if self._summon_timer <= 0:
            self._summon_timer = self.summon_cd
            for _ in range(self.minions_per_cast):
                ex = int(self.x + random.randint(-120, 120))
                ey = int(self.y + random.randint(-120, 120))
                enemy_rect = pygame.Rect(ex - ENEMY_SIZE//2, ey - ENEMY_SIZE//2, ENEMY_SIZE, ENEMY_SIZE)
                if not any(enemy_rect.colliderect(w) for w in game.walls):
                    game.enemies.append(Enemy(ex, ey, wave=max(1, game.current_wave)))
        
        # Sistema de tiro (balas que se dividem)
        if self._shoot_timer <= 0:
            self._shoot_timer = self.shoot_cd
            ang = math.atan2(game.player.y - self.y, game.player.x - self.x)
            self.bullets.append(SplitterBullet(self.x, self.y, ang, speed=400, damage=25, size=16, split_distance=300))

        # Atualiza balas e verifica divisão
        for b in self.bullets[:]:
            if isinstance(b, SplitterBullet):
                alive, split_bullets = b.update(dt, game.walls)
                
                if b.rect.colliderect(game.player.rect):
                    game.player.take_damage(b.damage)
                    self.bullets.remove(b)
                    continue
                
                if not alive:
                    self.bullets.remove(b)
                    if split_bullets:
                        self.bullets.extend(split_bullets)
            else:
                if not b.update(dt, game.walls):
                    self.bullets.remove(b)
                else:
                    if b.rect.colliderect(game.player.rect):
                        game.player.take_damage(b.damage)
                        if b in self.bullets:
                            self.bullets.remove(b)

    def draw(self, screen):
        """
        Desenha o sprite conforme estado (charge/shield/normal). Fallback usa cores e anel quando invulnerável.
        Também desenha todas as balas ativas.
        """
        # Escolhe a imagem baseado no estado
        if self.state == "charging" and self.finalboss_charge_image:
            image_to_use = self.finalboss_charge_image
        elif self.invulnerable and self.finalboss_shield_image:
            image_to_use = self.finalboss_shield_image
        elif self.finalboss_image:
            image_to_use = self.finalboss_image
        else:
            image_to_use = None
        
        if image_to_use:
            rect = image_to_use.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(image_to_use, rect)
        else:
            # Fallback caso as imagens não carreguem
            if self.state == "charging":
                base_color = RED
            elif self.invulnerable:
                base_color = (100, 160, 255)
            else:
                base_color = (255, 200, 120)
            
            pygame.draw.circle(screen, base_color, (int(self.x), int(self.y)), self.size//2)
            
            if self.invulnerable:
                pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size//2 + 10, 3)
            else:
                pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.size//2 + 8, 2)
        
        for b in self.bullets:
            b.draw(screen)
