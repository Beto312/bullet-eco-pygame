# 🎯 Bullet Echo — Top-Down Shooter em Pygame  

**Autor:** Pedro Waack, 
**Curso:** Engenharia da Computação — Insper  
**Linguagem:** Python 3.13.5(base) 
**Biblioteca Principal:** [Pygame](https://www.pygame.org/)  

---

## 🧩 Visão Geral

**Bullet Echo** é um jogo **top-down shooter 2D** desenvolvido em **Python + Pygame**, inspirado em mecânicas de arena survival.  
O jogador enfrenta **ondas crescentes de inimigos** e **chefes (bosses)**, coletando power-ups e realizando upgrades entre as fases.

O projeto foi desenvolvido como uma base sólida de **arquitetura orientada a objetos**, com foco em:
- Estrutura modular (múltiplos arquivos `.py` organizados por responsabilidade)  
- Sistema de **colisões físicas** e **knockback**  
- **Waves progressivas** com aumento de dificuldade  
- **Bosses** com habilidades únicas  
- **Power-ups** e **upgrades persistentes**  
- Docstrings completas e padrão de qualidade PEP-257  

---

## 🕹️ Gameplay

O jogador move-se pelo mapa evitando colisões com paredes e inimigos, dispara projéteis, coleta **power-ups** e derrota **chefes** em waves especiais.  
Após vencer uma wave, pode escolher um **upgrade** antes da próxima rodada.

### 🎮 Controles
| Ação | Tecla |
|------|-------|
| Mover para cima | **W** |
| Mover para baixo | **S** |
| Mover para a esquerda | **A** |
| Mover para a direita | **D** |
| Atirar | **Botão esquerdo do mouse** |
| Recarregar manualmente | **R** |
| Pausar / Retomar | **P** |
| Sair ou voltar ao menu | **Esc** |
| Iniciar o jogo no menu | **Espaço** |
| Escolher upgrade | **1**, **2** ou **3** |

---

## 🧠 Arquitetura do Projeto

Cada módulo foi documentado com docstrings e segue uma arquitetura modular clara:

bullet-echo/
│
├── constants.py # Configurações gerais e caminhos de arquivos
├── bullets.py # Classes de projéteis (comuns, boss, divisíveis)
├── enemy.py # Classe Enemy (movimento, dano, partículas)
├── bosses.py # Classes dos chefes (IA, habilidades, estados)
├── player.py # Jogador, movimentação, tiro, upgrades
├── powerup.py # Power-ups, timer, efeito de piscar, cache de imagens
├── game.py # Loop principal, lógica de ondas, eventos, UI
├── main.py # Entry point do jogo
│
└── assets/ # Imagens e sons usados no jogo


---

## 🧱 Estrutura de Classes

- **Player:** movimentação, tiro, upgrades, armadura, recarga.  
- **Enemy:** IA simples, dano por contato, partículas de morte.  
- **Bosses:** subclasses com IA avançada (`Charger`, `Summoner`, `Shielded`, `Sniper`, `Splitter`).  
- **Bullets:** projéteis do player e bosses, inclusive balas divisíveis.  
- **PowerUp:** itens temporários que somem com o tempo.  
- **Game:** loop principal, eventos, UI e sistema de waves.

---

## ⚙️ Requisitos

| Dependência | Versão recomendada |
|--------------|--------------------|
| Python | 3.10+ |
| Pygame | 2.5.0+ |

Instale com:
```bash
pip install pygame

## 🚀 Execução

python main.py

Se tudo estiver configurado corretamente, a janela "Bullet Echo" será aberta.
Use ESPAÇO para iniciar e ESC para sair.

