#package
#from replit import audio
from playsound import playsound
import os
import time

script_directory= os.path.dirname(__file__)

file_name= "Dream Sequence.mp3"

full_path = os.path.join(script_directory, file_name)

playsound (full_path, block=False)

gamestart="yes"

#Player Points
crew_safety= 100
mission_budget= 100
science_points= 0

print("Welcome to The Ares Horizon Game!")
print("======================================================================")

while gamestart=="yes":
    print("In this game you are a Flight Director at NASA Mission Control!")
    print("The Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!")
    print("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.")
    print("======================================================================")

    #Game Starts (Stage 1)
    print("\nSTAGE-1: T-MMINUS COUNTDOWN")
    print("")
    print("The Orion-X awaits launch")
    print("Suddenly, your lead flight engineer, Mark, announces on the comms:")
    print("Director! The Upper Atmosphere winds just excedded 8% past our safety limits!")
    
    #Choice 1 
    print("\nWhat do you do?")
    print("1) Launch Now- Push through the high speed winds and save time")
    print("2) Delay Launch- Abort the window and wait for a backup plan")
    print("")

    choice_1= input(" Enter 1 or 2: ").strip()

    #=================
    #BRANCH 1 Choice 1
    #=================
    if choice_1 == "1":
        print("IGNITION! The rocket vibrates violently as it puches through the wind")
        print("Minutes later you reach the edge of the atmosphere and enter orbit, but the stress caused by the wind resulted in an issue")
        print("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!")

        #Penalty for taking risk and damage
        crew_safety -= 20
        mission_budget -= 10

        #Display Points after choice
        print("")
        print(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} %")

        #Choice 1 Stage 2
        print("\nSTAGE-2: THE ORBIT")

    #=================
    #BRANCH 1 Choice 2
    #=================
    elif choice_1 == "2":
        print("\nYou stand down on the launch. The crew exits the spacecraft")
        print("Weeks later, you launch on a much longer and not as ideal route")
        print("Deep in space, a massive radiation storm knocks down your primary navigation computer")

        #Crew stays secure but delays drain cash
        mission_budget -= 40

        #Display points after choice
        print(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} %")
    #=======================  
    #BRANCH 1 Invalid Choice
    #=======================
    else:
        print("INVALID CHOICE")

gamestart= input(" Would you like to restart your mission, Director? (Y/N)")