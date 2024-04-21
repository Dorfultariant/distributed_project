## THREADING
from concurrent import futures
## GRPC tooling
import grpc
import reservation_pb2
import reservation_pb2_grpc

## TOKEN AND AUTHENTICATION
import jwt
import hashlib

## DB AND DATE
import sqlite3 as sq
import datetime
import os


## Connects username to their access token
loggedUsers = {
}

# Initialization and database files
dbInitFile = "db_init.sql"
dbFile = "main.db"

"""
WARNING: CHANGE SECRETS AND MOVE TO ENVIRONMENT VARIABLES
"""
_SECRET_KEY = """secret auth wallop key to be changed in the future
                wallop if this ever sees internet. As that is very unlikely, this will
                do just fine for this project, wallop"""

"""
Establishes a connection to the database and returns the database connection and cursor.

Returns:
    db (sqlite3.Connection): The database connection.
    cur (sqlite3.Cursor): The database cursor.
"""

def initConnection():
    db = sq.connect(dbFile)
    cur = db.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    return db, cur

"""
Initializes the database with basic information. This function is only executed when main.db does not exist.

Returns:
    bool: True if the database file is found or successfully created, False otherwise.
"""

def initDB():
    if os.path.isfile(dbFile):
        print("DB FILE FOUND")
        db, cur = initConnection()
        return True
    db, cur = initConnection()
    try:
        print("DB FILE NOT FOUND")
        print("Creating database")

        f = open(dbInitFile, "r")
        command = ""

        for l in f.readlines():
            command += l
        cur.executescript(command)

        db.commit()
        print("Database created succesfully")

    except FileNotFoundError:
        print(f"'{dbInitFile}' file not found. Abort!")
        print(f"Include '{dbInitFile}' file in the same folder as databaser.py")
        return False

    except sq.Error as e:
        print("Hmm, something went sideways. Abort!")
        print(e)
        db.rollback()
        db.close()
        return False
    db.close()

    return True


"""
A Class for intercepting, generating and verifying user
    request via token authentication
"""

