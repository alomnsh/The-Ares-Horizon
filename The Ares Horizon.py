#Importing packages
import os
import time
import termcolor
import tkinter as tk
from tkinter import ttk
import sys
import ctypes
import math
import random
from PIL import Image, ImageTk

#If key is pressed it is true, if it is released it is false
def handle_press(event):
    global key_states
    if event.keysym in key_states:
        key_states[event.keysym] = True

def handle_release(event):
    global key_states
    if event.keysym in key_states:
        key_states[event.keysym] = False


#Sound Effects

script_directory = os.path.dirname(os.path.abspath(__file__))

def send_mci_command(command):
    """Helper function to talk directly to the Windows audio engine."""
    buffer = ctypes.create_string_buffer(255)
    ctypes.windll.winmm.mciSendStringA(command.encode('utf-8'), buffer, 254, 0)
    return buffer.value.decode('utf-8')

file_name = "Dream Sequence.mp3"
full_path = f'"{os.path.join(script_directory, file_name)}"'

try: 
    send_mci_command(f"open {full_path} type mpegvideo alias bg_music")
    send_mci_command("play bg_music repeat")
except Exception: 
    pass

# --- SOUND EFFECT TRACK FILE DIRECTORIES ---
warning_file = f'"{os.path.join(script_directory, "Warning.mp3")}"'
pull_up_file = f'"{os.path.join(script_directory, "Pull Up.mp3")}"'
roger_that_file = f'"{os.path.join(script_directory, "Roger That.mp3")}"'
space_warning_file = f'"{os.path.join(script_directory, "Spacecraft Warning.mp3")}"'
click_file = f'"{os.path.join(script_directory, "Click.mp3")}"'
mission_success_file = f'"{os.path.join(script_directory, "Mission Success.mp3")}"'
mission_failed_file = f'"{os.path.join(script_directory, "Mission Failed.mp3")}"'

# Track state toggles
warning_sound = False
pull_up_sound = False
roger_that_sound = False
space_warning_sound = False
click_sound = False
mission_success_sound = False
mission_failed_sound = False

#Warning Sound Effect Setup
def trigger_warning_sound():
    global warning_sound
    if not warning_sound:
        warning_sound = True
        try:
            send_mci_command(f"open {warning_file} type mpegvideo alias sf_warning") #opens the audio file
            send_mci_command("play sf_warning repeat") #plays on repeat until the stop function is activated
        except Exception:
            pass

#Spacecraft warning setup
def trigger_spacecraft_warning_sound():
    global space_warning_sound
    if not space_warning_sound:
        space_warning_sound = True
        try:
            send_mci_command(f"open {space_warning_file} type mpegvideo alias sf_spacecraft_warning")
            send_mci_command("play sf_spacecraft_warning repeat")
        except Exception:
            pass

#Roger That sound effect
def trigger_roger_sound():
    global roger_that_sound
    if not roger_that_sound:
        roger_that_sound = True
        try:
            send_mci_command(f"open {roger_that_file} type mpegvideo alias sf_roger")
            send_mci_command("play sf_roger from 0") #only runs audio once
        except Exception:
            pass

#Pull Up Sound effect
def trigger_pullup_sound():
    global pull_up_sound
    if not pull_up_sound:
        pull_up_sound = True
        try:
            send_mci_command(f"open {pull_up_file} type mpegvideo alias sf_pullup")
            send_mci_command("play sf_pullup from 0 wait")
        except Exception:
            pass

#Click Sound effect
def trigger_click_sound():
    global click_sound
    if not click_sound:
        click_sound = True
        try:
            send_mci_command(f"open {click_file} type mpegvideo alias sf_click")
            send_mci_command("play sf_click from 0")
        except Exception:
            pass

#Mission Success Sound Effect
def trigger_mission_success_sound():
    global mission_success_sound
    if not mission_success_sound:
        mission_success_sound = True
        try:
            send_mci_command(f"open {mission_success_file} type mpegvideo alias sf_success")
            send_mci_command("play sf_success from 0")
        except Exception:
            pass

