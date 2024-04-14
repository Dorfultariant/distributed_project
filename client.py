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
                    print("#### Create Account ####")
                    while (1):
                        userName = input("Give username: ")
                        name = input("Give name: ")
                        uPass = getpass.getpass("New password: ")
                        verPass = getpass.getpass("Verify password: ")
                        if uPass != verPass:
                            print("Passwords do not match.")
                            continue
                        response = stub.CreateAccount(reservation_pb2.CreateAccountRequest(username=userName, name=name, password=uPass))

                        if response == None or response.token == None:
                            print("Account creation failed.")
                            #print(response.message)
                            continue
                        print(response.message)

                        sessionToken = response.token
                        print(metadata)
                        break

                elif (inp == "2"):
                    print("#### Login ####")
                    while (1):
                        userName = input("Give username: ")
                        uPass = input("Password: ")
                        response = stub.Login(reservation_pb2.LoginRequest(username=userName, password=uPass))

                        if response == None or response.token == None:
                            print("Account not found")
                            #print(response.message)
                        else:
                            metadata.append(("token", response.token))
                            sessionToken = response.token
                            print(metadata)
                        break
                else:
                    continue

            userInput = mainMenu()

            if (userInput == "1"):
                pass

            elif (userInput == "2"):
                pass

            elif (userInput == "3"):
                pass

            elif (userInput == "0"):

                response = stub.Logout(reservation_pb2.LogoutRequest(username=userName, token=sessionToken), metadata=metadata)
                print(response.message)
                print(response.token)
                break


if __name__=="__main__":
    run()
