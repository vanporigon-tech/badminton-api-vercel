// Telegram WebApp initialization
let tg = window.Telegram.WebApp;
let currentUser = null;
let currentRoom = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Telegram WebApp
    if (tg && tg.ready) {
        tg.ready();
        tg.expand();
        
        // Set theme
        tg.setHeaderColor('#233e39');
        tg.setBackgroundColor('#233e39');
        
        // Get user data
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            currentUser = tg.initDataUnsafe.user;
            console.log('Current user from Telegram:', currentUser);
        }
    }
    
    // Fallback for testing outside Telegram
    if (!currentUser) {
        currentUser = {
            id: Date.now(), // Уникальный ID на основе времени
            first_name: 'Гость',
            last_name: 'Неизвестный'
        };
        console.log('Using fallback user (please use in Telegram):', currentUser);
    }
    
    // Check if user exists, if not - redirect to registration
    checkUserRegistration();
    
    // Set up event listeners
    setupEventListeners();
});

// Check if user is registered
async function checkUserRegistration() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`/players/${currentUser.id}`);
        if (response.ok) {
            // User exists, show main menu
            showSection('main-menu');
        } else {
            // User doesn't exist, show registration
            showRegistrationForm();
        }
    } catch (error) {
        console.error('Error checking user registration:', error);
        showSection('main-menu');
    }
}

