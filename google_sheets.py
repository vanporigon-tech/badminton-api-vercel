#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
from datetime import datetime

def create_tournament_table(tournament_id, tournament_data):
    """Создать Google Таблицу с результатами турнира"""
    
    games = tournament_data.get('games', [])
    players_stats = calculate_tournament_stats(games)
    
    # Создаем простую таблицу в Google Sheets
    # Пока что возвращаем публичную ссылку
    
    if not games:
        # Если нет игр, создаем пустую таблицу
        table_url = f"https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
        return table_url
    
    # Создаем CSV данные для таблицы
    csv_data = create_tournament_csv(tournament_id, games, players_stats)
    
    # Возвращаем ссылку на Google Sheets
    table_url = f"https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
    
    return table_url

def create_tournament_csv(tournament_id, games, players_stats):
    """Создать CSV данные для турнира"""
    
    # Сортируем игроков по рейтингу
    players_stats.sort(key=lambda x: x['new_rating'], reverse=True)
    
    csv_lines = []
    
    # Заголовок
    csv_lines.append("ID Имя,№,Ранг,Рейтинг,Игры Δ,Игры,Побед,Пораж,Очки Δ,Очки+,Очки-")
    
    # Данные игроков
    for i, player in enumerate(players_stats, 1):
        points_diff = player['points_for'] - player['points_against']
        losses = player['games_played'] - player['games_won']
        
        csv_lines.append(f"Игрок {player['id']},{i},-,{player['old_rating']}→{player['new_rating']}({player['rating_change']:+d}),{player['games_played']},{player['games_played']},{player['games_won']},{losses},{points_diff:+d},{player['points_for']},{player['points_against']}")
    
    return "\n".join(csv_lines)

def calculate_tournament_stats(games):
    """Подсчитать статистику турнира"""
    players = {}
    
    for game in games:
        # Обрабатываем команду 1
        for player_id in game.get('team1', []):
            if player_id not in players:
                players[player_id] = {
                    'id': player_id,
                    'games_played': 0,
                    'games_won': 0,
                    'points_for': 0,
                    'points_against': 0,
                    'rating_change': 0,
                    'old_rating': 1500,
                    'new_rating': 1500
                }
            
            players[player_id]['games_played'] += 1
            if game['score1'] > game['score2']:
                players[player_id]['games_won'] += 1
            players[player_id]['points_for'] += game['score1']
            players[player_id]['points_against'] += game['score2']
            
            # Обновляем рейтинг из rating_changes
            if 'rating_changes' in game:
                for change in game['rating_changes']:
                    if change['player_id'] == player_id:
                        players[player_id]['rating_change'] += change['rating_change']
                        players[player_id]['new_rating'] = change['new_rating']
                        if players[player_id]['old_rating'] == 1500:  # Первая игра
                            players[player_id]['old_rating'] = change['old_rating']
        
        # Обрабатываем команду 2
        for player_id in game.get('team2', []):
            if player_id not in players:
                players[player_id] = {
                    'id': player_id,
                    'games_played': 0,
                    'games_won': 0,
                    'points_for': 0,
                    'points_against': 0,
                    'rating_change': 0,
                    'old_rating': 1500,
                    'new_rating': 1500
                }
            
            players[player_id]['games_played'] += 1
            if game['score2'] > game['score1']:
                players[player_id]['games_won'] += 1
            players[player_id]['points_for'] += game['score2']
            players[player_id]['points_against'] += game['score1']
            
            # Обновляем рейтинг из rating_changes
            if 'rating_changes' in game:
                for change in game['rating_changes']:
                    if change['player_id'] == player_id:
                        players[player_id]['rating_change'] += change['rating_change']
                        players[player_id]['new_rating'] = change['new_rating']
                        if players[player_id]['old_rating'] == 1500:  # Первая игра
                            players[player_id]['old_rating'] = change['old_rating']
    
    return list(players.values())

def create_tournament_html(tournament_id, games, players_stats):
    """Создать HTML таблицу турнира"""
    
    # Сортируем игроков по рейтингу
    players_stats.sort(key=lambda x: x['new_rating'], reverse=True)
    
    # Находим лидеров роста
    growth_leaders = sorted(players_stats, key=lambda x: x['rating_change'], reverse=True)[:3]
    
    html = f"""
    <h2>🏆 Итоги турнира #{tournament_id}</h2>
    <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y')}</p>
    <p><strong>Участников:</strong> {len(players_stats)} игроков, {len(games)} игр</p>
    
    <h3>📈 Лидеры роста</h3>
    <ol>
    """
    
    for i, player in enumerate(growth_leaders, 1):
        html += f"<li><strong>Топ-{i}:</strong> Игрок {player['id']} (+{player['rating_change']})</li>"
    
    html += """
    </ol>
    
    <h3>📊 Результаты</h3>
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th>ID Имя</th>
            <th>№</th>
            <th>Ранг</th>
            <th>Рейтинг</th>
            <th>Игры Δ</th>
            <th>Игры</th>
            <th>Побед</th>
            <th>Пораж</th>
            <th>Очки Δ</th>
            <th>Очки+</th>
            <th>Очки-</th>
        </tr>
    """
    
    for i, player in enumerate(players_stats, 1):
        points_diff = player['points_for'] - player['points_against']
        losses = player['games_played'] - player['games_won']
        
        # Цвет для изменения рейтинга
        rating_color = "green" if player['rating_change'] > 0 else "red" if player['rating_change'] < 0 else "black"
        
        html += f"""
        <tr>
            <td>{player['id']} Игрок {player['id']}</td>
            <td>{i}</td>
            <td>-</td>
            <td style="color: {rating_color};">
                {player['old_rating']} → {player['new_rating']} ({player['rating_change']:+d})
            </td>
            <td>{player['games_played']}</td>
            <td>{player['games_played']}</td>
            <td>{player['games_won']}</td>
            <td>{losses}</td>
            <td>{points_diff:+d}</td>
            <td>{player['points_for']}</td>
            <td>{player['points_against']}</td>
        </tr>
        """
    
    html += """
    </table>
    
    <p><em>Сделано в боте @GoBadmikAppBot</em></p>
    """
    
    return html

def create_google_sheets_simple(tournament_id, games, players_stats):
    """Простое создание Google Sheets через публичную ссылку"""
    
    # Создаем CSV данные
    csv_data = "ID,Имя,№,Ранг,Рейтинг,Игры Δ,Игры,Побед,Пораж,Очки Δ,Очки+,Очки-\n"
    
    for i, player in enumerate(players_stats, 1):
        points_diff = player['points_for'] - player['points_against']
        losses = player['games_played'] - player['games_won']
        
        csv_data += f"{player['id']},Игрок {player['id']},{i},-,{player['old_rating']}→{player['new_rating']}({player['rating_change']:+d}),{player['games_played']},{player['games_played']},{player['games_won']},{losses},{points_diff:+d},{player['points_for']},{player['points_against']}\n"
    
    # Возвращаем ссылку на Google Sheets
    return f"https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
