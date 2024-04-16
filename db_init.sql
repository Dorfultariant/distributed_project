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
-- Inserting rooms here
INSERT INTO Room (RoomID, Name)
VALUES (1, 'Gaming Lounge'),
       (2, 'Random example Room');

INSERT INTO Room VALUES (1, "IPH");

CREATE TABLE TimeSlot (
    TimeSlotID INTEGER PRIMARY KEY NOT NULL,
    FK_RoomID INT NOT NULL,
    Date DATE NOT NULL,
    StartTime TIME NOT NULL,
    IsAvailable BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (FK_RoomID) REFERENCES Room(RoomID) ON DELETE CASCADE
);
-- I was here. Me be soon doing stuff
-- Inserting Timeslots here, beginning with monday...
INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime, IsAvailable)
VALUES (1, 1, '2024-04-15', '08:00:00', TRUE),
       (2, 1, '2024-04-15', '09:00:00', TRUE),
       (3, 1, '2024-04-15', '10:00:00', TRUE),
       (4, 1, '2024-04-15', '11:00:00', TRUE),
       (5, 1, '2024-04-15', '12:00:00', TRUE),
       (6, 1, '2024-04-15', '13:00:00', TRUE),
       (7, 1, '2024-04-15', '14:00:00', TRUE),
       (8, 1, '2024-04-15', '15:00:00', TRUE);

       


INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime)
    VALUES (1, 1, "2024-04-20", "08:00:00");

INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime)
    VALUES (2, 1, "2024-04-20", "09:00:00");

INSERT INTO TimeSlot (TimeSlotID, FK_RoomID, Date, StartTime)
    VALUES (3, 1, "2024-04-20", "10:00:00");

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


CREATE VIEW FreeTimeSlots AS
    SELECT r.RoomID AS "Room ID",
        r.Name AS "Room",
        ts.Date AS "Date",
        ts.StartTime AS "Start Time"
    FROM Room r
    JOIN TimeSlot ts ON ts.FK_RoomID = r.RoomID
    --GROUP BY r.RoomID, r.Name, ts.StartTime, ts.EndTime
    ORDER BY ts.StartTime;