// Show registration form
function showRegistrationForm() {
    const html = `
        <div class="section">
            <h2>Добро пожаловать!</h2>
            <p style="text-align: center; margin-bottom: 25px; color: #b8d4d0;">
                Для начала работы необходимо указать ваши данные
            </p>
            <form id="registration-form">
                <div class="form-group">
                    <label for="first-name">Имя</label>
                    <input type="text" id="first-name" placeholder="Ваше имя" required>
                </div>
                <div class="form-group">
                    <label for="last-name">Фамилия</label>
                    <input type="text" id="last-name" placeholder="Ваша фамилия" required>
                </div>
                <div class="form-group">
                    <label for="initial-rating">Начальный рейтинг</label>
                    <select id="initial-rating" required>
                        <option value="1500">F (1500) - Начинающий</option>
                        <option value="600">E (600) - Любитель</option>
                        <option value="800">D (800) - Продвинутый</option>
                        <option value="1100">C (1100) - Опытный</option>
                        <option value="1400">B (1400) - Мастер</option>
                        <option value="1700">A (1700) - Эксперт</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Зарегистрироваться</button>
            </form>
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
    
    // Set up registration form handler
    document.getElementById('registration-form').addEventListener('submit', handleRegistration);
}

// Handle user registration
async function handleRegistration(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('first-name').value;
    const lastName = document.getElementById('last-name').value;
    const initialRating = parseInt(document.getElementById('initial-rating').value);
    
    console.log('Registering user:', { firstName, lastName, initialRating, currentUser });
    
    if (!currentUser || !currentUser.id) {
        showMessage('Ошибка: пользователь не определен', 'error');
        console.error('Current user is not defined:', currentUser);
        return;
    }
    
    try {
        const requestBody = {
            telegram_id: currentUser.id,
            first_name: firstName,
            last_name: lastName,
            rating: initialRating
        };
        
        console.log('Sending registration request:', requestBody);
        
        const response = await fetch('/players/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Registration response status:', response.status);
        
        if (response.ok) {
            const player = await response.json();
            console.log('Registration successful:', player);
            showMessage('Регистрация успешна!', 'success');
            setTimeout(() => {
                showMainMenu();
            }, 1500);
        } else {
            const error = await response.json();
            console.error('Registration API error:', error);
            showMessage(error.detail || 'Ошибка регистрации', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('Ошибка сети: ' + error.message, 'error');
    }
}

// Show main menu
function showMainMenu() {
    // Если пользователь в комнате, автоматически выходим
    if (currentRoom) {
        console.log('🚪 Автоматический выход из комнаты при переходе на главный экран');
        leaveRoom(currentRoom.id);
    }
    
    showSection('main-menu');
    currentRoom = null;
}

// Set up event listeners
function setupEventListeners() {
    // Search game button
    const searchBtn = document.getElementById('search-game');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            showSection('search-rooms');
            loadRooms();
        });
    }
    
    // Create game button
    const createBtn = document.getElementById('create-game');
    if (createBtn) {
        console.log('✅ Кнопка создания игры найдена');
        createBtn.addEventListener('click', () => {
            console.log('🖱️ Нажата кнопка создания игры');
            
            // Если пользователь уже в комнате, предупреждаем
            if (currentRoom) {
                if (confirm('⚠️ Вы уже находитесь в комнате. Создать новую комнату?')) {
                    // Сначала выходим из текущей
                    leaveRoom(currentRoom.id);
                    showSection('create-room');
                }
            } else {
                showSection('create-room');
            }
        });
    } else {
        console.log('❌ Кнопка создания игры не найдена');
    }
    
    // Back buttons
    const backToMain = document.getElementById('back-to-main');
    if (backToMain) {
        backToMain.addEventListener('click', () => {
            if (currentRoom) {
                // Пользователь в комнате - предупреждаем
                if (confirm('⚠️ Вы уверены, что хотите выйти из этой комнаты?')) {
                    leaveRoom(currentRoom.id);
                    showSection('main-menu');
                }
            } else {
                showSection('main-menu');
            }
        });
    }
    
    const backToMain2 = document.getElementById('back-to-main-2');
    if (backToMain2) {
        backToMain2.addEventListener('click', () => {
            if (currentRoom) {
                // Пользователь в комнате - предупреждаем
                if (confirm('⚠️ Вы уверены, что хотите выйти из этой комнаты?')) {
                    leaveRoom(currentRoom.id);
                    showSection('main-menu');
                }
            } else {
                showSection('main-menu');
            }
        });
    }
    
    const backToMain3 = document.getElementById('back-to-main-3');
    if (backToMain3) {
        backToMain3.addEventListener('click', () => {
            if (currentRoom) {
                // Пользователь в комнате - предупреждаем
                if (confirm('⚠️ Вы уверены, что хотите выйти из этой комнаты?')) {
                    leaveRoom(currentRoom.id);
                    showSection('main-menu');
                }
            } else {
                showSection('main-menu');
            }
        });
    }
    
    // Start game button (для лидера)
    const startGameBtn = document.getElementById('start-game-btn');
    if (startGameBtn) {
        startGameBtn.addEventListener('click', handleStartGame);
    }
    
    // Join room button
    const joinRoomBtn = document.getElementById('join-room-btn');
    if (joinRoomBtn) {
        joinRoomBtn.addEventListener('click', handleJoinRoom);
    }
    
    const backToRooms = document.getElementById('back-to-rooms');
    if (backToRooms) {
        backToRooms.addEventListener('click', () => {
            showSection('search-rooms');
            loadRooms();
        });
    }
    
    const backToRoom = document.getElementById('back-to-room');
    if (backToRoom) {
        backToRoom.addEventListener('click', () => {
            if (currentRoom) {
                showRoomDetails(currentRoom.id);
            } else {
                showSection('search-rooms');
            }
        });
    }
    
    // Room form
    const roomForm = document.getElementById('room-form');
    if (roomForm) {
        roomForm.addEventListener('submit', handleCreateRoom);
    }
    
    // Score form
    const scoreForm = document.getElementById('score-form');
    if (scoreForm) {
        scoreForm.addEventListener('submit', handleGameScore);
    }
}

// Show/hide sections
function showSection(sectionId) {
    console.log('🔍 Показываю секцию:', sectionId);
    
    const sections = ['main-menu', 'search-rooms', 'create-room', 'room-details', 'game-score'];
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
            section.classList.add('hidden');
            console.log(`📦 Скрываю секцию: ${id}`);
        } else {
            console.log(`❌ Секция не найдена: ${id}`);
        }
    });
    
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.remove('hidden');
        console.log(`✅ Показываю секцию: ${sectionId}`);
    } else {
        console.log(`❌ Целевая секция не найдена: ${sectionId}`);
    }
}

// Load available rooms
async function loadRooms() {
    try {
        const response = await fetch('/rooms/');
        if (response.ok) {
            const data = await response.json();
            displayRooms(data.rooms);
        } else {
            showMessage('Ошибка загрузки комнат', 'error');
        }
    } catch (error) {
        console.error('Error loading rooms:', error);
        showMessage('Ошибка сети', 'error');
    }
}

// Display rooms list
function displayRooms(rooms) {
    const roomsList = document.getElementById('rooms-list');
    if (!roomsList) return;
    
    if (rooms.length === 0) {
        roomsList.innerHTML = '<p style="text-align: center; color: #b8d4d0;">Нет доступных комнат</p>';
        return;
    }
    
    const roomsHtml = rooms.map(room => {
        // Отображаем информацию о создателе и участниках
        const creatorInfo = room.creator_name ? `👑 Создатель: ${room.creator_name}` : '';
        const membersInfo = room.members_names && room.members_names.length > 0 
            ? `👥 Участники: ${room.members_names.join(', ')}` 
            : '👥 Участники: нет';
        
        return `
            <div class="room-card" onclick="joinRoom(${room.id})">
                <h3>${room.name}</h3>
                <div class="room-creator-info">
                    <small>${creatorInfo}</small>
                </div>
                <div class="room-members-info">
                    <small>${membersInfo}</small>
                </div>
                <div class="room-info">
                    <span class="room-status ${room.is_game_started ? 'game-started' : 'active'}">
                        ${room.is_game_started ? 'Игра идет' : 'Ожидание игроков'}
                    </span>
                    <span class="player-count">${room.member_count}/${room.max_players}</span>
                </div>
                <button class="join-btn" onclick="event.stopPropagation(); joinRoom(${room.id})">
                    Присоединиться
                </button>
            </div>
        `;
    }).join('');
    
    roomsList.innerHTML = roomsHtml;
}

// Join room
async function joinRoom(roomId) {
    try {
        // Получаем информацию о пользователе из базы данных
        const playerResponse = await fetch(`/players/${currentUser.id}`);
        if (!playerResponse.ok) {
            showMessage('Ошибка: пользователь не найден в базе данных', 'error');
            return;
        }
        
        const player = await playerResponse.json();
        
        const response = await fetch(`/rooms/${roomId}/join?player_id=${player.id}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('Успешно присоединились к комнате!', 'success');
            setTimeout(() => {
                showRoomDetails(roomId);
            }, 1500);
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Ошибка присоединения', 'error');
        }
    } catch (error) {
        console.error('Join room error:', error);
        showMessage('Ошибка сети', 'error');
    }
}