#Mission Failed Sound Effect
def trigger_mision_failed_sound():
    global mission_failed_sound
    if not mission_failed_sound:
        mission_failed_sound = True
        try:
            send_mci_command(f"open {mission_failed_file} type mpegvideo alias sf_failed")
            send_mci_command("play sf_failed from 0")
        except Exception:
            pass
    
#Stop all sounds
def stop_all_sounds():
    global space_warning_sound, warning_sound, roger_that_sound, pull_up_sound, click_sound, mission_success_sound, mission_failed_sound

    space_warning_sound = False
    warning_sound = False
    roger_that_sound = False
    pull_up_sound = False
    click_sound = False

    aliases = ["sf_warning", "sf_pullup", "sf_roger", "sf_spacecraft_warning", "sf_click", "sf_success", "sf_failed"]
    for alias in aliases:
        try:
            send_mci_command(f"stop {alias}")
            send_mci_command(f"close {alias}")
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
font_console = ("Courier", 14)

#Game Stats and Point
gamestart="yes"
crew_safety = 100
mission_budget = 100
science_points = 0

active_timers = []

def cancel_all_timers():
    """Wipes out any ticking background timers to prevent crash errors."""
    global active_timers
    for timer_id in active_timers:
        try:
            root.after_cancel(timer_id)
        except Exception:
            pass
    active_timers.clear()

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

tk.Label(dashboard, text="CREW SAFETY STATUS:", font=("Courier", 13, "bold"), bg=BG_panel, fg=text_color).grid(row=0, column=0, padx=(15, 2), pady=8, sticky="e")
safety_bar = ttk.Progressbar(dashboard, orient="horizontal", length=180, mode="determinate", style="Safety.Horizontal.TProgressbar")
safety_bar.grid(row=0, column=1, padx=(2, 15), pady=8, sticky="w")

tk.Label(dashboard, text="MISSION BUDGET:", font=("Courier", 13, "bold"), bg=BG_panel, fg=text_color).grid(row=0, column=2, padx=(15, 2), pady=8, sticky="e")
budget_bar = ttk.Progressbar(dashboard, orient="horizontal", length=180, mode="determinate", style="Budget.Horizontal.TProgressbar")
budget_bar.grid(row=0, column=3, padx=(2, 15), pady=8, sticky="w")

points_label = tk.Label(dashboard, text="", font=("Courier", 13, "bold"), bg=BG_panel, fg=color_green)
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
    """Animates text into the GUI Text widget safely, checking if it exists first."""
    try:
        # Check if the text widget was destroyed or closed
        if not text_widget.winfo_exists():
            return
    except Exception:
        return

    text_widget.config(state=tk.NORMAL)
    tag_name = f"style_{time.time()}"
    font_style = ("Courier", 14, "bold" if bold else "normal")
    text_widget.tag_configure(tag_name, foreground=color, font=font_style)
    
    for letter in text:
        try:
            # Safety check before inserting every single letter
            if not text_widget.winfo_exists():
                return
            text_widget.insert(tk.END, letter, tag_name)
            text_widget.see(tk.END)
            text_widget.update()
            time.sleep(0.000000000000001) 
        except Exception:
            return
        
    try:
        text_widget.insert(tk.END, "\n")
        text_widget.config(state=tk.DISABLED)
    except Exception:
        return

