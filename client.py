import grpc
import reservation_pb2
import reservation_pb2_grpc

from datetime import datetime as dt
import getpass

def print_banner():
    date = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    print("========================================")
    print("||    ########## WELCOME ##########   ||")
    print("||    This is a Reservation System    ||")
    print("||                                    ||")
    print("||          Creators:                 ||")
    print("||          - Teemu Hiltunen          ||")
    print("||          - Antti Kukkonen          ||")
    print("||          - Iiro  Pitkänen          ||")
    print("||                                    ||")
    print("||       Current date and time:       ||")
    print("||        " + date +       "         ||")
    print("========================================")


def printLoginMenu():
    print()
    print("###### AUTHENTICATION ######")
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

# Function used to fetch data from server
# @param stub for method call
# @param username to connect find user information
# @param token for verification
# @param metadata (including token) used for authenctication
# @return list of reservations

def checkReservations(stub, userName, token, metadata):
    try:
        response = stub.ViewReservations(reservation_pb2.ViewReservationsRequest(username=userName, token=token), metadata=metadata)

    except grpc.RpcError as e:
        print("Could not fetch data from server: ", e)
        return None

    reservations = response.reservations.split("\n")
    parsed = [ r.split(';') for r in reservations if r ]
    return parsed


# Function used to print reservations from list
# @param List of reservations to be printed
# @return BOOLEAN for success or fail

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

# Function used to cancel specific reservation from user
# @param stub for method call
# @param username to connect find user information
# @param token for verification
# @param metadata (including token) used for authenctication
# @return BOOLEAN for success or fail

def cancelReservation(stub, userName, token, metadata):
    reservations = checkReservations(stub, userName, token, metadata)
    if not reservations:
        print("\nNo reservations to cancel.")
        return False

    printReservations(reservations)
    if len(reservations) <= 0:
        return False
    print("### Cancel Reservation ###")
    id = input("Give ID to cancel (ex. 2) (0 to exit): ")
    try:
        id = int(id)
    except ValueError:
        print("Incorrect indice.")
        return False

    if id <= 0:
        print("Exiting")
        return False
    try:
        response = stub.CancelReservation(reservation_pb2.CancelReservationRequest(username=userName, reservation_id=str(id), token=token), metadata=metadata)
        print(response.message)
    except grpc.RpcError:
        print("Could not fetch data from server")
        return False

    return True

# Function for fetching available rooms
# @param stub for method call
# @param username to connect find user information
# @param token for verification
# @param metadata (including token) used for authenctication
# @return list of rooms

def fetchRooms(stub, username, token, metadata):
    try:
        responses = stub.FetchRooms(reservation_pb2.FetchRoomsRequest(token=token), metadata=metadata)
    except grpc.RpcError:
        print("\nCould not fetch available rooms.\n")
        return []
    rooms = []
    for res in responses:
        rooms.append(res.rooms)
    return rooms


# Function for getting date from user
# @param None
# @return date or None

def getADate():
    date = input("Choose date (YYYY-MM-DD): ")
    try:
        dt.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("\nIncorrect date format, should be YYYY-MM-DD")
        return None
    return date


# Function for getting room index from user
# @param id limit
# @return room idx or None (-1 for exit)

def getARoom(maxs):
    room_idx = input("\nReserve room by number (ex. 2) (0 to exit): ")
    try:
        room_idx = int(room_idx) - 1
    except ValueError:
        print("\nInvalid room number\n")
        return None
    if room_idx == -1:
        return room_idx
    if room_idx > maxs or room_idx < 0:
        print("\nInvalid room number\n")
        return None
    return room_idx


# Function for fetching available timeslots
# @param stub for method call
# @param room (name: string)
# @param date (date: string)
# @param token for verification
# @param metadata (including token) used for authenctication
# @return list of free timeslots for a given room and date or None

def fetchFreeTimeslots(stub, room, date, token, metadata):
    try:
        responses = stub.FetchAvailableSlots(reservation_pb2.FetchAvailableSlotsRequest(
            room=room,
            date=date,
            token=token),
        metadata=metadata
    )
    except grpc.RpcError:
        print("\nError when fetching available slots.\n")
        return None

    freeslots = []
    for res in responses:
        for slot in res.slots:
            freeslots.append(slot)
    return freeslots


