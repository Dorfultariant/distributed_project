import grpc
import reservation_pb2
import reservation_pb2_grpc

from datetime import datetime as dt
import getpass

def loginMenu():
    print()
    print("###### WELCOME ######")
    print("[1] Create Account")
    print("[2] Login to Existing")
    print("[0] Exit")
    return input("Option: ")

def mainMenu():
    print()
    print("######## MENU ########")
    print("[1] Make reservation")
    print("[2] Cancel reservation")
    print("[3] View reservation")
    print("[0] Logout")
    return input("Option: ")

def checkReservations(stub, userName, token, metadata):
    try:
        response = stub.ViewReservations(reservation_pb2.ViewReservationsRequest(username=userName, token=token), metadata=metadata)

    except grpc.RpcError as e:
        print("Could not fetch data: ", e)
        return []

    reservations = response.reservations.split("\n")
    parsed = [ r.split(';') for r in reservations if r ]
    return parsed


def printReservations(reservations):
    if not reservations:
        print("\nNo reservations found.")
        return False

    print("\n### Found reservations ###")
    for r in reservations:
        ID, N, R, D, T = r
        print(f"[{ID}] Reservation:")
        print(f"Name: {N}")
        print(f"Room: {R}")
        print(f"Date: {D}")
        print(f"Time: {T}")
        print()
    return True


def cancelReservation(stub, userName, token, metadata):
    reservations = checkReservations(stub, userName, token, metadata)
    printReservations(reservations)
    if len(reservations) <= 0:
        return False
    print("### Cancel Reservation ###")
    id = input("Give ID to cancel (ex. 2): ")
    try:
        id = int(id)
    except ValueError:
        print("Incorrect ID")
        return False
    if id <= 0:
        print("No Reservation ID found")
        return False

    response = stub.CancelReservation(reservation_pb2.CancelReservationRequest(username=userName, reservation_id=str(id), token=token), metadata=metadata)
    print(response.message)

    return True

def printAvailableReservationInfo(stub, username, token, metadata):
    try: 
        responses = stub.FetchRooms(reservation_pb2.FetchRoomsRequest(token=token), metadata=metadata)
    except grpc.RpcError as e:
        print("gRPC error:", e.code(), e.details())
    i = 1
    roomList = []
    print("Available rooms:")
    for res in responses:
        print(f"[{i}] {res.rooms}")
        roomList.append(res.rooms)
        i+=1
    room = input("Reserver room by number (ex. 2): ")
    date = input("Choose date (YYYY-MM-DD): ")
    try:
        room = int(room)
    except ValueError:
        print("Wrong room number")
        return False
    room -= 1

    if room > len(roomList):
        print("Incorrect number")
        return False

    if len(date) < 1:
        print("Must give date, exiting...")
        return
    try:
        dt.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        print("Incorrect date format, should be YYYY-MM-DD", e)
        return False

    selectedRoom = roomList[room][0]

    try:
        responses = stub.FetchAvailableSlots(reservation_pb2.FetchAvailableSlotsRequest(room=selectedRoom, date=date, token=token), metadata=metadata)
    
    except grpc.RpcError as e:
        print("gRPC error when fetching available slots:", e.code(), e.details())
        
    if responses == None:
        print("Responses is None")
    
    i = 1
    freeList = []
    print("### Free Slots ###")
        
    for res in responses:
        for c in res.slots:
            print(f"[{i}]:", c)
            freeList.append(c)
            i+=1
    slot = -1
    while(slot != 0):
        slot = input("Select timeslot to reserve (ex. 1): ")
        try:
            slot = int(slot)
        except ValueError:
            print("Not correct")
            continue
        slot -= 1
        if slot >= len(freeList) or slot < 0:
            print("Incorrect slot")
            slot = -1
            continue
        break

    time = str(freeList[int(slot)])
    print("Selected 1 hour timeslot:", time)

    response = stub.MakeReservation(reservation_pb2.MakeReservationRequest(username=username, room=selectedRoom, date=date, timeslot=time, token=token), metadata=metadata)

    if not response.isSuccessful:
        print(response.message)
        ### TODO: ALLOW USER TO TRY TO SELECT NEW SLOT
        return False
    print(response.message)

    print("Receipt:")
    print(f"Reserved {selectedRoom} for 1 Hour \non {date} at {time} o'clock.")
    return True