def update_progress(text, text_widget, color=color_cyan, bold=False, add_newline=False):
    """Updates the terminal loading bar in place by instantly overwriting the previous line."""
    try:
        if not text_widget.winfo_exists(): return
    except Exception: return
    text_widget.config(state=tk.NORMAL)
    text_widget.delete("end-2c linestart", "end-1c")
    tag_name = f"progress_{time.time()}"
    font_style = ("Courier", 14, "bold" if bold else "normal")
    text_widget.tag_configure(tag_name, foreground=color, font=font_style)
    text_widget.insert(tk.END, text, tag_name)
    if add_newline:
        text_widget.insert(tk.END, "\n")
    text_widget.see(tk.END)
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
    """Updates the progress bars and points text safely within a try block."""
    try:
        safety_bar['value'] = crew_safety
        budget_bar['value'] = mission_budget
        points_label.config(text=f"SCIENCE POINTS ACCUMULATED: {science_points}")

        if crew_safety <= 40:
            style.configure("Safety.Horizontal.TProgressbar", background=color_red)
        else:
            style.configure("Safety.Horizontal.TProgressbar", background=color_cyan)
    except Exception:
        pass

def run_boot_sequence():
    """Plays the mainframe boot animation with a custom in-place updating console loading bar."""
    trigger_click_sound()
    cancel_all_timers() 
    welcome_frame.pack_forget()  
    log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 0)) 
    
    # Initial diagnostic logs
    #active_timers.append(root.after(100, lambda: typewriter("CONNECTING TO NASA CENTRAL MAINFRAME...", output_text, color=color_cyan)))
    #active_timers.append(root.after(1800, lambda: typewriter("LOADING ORION-X CRITICAL TELEMETRY STACKS... [OK]", output_text, color=color_green)))
    #active_timers.append(root.after(4200, lambda: typewriter("ESTABLISHING ENCRYPTED LINK TO LAUNCH PAD... [OK]", output_text, color=color_green)))
    
    # Initialize the Progress Bar header row
    #active_timers.append(root.after(6800, lambda: typewriter("\nINITIALIZING MAIN OPERATIONS ARRAY...", output_text, color=color_yellow, bold=True)))
    #active_timers.append(root.after(8500, lambda: typewriter("PROGRESS: [███.....................] 15%", output_text, color=color_cyan)))
    #active_timers.append(root.after(10000, lambda: update_progress("PROGRESS: [█████████...............] 35%", output_text, color=color_cyan)))
    #active_timers.append(root.after(11500, lambda: update_progress("PROGRESS: [██████████████..........] 55%", output_text, color=color_cyan)))
    #active_timers.append(root.after(13000, lambda: update_progress("PROGRESS: [███████████████████.....] 75%", output_text, color=color_cyan)))
    
    # Final step finishes the bar, locks it to green, and pushes the cursor down with add_newline=True
    #active_timers.append(root.after(14500, lambda: update_progress("PROGRESS: [████████████████████████] 100% [Loading Complete]", output_text, color=color_green, bold=True, add_newline=True)))
    
    # Wait for completion, then clear screen and trigger Chapter 1
    #active_timers.append(root.after(17500, trigger_game_start))
    trigger_game_start()

def trigger_game_start():
    """Wipes the boot console clean and initializes Chapter 1."""
    # ADD THESE TWO LINES AT THE VERY START OF THE FUNCTION:
    if not root.winfo_exists():
        return

    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    
    log_container.pack_forget()
    dashboard.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
    log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 0))
    update_gui()

    typewriter("Welcome to The Ares Horizon Game!", output_text, bold=True)
    typewriter("In this game you are a Flight Director at NASA Mission Control!", output_text)
    typewriter("The Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!", output_text)
    typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.", output_text)

    typewriter("\nSTAGE-1: T-MINUS COUNTDOWN", output_text, bold=True)
    typewriter("", output_text)
    typewriter("The Orion-X awaits launch", output_text)

    trigger_warning_sound()

    typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", output_text, color=color_red)
    typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', output_text, color=color_red)
    
    try:
        stage1_frame.pack(pady=10)
    except Exception:
        return
    