// Show room details
async function showRoomDetails(roomId) {
    try {
        // Получаем информацию о комнате
        const roomResponse = await fetch(`/rooms/${roomId}`);
        if (!roomResponse.ok) {
            showMessage('Ошибка получения информации о комнате', 'error');
            return;
        }
        
        const room = await roomResponse.json();
        
        // Сохраняем текущую комнату
        currentRoom = room;
        
        // Используем новый метод отображения с полными именами
        displayRoomDetails(room);
        
        showSection('room-details');
        
        // Просто отображаем детали комнаты с полными именами
        // displayRoomDetails будет вызвана выше
        
        // Получаем информацию о текущем пользователе
        const playerResponse = await fetch(`/players/${currentUser.id}`);
        let currentPlayer = null;
        if (playerResponse.ok) {
            currentPlayer = await playerResponse.json();
        }
        
        // Показываем/скрываем кнопки в зависимости от роли пользователя
        const isLeader = currentPlayer && room.creator_id === currentPlayer.id;
        const isMember = currentPlayer && room.members.some(m => m.player.id === currentPlayer.id);
        
        // Используем новую структуру данных
        // room содержит members, creator, creator_name, members_names
        
        // Отображаем информацию о комнате с полными именами
        if (isLeader) {
            // Пользователь - лидер
            document.getElementById('leader-controls').classList.remove('hidden');
            document.getElementById('join-controls').classList.add('hidden');
            
            // Проверяем количество участников для кнопки "Начать игру"
            const startGameBtn = document.getElementById('start-game-btn');
            if (room.member_count < 2) {
                startGameBtn.disabled = true;
                startGameBtn.textContent = '⏳ Недостаточно игроков (минимум 2)';
            } else {
                startGameBtn.disabled = false;
                startGameBtn.textContent = '🚀 Начать игру';
            }
        } else if (isMember) {
            // Пользователь уже в комнате
            document.getElementById('leader-controls').classList.add('hidden');
            document.getElementById('join-controls').classList.add('hidden');
        } else {
            // Пользователь может присоединиться
            document.getElementById('leader-controls').classList.add('hidden');
            document.getElementById('join-controls').classList.remove('hidden');
        }
        
        showSection('room-details');
        
    } catch (error) {
        console.error('Error showing room details:', error);
        showMessage('Ошибка загрузки информации о комнате', 'error');
    }
}