# Function for making a reservation request
# @param stub for method call
# @param username to make reservation for correct user
# @param room (name: string)
# @param date (date: string)
# @param timeslot (time: string)
# @param token for verification
# @param metadata (including token) used for authenctication
# @return BOOLEAN for success or fail

def makeReservation(stub, username, room, date, timeslot, token, metadata):
    try:
        response = stub.MakeReservation(reservation_pb2.MakeReservationRequest(
            username=username,
            room=room,
            date=date,
            timeslot=timeslot,
            token=token ),
        metadata=metadata
    )
    except grpc.RpcError as e:
        print("Error making reservation: ",e.code(), e.details())

    if not response.isSuccessful:
        print()
        print(response.message)
        return False
    print()
    print(response.message)
    return True


# Function used to run reservation loop
# and make calls to support functions
# @param stub for method call
# @param username to connect find user information
# @param token for verification
# @param metadata (including token) used for authenctication
# @return BOOLEAN for success or fail

def reservationSystem(stub, username, token, metadata):

    while(True):
        rooms = fetchRooms(stub, username, token, metadata)
        if rooms == None:
            print("\nNo rooms to reserve.\n")
            return False

        print("\nAvailable rooms:")
        for i, room in enumerate(rooms, 1):
            print(f"[{i}]: {room}")

        room_idx = getARoom(len(rooms))
        if room_idx == None:
            continue
        if room_idx == -1:
            print("\nExiting.\n")
            return False

        date = getADate()
        if date == None:
            continue

        selectedRoom = rooms[room_idx][0]

        freeSlots = fetchFreeTimeslots(stub, selectedRoom, date, token, metadata)
        if not freeSlots:
            print("\nNo free slots available for this room on selected date.\n")
            if input("\nTry again (y/n): ").lower() == "n":
                return False
            continue

        print("### Free Slots ###")
        for i, slot in enumerate(freeSlots, 1):
            print(f"[{i}]: {slot}")

        slot_idx = input("\nSelect timeslot to reserve (ex. 1) (0 to exit): ")
        
        try:
            slot_idx = int(slot_idx) - 1
        except ValueError:
            print("\nIncorrect slot number.\n")
            continue
        if slot_idx == -1:
            print("\nExiting")
            return False
        if slot_idx >= len(freeSlots) or slot_idx < 0:
            print("\nIncorrect slot number.\n")
            continue

        time = str(freeSlots[slot_idx])
        print("\nYou have selected a 1-hour timeslot at", time, "o'clock.")
        if input("\nContinue with reservation (y/n): ").lower() == "n":
            return False

        if makeReservation(stub, username, selectedRoom, date, time, token, metadata):
            print("\nReceipt: ")
            print(f"Reserved {selectedRoom} for 1 Hour.")
            print(f"Timeslot: {date} at {time} o'clock.")
            break
        else:
            print("Could not make reservation, try again.")

    return True

# Function for pinging server and ensuring that connection has been established
# @param stub for method call
# @return BOOLEAN for success or fail

def pingServer(stub):
    try:
        response = stub.PingServer(reservation_pb2.PingServerRequest(ping="Gib ping"))
    except grpc.RpcError as e:
        print("Could not connect to Server:", e.details())
        return False
    except Exception as e:
        print("Unexpected error:", e)
        return False
    if response.isPinging:
        print()
        print(response.ping)
        print()
    return True

# Function to handle user input for creating account
# @param None
# @return username, name, password or empty string

def createAccountMenu():
    print("#### Create Account ####")
    username = input("Give username: ")
    name = input("Give name: ")
    password = ""
    try:
        password = getpass.getpass("New password: ")
    except Exception as e:
        print("Error getting user password")
        return "", "", ""

    try:
        verifyPassword = getpass.getpass("Verify password: ")
    except Exception as e:
        print("\nError verifying password")
        return "", "", ""

    if len(password) < 1 or len(verifyPassword) < 1:
        print("\nPassword can not be empty.")
        return "", "", ""

    if password != verifyPassword:
        print("\nPasswords do not match.")
        return "", "", ""

    if input("\nConfirm [y/n]: ").lower() == "y":
        return str(username), str(name), str(password)

    return "", "", ""

# Function for createAccountRequest and handle errors:
# @param stub for method call
# @param username for account
# @param name for account
# @param password for authentication
# @return response for success or None

