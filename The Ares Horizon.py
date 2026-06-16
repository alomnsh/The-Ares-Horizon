#Importing packages
#from replit import audio

from playsound import playsound
import os
import time
import termcolor
import tkinter as tk
from tkinter import ttk

script_directory= os.path.dirname(__file__)

file_name= "Dream Sequence.mp3"

full_path = os.path.join(script_directory, file_name)

try:
    playsound(full_path, block=False)
except Exception:
    pass

#THEME OF THE GAME
BG_main = "#0b0e14"
BG_panel = "#161b22"
text_color = "#e6edf3"
color_cyan = "#58a6ff"
color_yellow = "#f2cc60" 
color_red = "#db2b1f"
color_green = "#7EE787"
font_console = ("Courier", 11)

#Game Stats and Point
gamestart="yes"
crew_safety = 100
mission_budget = 100
science_points = 0

root = tk.Tk()
root.title("The Ares Horizon — Mission Control Terminal")
root.geometry("950x720")  
root.configure(bg=BG_main)

# Global styles setup for progress bars
style = ttk.Style()
style.theme_use('default')
style.configure("Safety.Horizontal.TProgressbar", troughcolor=BG_main, background=color_cyan, thickness=12, borderwidth=0)
style.configure("Budget.Horizontal.TProgressbar", troughcolor=BG_main, background=color_yellow, thickness=12, borderwidth=0)

# Header Telemetry Panel (Hidden by default at startup)
dashboard = tk.Frame(root, bg=BG_panel, bd=1, relief=tk.SOLID, highlightbackground="#30363D", highlightthickness=1)

dashboard.columnconfigure(0, weight=1)
dashboard.columnconfigure(1, weight=1)
dashboard.columnconfigure(2, weight=1)
dashboard.columnconfigure(3, weight=1)

tk.Label(dashboard, text="CREW SAFETY STATUS:", font=("Courier", 10, "bold"), bg=BG_panel, fg=text_color).grid(row=0, column=0, padx=(15, 2), pady=8, sticky="e")
safety_bar = ttk.Progressbar(dashboard, orient="horizontal", length=180, mode="determinate", style="Safety.Horizontal.TProgressbar")
safety_bar.grid(row=0, column=1, padx=(2, 15), pady=8, sticky="w")

tk.Label(dashboard, text="MISSION BUDGET MAP:", font=("Courier", 10, "bold"), bg=BG_panel, fg=text_color).grid(row=0, column=2, padx=(15, 2), pady=8, sticky="e")
budget_bar = ttk.Progressbar(dashboard, orient="horizontal", length=180, mode="determinate", style="Budget.Horizontal.TProgressbar")
budget_bar.grid(row=0, column=3, padx=(2, 15), pady=8, sticky="w")

points_label = tk.Label(dashboard, text="", font=("Courier", 10, "bold"), bg=BG_panel, fg=color_green)
points_label.grid(row=1, column=0, columnspan=4, pady=(2, 6))

# Scrollable Output Log Space
log_container = tk.Frame(root, bg=BG_main)

scroller = tk.Scrollbar(log_container, orient=tk.VERTICAL)
scroller.pack(side=tk.RIGHT, fill=tk.Y)

output_text = tk.Text(log_container, wrap=tk.WORD, state=tk.DISABLED, bg=BG_main, fg=text_color, font=font_console, bd=0, highlightthickness=0, yscrollcommand=scroller.set)
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroller.config(command=output_text.yview)

# Text animations 
def typewriter(text, text_widget, color=text_color, bold=False):
    """Animates text into the GUI Text widget with custom colors and weights."""
    text_widget.config(state=tk.NORMAL)

    # Create a unique tag name using the current timestamp
    tag_name = f"style_{time.time()}"
    font_style = ("Courier", 14, "bold" if bold else "normal")
    text_widget.tag_configure(tag_name, foreground=color, font=font_style)
    
    for letter in text:
        text_widget.insert(tk.END, letter, tag_name)
        text_widget.see(tk.END)
        text_widget.update()
        time.sleep(0.05) 
        
    text_widget.insert(tk.END, "\n")
    text_widget.config(state=tk.DISABLED)

#Buttons interactions
def make_button_interactive(button):
    """Binds mouse hover color transformations to custom game buttons."""
    button.bind("<Enter>", lambda e: button.config(bg="#30363D", fg=color_yellow))
    button.bind("<Leave>", lambda e: button.config(bg=BG_panel, fg=text_color))


# ==========================================
# SCENE FRAME CONTAINERS LAYOUT DIRECTORY
# ==========================================
# The welcome frame is packed FIRST with expand=True to claim the absolute geometric center
welcome_frame = tk.Frame(root, bg=BG_main)
welcome_frame.pack(fill=tk.BOTH, expand=True)

#All other choice containers remain UNPACKED. They take up ZERO pixels of screen space at boot!
stage1_frame = tk.Frame(root, bg=BG_main)
stage2a_frame = tk.Frame(root, bg=BG_main)
stage3a_frame = tk.Frame(root, bg=BG_main)
stage2b_frame = tk.Frame(root, bg=BG_main)
stage3b_frame = tk.Frame(root, bg=BG_main)
restart_frame = tk.Frame(root, bg=BG_main)