// Clear all team slots
function clearAllSlots() {
    const slots = ['left-slot-1', 'left-slot-2', 'right-slot-1', 'right-slot-2'];
    slots.forEach(slotId => {
        const slot = document.getElementById(slotId);
        slot.innerHTML = '<div class="slot-placeholder">Пустой слот</div>';
        slot.className = 'player-slot';
    });
}

// Fill team slots with players
function fillTeamSlots(members) {
    if (members.length === 0) return;
    
    // Сортируем участников: лидер первый, остальные по алфавиту
    const sortedMembers = [...members].sort((a, b) => {
        if (a.is_leader && !b.is_leader) return -1;
        if (!a.is_leader && b.is_leader) return 1;
        return a.name.localeCompare(b.name);
    });
    
    // Распределяем по командам
    if (sortedMembers.length === 1) {
        // Один участник - помещаем в левую команду
        fillSlot('left-slot-1', sortedMembers[0], 'left');
    } else if (sortedMembers.length === 2) {
        // Два участника - 1v1
        fillSlot('left-slot-1', sortedMembers[0], 'left');
        fillSlot('right-slot-1', sortedMembers[1], 'right');
    } else if (sortedMembers.length === 3) {
        // Три участника - 2v1 (неполная команда)
        fillSlot('left-slot-1', sortedMembers[0], 'left');
        fillSlot('left-slot-2', sortedMembers[1], 'left');
        fillSlot('right-slot-1', sortedMembers[2], 'right');
    } else if (sortedMembers.length === 4) {
        // Четыре участника - 2v2
        fillSlot('left-slot-1', sortedMembers[0], 'left');
        fillSlot('left-slot-2', sortedMembers[1], 'left');
        fillSlot('right-slot-1', sortedMembers[2], 'right');
        fillSlot('right-slot-2', sortedMembers[3], 'right');
    }
}

// Fill individual slot
function fillSlot(slotId, player, teamSide) {
    const slot = document.getElementById(slotId);
    const teamClass = teamSide === 'left' ? 'filled-left' : 'filled-right';
    
    slot.innerHTML = `
        <div class="player-info">
            <div class="player-name">${player.name}</div>
            <div class="player-rating">Рейтинг: ${player.rating}</div>
        </div>
    `;
    
    slot.className = `player-slot filled ${teamClass}`;
}

// Display members list
function displayMembersList(members) {
    const membersUl = document.getElementById('members-ul');
    membersUl.innerHTML = '';
    
    members.forEach(member => {
        const li = document.createElement('li');
        li.className = member.is_leader ? 'member-item leader' : 'member-item';
        
        const leaderIcon = member.is_leader ? '👑 ' : '👤 ';
        const memberText = `${leaderIcon}${member.name}`;
        const ratingText = `Рейтинг: ${member.rating}`;
        
        li.innerHTML = `
            <span>${memberText}</span>
            <span>${ratingText}</span>
        `;
        
        membersUl.appendChild(li);
    });
}

