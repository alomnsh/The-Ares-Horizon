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

playsound (full_path, block=False)

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
    
#Player Points
crew_safety= 100
mission_budget= 100
science_points= 0

typewriter("Welcome to The Ares Horizon Game!", bold = True)
print(termcolor.colored("======================================================================", attrs=["bold"]))

while gamestart=="yes":
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
    typewriter("1) Launch Now- Push through the high speed winds and save time")
    typewriter("2) Delay Launch- Abort the window and wait for a backup plan")
    typewriter("")

    choice_1= input(" Enter 1 or 2: ").strip()

    #=================
    #BRANCH 1 Choice 1
    #=================
    if choice_1 == "1":
        typewriter("\nIGNITION! The rocket vibrates violently as it puches through the wind")
        typewriter("Minutes later you reach the edge of the atmosphere and enter orbit, but the stress caused by the wind resulted in an issue")
        typewriter("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!")

        #Penalty for taking risk and damage
        crew_safety -= 20
        mission_budget -= 10

        #Display Points after choice
        typewriter("")
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}")

        #Choice 1 Stage 2
        typewriter("\nSTAGE-2: THE ORBITAL ANOMALY", bold = True)
        typewriter("1) PUSH ENGINES- Fire the second stage anyway to immediatly clear the orbit", color= "red")
        typewriter("2) ABORT MISSION- Aactivate the escape tower to bring the crew back to Earth safely", color= "red")

        chocie_2a = input("Enter 1 or 2: ").strip()

        #Stage 2 Choice 1
        if chocie_2a == "1":
            typewriter("\nRisky Move, the engines fire hard. The pressure stabilizes just in time.")
            typewriter("Months pass in deep space, and the crew finally arrives at the Red Planet")

            #Penalize for taking risk but give points for science
            crew_safety -= 10
            science_points += 30

            #Display Points after choice
            typewriter("")
            typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}")

            #Choice 1 Stage 3
            typewriter("\nSTAGE-3: MARS LANDING", bold = True)
            print("")
            typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates")
            typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing")
            typewriter("\nWhat do you do?")
            typewriter("1) MANUAL CONTROL- Order the commander to take joystick control and land manually", color= "red")
            typewriter("2) AUTO-PILOT- Trust the computer to maneuver around the boulders", color= "red")

            choice_3a = input("Enter 1 or 2: ").strip()

            #Stage 3 Choice 1
            if choice_3a == "1":
                typewriter("\nHEROIC VICTORY! The Commander flies beautifully, touching down safely!")
                typewriter("Human step foot on the Red Planet for the first time!")
                typewriter("Excellent Work, Director")

                #Reward for landing safely and humans on Mars
                crew_safety += 10
                science_points += 50

                #Display Final Points
                typewriter(f"Congrats on finishing, Your total points for the mission are-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points} ")

            #Stage 3 Choice 2
            elif choice_3a == "2":
                typewriter("\nCRASH DOWN! The system clips a massicve hidden boulder")
                typewriter("The lander tips and loses pressure. Space is not forgiving.")
                typewriter("MISSION FAILED", bold = True)

                #Total loss of both the crew and the spacecraft
                crew_safety = 0
                mission_budget = 0

                #Display Final Points
                typewriter(f"The crew is no longer with us, and neither is the space craft. Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points} ")

            #Stage 3 Invalid Choice
            else:
                typewriter("INVALID CHOICE", color= "red", bold = True)

        #Stage 2 Choice 2
        elif chocie_2a == "2":
            typewriter("The emergency escape system rips apart from the capsule")
            typewriter("The crew safely splash down in the atlantic ocean")
            typewriter("The mission is over but the crew lives")

            #Total loss
            mission_budget = 0

            typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}")

        #Stage 2 Invalid Choice
        else:
            typewriter("INVALID CHOICE. The countdown grid locks up and the engine explodes", color= "red", bold = True)

    #=================
    #BRANCH 1 Choice 2
    #=================
    elif choice_1 == "2":
        typewriter("\nYou stand down on the launch. The crew exits the spacecraft")
        typewriter("Weeks later, you launch on a much longer and not as ideal route")
        typewriter("Deep in space, a massive radiation storm knocks down your primary navigation computer")

        #Crew stays secure but delays drain cash
        mission_budget -= 40

        #Display points after choice
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}")

        #Choice 2 Stage 2
        typewriter("\nSTAGE-2: LOST IN SPACE", bold = True)
        typewriter("\nMark scrambles: Director, the main computer is dead, we are drifting!")
        typewriter("1) UPLOAD A PATCH- Push an unverified software fix to reboot the system")
        typewriter("2) MANUAL TRAJECTORY- Force the crew to calculate engine burns using manual star maps and control th ship")

        choice_2b = input("Enter 1 or 2: ").strip()

        #Stage 2 Choice 1
        if choice_2b == "1":
            typewriter("The patch works! The navigation is back up again")
            typewriter("However the reboot drained 60% of your spacecraft power reserves")
            typewriter("The crew arrive at Mars in a critically underpowered ship")

            #Reward for recovering the ship
            science_points += 20

            typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}")

            #Choice 2 Stage 3
            typewriter("\nSTAGE-3: THE LANDING", bold = True)
            typewriter("\nWith the low power, you cannot run both the heaters and the landing thrusters")
            typewriter("1) DEPLOY SOLAR SAILS- Wait in orbit for 3 days to charge batteries using solar panels")
            typewriter("2) EMERGENCY BURN- Cut the life support heaters to power a descent")

            choice_3b = input("Enter 1 or 2: ").strip()

            #Stage 3 Choice 1 
            if choice_3b == "1":
                typewriter("The solar sails catch enoght sunlight to recharge")
                typewriter("The crew lands flawlessly with power to spare. You saved them with patience!")

                #Reward for safety an give science points
                crew_safety += 10
                science_points += 40

            #Stage 3 Choice 2 
            elif choice_3b == "2":
                typewriter("\n BURN OUT! The extreme cold freezes the fuel valves during descent.")
                typewriter("The engines fail 100 meters up. The ship impacts the surface.")
                typewriter("MISSION FAILED")
                crew_safety = 0

            #Stage 3 Invalid Choice
            else:
                typewriter("\nINVALID CHOICE. The ship loses total electrical power and becomes a ghost satellite.", bold = True)

                #Penalize for crew death
                crew_safety = 0

        #Stage 2 Choice 2
        elif choice_2b == "2":
            typewriter("LOSt ORBIT! The math is too complex with the light-lag delay")
            typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication")

            #Penalize for crew safety and loss
            crew_safety -= 50
            mission_budget = 0

            typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}")

        #Stage 2 Invalid Choice
        else:
            typewriter("\n INVALID CHOICE, the spacecraft drifts without and instructions for recovery", bold = True)

    #=======================  
    #BRANCH 1 Invalid Choice
    #=======================
    else:
        typewriter("INVALID CHOICE", color="red", bold=True)

print("=======================================================")
gameStart = input("Would you like to restart the mission? (yes/no): ").lower().strip()

typewriter("\nThank you for playing! Mission Control signing off. 🛰️")