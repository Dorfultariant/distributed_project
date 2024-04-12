# import sqlite3 as sq
# import threading as thread
# from datetime import datetime as dt
# import os
#
#
# dbFile = "main.db"
# dbInitFile = "db_init.sql"
#
#
# db = None
# cur = None
#
#
# def initConnection():
#     global db
#     global cur
#     db = sq.connect(dbFile)
#     cur = db.cursor()
#     cur.execute("PRAGMA foreign_keys = ON;")
#     return True
#
#
# def initDB():
#     if os.path.isfile(dbFile):
#         initConnection()
#         return True
#     initConnection()
#     try:
#         f = open(dbInitFile, "r")
#         command = ""
#         for l in f.readlines():
#             command += l
#         cur.executescript(command)
#         cur.execute('''INSERT INTO User1 VALUES ('0', 'Admin', 'Admin', '1234')''')
#
#
#         db.commit()
#     except FileNotFoundError:
#         print(f"'{dbInitFile}' file not found. Abort!")
#         print(f"Include '{dbInitFile}' file in the same folder as databaser.py")
#         return False
#
#     except sq.Error as e:
#         print("Hmm, something went sideways. Abort!")
#         print(e)
#         return False
#     return True
#
#
#
#
#
# def main():
#     if not initDB(): return -1
#     print ("hello there")
#     return
#
#
# main()


from concurrent import futures
import grpc
import reservation_pb2
import reservation_pb2_grpc
import jwt

import sqlite3 as sq
import datetime

users = {
    "Seppo": "",
}


loggedUsers = {
}


"""
TODO: CHANGE SECRET
"""

_SECRET_KEY = "secret auth key"


class AuthenticationInterceptor(grpc.ServerInterceptor):
    def __init__(self):
        self.exclude_methods = ["CreateAccount", "Login", "PingServer"]
        def abort(ignored_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid Signature")
        self.abort_handler = grpc.unary_unary_rpc_method_handler(abort)


    def intercept_service(self, continuation, handler_call_details):

        print("Handler details: ", handler_call_details)
        method = handler_call_details.method.split('/')[::-1][0]
        print("Method used: ", method)

        if method in self.exclude_methods:
            return continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        print("Metadata", metadata)
        # print(metadata["token"])
        if "token" in metadata :
            try:
                jwt.decode(metadata["token"],_SECRET_KEY, algorithms=["HS256"])
                return continuation(handler_call_details)

            except jwt.InvalidTokenError as e:
                print(e)
        return self.abort_handler


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
        print(payload)
        return True
    except jwt.ExpiredSignatureError as e:
        print(e)
    return False


class ReservationServiceServicer(reservation_pb2_grpc.ReservationServiceServicer):

    def PingServer(self, request, context):
        return reservation_pb2.PingServerResponse(ping="Server reached", isPinging=True)

    def CreateAccount(self, request, context):
        uName = request.username
        uPass = request.password
        print("So far so good")
        # Add to user "database"
        users[uName] = uPass
        newToken = generate_token(uName)

        print()
        print("Generated token: ", newToken)
        print()

        print(users)
        return reservation_pb2.CreateAccountResponse(message="User created", token=newToken)

        if uName in users:
            return reservation_pb2.CreateAccountResponse(message="Username already exists", token=None)

        users[uName] = uPass
        token = generate_token(uName)
        print("So far so good 2")
        return reservation_pb2.CreateAccountResponse(message="User added successfully", token=token)


    def Login(self, request, context):
        uName = request.username
        uPass = request.password

        if users[uName] != uPass:
            return reservation_pb2.LoginResponse(message="Incorrect credentials", token=None)
        token = generate_token(uName)
        return reservation_pb2.LoginResponse(message="Successful Login", token=token)


    def Logout(self, request, context):
        uName = request.username
        print("Users dict:", users)
        if not verify_token(request.token) or uName not in users:
            return reservation_pb2.LogoutResponse(message="Token is invalid...", token=request.token)

        users.pop(uName)
        return reservation_pb2.LogoutResponse(message="Successful Logout", token=None)


    def MakeReservation(self, request, context):

        return reservation_pb2.MakeReservationResponse(message="Successful reservation")


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
