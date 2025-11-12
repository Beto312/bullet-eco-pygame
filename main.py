"""Ponto de entrada do Bullet Echo: instancia o Game e inicia o loop principal."""

from game import Game

if __name__ == "__main__":
    """Garante execução apenas quando o módulo é chamado diretamente."""
    game = Game()
    game.run()
