#Importing packages
#from replit import audio

from playsound import playsound
import os
import time
import termcolor
import tkinter as tk

script_directory= os.path.dirname(__file__)

file_name= "Dream Sequence.mp3"

full_path = os.path.join(script_directory, file_name)

try:
    playsound(full_path, block=False)
except Exception:
    pass

# Typewriter effect function + change color function so that we don't lose the typewriter effect
def typewriter(text, color=None, bold=False):
    attributes = ["bold"] if bold else []
    
    # Check if either color or bold styling is active
    if color or bold:
        text = termcolor.colored(text, color=color, attrs=attributes)

    for letter in text:
        print(letter, end="", flush=True)
        time.sleep(0.05)
    print()


gamestart="yes"

typewriter("Welcome to The Ares Horizon Game!", bold = True)
print(termcolor.colored("======================================================================", attrs=["bold"]))

while gamestart=="yes":

    #Player Points
    crew_safety = 100
    mission_budget = 100
    science_points = 0

    typewriter("In this game you are a Flight Director at NASA Mission Control!")
    typewriter("The Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!")
    typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.")
    print(termcolor.colored("======================================================================", attrs=["bold"]))

    #Game Starts (Stage 1)
    typewriter("\nSTAGE-1: T-MMINUS COUNTDOWN", bold = True)
    typewriter("")
    typewriter("The Orion-X awaits launch")
    typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", color="red")
    typewriter("Director! The Upper Atmosphere winds just excedded 8% past our safety limits!", color= "red")
    
    #Branch 1 Choice  
    typewriter("\nWhat do you do?", bold = True)
    typewriter("1) Launch Now- Push through the high speed winds and save time", color= "red")
    typewriter("2) Delay Launch- Abort the window and wait for a backup plan", color= "red")

    #Invalid choice check
    while True:
        choice_1= input("\nEnter 1 or 2: ").strip()
        if choice_1 in ["1", "2"]:
            break
        typewriter("\nINVALID CHOICE. Please type exactly 1 or 2.", color= "yellow")

    #=================
    #BRANCH 1 Choice 1
    #=================
    if choice_1 == "1":
        typewriter("\nIGNITION! The rocket vibrates violently as it puches through the wind")
        typewriter("Minutes later you reach the edge of the atmosphere and enter orbit, but the stress caused by the wind resulted in an issue")
        typewriter("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!", color= "red")

        #Penalty for taking risk and damage
        crew_safety -= 20
        mission_budget -= 10

        #Display Points after choice
        typewriter("")
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color= "cyan")

        #Choice 1 Stage 2
        typewriter("\nSTAGE-2: THE ORBITAL ANOMALY", bold = True)
        typewriter("1) PUSH ENGINES- Fire the second stage anyway to immediatly clear the orbit", color= "red")
        typewriter("2) ABORT MISSION- Aactivate the escape tower to bring the crew back to Earth safely", color= "red")

        #Invalid choice check
        while True:
            choice_2a= input("\nEnter 1 or 2: ").strip()
            if choice_2a in ["1", "2"]:
                break
            typewriter("\nINVALID CHOICE. Please type exactly 1 or 2.", color= "yellow")

        #Stage 2 Choice 1
        if choice_2a == "1":
            typewriter("\nRisky Move, the engines fire hard. The pressure stabilizes just in time.")
            typewriter("Months pass in deep space, and the crew finally arrives at the Red Planet")

            #Penalize for taking risk but give points for science
            crew_safety -= 10
            science_points += 30

            #Display Points after choice
            typewriter("")
            typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color= "cyan")

            #Choice 1 Stage 3
            typewriter("\nSTAGE-3: MARS LANDING", bold = True)
            print("")
            typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates")
            typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", color= "red")
            typewriter("\nWhat do you do?")
            typewriter("1) MANUAL CONTROL- Order the commander to take joystick control and land manually", color= "red")
            typewriter("2) AUTO-PILOT- Trust the computer to maneuver around the boulders", color= "red")

            #Invalid choice check
            while True:
                choice_3a= input("\nEnter 1 or 2: ").strip()
                if choice_3a in ["1", "2"]:
                    break
                typewriter("\nINVALID CHOICE. Please type exactly 1 or 2.", color= "yellow")

            #Stage 3 Choice 1
            if choice_3a == "1":
                typewriter("\nHEROIC VICTORY! The Commander flies beautifully, touching down safely!", color= "green")
                typewriter("Human step foot on the Red Planet for the first time!", color= "green")
                typewriter("Excellent Work, Director", color= "green")

                #Reward for landing safely and humans on Mars
                crew_safety += 10
                science_points += 50

            #Stage 3 Choice 2
            elif choice_3a == "2":
                typewriter("\nCRASH DOWN! The system clips a massicve hidden boulder", color= "red")
                typewriter("The lander tips and loses pressure. Space is not forgiving.", color= "red")
                typewriter("MISSION FAILED", bold = True, color= "red")

                #Total loss of both the crew and the spacecraft
                crew_safety = 0
                mission_budget = 0

        #Stage 2 Choice 2
        elif choice_2a == "2":
            typewriter("The emergency escape system rips apart from the capsule")
            typewriter("The crew safely splash down in the atlantic ocean")
            typewriter("The mission is over but the crew lives")

            #Total loss
            mission_budget = 0

    #=================
    #BRANCH 1 Choice 2
    #=================
    elif choice_1 == "2":
        typewriter("\nYou stand down on the launch. The crew exits the spacecraft")
        typewriter("Weeks later, you launch on a much longer and not as ideal route")
        typewriter("Deep in space, a massive radiation storm knocks down your primary navigation computer", color= "red")

        #Crew stays secure but delays drain cash
        mission_budget -= 40

        #Display points after choice
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color= "cyan")

        #Choice 2 Stage 2
        typewriter("\nSTAGE-2: LOST IN SPACE", bold = True)
        typewriter("\nMark scrambles: Director, the main computer is dead, we are drifting!", color= "red")
        typewriter("1) UPLOAD A PATCH- Push an unverified software fix to reboot the system", color= "red")
        typewriter("2) MANUAL TRAJECTORY- Force the crew to calculate engine burns using manual star maps and control th ship", color= "red")

        #Invalid choice check
        while True:
            choice_2b= input("\nEnter 1 or 2: ").strip()
            if choice_2b in ["1", "2"]:
                break
            typewriter("\nINVALID CHOICE. Please type exactly 1 or 2.", color= "yellow")

        #Stage 2 Choice 1
        if choice_2b == "1":
            typewriter("The patch works! The navigation is back up again")
            typewriter("However the reboot drained 60% of your spacecraft power reserves", color= "red")
            typewriter("The crew arrive at Mars in a critically underpowered ship")

            #Reward for recovering the ship
            science_points += 20

            typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color= "cyan")

            #Choice 2 Stage 3
            typewriter("\nSTAGE-3: THE LANDING", bold = True)
            typewriter("\nWith the low power, you cannot run both the heaters and the landing thrusters")
            typewriter("1) DEPLOY SOLAR SAILS- Wait in orbit for 3 days to charge batteries using solar panels", color= "red")
            typewriter("2) EMERGENCY BURN- Cut the life support heaters to power a descent", color= "red")

            #Invalid choice check
            while True:
                choice_3b= input("\nEnter 1 or 2: ").strip()
                if choice_3b in ["1", "2"]:
                    break
                typewriter("\nINVALID CHOICE. Please type exactly 1 or 2.", color= "yellow")

            #Stage 3 Choice 1 
            if choice_3b == "1":
                typewriter("The solar sails catch enoght sunlight to recharge", color= "green")
                typewriter("The crew lands flawlessly with power to spare. You saved them with patience!", color= "green")

                #Reward for safety an give science points
                crew_safety += 10
                science_points += 40

            #Stage 3 Choice 2 
            elif choice_3b == "2":
                typewriter("\n BURN OUT! The extreme cold freezes the fuel valves during descent.", color= "red")
                typewriter("The engines fail 100 meters up. The ship impacts the surface.", color= "red")
                typewriter("MISSION FAILED", color= "red", bold=True)
                crew_safety = 0

        #Stage 2 Choice 2
        elif choice_2b == "2":
            typewriter("LOST ORBIT! The math is too complex with the light-lag delay", color= "red")
            typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication", color= "red")

            #Penalize for crew safety and loss
            crew_safety = 0
            mission_budget = 0

    print("=======================================================")
    gamestart = input("Would you like to restart the mission? (yes/no): ").lower().strip()

typewriter("\nThank you for playing! Mission Control signing off. 🛰️")