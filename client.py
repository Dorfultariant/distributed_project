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

def printAvailableReservationInfo(stub, token, metadata):
    try: 
        responses = stub.FetchRooms(reservation_pb2.FetchRoomsRequest(token=token), metadata=metadata)
    except grpc.RpcError as e:
        
        print("gRPC error:", e.code(), e.details())
        
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
    print("Fetching available slots")
    
    try:
        responses = stub.FetchAvailableSlots(reservation_pb2.FetchAvailableSlotsRequest(room=room, date=date, token=token), metadata=metadata)
    
    except grpc.RpcError as e:
        print("gRPC error when fetching available slots:", e.code(), e.details())
        
    if responses == None:
        print("Responses is  None")
    if  responses.token == None:
        print("responses.token is None")

        
    s = ""
    for res in responses:
        # s+=str(res.slots)
        for c in res.slots:
            s+=str(c)
        s+=' '

    #print("Row: ", res.slots[0])
    print(s)
    return

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
                        metadata.append(("response.token: ", response.token))
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
                            print("Successfull login: ", response.message)
                            metadata.append(("token", response.token))
                            sessionToken = response.token
                        break
                else:
                    continue

            userInput = mainMenu()

            if (userInput == "1"):
                printAvailableReservationInfo(stub, sessionToken, metadata)
                pass

            elif (userInput == "2"):
                pass

            elif (userInput == "3"):
                pass

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