def handle_choice1(choice):
    stop_all_sounds()
    trigger_click_sound()

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

        #Penalty for taking risk and damage
        crew_safety -= 20
        mission_budget -= 10
        update_gui()

        #Display Points after choice
        typewriter("", output_text)
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", output_text, color= "cyan")

        #Choice 1 Stage 2
        typewriter("\nSTAGE-2: THE ORBITAL ANOMALY", output_text, bold = True)
        trigger_spacecraft_warning_sound()
        typewriter("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!", output_text, color= "red")
        stage2a_frame.pack(pady=10)

        #=================
        #BRANCH 1 Choice 2
        #=================
    elif choice == "2":
        typewriter("\nYou stand down on the launch. The crew exits the spacecraft", output_text)
        typewriter("Weeks later, you launch on a much longer and not as ideal route", output_text)

        #Crew stays secure but delays drain cash
        mission_budget -= 40
        update_gui()
        
        #Display points after choice
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", output_text, color= "cyan")

        #Choice 2 Stage 2
        typewriter("\nSTAGE-2: LOST IN SPACE", output_text, bold = True)
        trigger_warning_sound()
        typewriter("Deep in space, a massive radiation storm knocks down your primary navigation computer", output_text, color= "red")
        typewriter("\nMark scrambles: Director, the main computer is dead, we are drifting!", output_text, color= "red")
        stage2b_frame.pack(pady=10)

def handle_choice2a(choice):
    stage2a_frame.pack_forget()
    global crew_safety, mission_budget, science_points
    
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        typewriter("\nRisky Move, the engines fire hard. The pressure stabilizes just in time.", output_text)
        typewriter("Months pass in deep space, and the crew finally arrives at the Red Planet", output_text)
        crew_safety -= 10
        science_points += 30
        update_gui()
        handle_landing_choice_branch_1()

    elif choice == "2":
        typewriter("The emergency escape system rips apart from the capsule", output_text)
        typewriter("The crew safely splash down in the atlantic ocean", output_text)
        typewriter("The mission is over but the crew lives", output_text)
        mission_budget = 0
        update_gui()
        end_game_session()

def handle_landing_choice_branch_1():
    typewriter("", output_text)
    typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", output_text, color="cyan")

    typewriter("\nSTAGE-3: MARS LANDING", output_text, bold=True)
    typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates", output_text)
    typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", output_text, color="red")
    stage3a_frame.pack(pady=10)

def handle_landing_choice_branch_2():
    typewriter("", output_text)
    typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", output_text, color="cyan")

    typewriter("\nSTAGE-4: MARS LANDING", output_text, bold=True)
    typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates", output_text)
    typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", output_text, color="red")
    stage3a_frame.pack(pady=10)

def handle_choice3a(choice):
    stage3a_frame.pack_forget()
    global crew_safety, mission_budget, science_points
        
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        landing_minigame_difficulty()
        #trigger_mission_success_sound()
        #typewriter("\nHEROIC VICTORY! The Commander flies beautifully, touching down safely!", output_text, color="green")
        #typewriter("Human step foot on the Red Planet for the first time!", output_text, color="green")
        #typewriter("Excellent Work, Director", output_text, color="green")
        #if crew_safety == 100:
            #crew_safety = 100
        #else:
            #crew_safety += 10

        #science_points += 50
        update_gui()

    elif choice == "2":
        trigger_pullup_sound()
        typewriter("\nCRASH DOWN! The system clips a massive hidden boulder", output_text, color="red")
        typewriter("The lander tips and loses pressure. Space is not forgiving.", output_text, color="red")
        trigger_mision_failed_sound()
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
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        typewriter("The patch works! The navigation is back up again", output_text)
        typewriter("However the reboot drained 60% of your spacecraft power reserves", output_text, color="red")
        science_points += 20
        update_gui()

        typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", output_text, color="cyan")
        typewriter("\nSTAGE-3: LOW POWER", output_text, bold=True)
        trigger_spacecraft_warning_sound()
        typewriter("The crew arrive at Mars in a critically underpowered ship", output_text, color="red")
        typewriter("With the low power, you cannot run both the heaters and the landing thrusters", output_text, color="red")
        stage3b_frame.pack(pady=10)

    elif choice == "2":
        typewriter("LOST ORBIT! The math is too complex with the light-lag delay", output_text, color="red")
        typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication", output_text, color="red")
        trigger_mision_failed_sound()
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
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        typewriter("The solar sails catch enough sunlight to recharge", output_text, color="green")
        science_points += 40
        update_gui()
        handle_landing_choice_branch_2()

    elif choice == "2":
        typewriter("\n BURN OUT! The extreme cold freezes the fuel valves during descent.", output_text, color="red")
        typewriter("The engines fail 100 meters up. The ship impacts the surface.", output_text, color="red")
        trigger_mision_failed_sound()
        typewriter("MISSION FAILED", output_text, color="red", bold=True)
        crew_safety = 0
        update_gui()

    end_game_session()