def pingServer(stub):
    try:
        response = stub.PingServer(reservation_pb2.PingServerRequest(ping="Gib ping"))
    except grpc.RpcError as e:
        print("gRPC error when pingin server:", e.code(), e.details())
        return False
    except Exception as e:
        print("Unexpected error:", e)
        return False
    if response.isPinging:
        print(response.ping)
    return True

def createAccountMenu():
    print("#### Create Account ####")
    username = input("Give username: ")
    name = input("Give name: ")
    password = ""
    try:
        password = getpass.getpass("New password: ")
    except Exception as e:
        print("Error getting user password")
        return None
    try:
        verifyPassword = getpass.getpass("Verify password: ")
    except Exception as e:
        print("Error verifying password")
        return None
    if len(password) < 1 or len(verifyPassword) < 1:
        print("Password can not be empty.")

    if password != verifyPassword:
        print("Passwords do not match.")
        return None

    if input("Confirm [y/n]: ").lower() == "n":
        return None
    return username, name, password

def createAccountRequest(stub, username, name, password):
    try:
        response = stub.CreateAccount(reservation_pb2.CreateAccountRequest(username=str(username), name=str(name), password=str(password)))
    except grpc.RpcError as e:
        print("gRPC error when creating account request:", e.code(), e.details())
        return None
    except Exception as e:
        print("Unexpected error when creating account:", e)
        return None
    if response == None:
        print("Account creation failed, response is None")
        return None
    if response.token == None:
        print("Account creation failed, response.token is None")
        return None
    print("Response.message: ",response.message)
    return response

def run():
    rootCertificates = open("ca.pem", "rb").read()
    try:
        channelCredentials = grpc.ssl_channel_credentials(rootCertificates)
    except grpc.RpcError as e:
        print("gRPC error when getting channel credentials:", e.code(), e.details())
        
    with grpc.secure_channel("localhost:44000", channelCredentials) as channel:
        stub = reservation_pb2_grpc.ReservationServiceStub(channel)
        # TEST PING TO SERVER
        if not pingServer(stub):
            exit(-1)

        sessionToken = None
        userName = None
        userInput = "-1"
        response = None

        metadata = []

        while (userInput != "0"):

            if (sessionToken == None):
                inp = loginMenu()
                if inp == "0": break

                if (inp == "1"):
                    while (1):
                        userName, name, uPass = createAccountMenu()
                        if userName == None:
                            continue
                        response = createAccountRequest(stub, userName, name, uPass)
                        if response == None:
                            continue
                        metadata.append(("token", response.token))
                        sessionToken = response.token
                        break

                elif (inp == "2"):
                    while (1):
                        print("#### Login ####")
                        userName = input("Give username: ")
                        try:
                            uPass = getpass.getpass("Password: ")
                        except Exception as e:
                            print("Error while getting password")
                        try:
                            response = stub.Login(reservation_pb2.LoginRequest(username=userName, password=uPass))
                        except grpc.RpcError as e:
                            print("Error while getting login request", e.code(), e.details())
                        if not response.isValid:
                            print("server's response: ",response.message)
                            continue
                        else:
                            print("Response message from server: ", response.message)
                            metadata.append(("token", response.token))
                            sessionToken = response.token
                        break
                else:
                    continue

            userInput = mainMenu()

            if (userInput == "1"):
                if not printAvailableReservationInfo(stub, userName, sessionToken, metadata):
                    print("Something did not go as planned")
                print("Reservation Done")

            elif (userInput == "2"):
                cancelReservation(stub, userName, sessionToken, metadata)

            elif (userInput == "3"):
                res = checkReservations(stub, userName, sessionToken, metadata)
                printReservations(res)

            elif (userInput == "0"):
                try:
                    response = stub.Logout(reservation_pb2.LogoutRequest(username=userName, token=sessionToken), metadata=metadata)
                    print(response.message)
                except grpc.RpcError as e:
                    print("Grpc Error when logging out:", e.code(), e.details())
                break
            else:
                print("Unknown selection")
                continue


if __name__=="__main__":
    run()
