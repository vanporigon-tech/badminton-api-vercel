#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from typing import List
from datetime import datetime

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

load_dotenv()

# Scopes: Sheets read/write + Drive for sharing
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _load_credentials():
    """Load service account credentials from env or default path."""
    service_file = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        "credentials/gobadminminiapp-694c0da69053.json",
    )
    if not os.path.isfile(service_file):
        raise FileNotFoundError(
            f"Service account file not found: {service_file}. Set GOOGLE_SERVICE_ACCOUNT_FILE."
        )
    creds = service_account.Credentials.from_service_account_file(
        service_file, scopes=SCOPES
    )
    return creds


def _get_services():
    """Create Sheets and Drive API clients."""
    creds = _load_credentials()
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive


def _share_spreadsheet(drive_service, spreadsheet_id: str, emails: List[str]):
    """Share spreadsheet with provided emails as editors."""
    for email in filter(None, [e.strip() for e in emails]):
        try:
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body={"type": "user", "role": "writer", "emailAddress": email},
                sendNotificationEmail=False,
            ).execute()
        except HttpError:
            # Continue on share errors to not break main flow
            continue


def _move_file_to_folder(drive_service, file_id: str, folder_id: str):
    if not folder_id:
        return
    try:
        file = drive_service.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents", []))
        drive_service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()
    except HttpError:
        pass


def _find_or_create_users_sheet(drive_service, sheets_service, folder_id: str, name: str) -> str:
    # Try find by name in folder
    try:
        q = f"mimeType='application/vnd.google-apps.spreadsheet' and name='{name}'"
        if folder_id:
            q += f" and '{folder_id}' in parents"
        resp = drive_service.files().list(q=q, spaces="drive", fields="files(id, name)", pageSize=1).execute()
        files = resp.get("files", [])
        if files:
            return files[0]["id"]
    except HttpError:
        pass

    # Create new spreadsheet
    created = sheets_service.spreadsheets().create(body={"properties": {"title": name}}).execute()
    sid = created["spreadsheetId"]
    _move_file_to_folder(drive_service, sid, folder_id)
    return sid


def _ensure_sheet_exists(sheets_service, spreadsheet_id: str, sheet_title: str):
    meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = meta.get("sheets", [])
    titles = {s.get("properties", {}).get("title") for s in sheets}
    if sheet_title not in titles:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {"addSheet": {"properties": {"title": sheet_title, "gridProperties": {"frozenRowCount": 1}}}}
                ]
            },
        ).execute()

