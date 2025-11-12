"""
Módulo PowerUp — gerencia os itens coletáveis do jogo (vida, armadura e regeneração).

Responsabilidades:
- Carregar e cachear imagens dos power-ups.
- Controlar o tempo de vida (desaparecem após alguns segundos).
- Detectar coleta pelo jogador.
- Desenhar o ícone visual correspondente (com efeito de piscar antes de sumir).

Depende de:
- constants.py (POWER_UP_IMAGE_FILES, cores, tamanhos).
- pygame (para imagens, colisão e desenho).
"""

import pygame
from constants import *


class PowerUp:
    """Classe que representa um power-up (item coletável) no jogo."""

    _image_cache = {}

    @classmethod
    def _load_image(cls, power_type: str, size: int):
        """
        Carrega e redimensiona a imagem do power-up correspondente ao tipo.

        Implementa cache interno para evitar múltiplos loads do mesmo arquivo.

        Args:
            power_type (str): tipo do power-up ("health", "armor", "regen").
            size (int): tamanho em pixels para redimensionamento.

        Returns:
            pygame.Surface | None: imagem carregada, ou None se não existir arquivo.
        """
        if power_type in cls._image_cache:
            return cls._image_cache[power_type]

        file_name = POWER_UP_IMAGE_FILES.get(power_type)
        if not file_name:
            cls._image_cache[power_type] = None
            return None

        loaded = pygame.image.load(file_name).convert_alpha()
        image = pygame.transform.smoothscale(loaded, (size, size))
        cls._image_cache[power_type] = image
        return image

    def __init__(self, x: float, y: float, power_type: str, lifetime: float = 12.0):
        """
        Inicializa o power-up na posição (x, y) e define suas propriedades.

        Args:
            x, y (float): posição do centro do item.
            power_type (str): tipo do item (define imagem e efeito).
            lifetime (float): tempo de vida em segundos antes de desaparecer.
        """
        self.x = x
        self.y = y
        self.power_type = power_type
        self.size = 28
        self.rect = pygame.Rect(int(x - self.size // 2), int(y - self.size // 2), self.size, self.size)
        self.collected = False

        self.lifetime = lifetime
        self.time_left = lifetime

        # Carrega imagem (com cache global)
        self.image = self._load_image(power_type, self.size)

    def update(self, dt: float) -> bool:
        """
        Atualiza o tempo de vida do item.

        Args:
            dt (float): delta de tempo desde o último frame.

        Returns:
            bool: True se o item ainda está ativo; False se expirou ou foi coletado.
        """
        if self.collected:
            return False
        self.time_left -= dt
        return self.time_left > 0

    def draw(self, screen):
        """
        Desenha o item na tela, aplicando efeito de piscar nos últimos 3 segundos.

        Args:
            screen (pygame.Surface): superfície onde o item será desenhado.
        """
        if self.collected:
            return

        # Pisca nos últimos 3 segundos (visível 50% do tempo)
        blinking = self.time_left <= 3.0 and (int(self.time_left * 10) % 2 == 0)
        if blinking:
            return

        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.image, rect)