def createAccountRequest(stub, username, name, password):
    try:
        response = stub.CreateAccount(reservation_pb2.CreateAccountRequest(
            username=username,
            name=name,
            password=password)
        )
    except grpc.RpcError as e:
        print("gRPC error when creating account request:", e.code(), e.details())
        return None
    except Exception as e:
        print("Unexpected error when creating account:", e)
        return None

    if response == None:
        print("Account creation failed, server did not respond")
        return None

    if response.token == None:
        print(response.message)
        return None

    print()
    print(response.message)
    return response

# Function to get user login credentials:
# @param None
# @return username, password or empty string

def loginMenu():
    print("#### Login ####")
    username = input("Give username: ")
    try:
        password = getpass.getpass("Password: ")
    except Exception as e:
        print("Error while getting password")
        return "", ""
    return str(username), str(password)


# Function to make the login request:
# @param stub for server method
# @param username string
# @param password string
# @return token or None

def loginRequest(stub, username, password):
    try:
        response = stub.Login(reservation_pb2.LoginRequest(
            username=username,
            password=password)
        )

    except grpc.RpcError as e:
        print("Error while getting login response.", e.code(), e.details())
        return None

    if not response.isValid:
        print(response.message)
        return None

    print()
    print(response.message)
    return response.token


# Function for handling login and account creation logic
#   and function calls
# @param stub for server method
# @return username, token or empty string, None for exit

def loginSystem(stub):
    inp = printLoginMenu()
    if inp == "0":
        return None, None

    username = None
    token = None

    if (inp == "1"):
        username, name, password = createAccountMenu()
        if len(username) < 1 or len(password) < 1 or len(name) < 1:
            return "", ""
        response = createAccountRequest(stub, username, name, password)
        if response == None:
            return "", ""
        if len(response.token) < 1:
            return "", ""
        token = response.token


    elif (inp == "2"):
        username, password = loginMenu()
        if len(username) < 1 or len(password) < 1:
            return "", ""

        if input("\nConfirm (y/n): ").lower() == "n":
            return "", ""

        token = loginRequest(stub, username, password)
        if token is None:
            return "", ""
    else:
        return "", ""

    return username, token


# ### MAIN FUNCTION ###
# Handles main logic structure of the clientside program
# @param None
# @return None

def run():
    ## Certification to verify server-client connection
    rootCertificates = open("ca.pem", "rb").read()
    try:
        channelCredentials = grpc.ssl_channel_credentials(rootCertificates)
    except grpc.RpcError as e:
        print("gRPC error when getting channel credentials:", e.code(), e.details())

    host = "localhost"
    port = input("Give connection port (enter to use default): ")
    ## Uses default port of server
    port.replace(" ", "")
    if port == "":
        port = 44000

    ## Connection to server at host: localhost port: 44000 as the application is tested
    ##  on localhost network
    with grpc.secure_channel(f"{host}:{port}", channelCredentials) as channel:
        stub = reservation_pb2_grpc.ReservationServiceStub(channel)
        # TEST PING TO SERVER
        if not pingServer(stub):
            exit(-1)

        sessionToken = None
        userName = None
        userInput = "-1"
        response = None

        metadata = []
        print_banner()


        # ### Main loop ###
        while (userInput != "0"):

            ## User authenctication
            if (sessionToken == None or len(sessionToken) < 1):
                userName, sessionToken = loginSystem(stub)
                if userName is None or sessionToken is None:
                    break
                if len(userName) > 0 and len(sessionToken) > 0:
                    metadata.append(("token", sessionToken))
                continue

            ## Program main menu ##
            userInput = mainMenu()

            ## Making reservation
            if (userInput == "1"):
                if reservationSystem(stub, userName, sessionToken, metadata):
                    print("Reservation Done")

            ## Cancelling reservation
            elif (userInput == "2"):
                cancelReservation(stub, userName, sessionToken, metadata)

            ## Viewing existing reservations
            elif (userInput == "3"):
                res = checkReservations(stub, userName, sessionToken, metadata)
                printReservations(res)

            ## Logging out
            elif (userInput == "0"):
                try:
                    response = stub.Logout(reservation_pb2.LogoutRequest(username=userName, token=sessionToken), metadata=metadata)
                    print()
                    print(response.message)
                # If exception occurs, the client will still be stopped
                except grpc.RpcError:
                    pass
                print()
                print("Bye bye!")
                print()
                break
            else:
                print("Unknown selection...")
                continue


if __name__=="__main__":
    run()