// Display room details
function displayRoomDetails(room) {
    document.getElementById('room-title').textContent = room.name;
    
    // Display members
    const membersList = document.getElementById('room-members');
    const membersHtml = room.members.map(member => `
        <div class="member-item">
            <div class="member-info">
                <div class="member-avatar">
                    ${member.player.first_name.charAt(0)}${member.player.last_name.charAt(0)}
                </div>
                <div class="member-details">
                    <h4>${member.player.first_name} ${member.player.last_name}</h4>
                    <div class="rating">Рейтинг: ${Math.round(member.player.rating)}</div>
                </div>
            </div>
            <div class="member-status">
                ${member.is_leader ? '<span class="leader-badge">Лидер</span>' : ''}
            </div>
        </div>
    `).join('');
    
    membersList.innerHTML = membersHtml;
    
    // Display room actions
    const roomActions = document.getElementById('room-actions');
    
    // Получаем информацию о пользователе для проверки роли
    let isLeader = false;
    let isInRoom = false;
    
    try {
        const playerResponse = await fetch(`/players/${currentUser.id}`);
        if (playerResponse.ok) {
            const player = await playerResponse.json();
            isLeader = room.members.find(m => m.player.id === player.id)?.is_leader || false;
            isInRoom = room.members.find(m => m.player.id === player.id) !== undefined;
        }
    } catch (error) {
        console.error('Ошибка получения информации о пользователе:', error);
    }
    
    let actionsHtml = '';
    
    if (isInRoom) {
        actionsHtml += `
            <button class="action-btn leave-room-btn" onclick="leaveRoom(${room.id})">
                🚪 Покинуть комнату
            </button>
        `;
    }
    
    if (isLeader && room.members.length >= 2 && !room.is_game_started) {
        actionsHtml += `
            <button class="action-btn start-game-btn" onclick="startGame(${room.id})">
                🏸 Начать игру
            </button>
        `;
    }
    
    if (isLeader && room.is_game_started) {
        actionsHtml += `
            <button class="action-btn btn-primary" onclick="showScoreForm()">
                📊 Ввести счет
            </button>
        `;
    }
    
    roomActions.innerHTML = actionsHtml;
}