class AuthenticationInterceptor(grpc.ServerInterceptor):

    """
        Authenticator initialization with request exceptions to authentication
            as token does not yet exist at those points.
    """
    def __init__(self):
        self._exclude_methods = ["CreateAccount", "Login", "PingServer"]
        def abort(ignored_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid Signature")
        self._abort_handler = grpc.unary_unary_rpc_method_handler(abort)

    """
        Verifies the token during the intercept of requests.

        Parameters:
            continuation (callable): A function that takes a HandlerCallDetails and proceeds to invoke the next interceptor in the chain, if any.
            handler_call_details (grpc.HandlerCallDetails): A HandlerCallDetails describing the RPC.

        Returns:
            grpc.RpcMethodHandler: The handler to process the incoming RPC.
    """
    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method.split('/')[::-1][0]
        if method in self._exclude_methods:
            return continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        if "token" in metadata :
            try:
                jwt.decode(metadata["token"],_SECRET_KEY, algorithms=["HS256"])
                return continuation(handler_call_details)

            except jwt.InvalidTokenError as e:
                print(e)

        return self._abort_handler

    ### Method used to create token for user
    ### NOTE: Token has an expiration time which is checked during intercept
    """
        Generates the token during account creation and login.

        Parameters:
            Username (string): Username for which the token is generated
        Returns:
            Token (string): Generated token
    """
    def generate_token(self, username):
        pl = {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }
        try:
            token = jwt.encode(pl, _SECRET_KEY, algorithm="HS256")
        except jwt.DecodeError as e:
            print("Error while encoding jwt: ",e)
        return token


### NOTE: Password hashing function
"""
    Generates salt and hashed version of user password to be stored in a database

    Parameters:
        Password (string): Users password to be hashed

    Returns:
        Salt (string): For the password
        Hash (string): Salt + password hash
"""

def hashPasswd(passwd):
    salt = None
    key = None
    try:
        # Generates 16 bytes of random data as salt for each user
        salt = os.urandom(32)
    
        key = hashlib.pbkdf2_hmac(
        'sha256',
        passwd.encode("utf-8"),
        salt,
        100000
    )
    except Exception as e:
        print("error while hashing or salting key: ",e)
    return salt, key

"""
    Verifies user password based on their salt and given password

    Parameters:
        Salt (string): Salt from database matching username
        Key (string): Hash from database matching username
        Password (string): Given by the user during login
    Returns:
        Bool: True if keys match, False otherwise
"""

def verifyPasswd(salt, key, passwd):
    newKey = None
    try:
        newKey = hashlib.pbkdf2_hmac(
            "sha256",
            passwd.encode("utf-8"),
            salt,
            100000
        )
    except Exception as e:
        print("Error while generating new key:", e)
    return key == newKey


"""
    Main Reservation Class that handles main logic of services this application provides

    All methods generated with .proto file are implemented here.
"""

class ReservationServiceServicer(reservation_pb2_grpc.ReservationServiceServicer):
    ## Interceptor for handling user authentications
    def __init__(self):
        self._auth_intrcptr = AuthenticationInterceptor()

    ## Testing connection between server and client
    def PingServer(self, request, context):
        return reservation_pb2.PingServerResponse(ping="Server reached", isPinging=True)

    """
        Method for creating a new user and adding them to the database.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Object containing message and token
    """
    def CreateAccount(self, request, context):
        ### FOR EACH USER // REQUEST, A NEW CUR AND DB ARE CREATED TO ACCESS DATABASE
        try:
            db, cur = initConnection()
        except Exception as e:
            print("Error connecting to server")
        uName = str(request.username)
        name = str(request.name)
        password = str(request.password)

        if len(uName) < 1 or len(name) < 1 or len(password) < 1:
            return reservation_pb2.CreateAccountResponse(
                message="Credentials are too short.",
                token=None
            )

        ### CHECKING WHETHER USER ALREADY EXISTS IN DATABASE
        cmd = "SELECT username FROM Member WHERE username = ?;"
        cur.execute(cmd, (uName,))
        if cur.fetchall():
            return reservation_pb2.CreateAccountResponse(
                message="User already exists", token=None
            )

        ### IF NOT THEN WE CAN MOVE ON
        newToken = self._auth_intrcptr.generate_token(uName)

        salt, hashedPasswd = hashPasswd(password)

        cmd = "INSERT INTO Member (USERNAME, NAME, PASSWORD, SALT) VALUES (?, ?, ?, ?);"

        try:
            cur.execute(cmd, (uName, name, hashedPasswd, salt,))

            db.commit()
            db.close()

        except sq.Error as e:
            print("Error while inserting data to Member",e)
            db.rollback()
            db.close()
            return reservation_pb2.CreateAccountResponse(message="Could not add user", token=None)

        loggedUsers[uName] = newToken
        return reservation_pb2.CreateAccountResponse(message="User added successfully", token=newToken)

    """
        Method for logging in a user based on their given credentials and
            data found from database.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Object containing message and token
    """
    def Login(self, request, context):
        uName = request.username
        uPass = request.password

        cmd = "SELECT * FROM Member WHERE username = ?;"
        db, cur = initConnection()

        info = []
        try:
            cur.execute(cmd, (uName,))
            info = cur.fetchone()
            db.close()
            if info is None:
                return reservation_pb2.LoginResponse(
                    message="User not found.", isValid=False, token=None)


        except sq.Error as e:
            print("User not found:", e)
            db.close()
            return reservation_pb2.LoginResponse(message="Incorrect credentials", isValid=False, token=None)

        if not verifyPasswd(info[4], info[3], uPass):
            print("User password was incorrect")
            return reservation_pb2.LoginResponse(message="Incorrect credentials", isValid=False, token=None)

        newToken = self._auth_intrcptr.generate_token(uName)
        loggedUsers[uName] = newToken
        return reservation_pb2.LoginResponse(message="Successful Login", isValid=True, token=newToken)

    """
        Method for logging out a user based on their given token and
            data found from database.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Object containing message and token (None)
    """

    def Logout(self, request, context):
        uName = request.username

        try:
            db, cur = initConnection()
        except Exception as e:
            print("Error connecting to server")
        cmd = "SELECT username FROM Member WHERE username = ?;"
        try:
            cur.execute(cmd, (uName,))
            if not cur.fetchall():
                db.close()
                return reservation_pb2.LogoutResponse(
                    message="User not found from database",
                    token=request.token)

        except sq.Error as e:
            print("\nSQLITE error in Logout:\n ", e)

        loggedUsers.pop(uName)
        return reservation_pb2.LogoutResponse(message="Successful Logout", token=None)

    """
        Method for fetching available rooms for the client from database.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Stream of rooms
    """
    def FetchRooms(self, request, context):
        try:
            db, cur = initConnection()
        except Exception as e:
            print("Error connecting to server")
        try:  
            cmd = "SELECT Name FROM Room;"
        except Exception as e:
            print("Error getting name for room",e)
        info = None
        try:
            cur.execute(cmd)
            info = cur.fetchall()
            print("Info: ", info)
            for room in info:
                yield reservation_pb2.FetchRoomsResponse(rooms=room)

        except sq.Error as e:
            print("Errow while fetching rooms",e)
            db.close()
            return reservation_pb2.FetchRoomsResponse(rooms=None)
        finally:
            db.close()
    """
        Method for fetching available timeslots from the database to be sent to the
            client as a stream.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Stream of messages and timeslots
    """

    def FetchAvailableSlots(self, request, context):
        
        try:
            db, cur = initConnection()
            room = request.room
            date = request.date
            cmd = """SELECT * FROM FreeTimeSlots WHERE "Available" = True AND "Room" = ? AND Date = ?;"""
            cur.execute(cmd, (room,date,))
            dat = cur.fetchall()
            startTime = [ r[3] for r in dat ]
            msg = f"Available slots for {date}"
            yield reservation_pb2.FetchAvailableSlotsResponse(message=msg, slots=startTime)
            db.close()
        except grpc.RpcError as e:
            print("Error while fetching available slots", e.code(), e.details())
        except Exception as e:
            print("Error fetching slots: ", e)

    """
        Method for making reservation for a user if the slot is still available.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Object containing message and boolean indicating the
                    success.
    """

    def MakeReservation(self, request, context):
        try:
            uname = request.username
            room = request.room
            timeslot = request.timeslot    
            date = request.date    

        except Exception as e:
            print("Error while getting data from request: ", e)
            print("User:",uname, " Room:", room, " Time:",timeslot, "Date:", date)
            return reservation_pb2.MakeReservationResponse(
                message="Unable to make reservation.", isSuccessful=False)

        db, cur = initConnection()
        
        # Construct the SQL insert query
        cmd = """
            INSERT INTO Reservation (ReservationDate, FK_TimeSlotID, FK_RoomID, FK_UserID)
            VALUES (?, 
            (SELECT TimeSlotID FROM TimeSlot WHERE Date = ? AND StartTime = ? AND FK_RoomID = (SELECT RoomID FROM Room WHERE Name = ?)), 
            (SELECT RoomID FROM Room WHERE Name = ?), 
            (SELECT UserID FROM Member WHERE Username = ?))
            """
        try:
            # Add to database the reservation + set timeslot to reserved
            cur.execute(cmd, (date, date, timeslot, room, room, uname))
            cmd = '''UPDATE TimeSlot SET isAvailable = False WHERE TimeSlotID = (SELECT TimeSlotID FROM TimeSlot WHERE Date = ? AND StartTime = ? AND FK_RoomID = (SELECT RoomID FROM Room WHERE Name = ?));'''
            cur.execute(cmd, (date, timeslot, room))
            db.commit()

        except sq.Error as e:
            print("Reservation failed:",e)
            return reservation_pb2.MakeReservationResponse(
                message="Timeslot is not available anymore.",
                isSuccessful=False)

        return reservation_pb2.MakeReservationResponse(
            message="Successful reservation",
            isSuccessful=True)

    """
        Method for fetching reservation existing reservation information
            of a user.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Reservations as a ; and newline separated string.
    """

    def ViewReservations(self, request, context):
        uname = request.username

        if '-' in uname:
            uname.replace('-','')
        try:
            db, cur = initConnection()
        except Exception as e:
            print("Error connecting to the database: ", e)
            return reservation_pb2.ViewReservationsResponse(message="Database connection error")
        try:
            
            cmd = "SELECT UserID FROM Member WHERE UserName = ?;"
            cur.execute(cmd, (uname,))
            uid = cur.fetchone()
            if uid == None:
                print("No user found in ViewReservations...")
                return reservation_pb2.ViewReservationsResponse(message="No user found")

            uid = int(uid[0])

            cmd = """SELECT * FROM UserReservations WHERE "UID" = ?;"""
            cur.execute(cmd, (uid,))
            reservations = cur.fetchall()

            resString = ""

            ## We want to select specific columns from the query:
            for res in reservations:
                resString += f"{res[0]};"
                resString += f"{res[2]};"
                resString += f"{res[4]};"
                resString += f"{res[5]};"
                resString += f"{res[6]}\n"

            ## Remove trailing newline
            resString = resString.rstrip('\n')

        except sq.Error as e:
            print("Sqlite error during ViewReservations:",e)
            return reservation_pb2.ViewReservationsResponse(
                reservations="")
        except Exception as e:
            print("Error retrieving reservations:", e)
            return reservation_pb2.ViewReservationsResponse(
                reservations="")

        return reservation_pb2.ViewReservationsResponse(reservations=resString)

    """
        Method for cancelling users existing reservation based on reservation id.

        Parameters:
            Request (Request Object): Containing information sent by client
            Context (Context Object): Additional configuration information
        Returns:
            Response (Response Object): Message indicating success or failure
    """

    def CancelReservation(self, request, context):
        try:
            db, cur = initConnection()
            uname = request.username
            rid = request.reservation_id
            ## Fetch userid from db
        except Exception as e:
            print("Error getting information from server: ",e)
        try:
            cmd = '''SELECT UserID FROM Member WHERE UserName = ?;'''
            cur.execute(cmd, (uname,))
            uid = cur.fetchone()
            
        except Exception as e:
            print("Error getting username from database: ",e)
        
        try:
            uid = uid[0]
            rid = int(rid)
            uid = int(uid)

        except IndexError:
            db.close()
            return reservation_pb2.CancelReservationResponse(
                message="No reservation found.")

        except ValueError:
            db.close()
            return reservation_pb2.CancelReservationResponse(
                message="No reservation found.")

        ## Verify that user has reservation match
        cmd = '''SELECT FK_TimeSlotID FROM Reservation WHERE FK_UserID = ? AND ReservationID = ?;'''
        try:
            cur.execute(cmd, (uid, rid,))
            reserv = cur.fetchone()

            tsid = int(reserv[0])
        except sq.OperationalError as e:
            print("SQLITE operational error: ",e)
            db.close()
            return reservation_pb2.CancelReservationResponse(message="No reservation found.")
        except IndexError:
            print("Parse index error.")
            return reservation_pb2.CancelReservationResponse(message="No reservation found.")
        except ValueError:
            print("ValueError in cancelling reservation")
            db.close()
            return reservation_pb2.CancelReservationResponse(message="No reservation found.")
        except TypeError:
            print("TypeError in cancelling reservation")
            db.close()
            return reservation_pb2.CancelReservationResponse(message="No reservation found.")

        try:
            cmd = '''UPDATE TimeSlot SET isAvailable = True WHERE TimeSlotID = ?;'''
            cur.execute(cmd, (tsid,))
            cmd = '''DELETE FROM Reservation WHERE ReservationID = ?;'''
            cur.execute(cmd, (rid,))
            db.commit()
        except sq.OperationalError as e:
            print("Update and delete error: ", e)
            db.rollback()
            db.close()
            return reservation_pb2.CancelReservationResponse(
                message="No reservation found.")

        db.close()
        return reservation_pb2.CancelReservationResponse(
            message="Successfully removed reservation")

"""
    Server serve method which creates the server verification and SSL / TLS connection
        to create an encrypted channel between connecting clients via CA certificates.

    Opens server in localhost to port 44000.
"""
def serve():
    try:
        server = grpc.server(
            futures.ThreadPoolExecutor(),
            interceptors=(AuthenticationInterceptor(),),
        )

        reservation_pb2_grpc.add_ReservationServiceServicer_to_server(ReservationServiceServicer(), server)
        port = 44000

        # stores servers private key and cert
        privateKey = open("server.key", "rb").read()
        certificateChain = open("server.pem", "rb").read()

        # Generate server credentials
        serverCredentials = grpc.ssl_server_credentials(
            ((privateKey, certificateChain),),
        )

        server.add_secure_port("localhost:" + str(port), serverCredentials)
        print("Server rev up on: "+  str(port))
        server.start()
        server.wait_for_termination()
    except Exception as e:
        print("Error starting server:", e)


## Starts server when program file is loaded.
if __name__=="__main__":
    if initDB():
        serve()


# ################################################
# CA Certificate generation commands:
#
# openssl genrsa -out ca.key 2048
# openssl req -x509 -new -nodes -key ca.key -sha256 -days 1024 -out ca.pem
# openssl genrsa -out server.key 2048
# openssl req -new -key server.key -out server.csr
# openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out server.pem -days 500 -sha256
#