#===========================================================================
#LANDING MINI GAME (PYGAME EMBEDDED EDITION)
#===========================================================================
def run_physics_frame():
    global altitude, velocity_y, ship_angle, ship_x, ship_y, game_running, current_difficulty
    import pygame
    
    if not game_running:
        return
        
    f_w = game_frame.winfo_width()
    f_h = game_frame.winfo_height()
    
    screen_center_x = f_w // 2
    left_wall = screen_center_x - 175
    right_wall = screen_center_x + 175
    
    # 1. Continuous stabilization dampening for visual animations
    ship_angle *= 0.85
    
    # Boundary constraints to make sure the ship doesn't go off screen
    if ship_x - 25 < left_wall: ship_x = left_wall + 25
    if ship_x + 25 > right_wall: ship_x = right_wall - 25
        
    # Adjust scrolling speed dynamically depending on active difficulty choice
    if current_difficulty == "EASY":
        altitude += 2.0
    elif current_difficulty == "MEDIUM":
        altitude += 3.2
    else:
        altitude += 4.5  
    
    # 2. Graphics Rendering Operations
    pg_screen.fill((15, 15, 25)) 
    
    # Loop and draw moving spike segments dynamically
    for obs in obstacles:
        screen_y = obs["y"] - int(altitude)
        if -150 < screen_y < f_h + 150:
            calculated_height = int(obs["width"] * 0.3)
            
            if obs["side"] == "LEFT":
                scaled_spike = pygame.transform.scale(spike_left, (obs["width"], calculated_height))
                pg_screen.blit(scaled_spike, (left_wall - 40, screen_y))
            else:
                scaled_spike = pygame.transform.scale(spike_right, (obs["width"], calculated_height))
                pg_screen.blit(scaled_spike, (right_wall + 40 - obs["width"], screen_y))
                
    # Draw solid dark gray side columns right on top of outer edges to mask spike bases
    pygame.draw.rect(pg_screen, (40, 40, 45), (0, 0, left_wall, f_h))
    pygame.draw.rect(pg_screen, (40, 40, 45), (right_wall, 0, f_w - right_wall, f_h))
    
    # Draw White HUD text element inside the bottom right corner
    hud_font = pygame.font.SysFont("Courier", 18, bold=True)
    hud_string = f"SYS-MODE: {current_difficulty}"
    text_surface = hud_font.render(hud_string, True, (255, 255, 255))
    text_x = f_w - text_surface.get_width() - 25
    text_y = f_h - text_surface.get_height() - 25
    pg_screen.blit(text_surface, (text_x, text_y))
    
    # 3. Ship Rect Modeling & Collision Check (Sized 50x90px)
    ship_rect = pygame.Rect(ship_x - 25, ship_y - 45, 50, 90)
    pg_screen.blit(ship_surface, (ship_rect.x, ship_rect.y))
    
    # Collision Verification Engine
    crashed = False
    if ship_rect.left <= left_wall or ship_rect.right >= right_wall:
        crashed = True
    else:
        for obs in obstacles:
            screen_y = obs["y"] - int(altitude)
            calculated_height = int(obs["width"] * 0.3)
            
            if -150 < screen_y < f_h + 150:
                if obs["side"] == "LEFT":
                    obs_rect = pygame.Rect(left_wall - 40, screen_y, obs["width"], calculated_height)
                else:
                    obs_rect = pygame.Rect(right_wall + 40 - obs["width"], screen_y, obs["width"], calculated_height)
                    
                if ship_rect.colliderect(obs_rect):
                    crashed = True
                    break

    # 4. Pipeline Refresh Execution
    pygame.display.flip()
    
    if crashed:
        game_running = False
        # Unbind our temporary keys before crashing so they don't break other text areas
        root.unbind("<Left>")
        root.unbind("<Right>")
        pygame.quit()
        game_frame.place_forget() 
        space_ship_crash()        
    else:
        root.after(16, run_physics_frame)