#Updating GUI
def update_gui():
    """Updates the progress bars and points text in the dashboard"""
    safety_bar['value'] = crew_safety
    budget_bar['value'] = mission_budget
    points_label.config(text=f"SCIENCE POINTS ACCUMULATED: {science_points}")

    # Visual Warning
    if crew_safety <= 40:
        style.configure("Safety.Horizontal.TProgressbar", background=color_red)
    else:
        style.configure("Safety.Horizontal.TProgressbar", background=color_cyan)

def run_boot_sequence():
    """Plays a beautifully timed mainframe boot animation sequentially."""
    welcome_frame.pack_forget()  # Hide button frame right away
    
    # Carefully spaced out delays so strings print one after another cleanly
    root.after(100, lambda: typewriter("CONNECTING TO NASA CENTRAL MAINFRAME...", output_text, color=color_cyan))
    root.after(900, lambda: typewriter("LOADING ORION-X CRITICAL TELEMETRY STACKS... [OK]", output_text, color=color_green))
    root.after(1700, lambda: typewriter("ESTABLISHING ENCRYPTED LINK TO LAUNCH PAD... [OK]", output_text, color=color_green))
    
    # Draw out a crisp sci-fi ASCII Title Logo
    root.after(2500, lambda: typewriter("\n      ▲  ====  ===  ===  ===   ===   ===  ===  ===  ===  ▲", output_text, color=color_yellow, bold=True))
    root.after(2700, lambda: typewriter("     /_\\ |==|  |==  |==  |==   |==   |==  |==  |==  |== /_\\", output_text, color=color_yellow, bold=True))
    root.after(2900, lambda: typewriter("    /___\\|==|  |==  |==  |==   |==   |==  |==  |==  |==/___\\", output_text, color=color_yellow, bold=True))
    root.after(3100, lambda: typewriter("         ====  ===  ===  ===   ===   ===  ===  ===  ===", output_text, color=color_yellow, bold=True))
    root.after(3300, lambda: typewriter("                  --- THE ARES HORIZON v3.0 ---", output_text, color=color_cyan, bold=True))
    root.after(3500, lambda: typewriter("      ▼=================================================▼\n", output_text, color=color_yellow, bold=True))
    
    # Wait for the logo to finish typing, then clear screen and start game
    root.after(5000, trigger_game_start)


def trigger_game_start():
    """Wipes the boot console clean and initializes Chapter 1."""
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)  
    output_text.config(state=tk.DISABLED)
    
    # Forces the dashboard panel to the absolute TOP of the window layout
    log_container.pack_forget()
    dashboard.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
    log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 0)) 
    update_gui()

    # Now type the welcome text safely onto a fresh screen
    typewriter("Welcome to The Ares Horizon Game!", output_text, bold=True)
    typewriter("======================================================================", output_text, bold=True)
    typewriter("In this game you are a Flight Director at NASA Mission Control!", output_text)
    typewriter("The Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!", output_text)
    typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.", output_text)
    typewriter("======================================================================", output_text, bold=True)

    typewriter("\nSTAGE-1: T-MINUS COUNTDOWN", output_text, bold=True)
    typewriter("", output_text)
    typewriter("The Orion-X awaits launch", output_text)
    typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", output_text, color=color_red)
    typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', output_text, color=color_red)
    
    stage1_frame.pack(pady=10)
    
def handle_choice1(choice):
    stage1_frame.pack_forget()
    global crew_safety, mission_budget, science_points

    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)

    #=================
    #BRANCH 1 Choice 1
    #=================
    if choice == "1":
        typewriter("\nIGNITION! The rocket vibrates violently as it puches through the wind", output_text)
        typewriter("Minutes later you reach the edge of the atmosphere and enter orbit, but the stress caused by the wind resulted in an issue", output_text)
        typewriter("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!", output_text, color= "red")

        #Penalty for taking risk and damage
        crew_safety -= 20
        mission_budget -= 10
        update_gui()

        #Display Points after choice
        typewriter("", output_text)
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", output_text, color= "cyan")

        #Choice 1 Stage 2
        typewriter("\nSTAGE-2: THE ORBITAL ANOMALY", output_text, bold = True)
        stage2a_frame.pack(pady=10)

        #=================
        #BRANCH 1 Choice 2
        #=================
    elif choice == "2":
        typewriter("\nYou stand down on the launch. The crew exits the spacecraft", output_text)
        typewriter("Weeks later, you launch on a much longer and not as ideal route", output_text)
        typewriter("Deep in space, a massive radiation storm knocks down your primary navigation computer", output_text, color= "red")

        #Crew stays secure but delays drain cash
        mission_budget -= 40
        update_gui()
        
        #Display points after choice
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", output_text, color= "cyan")

        #Choice 2 Stage 2
        typewriter("\nSTAGE-2: LOST IN SPACE", output_text, bold = True)
        typewriter("\nMark scrambles: Director, the main computer is dead, we are drifting!", output_text, color= "red")
        stage2b_frame.pack(pady=10)