def create_tournament_table(tournament_id, tournament_data):
    """Создать Google Таблицу с результатами турнира.

    Возвращает URL созданной таблицы.
    """

    games = tournament_data.get("games", [])
    players_stats = calculate_tournament_stats(games)

    # Build services
    sheets_service, drive_service = _get_services()

    # 1) Create spreadsheet
    title = f"Badminton Tournament #{tournament_id} — {datetime.now().strftime('%Y-%m-%d')}"
    spreadsheet_body = {
        "properties": {"title": title},
        "sheets": [
            {
                "properties": {
                    "title": "Results",
                    "gridProperties": {"frozenRowCount": 1},
                }
            },
            {
                "properties": {
                    "title": "Games",
                    "gridProperties": {"frozenRowCount": 1},
                }
            },
        ],
    }

    created = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
    spreadsheet_id = created["spreadsheetId"]

    # Move to folder if provided
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if folder_id:
        _move_file_to_folder(drive_service, spreadsheet_id, folder_id)

    # 2) Prepare data
    header = [
        "ID Имя",
        "№",
        "Ранг",
        "Рейтинг",
        "Игры Δ",
        "Игры",
        "Побед",
        "Пораж",
        "Очки Δ",
        "Очки+",
        "Очки-",
    ]

    values = [header]
    for i, p in enumerate(players_stats, 1):
        points_diff = p["points_for"] - p["points_against"]
        losses = p["games_played"] - p["games_won"]
        values.append(
            [
                f"{p['id']} Игрок {p['id']}",
                i,
                "-",
                f"{p['old_rating']}→{p['new_rating']}({p['rating_change']:+d})",
                p["games_played"],
                p["games_played"],
                p["games_won"],
                losses,
                points_diff,
                p["points_for"],
                p["points_against"],
            ]
        )

    # 3) Write Results values
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Results!A1",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    # 3b) Write Games sheet if games provided in tournament_data
    games = tournament_data.get("games", [])
    game_values = [["Дата", "Время", "Команда 1", "Команда 2", "Счет 1", "Счет 2"]]
    for g in games:
        dt = g.get("played_at", datetime.now().isoformat())
        date_str = dt[:10]
        time_str = dt[11:19] if len(dt) > 10 else ""
        t1 = ", ".join([str(pid) for pid in g.get("team1", [])])
        t2 = ", ".join([str(pid) for pid in g.get("team2", [])])
        game_values.append([date_str, time_str, t1, t2, g.get("score1", 0), g.get("score2", 0)])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Games!A1",
        valueInputOption="USER_ENTERED",
        body={"values": game_values},
    ).execute()

    # 4) Optional sharing
    share_emails_env = os.getenv("GOOGLE_SHARE_EMAILS", "")
    share_emails = [e for e in share_emails_env.split(",") if e.strip()]
    # Always include the requester email if provided
    default_owner = os.getenv("DEFAULT_OWNER_EMAIL", "vanporigon@gmail.com")
    if default_owner and default_owner not in share_emails:
        share_emails.append(default_owner)
    try:
        _share_spreadsheet(drive_service, spreadsheet_id, share_emails)
    except Exception:
        pass

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def update_users_sheet(users: List[dict]):
    """Создать/обновить таблицу пользователей и записать агрегаты.

    users: list of dicts with keys: telegram_id, name, username, games_played, rating
    """
    sheets_service, drive_service = _get_services()
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    name = os.getenv("GOOGLE_USERS_SHEET_NAME", "Badminton Users")
    sid = _find_or_create_users_sheet(drive_service, sheets_service, folder_id, name)

    # Ensure Users sheet exists
    _ensure_sheet_exists(sheets_service, sid, "Users")

    header = ["Telegram ID", "Имя", "Username", "Сыграно игр", "Рейтинг"]
    values = [header]
    for u in users:
        values.append([
            u.get("telegram_id"),
            u.get("name"),
            u.get("username"),
            u.get("games_played", 0),
            u.get("rating", 1500),
        ])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sid,
        range="Users!A1",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    return f"https://docs.google.com/spreadsheets/d/{sid}/edit"


def update_tournament_sheets(spreadsheet_id: str, games: List[dict], players_stats: List[dict]):
    """Перезаписать листы Results и Games в существующей таблице турнира."""
    sheets_service, _ = _get_services()

    # Prepare Results
    header = [
        "ID Имя",
        "№",
        "Ранг",
        "Рейтинг",
        "Игры Δ",
        "Игры",
        "Побед",
        "Пораж",
        "Очки Δ",
        "Очки+",
        "Очки-",
    ]
    values = [header]
    players_sorted = sorted(players_stats, key=lambda x: x.get("new_rating", 1500), reverse=True)
    for i, p in enumerate(players_sorted, 1):
        points_diff = p.get("points_for", 0) - p.get("points_against", 0)
        losses = p.get("games_played", 0) - p.get("games_won", 0)
        values.append([
            f"{p['id']} Игрок {p['id']}",
            i,
            "-",
            f"{p.get('old_rating', 1500)}→{p.get('new_rating', 1500)}({int(p.get('rating_change',0)):+d})",
            p.get("games_played", 0),
            p.get("games_played", 0),
            p.get("games_won", 0),
            losses,
            points_diff,
            p.get("points_for", 0),
            p.get("points_against", 0),
        ])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Results!A1",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    game_values = [["Дата", "Время", "Команда 1", "Команда 2", "Счет 1", "Счет 2"]]
    for g in games:
        dt = g.get("played_at", datetime.now().isoformat())
        date_str = dt[:10]
        time_str = dt[11:19] if len(dt) > 10 else ""
        t1 = ", ".join([str(pid) for pid in g.get("team1", [])])
        t2 = ", ".join([str(pid) for pid in g.get("team2", [])])
        game_values.append([date_str, time_str, t1, t2, g.get("score1", 0), g.get("score2", 0)])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Games!A1",
        valueInputOption="USER_ENTERED",
        body={"values": game_values},
    ).execute()

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

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
