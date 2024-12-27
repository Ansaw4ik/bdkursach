DROP TABLE IF EXISTS QueueHistory CASCADE;
DROP TABLE IF EXISTS EntryComments CASCADE;
DROP TABLE IF EXISTS EntryFiles CASCADE;
DROP TABLE IF EXISTS QueueEntries CASCADE;
DROP TABLE IF EXISTS Queues CASCADE;
DROP TABLE IF EXISTS RoomParticipants CASCADE;
DROP TABLE IF EXISTS Rooms CASCADE;
DROP TABLE IF EXISTS Roles CASCADE;
DROP TABLE IF EXISTS Users CASCADE;


-- Создание таблицы пользователей
CREATE TABLE Users (
    email VARCHAR(255) PRIMARY KEY,
    password bytea NOT NULL
);


-- Создание таблицы ролей
CREATE TABLE Roles (
    role_name VARCHAR(255) PRIMARY KEY
);

-- Создание таблицы комнат
CREATE TABLE Rooms (
    room_id UUID PRIMARY KEY,
    creator_email VARCHAR(255) REFERENCES Users(email),
    room_name VARCHAR(255) NOT NULL,
    room_password bytea NOT NULL
);

-- Создание таблицы участников комнат
CREATE TABLE RoomParticipants (
    email VARCHAR(255) REFERENCES Users(email),
    room_id UUID  REFERENCES Rooms(room_id),
    role_name VARCHAR(255) REFERENCES Roles(role_name),
    username_in_room VARCHAR(255) NOT NULL,
    CONSTRAINT room_participant_pkey PRIMARY KEY (email, room_id)
);

-- Создание таблицы очередей
CREATE TABLE Queues (
    queue_id SERIAL PRIMARY KEY,
    room_id UUID REFERENCES Rooms(room_id),
    queue_name VARCHAR(255) NOT NULL,
    creation_date TIMESTAMP WITH TIME ZONE NOT NULL,
    available_entries INTEGER,
    entry_end_time TIMESTAMP WITH TIME ZONE,
    deletion_time TIMESTAMP WITH TIME ZONE
);

-- Создание таблицы записей в очереди
CREATE TABLE QueueEntries (
    entry_id INTEGER NOT NULL, -- ID записи внутри очереди
    queue_id INTEGER REFERENCES Queues(queue_id), -- Связь с очередью
    creator_email VARCHAR(255) REFERENCES Users(email),
    username_in_room VARCHAR(255) NOT NULL,
    room_id UUID,
    entry_subject VARCHAR(255),
    creation_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_completed BOOLEAN,
    PRIMARY KEY (entry_id, queue_id) -- Уникальность пары queue_id + entry_id
);


-- Создание таблицы файлов к записям
CREATE TABLE EntryFiles (
    entry_id INTEGER REFERENCES QueueEntries(entry_id),
    queue_id INTEGER REFERENCES Queues(queue_id),
  
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    CONSTRAINT entry_files_pkey PRIMARY KEY (entry_id, queue_id) --Изменён первичный ключ
);


-- Создание таблицы комментариев к записям
CREATE TABLE EntryComments (
    comment_id SERIAL PRIMARY KEY,
    entry_id INTEGER REFERENCES QueueEntries(entry_id),
    queue_id INTEGER REFERENCES Queues(queue_id),
    comment_text TEXT NOT NULL,
    commentator_email VARCHAR(255) REFERENCES Users(email),
    creation_date TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Создание таблицы истории очередей
CREATE TABLE QueueHistory (
    history_id SERIAL PRIMARY KEY,
    room_id UUID REFERENCES Rooms(room_id),
    queue_id INTEGER REFERENCES Queues(queue_id),
    action_type VARCHAR(255), --  (добавление, удаление, изменение)
    modification_date TIMESTAMP WITH TIME ZONE
);

INSERT INTO roles (role_name) VALUES ('Admin'), ('User');