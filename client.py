import grpc
import reservation_pb2
import reservation_pb2_grpc

from datetime import datetime as dt
import getpass

def loginMenu():
    print()
    print("[1] Create Account")
    print("[2] Login to Existing")
    print("[0] Exit")
    return input("Option: ")

def mainMenu():
    print()
    print("[1] Make reservation")
    print("[2] Cancel reservation")
    print("[3] View reservation")
    print("[0] Logout")
    return input("Option: ")

def makeResMenu():
    print("")


def printAvailableReservationInfo(stub, username, token, metadata):
    responses = stub.FetchRooms(reservation_pb2.FetchRoomsRequest(token=token), metadata=metadata)
    for res in responses:
        print(res.rooms)

    room = input("Room to reserve: ")
    date = input("Choose date (YYYY-MM-DD): ")
    if len(room) < 1:
        print("Must give room, exiting...")
        return

    if len(date) < 1:
        print("Must give date, exiting...")
        return

    try:
        dt.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        print("Incorrect date format, should be YYYY-MM-DD", e)
        return False

    responses = stub.FetchAvailableSlots(reservation_pb2.FetchAvailableSlotsRequest(room=room, date=date, token=token), metadata=metadata)

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

    response = stub.MakeReservation(reservation_pb2.MakeReservationRequest(username=username, room=room, date=date, timeslot=time, token=token), metadata=metadata)

    if not response.isSuccessful:
        print(response.message)
        ### TODO: ALLOW USER TO TRY TO SELECT NEW SLOT
    print(response.message)

    print("Receipt:")
    print(f"Reserved {room} for 1 Hour \non {date} at {time} o'clock.")
    return True

# // RPC reservation methods
# message MakeReservationRequest {
#   string username = 1;
#   string room = 2;
#   string timeslot = 3;
#   string token = 4;
# }

def run():
    rootCertificates = open("ca.pem", "rb").read()
    channelCredentials = grpc.ssl_channel_credentials(rootCertificates)

    with grpc.secure_channel("localhost:44000", channelCredentials) as channel:
        stub = reservation_pb2_grpc.ReservationServiceStub(channel)
        # TEST PING TO SERVER
        response = stub.PingServer(reservation_pb2.PingServerRequest(ping="Gib ping"))
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
                        uPass = getpass.getpass("New password: ")
                        verPass = getpass.getpass("Verify password: ")
                        if uPass != verPass:
                            print("Passwords do not match.")
                            continue
                        if len(uPass) < 1:
                            print("Password can not be empty.")
                            continue
                        if input("Confirm [y/n]: ").lower() == "n":
                            continue

                        response = stub.CreateAccount(reservation_pb2.CreateAccountRequest(username=str(userName), name=name, password=uPass))

                        if response == None or response.token == None:
                            print("Account creation failed.")
                            continue

                        print(response.message)
                        metadata.append(("token", response.token))
                        sessionToken = response.token
                        break

                elif (inp == "2"):
                    while (1):
                        print("#### Login ####")
                        userName = input("Give username: ")
                        uPass = getpass.getpass("Password: ")
                        response = stub.Login(reservation_pb2.LoginRequest(username=userName, password=uPass))
                        if not response.isValid:
                            print(response.message)
                            continue
                        else:
                            print("Succ", response.message)
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
                pass

            elif (userInput == "0"):

                response = stub.Logout(reservation_pb2.LogoutRequest(username=userName, token=sessionToken), metadata=metadata)
                print(response.message)
                break
            else:
                print("Unknown selection")
                continue


if __name__=="__main__":
    run()