def start_landing_simulation_canvas():
    global game_frame, pg_screen, pg_clock, altitude, velocity_y, ship_angle, game_running
    global ship_x, ship_y, obstacles, ship_surface, spike_left, spike_right, current_difficulty
    import os
    import pygame
    import random
    
    # 1. Reset Physics Engine States
    altitude = 0.0
    velocity_y = 0.0
    ship_angle = 0.0
    game_running = True
    
    # 2. Pull actual window geometry dynamically
    root.update_idletasks()
    win_w = root.winfo_width()
    win_h = root.winfo_height()
    
    frame_w = win_w
    frame_h = win_h - 100
    
    # 3. Create a clean Tkinter Frame container for Pygame
    game_frame = tk.Frame(root, width=frame_w, height=frame_h, bg="black")
    game_frame.place(x=0, y=100, width=frame_w, height=frame_h)
    root.update() 
    
    # 4. Redirect the Pygame pipeline window hook inside Tkinter
    os.environ['SDL_WINDOWID'] = str(game_frame.winfo_id())
    os.environ['SDL_VIDEODRIVER'] = 'windib' if os.name == 'nt' else 'x11'
    
    # Initialize Pygame embedded sub-window frame
    pygame.init()
    pg_screen = pygame.display.set_mode((frame_w, frame_h))
    pg_clock = pygame.time.Clock()
    
    # 5. Load and scale your 50x90px custom Spaceship design
    try:
        raw_ship = pygame.image.load("Spaceship.png").convert_alpha()
        ship_surface = pygame.transform.scale(raw_ship, (50, 90))
    except pygame.error:
        ship_surface = pygame.Surface((50, 90))
        ship_surface.fill((0, 240, 240)) 

    # 6. Load your single native 200x60px Spike image ("Small Spike.png") & mirror it
    try:
        raw_spike = pygame.image.load("Small Spike.png").convert_alpha()
        spike_left = pygame.transform.scale(raw_spike, (200, 60))
        spike_right = pygame.transform.flip(spike_left, True, False)
    except pygame.error:
        spike_left = pygame.Surface((200, 60)); spike_left.fill((130, 45, 45))
        spike_right = pygame.Surface((200, 60)); spike_right.fill((130, 45, 45))
    
    # 7. Core Ship Coordinates (True Dead Center Math)
    ship_x = frame_w // 2
    ship_y = frame_h // 2
    
    # 8. Symmetrical Dense Spacing Properties
    if current_difficulty == "EASY":
        small_w = 60
        medium_w = 90
        large_w = 120
        gap_spacing = 160  
    elif current_difficulty == "MEDIUM":
        small_w = 80
        medium_w = 120
        large_w = 150
        gap_spacing = 130  
    else: # HARD MODE
        small_w = 110
        medium_w = 160
        large_w = 200  
        gap_spacing = 100  
    
    # Generate balanced obstacle arrays
    obstacles = []
    for i in range(60):
        obs_y = 450 + (i * gap_spacing)
        side = "LEFT" if i % 2 == 0 else "RIGHT"
        width = random.choice([small_w, medium_w, large_w])
        obstacles.append({"y": obs_y, "side": side, "width": width})
        
    def move_left(event):
        global ship_x, ship_angle
        ship_x -= 15 # Move speed step
        ship_angle = min(25, ship_angle + 5)

    def move_right(event):
        global ship_x, ship_angle
        ship_x += 15 # Move speed step
        ship_angle = max(-25, ship_angle - 5)

    root.bind("<Left>", move_left)
    root.bind("<Right>", move_right)
    
    # Force keyboard focus to root window container layer
    root.focus_set()
    
    # Kick off loop
    run_physics_frame()

