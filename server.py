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


loggedUsers = {
}


dbInitFile = "db_init.sql"
dbFile = "main.db"


def initConnection():
    db = sq.connect(dbFile)
    cur = db.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    return db, cur


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
        # x=7
        # for i in range(1,8):
        #     x=x+1
        #     cur.execute("INSERT INTO Room1 (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday) VALUES (?, ?, ?, ?, ?, ?, ?);", (x, x, x, x, x, x, x))

        
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
TODO: CHANGE SECRETS
"""


_SECRET_KEY = "secret auth key"
_SECRET_SALT_SEED = 59050


### NOTE: THIS CLASS IS FOR INTERCEPTING AND VERIFYING USER REQUESTS VIA TOKEN AUTHENTICATION:
class AuthenticationInterceptor(grpc.ServerInterceptor):
    def __init__(self):
        self._exclude_methods = ["CreateAccount", "Login", "PingServer"]
        def abort(ignored_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid Signature")
        self._abort_handler = grpc.unary_unary_rpc_method_handler(abort)

    def intercept_service(self, continuation, handler_call_details):

        method = handler_call_details.method.split('/')[::-1][0]
        print("Method called", method)
        if method in self._exclude_methods:
            return continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        if "token" in metadata :
            print("\nToken to decode: ", metadata["token"])
            print()
            try:
                jwt.decode(metadata["token"],_SECRET_KEY, algorithms=["HS256"])
                return continuation(handler_call_details)

            except jwt.InvalidTokenError as e:
                print(e)

        return self._abort_handler

"""

"""
def generate_token(username):
    pl = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }

    token = jwt.encode(pl, _SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token):
    try:
        payload = jwt.decode(
            token,
            key=_SECRET_KEY,
            algorithms=["HS256"],
        )
        return True
    except jwt.ExpiredSignatureError as e:
        print(e)
    return False


### NOTE: PASSWORD HASHING FOR DATABASE STORAGE
def hash_passwd(passwd):
    salt = os.urandom(_SECRET_SALT_SEED)

    key = hashlib.pbkdf2_hmac(
        'sha256',
        passwd.encode("utf-8"),
        salt,
        100000
    )
    return salt, key


def verify_passwd(salt, key, passwd):
    newKey = hashlib.pbkdf2_hmac(
        "sha256",
        passwd.encode("utf-8"),
        salt,
        100000
        )
    return key == newKey


class ReservationServiceServicer(reservation_pb2_grpc.ReservationServiceServicer):

    def PingServer(self, request, context):
        return reservation_pb2.PingServerResponse(ping="Server reached", isPinging=True)

    def CreateAccount(self, request, context):
        ### FOR EACH USER // REQUEST, A NEW CUR AND DB ARE CREATED TO ACCESS DATABASE
        db, cur = initConnection()

        uName = request.username
        name = request.name

        ### CHECKING WHETHER USER ALREADY EXISTS IN DATABASE
        cmd = "SELECT username FROM Member WHERE username = ?;"
        cur.execute(cmd, (uName,))
        if cur.fetchall():
            return reservation_pb2.CreateAccountResponse(message="User already exists", token=None)

        ### IF NOT THEN WE CAN MOVE ON
        newToken = generate_token(uName)
        salt, hashPasswd = hash_passwd(request.password)

        print()
        print("Generated token: ", newToken)
        print()

        cmd = "INSERT INTO Member (USERNAME, NAME, PASSWORD, SALT) VALUES (?, ?, ?, ?);"

        try:
            cur.execute(cmd, (uName, name, hashPasswd, salt,))

            db.commit()
            db.close()

        except sq.Error as e:
            print(e)
            db.rollback()
            db.close()
            return reservation_pb2.CreateAccountResponse(message="Could not add user", token=None)

        loggedUsers[uName] = newToken
        return reservation_pb2.CreateAccountResponse(message="User added successfully", token=newToken)


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

        except sq.Error as e:
            print("User not found:", e)
            db.close()
            return reservation_pb2.LoginResponse(message="Incorrect credentials", isValid=False, token=None)

        if not verify_passwd(info[4], info[3], uPass):
            print("User password was incorrect")
            return reservation_pb2.LoginResponse(message="Incorrect credentials", isValid=False, token=None)

        newToken = generate_token(uName)
        loggedUsers[uName] = newToken
        print()
        print("Generated token: ", newToken)
        print()
        return reservation_pb2.LoginResponse(message="Successful Login", isValid=True, token=newToken)


    def Logout(self, request, context):
        uName = request.username
        db, cur = initConnection()
        cmd = "SELECT username FROM Member WHERE username = ?;"
        try:
            cur.execute(cmd, (uName,))
            if not cur.fetchall():
                db.close()
                return reservation_pb2.LogoutResponse(message="User not found from database", token=request.token)
            if not verify_token(request.token):
                db.close()
                return reservation_pb2.LogoutResponse(message="Token is invalid...", token=request.token)
        except sq.Error as e:
            print("\nSQLITE error in Logout:\n ", e)

        loggedUsers.pop(uName)

        return reservation_pb2.LogoutResponse(message="Successful Logout", token=None)

    def FetchRooms(self, request, context):
        db, cur = initConnection()
        cmd = "SELECT Name FROM Room;"
        info = None
        try:
            cur.execute(cmd)
            info = cur.fetchall()
            print("Info: ", info)
            for room in info:
                yield reservation_pb2.FetchRoomsResponse(rooms=room)

        except sq.Error as e:
            print(e)
            db.close()
            return reservation_pb2.FetchRoomsResponse(rooms=None)
        finally:
            db.close()

    def FetchAvailableSlots(self, request, context):
        ## Test data:
        db, cur = initConnection()
        room = request.room
        date = request.date
        cmd = """SELECT * FROM FreeTimeSlots WHERE "Room" = ? AND Date = ?;"""
        cur.execute(cmd, (room,date,))

        dat = cur.fetchall()
        startTime = [ r[3] for r in dat ]
        msg = f"Available slots for {date}"

        yield reservation_pb2.FetchAvailableSlotsResponse(message=msg, slots=startTime)

        db.close()


    def MakeReservation(self, request, context):
        uname = request.username
        room = request.room
        timeslot = request.timeslot
        print("User:",uname, " Room:", room, " Time:",timeslot)

        cmd = "SELECT "

        return reservation_pb2.MakeReservationResponse(message="Successful reservation", isSuccessful=True)


    def ViewReservations(self, request, context):

        return reservation_pb2.ViewReservationsResponse(reservations="List of your reservations:")


    def CancelReservation(self, request, context):

        return reservation_pb2.CancelReservationResponse(message="Successfully removed reservation")


def serve():
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
