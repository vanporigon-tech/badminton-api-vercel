#!/usr/bin/env python3
"""
Демонстрация работы системы рейтинга Glicko-2 для бадминтона
"""

from glicko2 import glicko2, calculate_team_rating, distribute_rating_changes

def demo_individual_game():
    """Демонстрация игры 1 на 1"""
    print("🏸 ДЕМОНСТРАЦИЯ ИГРЫ 1 НА 1")
    print("=" * 50)
    
    # Игрок 1: рейтинг 1500, RD 350, волатильность 0.06
    player1_rating = 1500.0
    player1_rd = 350.0
    player1_vol = 0.06
    
    # Игрок 2: рейтинг 1600, RD 300, волатильность 0.06
    player2_rating = 1600.0
    player2_rd = 300.0
    player2_vol = 0.06
    
    print(f"Игрок 1: Рейтинг {player1_rating}, RD {player1_rd}")
    print(f"Игрок 2: Рейтинг {player2_rating}, RD {player2_rd}")
    print()
    
    # Игрок 1 выиграл
    print("🎯 Результат: Игрок 1 выиграл")
    
    # Рассчитываем новые рейтинги
    new_player1_rating, new_player1_rd, new_player1_vol = glicko2.calculate_new_rating(
        player1_rating, player1_rd, player1_vol,
        [player2_rating], [player2_rd], [1.0]  # 1.0 = победа
    )
    
    new_player2_rating, new_player2_rd, new_player2_vol = glicko2.calculate_new_rating(
        player2_rating, player2_rd, player2_vol,
        [player1_rating], [player1_rd], [0.0]  # 0.0 = поражение
    )
    
    print(f"📊 НОВЫЕ РЕЙТИНГИ:")
    print(f"Игрок 1: {player1_rating:.1f} → {new_player1_rating:.1f} (+{new_player1_rating - player1_rating:.1f})")
    print(f"Игрок 2: {player2_rating:.1f} → {new_player2_rating:.1f} ({new_player2_rating - player2_rating:.1f})")
    print()