def landing_minigame_difficulty():
    global menu_backdrop
    
    font_subtitle = ("Courier", 16, "bold")
    
    # 1. Create a master full-screen overlay frame
    menu_backdrop = tk.Frame(root, bg=BG_main)
    menu_backdrop.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

    # 2. Expanded container to fit all three choices perfectly
    button_container = tk.Frame(menu_backdrop, bg=BG_panel, bd=2, relief=tk.RIDGE)
    button_container.place(relx=0.5, rely=0.5, width=400, height=400, anchor=tk.CENTER)
    
    # Title Label
    lbl_title = tk.Label(button_container, text="CHOOSE DIFFICULTY", font=font_subtitle, fg=text_color, bg=BG_panel)
    lbl_title.pack(pady=25)
    
    def select_mode(mode_setting):
        global current_difficulty
        current_difficulty = mode_setting
        menu_backdrop.place_forget() 
        start_landing_simulation_canvas() 
        
    # Three Distinct Symmetrical Options
    btn_easy = tk.Button(button_container, text="EASY MODE", font=font_console, bg=color_cyan, fg="black", command=lambda: select_mode("EASY"), width=20)
    btn_easy.pack(pady=10)
    
    btn_med = tk.Button(button_container, text="MEDIUM MODE", font=font_console, bg="yellow", fg="black", command=lambda: select_mode("MEDIUM"), width=20)
    btn_med.pack(pady=10)
    
    btn_hard = tk.Button(button_container, text="HARD MODE", font=font_console, bg=color_red, fg="white", command=lambda: select_mode("HARD"), width=20)
    btn_hard.pack(pady=10)

#CRASH SCREEN
def space_ship_crash():
    typewriter ("💥 CRASH: Space shuttle hull compromised!", output_text)
    trigger_mision_failed_sound
    end_game_session()

def end_game_session():
    typewriter(f"\nFinal Session Summary-> Crew Safety: {crew_safety}% | Budget: {mission_budget}% | Science Points: {science_points}", output_text, color=color_cyan)
    restart_frame.pack(pady=15)

def reboot_mission():
    global crew_safety, mission_budget, science_points
    cancel_all_timers()
    restart_frame.pack_forget()
    
    # Reset tracking state metrics
    crew_safety = 100
    mission_budget = 100
    science_points = 0
    update_gui()
    
    try:
        dashboard.pack_forget()  
        log_container.pack_forget()
        
        # Clear out any leftover typed text
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.config(state=tk.DISABLED)
    except Exception:
        pass
    
    welcome_frame.pack(fill=tk.BOTH, expand=True)
    btn_start.pack(expand=True)

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
btn_start.pack(expand=True) 
make_button_interactive(btn_start)

