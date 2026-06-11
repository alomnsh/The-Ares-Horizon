gamestart="yes"

print("Welcome to The Ares Horizon Game!")
print("======================================================================")

while gamestart=="yes":
    print("In this game you are a Flight Director at NASA Mission Control!")
    print("The Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!")
    print("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.")
    print("======================================================================")

    #Game Starts
    print("")
    print("The Orion-X awaits launch")
    print("Suddenly, your lead flight engineer, Mark, announces on the comms:")
    print("'Director! The Upper Atmosphere winds just excedded 8% past our safety limits!")
    
    #Choice 1 
    print("\nWhat do you do?")
    print("1) Launch Now- Push through the high speed winds and save time")
    print("2) Delay Launch- Abort the window and wait for a backup plan")

    choice1= input(" Enter 1 or 2")

gamestart= input(" Would you like to restart your mission, Director? (Y/N)")