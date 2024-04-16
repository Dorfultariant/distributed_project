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
    StartTime DATE NOT NULL,
    EndTime DATE NOT NULL,
    IsAvailable BOOLEAN NOT NULL DEFAULT TRUE
);


CREATE TABLE RoomTimeSlots (
    FK_RoomID INT NOT NULL,
    FK_TimeSlotID INT NOT NULL,
    FOREIGN KEY (FK_RoomID) REFERENCES Room(RoomID) ON DELETE CASCADE,
    FOREIGN KEY (FK_TimeSlotID) REFERENCES TimeSlot(TimeSlotID) ON DELETE CASCADE
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


CREATE VIEW FreeTimeSlots AS
    SELECT r.RoomID AS "Room ID",
        r.Name AS "Room",
        ts.StartTime AS "Start",
        ts.EndTime AS "End"
    FROM Room r
    JOIN RoomTimeSlots rts ON r.RoomID = rts.FK_RoomID
    JOIN TimeSlot ts ON rts.FK_TimeSlotID = ts.TimeSlotID
    --GROUP BY r.RoomID, r.Name, ts.StartTime, ts.EndTime
    ORDER BY ts.StartTime;