// Leave room
async function leaveRoom(roomId) {
    try {
        // Получаем информацию о пользователе из базы данных
        const playerResponse = await fetch(`/players/${currentUser.id}`);
        if (!playerResponse.ok) {
            showMessage('Ошибка: пользователь не найден в базе данных', 'error');
            return;
        }
        
        const player = await playerResponse.json();
        
        const response = await fetch(`/rooms/${roomId}/leave?player_id=${player.id}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('Успешно покинули комнату', 'success');
            currentRoom = null;
            setTimeout(() => {
                showSection('search-rooms');
                loadRooms();
            }, 1500);
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Ошибка выхода из комнаты', 'error');
        }
    } catch (error) {
        console.error('Leave room error:', error);
        showMessage('Ошибка сети', 'error');
    }
}

// Start game
async function startGame(roomId) {
    try {
        const response = await fetch(`/rooms/${roomId}/start`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('Игра началась!', 'success');
            setTimeout(() => {
                showRoomDetails(roomId);
            }, 1500);
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Ошибка запуска игры', 'error');
        }
    } catch (error) {
        console.error('Start game error:', error);
        showMessage('Ошибка сети', 'error');
    }
}

// Show score form
function showScoreForm() {
    showSection('game-score');
}

// Handle game score submission
async function handleGameScore(event) {
    event.preventDefault();
    
    const scoreTeam1 = parseInt(document.getElementById('score-team1').value);
    const scoreTeam2 = parseInt(document.getElementById('score-team2').value);
    
    if (!currentRoom) {
        showMessage('Ошибка: комната не найдена', 'error');
        return;
    }
    
    try {
        const response = await fetch('/games/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                room_id: currentRoom.id,
                score_team1: scoreTeam1,
                score_team2: scoreTeam2
            })
        });
        
        if (response.ok) {
            const game = await response.json();
            showMessage('Игра завершена! Рейтинги обновлены.', 'success');
            setTimeout(() => {
                showRoomDetails(currentRoom.id);
            }, 2000);
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Ошибка завершения игры', 'error');
        }
    } catch (error) {
        console.error('Game score error:', error);
        showMessage('Ошибка сети', 'error');
    }
}

// Handle create room
async function handleCreateRoom(event) {
    event.preventDefault();
    
    const roomName = document.getElementById('room-name').value;
    
    console.log('Creating room:', { roomName, currentUser });
    
    if (!currentUser || !currentUser.id) {
        showMessage('Ошибка: пользователь не определен', 'error');
        console.error('Current user is not defined:', currentUser);
        return;
    }
    
    // Сначала получаем информацию о пользователе
    try {
        const playerResponse = await fetch(`/players/${currentUser.id}`);
        if (!playerResponse.ok) {
            showMessage('Ошибка: пользователь не найден в базе данных', 'error');
            return;
        }
        
        const player = await playerResponse.json();
        
        const requestBody = {
            name: roomName,
            creator_id: player.id  // Используем ID из базы данных, а не Telegram ID
        };
        
        console.log('Sending request to /rooms/', requestBody);
        
        const response = await fetch('/rooms/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const room = await response.json();
            console.log('Room created successfully:', room);
            showMessage('Комната создана!', 'success');
            setTimeout(() => {
                showRoomDetails(room.id);
            }, 1500);
        } else {
            const error = await response.json();
            console.error('API error:', error);
            showMessage(error.detail || 'Ошибка создания комнаты', 'error');
        }
    } catch (error) {
        console.error('Create room error:', error);
        showMessage('Ошибка сети: ' + error.message, 'error');
    }
}

// Show message
function showMessage(text, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;
    
    const app = document.getElementById('app');
    app.insertBefore(messageDiv, app.firstChild);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Utility function to get rating category
function getRatingCategory(rating) {
    if (rating < 500) return 'F';
    if (rating < 600) return 'E-';
    if (rating < 700) return 'E';
    if (rating < 800) return 'E+';
    if (rating < 900) return 'D-';
    if (rating < 1000) return 'D';
    if (rating < 1100) return 'D+';
    if (rating < 1200) return 'C-';
    if (rating < 1300) return 'C';
    if (rating < 1400) return 'C+';
    if (rating < 1500) return 'B-';
    if (rating < 1600) return 'B';
    if (rating < 1700) return 'B+';
    if (rating < 1800) return 'A-';
    if (rating < 1900) return 'A';
    return 'A+';
}

// Handle start game (для лидера)
async function handleStartGame() {
    if (!currentRoom) {
        showMessage('Ошибка: комната не выбрана', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/rooms/${currentRoom.id}/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                leader_id: currentUser.id
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage('🎮 Игра началась!', 'success');
            
            // Переходим к экрану игры
            setTimeout(() => {
                showGameScore(currentRoom.id);
            }, 1500);
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Ошибка начала игры', 'error');
        }
    } catch (error) {
        console.error('Start game error:', error);
        showMessage('Ошибка сети при начале игры', 'error');
    }
}

// Handle join room
async function handleJoinRoom() {
    if (!currentRoom) {
        showMessage('Ошибка: комната не выбрана', 'error');
        return;
    }
    
    try {
        // Получаем информацию о пользователе из базы данных
        const playerResponse = await fetch(`/players/${currentUser.id}`);
        if (!playerResponse.ok) {
            showMessage('Ошибка: пользователь не найден в базе данных', 'error');
            return;
        }
        
        const player = await playerResponse.json();
        
        const response = await fetch(`/rooms/${currentRoom.id}/join?player_id=${player.id}`);
        
        if (response.ok) {
            const result = await response.json();
            showMessage('✅ Вы присоединились к комнате!', 'success');
            
            // Обновляем отображение комнаты
            setTimeout(() => {
                showRoomDetails(currentRoom.id);
            }, 1500);
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Ошибка присоединения к комнате', 'error');
        }
    } catch (error) {
        console.error('Join room error:', error);
        showMessage('Ошибка сети при присоединении к комнате', 'error');
    }
}