def demo_team_game():
    """Демонстрация командной игры 2 на 2"""
    print("🏸 ДЕМОНСТРАЦИЯ КОМАНДНОЙ ИГРЫ 2 НА 2")
    print("=" * 50)
    
    # Команда 1
    team1_player1 = (1500.0, 350.0, 0.06)  # (рейтинг, RD, волатильность)
    team1_player2 = (1550.0, 320.0, 0.06)
    
    # Команда 2
    team2_player1 = (1600.0, 300.0, 0.06)
    team2_player2 = (1580.0, 310.0, 0.06)
    
    print("Команда 1:")
    print(f"  Игрок 1: Рейтинг {team1_player1[0]}, RD {team1_player1[1]}")
    print(f"  Игрок 2: Рейтинг {team1_player2[0]}, RD {team1_player2[1]}")
    print()
    
    print("Команда 2:")
    print(f"  Игрок 1: Рейтинг {team2_player1[0]}, RD {team2_player1[1]}")
    print(f"  Игрок 2: Рейтинг {team2_player2[0]}, RD {team2_player2[1]}")
    print()
    
    # Рассчитываем рейтинги команд
    team1_rating, team1_rd, team1_vol = calculate_team_rating([team1_player1, team1_player2])
    team2_rating, team2_rd, team2_vol = calculate_team_rating([team2_player1, team2_player2])
    
    print(f"📊 РЕЙТИНГИ КОМАНД:")
    print(f"Команда 1: {team1_rating:.1f} (RD: {team1_rd:.1f})")
    print(f"Команда 2: {team2_rating:.1f} (RD: {team2_rd:.1f})")
    print()
    
    # Команда 1 выиграла
    print("🎯 Результат: Команда 1 выиграла")
    
    # Рассчитываем новые рейтинги команд
    new_team1_rating, new_team1_rd, new_team1_vol = glicko2.calculate_new_rating(
        team1_rating, team1_rd, team1_vol,
        [team2_rating], [team2_rd], [1.0]  # 1.0 = победа
    )
    
    new_team2_rating, new_team2_rd, new_team2_vol = glicko2.calculate_new_rating(
        team2_rating, team2_rd, team2_vol,
        [team1_rating], [team1_rd], [0.0]  # 0.0 = поражение
    )
    
    print(f"📊 НОВЫЕ РЕЙТИНГИ КОМАНД:")
    print(f"Команда 1: {team1_rating:.1f} → {new_team1_rating:.1f} (+{new_team1_rating - team1_rating:.1f})")
    print(f"Команда 2: {team2_rating:.1f} → {new_team2_rating:.1f} ({new_team2_rating - team2_rating:.1f})")
    print()
    
    # Распределяем изменения между игроками
    team1_changes = (
        new_team1_rating - team1_rating,
        new_team1_rd - team1_rd,
        new_team1_vol - team1_vol
    )
    
    team2_changes = (
        new_team2_rating - team2_rating,
        new_team2_rd - team2_rd,
        new_team2_vol - team2_vol
    )
    
    new_team1_players = distribute_rating_changes([team1_player1, team1_player2], *team1_changes)
    new_team2_players = distribute_rating_changes([team2_player1, team2_player2], *team2_changes)
    
    print(f"📊 НОВЫЕ РЕЙТИНГИ ИГРОКОВ:")
    print("Команда 1:")
    print(f"  Игрок 1: {team1_player1[0]:.1f} → {new_team1_players[0][0]:.1f} (+{new_team1_players[0][0] - team1_player1[0]:.1f})")
    print(f"  Игрок 2: {team1_player2[0]:.1f} → {new_team1_players[1][0]:.1f} (+{new_team1_players[1][0] - team1_player2[0]:.1f})")
    print()
    
    print("Команда 2:")
    print(f"  Игрок 1: {team2_player1[0]:.1f} → {new_team2_players[0][0]:.1f} ({new_team2_players[0][0] - team2_player1[0]:.1f})")
    print(f"  Игрок 2: {team2_player2[0]:.1f} → {new_team2_players[1][0]:.1f} ({new_team2_players[1][0] - team2_player2[0]:.1f})")
    print()

def demo_rating_categories():
    """Демонстрация категорий рейтинга"""
    print("🏆 КАТЕГОРИИ РЕЙТИНГА В БАДМИНТОНЕ")
    print("=" * 50)
    
    categories = [
        (500, "F", "Начинающий"),
        (600, "E-", "Любитель"),
        (700, "E", "Любитель+"),
        (800, "E+", "Продвинутый"),
        (900, "D-", "Продвинутый+"),
        (1000, "D", "Опытный"),
        (1100, "D+", "Опытный+"),
        (1200, "C-", "Мастер"),
        (1300, "C", "Мастер+"),
        (1400, "C+", "Эксперт"),
        (1500, "B-", "Эксперт+"),
        (1600, "B", "Профессионал"),
        (1700, "B+", "Профессионал+"),
        (1800, "A-", "Элита"),
        (1900, "A", "Элита+"),
        (2000, "A+", "Легенда")
    ]
    
    for rating, category, description in categories:
        print(f"{category:>3} ({rating:>4}): {description}")
    
    print()

def main():
    """Запуск всех демонстраций"""
    print("🎯 ДЕМОНСТРАЦИЯ СИСТЕМЫ РЕЙТИНГА Glicko-2")
    print("=" * 60)
    print()
    
    demo_rating_categories()
    demo_individual_game()
    demo_team_game()
    
    print("🎉 Демонстрация завершена!")
    print("\nЭта система используется в Mini App для автоматического")
    print("расчета рейтинга после каждой игры в бадминтон.")

if __name__ == "__main__":
    main()

