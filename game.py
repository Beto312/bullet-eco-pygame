"""
Loop principal do Bullet Echo: estados, eventos, spawns, rendering e interface.
"""

import pygame
import random
import sys
from constants import *
from player import Player
from enemy import Enemy
from bullets import Bullet
from powerup import PowerUp
from bosses import (
    BossCharger, BossSummoner, BossShielded, BossSniper, BossSplitter
)
from snow import Snowflake, WindOverlay

class Game:
    """Gerencia ciclo principal: eventos, lógica de waves, áudio, rendering e UI."""

    def __init__(self):
        """Inicializa pygame, assets, estados e coleções usadas pelo jogo."""
        pygame.init()
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
        self.power_up_sound = None
        self.gunshot_sound = None
        if pygame.mixer.get_init() is not None:
            self.power_up_sound = pygame.mixer.Sound(POWER_UP_SOUND_FILE)
            self.gunshot_sound = pygame.mixer.Sound(GUNSHOT_SOUND_FILE)
            pygame.mixer.music.load(BACKGROUND_MUSIC_FILE)
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Bullet Echo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Carregar imagens
        try:
            self.menu_image = pygame.image.load("inicio.png").convert()
            self.menu_image = pygame.transform.smoothscale(self.menu_image, (SCREEN_W, SCREEN_H))
        except Exception as e:
            print(f"Warning: Failed to load 'inicio.png': {e}")
            self.menu_image = None
        try:
            self.background_image = pygame.image.load("background.png").convert()
            self.background_image = pygame.transform.smoothscale(self.background_image, (SCREEN_W, SCREEN_H))
        except Exception as e:
            print(f"Warning: Could not load background.png: {e}")
            self.background_image = None
            self.background_image = None

        # Efeitos climáticos
        self.snowflakes = [Snowflake() for _ in range(160)]
        self.wind_overlay = WindOverlay()

        # Estado
        self.running = True
        self.paused = False
        self.game_over = False
        self.in_menu = True
        self.showing_upgrades = False
        self.current_wave = 1
        self.enemies_remaining = 0
        self.wave_clear_time = 0.0
        self.wave_clear_delay = 2.0

        # Objetos
        self.player = Player(SCREEN_W//2, SCREEN_H//2)
        self.bullets = []
        self.enemies = []
        self.walls = self.create_map()

        # Power-ups
        self.power_ups = []
        self.power_up_spawn_timer = 0.0
        self.power_up_spawn_rate = 8.0

        # Upgrades
        self.available_upgrades = []
        self.generate_upgrades()

        # Boss system
        self.active_boss = None
        self.boss_waves = {
            3: BossCharger,
            6: BossSummoner,
            9: BossShielded,
            12: BossSniper,
            15: BossSplitter,
        }

    def create_map(self):
        """Cria paredes retangulares que limitam o jogador e inimigos no cenário."""
        walls = []
        walls.append(pygame.Rect(0, 0, SCREEN_W, 20))
        walls.append(pygame.Rect(0, SCREEN_H-20, SCREEN_W, 20))
        walls.append(pygame.Rect(0, 0, 20, SCREEN_H))
        walls.append(pygame.Rect(SCREEN_W-20, 0, 20, SCREEN_H))
        return walls

    def update_weather_effects(self, dt: float):
        """Anima flocos de neve e rajadas de vento com base no delta de tempo."""
        for snowflake in self.snowflakes:
            snowflake.update(dt)
        self.wind_overlay.update(dt)

    def draw_weather_layer(self, with_wind: bool):
        """Desenha a camada climática (neve e, opcionalmente, a névoa de vento)."""
        for snowflake in self.snowflakes:
            snowflake.draw(self.screen)
        if with_wind:
            self.wind_overlay.draw(self.screen)

    def spawn_enemy(self):
        """Tenta gerar um inimigo longe do jogador/paredes; retorna True se conseguir."""
        if self.active_boss is not None:
            return False
        for _ in range(20):
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                x = random.randint(100, SCREEN_W-100)
                y = random.randint(50, 100)
            elif side == 'bottom':
                x = random.randint(100, SCREEN_W-100)
                y = random.randint(SCREEN_H-100, SCREEN_H-50)
            elif side == 'left':
                x = random.randint(50, 100)
                y = random.randint(100, SCREEN_H-100)
            else:
                x = random.randint(SCREEN_W-100, SCREEN_W-50)
                y = random.randint(100, SCREEN_H-100)

            enemy_rect = pygame.Rect(x - ENEMY_SIZE//2, y - ENEMY_SIZE//2, ENEMY_SIZE, ENEMY_SIZE)
            if any(enemy_rect.colliderect(w) for w in self.walls):
                continue
            if enemy_rect.colliderect(self.player.rect.inflate(40, 40)):
                continue
            if any(enemy_rect.colliderect(e.rect.inflate(10, 10)) for e in self.enemies):
                continue

            self.enemies.append(Enemy(x, y, self.current_wave))
            return True
        return False

    def spawn_power_up(self):
        """Gera um power-up aleatório em local seguro longe de paredes e entidades."""
        power_type = random.choice(["health", "armor", "regen"])
        for _ in range(50):
            x = random.randint(100, SCREEN_W - 100)
            y = random.randint(100, SCREEN_H - 100)
            r = pygame.Rect(x - 20, y - 20, 40, 40)
            if any(r.colliderect(w) for w in self.walls):
                continue
            if r.colliderect(self.player.rect.inflate(20, 20)):
                continue
            if any(r.colliderect(e.rect.inflate(10, 10)) for e in self.enemies):
                continue
            self.power_ups.append(PowerUp(x, y, power_type))
            return

    def check_power_up_collision(self):
        """Verifica se o player coletou algum power-up ativo e aplica efeito."""
        for power_up in self.power_ups[:]:
            if not power_up.collected and self.player.rect.colliderect(power_up.rect):
                self.apply_power_up(power_up)

    def apply_power_up(self, power_up):
        """Aplica o efeito do power-up coletado e remove da lista ativa."""
        if power_up.power_type == "health":
            self.player.max_hp += 25
            self.player.hp = min(self.player.max_hp, self.player.hp + 25)
        elif power_up.power_type == "armor":
            self.player.armor += 3
        elif power_up.power_type == "regen":
            self.player.hp = min(self.player.max_hp, self.player.hp + 10)
        power_up.collected = True
        if self.power_up_sound:
            self.power_up_sound.play()
        if power_up in self.power_ups:
            self.power_ups.remove(power_up)

    def check_upgrade_click(self, mouse_pos):
        """Detecta cliques em cartões de upgrade durante a tela de recompensa."""
        if hasattr(self, 'upgrade_rects'):
            for i, rect in enumerate(self.upgrade_rects):
                if rect.collidepoint(mouse_pos):
                    self.select_upgrade(i)
                    return True
        return False

    def generate_upgrades(self):
        """Lista os upgrades disponíveis após cada wave limpa."""
        self.available_upgrades = [
            ("Velocidade", "Aumenta velocidade", GREEN),
            ("Dano", "Aumenta dano", RED),
            ("Capacidade", "Aumenta munição por pente", YELLOW),
        ]

    def start_wave(self):
        """Configura contadores da próxima wave e decide se será wave de boss."""
        self.current_wave += 1
        self.active_boss = None
        if self.current_wave in self.boss_waves:
            self.enemies_remaining = 0
            self.spawn_timer = 0.0
        else:
            base_enemies = 3
            enemies_per_wave = 2
            self.enemies_remaining = base_enemies + (self.current_wave - 1) * enemies_per_wave
            self.spawn_timer = 0.0

    def spawn_boss(self):
        """Instancia o boss associado à wave atual, se houver."""
        if self.active_boss is not None:
            return
        BossCls = self.boss_waves.get(self.current_wave)
        if BossCls:
            bx, by = SCREEN_W//2, SCREEN_H//2 - 150
            self.active_boss = BossCls(bx, by)

    def update_wave(self, dt: float):
        """Avança timers de spawn ou bosses e controla tela de upgrades ao limpar waves."""
        if self.current_wave in self.boss_waves:
            if self.active_boss is None and not self.enemies:
                self.spawn_boss()
            if self.active_boss and self.active_boss.is_dead() and not self.showing_upgrades:
                if isinstance(self.active_boss, BossSplitter):
                    self.game_over = True
                    return
                
                # Remove todos os inimigos restantes quando o boss morre (incluindo minions)
                self.enemies.clear()
                
                if self.wave_clear_time == 0:
                    self.wave_clear_time = pygame.time.get_ticks() / 1000.0
                    self.showing_upgrades = True
                now = pygame.time.get_ticks() / 1000.0
                if now - self.wave_clear_time >= self.wave_clear_delay:
                    self.start_wave()
                    self.wave_clear_time = 0.0
                    self.showing_upgrades = False
            return

        if self.enemies_remaining > 0:
            self.spawn_timer += dt
            if self.spawn_timer >= ENEMY_SPAWN_RATE:
                if self.spawn_enemy():
                    self.enemies_remaining -= 1
                    self.spawn_timer = 0.0
        elif len(self.enemies) == 0 and not self.showing_upgrades:
            if self.wave_clear_time == 0:
                self.wave_clear_time = pygame.time.get_ticks() / 1000.0
                self.showing_upgrades = True
            now = pygame.time.get_ticks() / 1000.0
            if now - self.wave_clear_time >= self.wave_clear_delay:
                self.start_wave()
                self.wave_clear_time = 0.0
                self.showing_upgrades = False

    def select_upgrade(self, index: int):
        """Aplica o upgrade escolhido pelo jogador e fecha a tela de seleção."""
        if 0 <= index < len(self.available_upgrades):
            name = self.available_upgrades[index][0]
            if name == "Velocidade":
                self.player.upgrade_speed()
            elif name == "Dano":
                self.player.upgrade_damage()
            elif name == "Capacidade":
                self.player.upgrade_ammo_capacity()
            self.showing_upgrades = False
            if hasattr(self, 'upgrade_rects'):
                self.upgrade_rects.clear()

    def handle_events(self):
        """Processa eventos do pygame (teclado, mouse e fechamento da janela)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.in_menu:
                        self.running = False
                    elif self.showing_upgrades:
                        self.showing_upgrades = False
                    else:
                        self.in_menu = True
                elif event.key == pygame.K_r:
                    if self.game_over:
                        self.restart_game()
                    elif not self.in_menu and not self.showing_upgrades and not self.paused and not self.game_over:
                        current_time = pygame.time.get_ticks() / 1000.0
                        self.player.start_reload(current_time)
                elif event.key == pygame.K_p and not self.in_menu and not self.showing_upgrades and not self.game_over:
                    self.paused = not self.paused
                elif event.key == pygame.K_SPACE and self.in_menu:
                    self.start_game()
                elif event.key == pygame.K_1 and self.showing_upgrades:
                    self.select_upgrade(0)
                elif event.key == pygame.K_2 and self.showing_upgrades:
                    self.select_upgrade(1)
                elif event.key == pygame.K_3 and self.showing_upgrades:
                    self.select_upgrade(2)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.showing_upgrades:
                        self.check_upgrade_click(mouse_pos)
                    elif not self.in_menu and not self.paused and not self.game_over:
                        self.shoot_bullets(pygame.time.get_ticks() / 1000.0)

            elif event.type == pygame.MOUSEMOTION and not self.in_menu and not self.showing_upgrades and not self.paused and not self.game_over:
                self.player.rotate_to_mouse(pygame.mouse.get_pos())

    def shoot_bullets(self, current_time: float):
        """Solicita disparo ao player e, se houver projétil, toca som e adiciona à lista."""
        bullet = self.player.shoot(current_time)
        if bullet:
            self.bullets.append(bullet)
            if self.gunshot_sound:
                self.gunshot_sound.play()

    def start_game(self):
        """Reinicia estado para início de partida a partir do menu."""
        self.in_menu = False
        self.game_over = False
        self.paused = False
        self.showing_upgrades = False
        self.current_wave = 1
        self.enemies_remaining = 3
        self.wave_clear_time = 0.0
        self.spawn_timer = 0.0
        self.power_up_spawn_timer = 0.0
        self.player = Player(SCREEN_W//2, SCREEN_H//2)
        self.bullets.clear()
        self.enemies.clear()
        self.power_ups.clear()
        self.active_boss = None
        self.generate_upgrades()

    def update(self, dt: float):
        """Executa lógica por frame: movimentações, colisões, spawns, bosses e verificações de game over."""
        self.update_weather_effects(dt)
        if self.in_menu or self.paused or self.game_over or self.showing_upgrades:
            return

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.walls)
        self.player.rotate_to_mouse(pygame.mouse.get_pos())

        current_time = pygame.time.get_ticks() / 1000.0
        self.player.update_reload(current_time)

        # Power-ups
        self.power_up_spawn_timer += dt
        if self.power_up_spawn_timer >= self.power_up_spawn_rate:
            self.spawn_power_up()
            self.power_up_spawn_timer = 0.0
        for pu in self.power_ups[:]:
            if not pu.update(dt):
                if pu in self.power_ups:
                    self.power_ups.remove(pu)
        self.check_power_up_collision()

        # Balas do player
        for bullet in self.bullets[:]:
            if not bullet.update(dt, self.walls):
                self.bullets.remove(bullet)

        # Inimigos comuns
        for enemy in self.enemies[:]:
            enemy.update(dt, self.player, self.walls)
            enemy.attack(self.player, current_time)
            if enemy.is_dead():
                self.enemies.remove(enemy)

        # Boss
        if self.active_boss is not None:
            self.active_boss.update(dt, self)

        # Colisão bala-inimigo/boss
        if self.bullets and (self.enemies or self.active_boss):
            for bullet in self.bullets[:]:
                hit = False
                for enemy in self.enemies[:]:
                    if bullet.rect.colliderect(enemy.rect):
                        enemy.take_damage(bullet.damage, bullet.angle)
                        hit = True
                        break
                if not hit and self.active_boss is not None:
                    if bullet.rect.colliderect(self.active_boss.rect):
                        self.active_boss.take_damage(bullet.damage, bullet.angle)
                        hit = True
                if hit and bullet in self.bullets:
                    self.bullets.remove(bullet)

        # Dano de contato do boss
        if self.active_boss is not None and self.player.rect.colliderect(self.active_boss.rect):
            self.player.take_damage(15)

        # Game over
        if self.player.hp <= 0:
            self.game_over = True

        # Waves
        self.update_wave(dt)

    def draw_menu(self):
        """Renderiza tela inicial com imagem ou fallback e aplica camada climática."""
        if self.menu_image:
            self.screen.blit(self.menu_image, (0, 0))
        else:
            self.screen.fill(BLACK)
        self.draw_weather_layer(with_wind=False)
        if not self.menu_image:
            title = self.font.render("BULLET ECHO", True, BLUE)
            self.screen.blit(title, title.get_rect(center=(SCREEN_W//2, 200)))
            sub = self.small_font.render("Pressione ESPAÇO para começar", True, WHITE)
            self.screen.blit(sub, sub.get_rect(center=(SCREEN_W//2, 300)))
    def draw_upgrades(self):
        """Mostra a tela de escolha de upgrades com destaque para hover/mouse."""
        self.screen.fill(BLACK)
        t1 = self.font.render("WAVE CLEAR!", True, GREEN)
        self.screen.blit(t1, t1.get_rect(center=(SCREEN_W//2, 100)))
        t2 = self.font.render("Escolha um upgrade:", True, WHITE)
        self.screen.blit(t2, t2.get_rect(center=(SCREEN_W//2, 180)))

        # Só recalcula upgrade_rects se não existir ou se o número de upgrades mudou
        if not hasattr(self, 'upgrade_rects') or len(self.upgrade_rects) != len(self.available_upgrades):
            self.upgrade_rects = []
            y = 250
            for _ in self.available_upgrades:
                rect = pygame.Rect(200, y - 20, SCREEN_W - 400, 80)
                self.upgrade_rects.append(rect)
                y += 120

        mouse_pos = pygame.mouse.get_pos()
        y = 250
        for i, (name, desc, color) in enumerate(self.available_upgrades):
            rect = self.upgrade_rects[i]
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, WHITE, rect, 5)
                pygame.draw.rect(self.screen, color, rect, 3)
            else:
                pygame.draw.rect(self.screen, color, rect, 3)
            pygame.draw.rect(self.screen, DARK_GRAY, rect)

            num = self.font.render(f"{i+1}", True, color)
            self.screen.blit(num, num.get_rect(center=(250, y + 20)))

            nm = self.font.render(name, True, WHITE)
            self.screen.blit(nm, nm.get_rect(center=(SCREEN_W//2, y)))

            ds = self.small_font.render(desc, True, GRAY)
            self.screen.blit(ds, ds.get_rect(center=(SCREEN_W//2, y + 30)))
            y += 120

        info = self.small_font.render("Clique no upgrade desejado ou pressione 1, 2 ou 3", True, YELLOW)
        self.screen.blit(info, info.get_rect(center=(SCREEN_W//2, y + 40)))
        self.screen.blit(info, info.get_rect(center=(SCREEN_W//2, y + 40)))

    def draw_boss_healthbar(self):
        """Desenha barra de vida do boss ativo na parte superior da tela."""
        if self.active_boss is None or self.active_boss.is_dead():
            return
        pad = 20
        bar_w = SCREEN_W - 2*pad
        bar_h = 20
        x = pad
        y = 20
        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, bar_w, bar_h))
        frac = max(0.0, self.active_boss.hp / self.active_boss.max_hp)
        pygame.draw.rect(self.screen, RED, (x, y, int(bar_w * frac), bar_h))
        name = self.small_font.render(f"Boss HP: {int(self.active_boss.hp)}/{self.active_boss.max_hp}", True, WHITE)
        self.screen.blit(name, (x, y - 18))

    def draw(self):
        """Renderiza a cena dependendo do estado atual (menu, upgrades ou gameplay)."""
        if self.in_menu:
            self.draw_menu()
        elif self.showing_upgrades:
            self.draw_upgrades()
        else:
            # Desenha o fundo
            if self.background_image:
                self.screen.blit(self.background_image, (0, 0))
            else:
                self.screen.fill(BLACK)
            for wall in self.walls:
                pygame.draw.rect(self.screen, GRAY, wall)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            for power_up in self.power_ups:
                power_up.draw(self.screen)
            for bullet in self.bullets:
                bullet.draw(self.screen)
            if self.active_boss is not None:
                self.active_boss.draw(self.screen)
            self.player.draw(self.screen)
            self.draw_weather_layer(with_wind=True)
            self.draw_ui()
            self.draw_boss_healthbar()
        pygame.display.flip()

    def draw_ui(self):
        """Atualiza HUD com wave, HP, armadura, munição e mensagens contextuais."""
        # Wave - em cima no meio
        wave_text = self.font.render(f"Wave: {self.current_wave}", True, WHITE)
        wave_rect = wave_text.get_rect(center=(SCREEN_W//2, 30))
        self.screen.blit(wave_text, wave_rect)

        # Vida - embaixo no meio
        hp_text = f"HP: {self.player.hp}/{self.player.max_hp}"
        hp_surface = self.font.render(hp_text, True, WHITE)
        hp_rect = hp_surface.get_rect(center=(SCREEN_W//2, SCREEN_H - 80))
        self.screen.blit(hp_surface, hp_rect)

        # Barra HP - embaixo no meio (abaixo do texto)
        bar_w, bar_h = 200, 20
        bar_x = SCREEN_W//2 - bar_w//2
        bar_y = SCREEN_H - 50
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        hp_w = int((self.player.hp / self.player.max_hp) * bar_w)
        hp_color = GREEN if self.player.hp > self.player.max_hp * 0.5 else YELLOW if self.player.hp > self.player.max_hp * 0.25 else RED
        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, hp_w, bar_h))

        # Armadura - esquerda embaixo
        armor_text = f"ARMADURA: {self.player.armor}"
        armor_surface = self.font.render(armor_text, True, BLUE)
        self.screen.blit(armor_surface, (20, SCREEN_H - 50))

        # Munição - embaixo do lado direito
        ammo_color = WHITE if not self.player.is_reloading else YELLOW
        ammo_text = f"Munição: {self.player.current_ammo}/{self.player.max_ammo}"
        if self.player.is_reloading:
            now = pygame.time.get_ticks() / 1000.0
            remaining = max(0.0, self.player.reload_time - (now - self.player.reload_start))
            ammo_text += f" (Recarregando: {remaining:.1f}s)"
        ammo_surface = self.font.render(ammo_text, True, ammo_color)
        ammo_rect = ammo_surface.get_rect()
        ammo_rect.right = SCREEN_W - 20
        ammo_rect.bottom = SCREEN_H - 20
        self.screen.blit(ammo_surface, ammo_rect)

        # Mensagens
        if self.game_over:
            go = self.font.render("GAME OVER", True, RED)
            rs = self.small_font.render("Pressione R para reiniciar", True, WHITE)
            self.screen.blit(go, go.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 40)))
            self.screen.blit(rs, rs.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
        elif self.paused:
            p = self.font.render("PAUSADO", True, YELLOW)
            self.screen.blit(p, p.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))

    def restart_game(self):
        """Reseta o estado durante tela de game over para recomeçar rapidamente."""
        self.player = Player(SCREEN_W//2, SCREEN_H//2)
        self.bullets.clear()
        self.enemies.clear()
        self.power_ups.clear()
        self.active_boss = None
        self.current_wave = 1
        self.enemies_remaining = 3
        self.wave_clear_time = 0.0
        self.spawn_timer = 0.0
        self.power_up_spawn_timer = 0.0
        self.game_over = False
        self.paused = False
        self.showing_upgrades = False
        self.in_menu = False
        self.generate_upgrades()

    def run(self):
        """Loop principal: processa eventos, atualiza lógica e desenha até fechar."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()
