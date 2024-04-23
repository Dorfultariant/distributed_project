CREATE TABLE Member (
    UserID INTEGER PRIMARY KEY NOT NULL,
    UserName CHAR(100) UNIQUE NOT NULL,
    Name CHAR(100) NOT NULL,
    PASSWORD CHAR(256) NOT NULL,
    SALT CHAR(256) NOT NULL
);

CREATE TABLE Room (
    RoomID INTEGER PRIMARY KEY NOT NULL,
    Name CHAR(100) NOT NULL
);

CREATE TABLE TimeSlot (
    TimeSlotID INTEGER PRIMARY KEY NOT NULL,
    FK_RoomID INT NOT NULL,
    Date DATE NOT NULL,
    StartTime TIME NOT NULL,
    IsAvailable BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (FK_RoomID) REFERENCES Room(RoomID) ON DELETE CASCADE
);

CREATE TABLE Reservation (
    ReservationID INTEGER PRIMARY KEY NOT NULL,
    ReservationDate DATE NOT NULL,
    FK_TimeSlotID INT NOT NULL,
    FK_RoomID INT NOT NULL,
    FK_UserID INT NOT NULL,
    FOREIGN KEY (FK_TimeSlotID) REFERENCES TimeSlot(TimeSlotID) ON DELETE CASCADE,
    FOREIGN KEY (FK_RoomID) REFERENCES Room(RoomID) ON DELETE CASCADE,
    FOREIGN KEY (FK_UserID) REFERENCES Member(UserID) ON DELETE CASCADE
);



-- INSERT OPERATIONS TO CREATE A DATABASE
--


-- Making a test-user
INSERT INTO Member VALUES (1, 'Tester', 'test', '1234', 'SALT');

-- Inserting rooms here
INSERT INTO Room (RoomID, Name)
VALUES (1, 'Da Gaming Lounge');

-- Inserting Timeslots here, beginning with monday...
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (1, 1, '2024-04-15', '08:00:00', TRUE),
       (2, 1, '2024-04-15', '09:00:00', FALSE),
       (3, 1, '2024-04-15', '10:00:00', TRUE),
       (4, 1, '2024-04-15', '11:00:00', FALSE),
       (5, 1, '2024-04-15', '12:00:00', TRUE),
       (6, 1, '2024-04-15', '13:00:00', TRUE),
       (7, 1, '2024-04-15', '14:00:00', TRUE),
       (8, 1, '2024-04-15', '15:00:00', TRUE);

-- Tuesday here... 
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (9, 1, '2024-04-16', '08:00:00', TRUE),
       (10, 1, '2024-04-16', '09:00:00', TRUE),
       (11, 1, '2024-04-16', '10:00:00', TRUE),
       (12, 1, '2024-04-16', '11:00:00', TRUE),
       (13, 1, '2024-04-16', '12:00:00', TRUE),
       (14, 1, '2024-04-16', '13:00:00', TRUE),
       (15, 1, '2024-04-16', '14:00:00', TRUE),
       (16, 1, '2024-04-16', '15:00:00', TRUE);

-- Wednesday here... 
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (17, 1, '2024-04-17', '08:00:00', TRUE),
       (18, 1, '2024-04-17', '09:00:00', TRUE),
       (19, 1, '2024-04-17', '10:00:00', TRUE),
       (20, 1, '2024-04-17', '11:00:00', TRUE),
       (21, 1, '2024-04-17', '12:00:00', TRUE),
       (22, 1, '2024-04-17', '13:00:00', TRUE),
       (23, 1, '2024-04-17', '14:00:00', TRUE),
       (24, 1, '2024-04-17', '1username5:00:00', TRUE);

-- Thursday here... 
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (25, 1, '2024-04-18', '08:00:00', TRUE),
       (26, 1, '2024-04-18', '09:00:00', TRUE),
       (27, 1, '2024-04-18', '10:00:00', TRUE),
       (28, 1, '2024-04-18', '11:00:00', TRUE),
       (29, 1, '2024-04-18', '12:00:00', TRUE),
       (30, 1, '2024-04-18', '13:00:00', TRUE),
       (31, 1, '2024-04-18', '14:00:00', TRUE),
       (32, 1, '2024-04-18', '15:00:00', TRUE);

-- Friday here... 
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (33, 1, '2024-04-19', '08:00:00', TRUE),
       (34, 1, '2024-04-19', '09:00:00', TRUE),
       (35, 1, '2024-04-19', '10:00:00', TRUE),
       (36, 1, '2024-04-19', '11:00:00', TRUE),
       (37, 1, '2024-04-19', '12:00:00', TRUE),
       (38, 1, '2024-04-19', '13:00:00', TRUE),
       (39, 1, '2024-04-19', '14:00:00', TRUE),
       (40, 1, '2024-04-19', '15:00:00', TRUE);

-- Saturday here... 
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (41, 1, '2024-04-20', '08:00:00', TRUE),
       (42, 1, '2024-04-20', '09:00:00', TRUE),
       (43, 1, '2024-04-20', '10:00:00', TRUE),
       (44, 1, '2024-04-20', '11:00:00', TRUE),
       (45, 1, '2024-04-20', '12:00:00', TRUE),
       (46, 1, '2024-04-20', '13:00:00', TRUE),
       (47, 1, '2024-04-20', '14:00:00', TRUE),
       (48, 1, '2024-04-20', '15:00:00', TRUE);

-- Sunday here... 
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (49, 1, '2024-04-21', '08:00:00', TRUE),
       (50, 1, '2024-04-21', '09:00:00', TRUE),
       (51, 1, '2024-04-21', '10:00:00', TRUE),
       (52, 1, '2024-04-21', '11:00:00', TRUE),
       (53, 1, '2024-04-21', '12:00:00', TRUE),
       (54, 1, '2024-04-21', '13:00:00', TRUE),
       (55, 1, '2024-04-21', '14:00:00', TRUE),
       (56, 1, '2024-04-21', '15:00:00', TRUE);



INSERT INTO Reservation
    (ReservationID, ReservationDate, FK_TimeSlotID, FK_RoomID, FK_UserID)
    VALUES (1, '2024-04-16', 2, 1, 1),
       (2, '2024-04-16', 4, 1, 1);
       
CREATE VIEW FreeTimeSlots AS
    SELECT r.RoomID AS "Room ID",
        r.Name AS "Room",
        ts.Date AS "Date",
        ts.StartTime AS "Start Time",
        ts.IsAvailable AS "Available"
    FROM Room r
    JOIN TimeSlot ts ON ts.FK_RoomID = r.RoomID
    ORDER BY ts.StartTime;

CREATE VIEW UserReservations AS
    SELECT
        rs.ReservationID AS "RID",
        u.UserID AS "UID",
        u.UserName AS "Name",
        r.RoomID AS "Room ID",
        r.Name AS "Room",
        ts.Date AS "Date",
        ts.StartTime AS "Start Time"
FROM Member u
    JOIN TimeSlot ts    ON rs.FK_TimeSlotID = ts.TimeSlotID
    JOIN Room r         ON rs.FK_RoomID     = r.RoomID
    JOIN Reservation rs ON rs.FK_UserID     = u.UserID
    ORDER BY ts.Date;