def end_game_session():
    typewriter("\n=======================================================", output_text)
    typewriter(f"Final Session Archive Summary-> Crew Safety: {crew_safety}% | Budget: {mission_budget}% | Science Points: {science_points}", output_text, color=color_cyan)
    restart_frame.pack(pady=15)

def reboot_mission():
    global crew_safety, mission_budget, science_points
    restart_frame.pack_forget()
    
    crew_safety = 100
    mission_budget = 100
    science_points = 0
    update_gui()
    
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    
    welcome_frame.pack(pady=40)


# ==========================================
# POPULATE WIDGETS INTO THE FRAMES
# ==========================================

# --- 1. Welcome Screen elements (Centered Perfectly) ---
btn_start = tk.Button(welcome_frame, 
                      text="[ LETS BEGIN ]", 
                      font=("Courier", 16, "bold"), 
                      bg=BG_panel, 
                      fg=text_color, 
                      bd=0, 
                      padx=50, 
                      pady=25, 
                      highlightthickness=1, 
                      highlightbackground="#30363D", 
                      activebackground="#21262D", 
                      cursor="hand2", 
                      command=run_boot_sequence)
btn_start.pack(expand=True) # This is what locks it to the horizontal and vertical center!
make_button_interactive(btn_start)


def handle_choice2a(choice):
    stage2a_frame.pack_forget()
    global crew_safety, mission_budget, science_points
    
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    
    if choice == "1":
        typewriter("\nRisky Move, the engines fire hard. The pressure stabilizes just in time.", output_text)
        typewriter("Months pass in deep space, and the crew finally arrives at the Red Planet", output_text)
        crew_safety -= 10
        science_points += 30
        update_gui()

        typewriter("", output_text)
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", output_text, color="cyan")

        typewriter("\nSTAGE-3: MARS LANDING", output_text, bold=True)
        typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates", output_text)
        typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", output_text, color="red")
        stage3a_frame.pack(pady=10)

    elif choice == "2":
        typewriter("The emergency escape system rips apart from the capsule", output_text)
        typewriter("The crew safely splash down in the atlantic ocean", output_text)
        typewriter("The mission is over but the crew lives", output_text)
        mission_budget = 0
        update_gui()
        end_game_session()

def handle_choice3a(choice):
    stage3a_frame.pack_forget()
    global crew_safety, mission_budget, science_points
        
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    
    if choice == "1":
        typewriter("\nHEROIC VICTORY! The Commander flies beautifully, touching down safely!", output_text, color="green")
        typewriter("Human step foot on the Red Planet for the first time!", output_text, color="green")
        typewriter("Excellent Work, Director", output_text, color="green")
        crew_safety += 10
        science_points += 50
        update_gui()

    elif choice == "2":
        typewriter("\nCRASH DOWN! The system clips a massive hidden boulder", output_text, color="red")
        typewriter("The lander tips and loses pressure. Space is not forgiving.", output_text, color="red")
        typewriter("MISSION FAILED", output_text, bold=True, color="red")
        crew_safety = 0
        mission_budget = 0
        update_gui()

    end_game_session()

def handle_choice2b(choice):
    stage2b_frame.pack_forget()
    global crew_safety, mission_budget, science_points
    
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    
    if choice == "1":
        typewriter("The patch works! The navigation is back up again", output_text)
        typewriter("However the reboot drained 60% of your spacecraft power reserves", output_text, color="red")
        typewriter("The crew arrive at Mars in a critically underpowered ship", output_text)
        science_points += 20
        update_gui()

        typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", output_text, color="cyan")
        typewriter("\nSTAGE-3: THE LANDING", output_text, bold=True)
        typewriter("\nWith the low power, you cannot run both the heaters and the landing thrusters", output_text)
        stage3b_frame.pack(pady=10)

    elif choice == "2":
        typewriter("LOST ORBIT! The math is too complex with the light-lag delay", output_text, color="red")
        typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication", output_text, color="red")
        crew_safety = 0
        mission_budget = 0
        update_gui()
        end_game_session()

def handle_choice3b(choice):
    stage3b_frame.pack_forget()
    global crew_safety, mission_budget, science_points
          
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
          
    if choice == "1":
        typewriter("The solar sails catch enough sunlight to recharge", output_text, color="green")
        typewriter("The crew lands flawlessly with power to spare. You saved them with patience!", output_text, color="green")
        crew_safety += 10
        science_points += 40
        update_gui()

    elif choice == "2":
        typewriter("\n BURN OUT! The extreme cold freezes the fuel valves during descent.", output_text, color="red")
        typewriter("The engines fail 100 meters up. The ship impacts the surface.", output_text, color="red")
        typewriter("MISSION FAILED", output_text, color="red", bold=True)
        crew_safety = 0
        update_gui()

    end_game_session()


# Run structural sync data metrics counters
update_gui()

root.mainloop()