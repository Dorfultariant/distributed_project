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
        print("No reservations found")
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
    size = len(reservations)
    printReservations(reservations)

    print("### Cancel Reservation ###")
    id = input("Give number to cancel (ex. 2): ")
    try:
        id = int(id) - 1
    except ValueError as e:
        print("Incorrect indice: ", e)
        return False
    if id < 0 or id >= size:
        print("No Reservation ID found")
        return False


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
        except ValueError as e:
            print("Not correct: ", e)
            continue
        
        slot -= 1
        if slot >= len(freeList) or slot < 0:
            print("Incorrect slot")
            slot = -1
            continue
        break

    time = str(freeList[int(slot)])
    print("Selected 1 hour timeslot:", time)
    
    try:
        response = stub.MakeReservation(reservation_pb2.MakeReservationRequest(username=username, room=selectedRoom, date=date, timeslot=time, token=token), metadata=metadata)
    except grpc.RpcError as e:
        print("Error making reservation: ",e.code(), e.details())
        
    if not response.isSuccessful:
        print(response.message)
        ### TODO: ALLOW USER TO TRY TO SELECT NEW SLOT
        return False
    print(response.message)

    print("Receipt: ")
    print(f"Reserved {selectedRoom} for 1 Hour \non {date} at {time} o'clock.")
    return True



def run():
    rootCertificates = open("ca.pem", "rb").read()
    try:
        channelCredentials = grpc.ssl_channel_credentials(rootCertificates)
    except grpc.RpcError as e:
        print("gRPC error when getting channel credentials:", e.code(), e.details())
        
    with grpc.secure_channel("localhost:44000", channelCredentials) as channel:
        stub = reservation_pb2_grpc.ReservationServiceStub(channel)
        # TEST PING TO SERVER
        try:
            response = stub.PingServer(reservation_pb2.PingServerRequest(ping="Gib ping"))
        except grpc.RpcError as e:
            print("gRPC error when pingin server:", e.code(), e.details())
        except Exception as e:
            print("Unexpected error:", e)
        if response.isPinging:
            print(response.ping)

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
                        print("#### Create Account ####")
                        userName = input("Give username: ")
                        name = input("Give name: ")
                        try:
                            uPass = getpass.getpass("New password: ")
                        except Exception as e:
                            print("Error getting user password")
                        try:    
                            verPass = getpass.getpass("Verify password: ")
                        except Exception as e:
                            print("Error verifying password")
                            
                        if uPass != verPass:
                            print("Passwords do not match.")
                            continue
                        if len(uPass) < 1:
                            print("Password can not be empty.")
                            continue
                        if input("Confirm [y/n]: ").lower() == "n":
                            continue
                        try:
                            response = stub.CreateAccount(reservation_pb2.CreateAccountRequest(username=str(userName), name=name, password=uPass))
                        except grpc.RpcError as e:
                            print("gRPC error when creating account request:", e.code(), e.details())
                        except Exception as e:
                            print("Unexpected error when creating account:", e)
                            
                        if response == None:
                            print("Account creation failed, response is None")
                            continue
                        if response.token == None:
                            print("Account creation failed, response.token is None")

                        print("Response.message: ",response.message)
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
                pass

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