# 2. Stage 1 Elements (RESTORED)
tk.Label(stage1_frame, text="AWAITING STRATEGIC DIRECTIVE INSTRUCTIONS...", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold")).pack(pady=4)
b1_1 = tk.Button(stage1_frame, text="1) Launch Now - Push past high winds and save time", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice1("1"))
b1_1.pack(in_=stage1_frame, fill=tk.X, pady=2)
b1_2 = tk.Button(stage1_frame, text="2) Delay Launch - Abort current window and wait", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice1("2"))
b1_2.pack(in_=stage1_frame, fill=tk.X, pady=2)
make_button_interactive(b1_1); make_button_interactive(b1_2)

# 3. Stage 2A Elements
tk.Label(stage2a_frame, text="CRITICAL PRESSURE DROP DETECTED. CHOOSE ROUTE:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold")).pack(pady=4)
b2a_1 = tk.Button(stage2a_frame, text="1) PUSH ENGINES - Fire second stage anyway to clear orbit", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice2a("1"))
b2a_1.pack(in_=stage2a_frame, fill=tk.X, pady=2)
b2a_2 = tk.Button(stage2a_frame, text="2) ABORT MISSION - Activate the emergency escape tower", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice2a("2"))
b2a_2.pack(in_=stage2a_frame, fill=tk.X, pady=2)
make_button_interactive(b2a_1); make_button_interactive(b2a_2)

# 4. Stage 3A Elements
tk.Label(stage3a_frame, text="AUTOMATED LANDING FAILURE! CHOOSE FLIGHT CONTROLS:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold")).pack(pady=4)
b3a_1 = tk.Button(stage3a_frame, text="1) MANUAL CONTROL - Commander flies manual flight joystick", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice3a("1"))
b3a_1.pack(in_=stage3a_frame, fill=tk.X, pady=2)
b3a_2 = tk.Button(stage3a_frame, text="2) AUTO-PILOT - Trust flight computer mapping systems", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice3a("2"))
b3a_2.pack(in_=stage3a_frame, fill=tk.X, pady=2)
make_button_interactive(b3a_1); make_button_interactive(b3a_2)

# 5. Stage 2B (Lost in Space) Elements
tk.Label(stage2b_frame, text="STAGE-2: LOST IN SPACE // ARRAY REBOOT INTERFACE:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold")).pack(pady=4)
b2b_1 = tk.Button(stage2b_frame, text="1) UPLOAD A PATCH - Push an unverified software fix to reboot the system", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice2b("1"))
b2b_1.pack(in_=stage2b_frame, fill=tk.X, pady=2)
b2b_2 = tk.Button(stage2b_frame, text="2) MANUAL TRAJECTORY - Force crew to navigate manually using star maps", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice2b("2"))
b2b_2.pack(in_=stage2b_frame, fill=tk.X, pady=2)
make_button_interactive(b2b_1); make_button_interactive(b2b_2)

# 6. Stage 3B (Low Power Descent) Elements
tk.Label(stage3b_frame, text="STAGE-3: THE LANDING // ROUTE AVAILABLE BATTERY POWER:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold")).pack(pady=4)
b3b_1 = tk.Button(stage3b_frame, text="1) DEPLOY SOLAR SAILS - Wait in orbit for 3 days to charge batteries", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice3b("1"))
b3b_1.pack(in_=stage3b_frame, fill=tk.X, pady=2)
b3b_2 = tk.Button(stage3b_frame, text="2) EMERGENCY BURN - Cut the life support heaters to power a descent", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=10, pady=6, highlightthickness=1, highlightbackground="#30363D", command=lambda: handle_choice3b("2"))
b3b_2.pack(in_=stage3b_frame, fill=tk.X, pady=2)
make_button_interactive(b3b_1); make_button_interactive(b3b_2)

# 7. Restart Elements
btn_restart = tk.Button(restart_frame, text="TRY AGAIN?", font=("Courier", 13, "bold"), bg=BG_panel, fg=color_cyan, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", command=reboot_mission)
btn_restart.pack(in_=restart_frame, pady=5)
make_button_interactive(btn_restart)

# Run structural sync data metrics counters
update_gui()

def on_close_window():
    """Intercepts clicking the 'X' button to kill background timer threads instantly."""
    stop_all_sounds()
    cancel_all_timers()
    root.destroy()

# Tell Tkinter to run our cleanup function when the window closes
root.protocol("WM_DELETE_WINDOW", on_close_window)

root.mainloop()