#Importing packages
import os
import time
import termcolor
import tkinter as tk
from tkinter import ttk
import sys
import math
import random
from PIL import Image, ImageTk
import pygame
import json

if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"

#If key is pressed it is true, if it is released it is false
def handle_press(event):
    global key_states
    if event.keysym in key_states:
        key_states[event.keysym] = True

def handle_release(event):
    global key_states
    if event.keysym in key_states:
        key_states[event.keysym] = False

script_directory = os.path.dirname(os.path.abspath(__file__))

# 1. Initialize volumes cleanly as raw floats
is_muted = False
pre_mute_music_volume = 0.5
pre_mute_emergency_volume = 0.5
background_music_volume = 0.5
emergency_volume = 0.5 
settings_window = None
DEFAULT_TYPING_SPEED = 0.03

SETTING_FILE = os.path.join(script_directory, "settings.json")

# 2. Ultra-safe JSON loader that strips any old corrupted tuple data
def load_settings():
    global background_music_volume, emergency_volume, is_muted
    global pre_mute_emergency_volume, pre_mute_music_volume
    global text_speed

    if os.path.exists(SETTING_FILE):
        try:
            with open(SETTING_FILE, "r") as f:
                data = json.load(f)
                
                is_muted = data.get("is_muted", False)
                pre_mute_music_volume = float(data.get("pre_mute_music_volume", 0.5))
                pre_mute_emergency_volume = float(data.get("pre_mute_emergency_volume", 0.5))

                text_speed = data.get("text_speed", DEFAULT_TYPING_SPEED)

                # Extract music volume safely
                raw_music = data.get("background_music_volume", 0.5)
                if isinstance(raw_music, (list, tuple)):
                    background_music_volume = float(raw_music[0]) if raw_music else 0.5
                else:
                    background_music_volume = float(raw_music)
                
                # Extract emergency volume safely
                raw_emergency = data.get("emergency_volume", 0.5)
                if isinstance(raw_emergency, (list, tuple)):
                    emergency_volume = float(raw_emergency[0]) if raw_emergency else 0.5
                else:
                    emergency_volume = float(raw_emergency)
        except Exception:
            background_music_volume = 0.5
            emergency_volume = 0.5
            is_muted = False
            pre_mute_emergency_volume = 0.5
            pre_mute_music_volume = 0.5
            text_speed = DEFAULT_TYPING_SPEED
            
    else:
        background_music_volume = 0.5
        emergency_volume = 0.5
        is_muted = False
        pre_mute_emergency_volume = 0.5
        pre_mute_music_volume = 0.5
        text_speed = DEFAULT_TYPING_SPEED

    # Absolute guard rails: clamp volumes between 0.0 and 1.0
    background_music_volume = max(0.0, min(1.0, float(background_music_volume)))
    emergency_volume = max(0.0, min(1.0, float(emergency_volume)))
    pre_mute_music_volume = max(0.0, min(1.0, float(pre_mute_music_volume)))
    pre_mute_emergency_volume = max(0.0, min(1.0, float(pre_mute_emergency_volume)))

    # Text speed rail: prevent negative speeds or excessive delays
    text_speed = max(0.0, min(0.15, float(text_speed)))

def save_settings():
    try:
        data = {
            "background_music_volume": background_music_volume,
            "emergency_volume" : emergency_volume,
            "is muted" : is_muted,
            "pre_mute_music_volume": pre_mute_music_volume,
            "pre_mute_emergency_volume": pre_mute_emergency_volume,
            "text_speed": text_speed
        }
        with open(SETTING_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

# Initial settings load
load_settings()

# 3. Audio Engine Initialization
try:
    pygame.mixer.init()
    pygame.mixer.set_reserved(6) 
except Exception:
    pass

warning_sound = False
space_warning_sound = False

bg_music_file = os.path.join(script_directory, "Dream Sequence.mp3")
warning_file = os.path.join(script_directory, "Warning.mp3")
pull_up_file = os.path.join(script_directory, "Pull Up.mp3")
roger_that_file = os.path.join(script_directory, "Roger That.mp3")
space_warning_file = os.path.join(script_directory, "Spacecraft Warning.mp3")
click_file = os.path.join(script_directory, "Click.mp3")
mission_success_file = os.path.join(script_directory, "Mission Success.mp3")
mission_failed_file = os.path.join(script_directory, "Mission Failed.mp3")

# Start background music loop
try:
    pygame.mixer.music.load(bg_music_file)
    pygame.mixer.music.set_volume(background_music_volume)
    pygame.mixer.music.play(-1)
except Exception:
    pass

# 4. Volume Mixer 
def set_mixer_volumes():
    """Applies values directly to active Pygame channels."""
    try:
        pygame.mixer.music.set_volume(background_music_volume)
        pygame.mixer.Channel(1).set_volume(emergency_volume)
        pygame.mixer.Channel(2).set_volume(emergency_volume)
    except Exception:
        pass

def toggle_mute():
    global is_muted, background_music_volume, emergency_volume
    global pre_mute_music_volume, pre_mute_emergency_volume

    if not is_muted:
        pre_mute_music_volume = background_music_volume
        pre_mute_emergency_volume = emergency_volume
        background_music_volume = 0.0
        emergency_volume = 0.0
        is_muted = True
    else:
        background_music_volume = pre_mute_music_volume
        emergency_volume = pre_mute_emergency_volume
        is_muted = False

    set_mixer_volumes()
    save_settings()

def update_music_from_slider(percentage):
    global background_music_volume, is_muted
    background_music_volume = round(percentage, 2)
    pygame.mixer.music.set_volume(background_music_volume)
    
    if background_music_volume > 0 and is_muted:
        is_muted = False
    save_settings()

def update_emergency_from_slider(percentage):
    global emergency_volume, is_muted
    emergency_volume = round(percentage, 2)
    pygame.mixer.Channel(1).set_volume(emergency_volume)
    pygame.mixer.Channel(2).set_volume(emergency_volume)
    
    if emergency_volume > 0 and is_muted:
        is_muted = False
    save_settings()

def reset_all_settings():
    """Forces all configurations settings back to default"""
    global background_music_volume, emergency_volume, is_muted
    global pre_mute_emergency_volume, pre_mute_music_volume
    global text_speed

    # Reset all data
    background_music_volume = 0.5
    emergency_volume = 0.5
    is_muted = False
    pre_mute_emergency_volume = 0.5
    pre_mute_music_volume = 0.5
    text_speed = DEFAULT_TYPING_SPEED

    set_mixer_volumes()
    save_settings()

# --- 4. PYGAME CANVAS ENGINE WITH HIGH-VISIBILITY COLOR-FILL TRACKS (PART 1) ---
def open_settings_menu():
    global background_music_volume, emergency_volume, is_muted
    global text_speed  # <-- Added global variable tracking
    
    # Temporarily freeze all audio outputs while interacting with controls
    trigger_click_sound()
    
    # 1. Initialize Pygame display instance window context
    pygame.init()
    pygame.font.init()
    
    # EXPANDED HEIGHT: Changed from 390 to 470 to support the new Text Speed interface smoothly
    menu_w, menu_h = 320, 470
    menu_screen = pygame.display.set_mode((menu_w, menu_h))
    pygame.display.set_caption("Mission Audio & Text Systems")
    menu_clock = pygame.time.Clock()
    menu_font = pygame.font.SysFont("Courier", 14, bold=True)
    
    # Component Hitboxes (Tracks thickened from 10px to 14px for better visibility)
    music_track_rect = pygame.Rect(40, 80, 240, 14)
    emergency_track_rect = pygame.Rect(40, 160, 240, 14)
    text_track_rect = pygame.Rect(40, 240, 240, 14)  # <-- Added text speed slider track
    
    # Shifted checkboxes and buttons downwards due to text speed placement
    checkbox_rect = pygame.Rect(40, 290, 20, 20)
    reset_btn_rect = pygame.Rect(40, 335, 240, 35)
    confirm_yes_rect = pygame.Rect(40, 335, 110, 35)
    confirm_no_rect = pygame.Rect(170, 335, 110, 35)
    close_btn_rect = pygame.Rect(95, 400, 130, 35)
    
    # State tracking variables for explicit holding locks
    is_dragging_music = False
    is_dragging_emergency = False
    is_dragging_text = False  # <-- Added state tracker for text slider drag
    
    # Confirmation sub-menu processing flag
    show_reset_confirmation = False
    
    # FORCE WINDOW FOCUS
    pygame.event.set_grab(True)
    
    menu_running = True
    
    while menu_running:
        mouse_pos = pygame.mouse.get_pos()  # Returns a tuple (x, y)
        mouse_pressed = pygame.mouse.get_pressed()  # Returns tuple (left, middle, right)
        
        # 2. Monitor Mouse Click States
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Click Down
                    if close_btn_rect.collidepoint(event.pos):
                        menu_running = False
                    
                    # Lock sliders out entirely if user is interacting with prompt
                    if not show_reset_confirmation:
                        if checkbox_rect.collidepoint(event.pos):
                            toggle_mute()
                        elif reset_btn_rect.collidepoint(event.pos):
                            trigger_click_sound()
                            show_reset_confirmation = True
                        
                        # Track dragging activation cleanly
                        if music_track_rect.inflate(0, 20).collidepoint(event.pos):
                            is_dragging_music = True
                        elif emergency_track_rect.inflate(0, 20).collidepoint(event.pos):
                            is_dragging_emergency = True
                        elif text_track_rect.inflate(0, 20).collidepoint(event.pos):  # <-- Check text speed track click
                            is_dragging_text = True
                    else:
                        # Process Confirmation Sub-Menu Click Responses
                        if confirm_yes_rect.collidepoint(event.pos):
                            trigger_click_sound()
                            reset_all_settings()
                            show_reset_confirmation = False
                        elif confirm_no_rect.collidepoint(event.pos):
                            trigger_click_sound()
                            show_reset_confirmation = False
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Releasing Left Click breaks all locks
                    is_dragging_music = False
                    is_dragging_emergency = False
                    is_dragging_text = False
                    save_settings()  # Automatically save JSON configurations on release
                    
        # 3. Safety Backup Check: If the mouse button is not being pressed at all, kill drag states
        if not mouse_pressed[0] or show_reset_confirmation:
            is_dragging_music = False
            is_dragging_emergency = False
            is_dragging_text = False
        else:
            # Fallback Drag Catch: If they are pressing the mouse over a track and weren't dragging yet, let them slide it!
            if not is_dragging_music and not is_dragging_emergency and not is_dragging_text:
                if music_track_rect.inflate(0, 20).collidepoint(mouse_pos):
                    is_dragging_music = True
                elif emergency_track_rect.inflate(0, 20).collidepoint(mouse_pos):
                    is_dragging_emergency = True
                elif text_track_rect.inflate(0, 20).collidepoint(mouse_pos):  # <-- Fallback check
                    is_dragging_text = True
                    
        # 4. mouse_pos cleanly extracts the absolute horizontal X position integer
        if is_dragging_music:
            relative_x = max(0, min(mouse_pos[0] - music_track_rect.x, music_track_rect.width))
            update_music_from_slider(relative_x / music_track_rect.width)
        elif is_dragging_emergency:
            relative_x = max(0, min(mouse_pos[0] - emergency_track_rect.x, emergency_track_rect.width))
            update_emergency_from_slider(relative_x / emergency_track_rect.width)
        elif is_dragging_text:  # <-- Calculate text speed configuration mapping
            relative_x = max(0, min(mouse_pos[0] - text_track_rect.x, text_track_rect.width))
            percentage = relative_x / text_track_rect.width
            # Map percentages cleanly: 100% right means 0.0s delay (fastest); 0% left means 0.15s delay (slowest)
            text_speed = max(0.0, min(0.15, 0.15 * (1.0 - percentage)))
        
        # 5. Draw Layout Canvas (#1c1c1c Dark Theme)
        menu_screen.fill((28, 28, 28))
        
        # Calculate dynamic text percentages 
        music_pct = int(background_music_volume * 100)
        emergency_pct = int(emergency_volume * 100)
        
        # Invert the display calculation so 0.0s delay prints as "100% speed"
        text_speed_pct = int((1.0 - (text_speed / 0.15)) * 100)
        
        # Generate Text Strings with Percentages appended
        title_txt = menu_font.render("SYSTEM SETTINGS", True, (255, 255, 255))
        music_txt = menu_font.render(f"Background Music: {music_pct}%", True, (180, 180, 180))
        emergency_txt = menu_font.render(f"Sound Effects: {emergency_pct}%", True, (180, 180, 180))
        text_speed_txt = menu_font.render(f"Typewriting Speed: {text_speed_pct}%", True, (180, 180, 180)) # <-- Text speed label
        mute_txt = menu_font.render("Mute All Sounds", True, (255, 255, 255))
        close_txt = menu_font.render("Apply Changes", True, (255, 255, 255))
        
        menu_screen.blit(title_txt, (95, 15))
        menu_screen.blit(music_txt, (40, 55))
        menu_screen.blit(emergency_txt, (40, 135))
        menu_screen.blit(text_speed_txt, (40, 215))  # <-- Blit text speed string labels
        menu_screen.blit(mute_txt, (75, 290))
        
        # --- RENDER MUSIC SLIDER ---
        pygame.draw.rect(menu_screen, (45, 45, 45), music_track_rect, border_radius=4)
        h1_x = music_track_rect.x + int(background_music_volume * music_track_rect.width)
        
        music_color = (int(30 + (background_music_volume * 100)), int(80 + (background_music_volume * 175)), 40)
        if h1_x > music_track_rect.x:
            fill1_rect = pygame.Rect(music_track_rect.x, music_track_rect.y, h1_x - music_track_rect.x, music_track_rect.height)
            pygame.draw.rect(menu_screen, music_color, fill1_rect, border_radius=4)
        
        pygame.draw.circle(menu_screen, (20, 20, 20), (h1_x, music_track_rect.centery), 11)
        pygame.draw.circle(menu_screen, music_color, (h1_x, music_track_rect.centery), 9)
        
        # --- RENDER EMERGENCY SLIDER ---
        pygame.draw.rect(menu_screen, (45, 45, 45), emergency_track_rect, border_radius=4)
        h2_x = emergency_track_rect.x + int(emergency_volume * emergency_track_rect.width)
        
        emergency_color = (int(200 + (emergency_volume * 55)), int(160 - (emergency_volume * 140)), 20)
        if h2_x > emergency_track_rect.x:
            fill2_rect = pygame.Rect(emergency_track_rect.x, emergency_track_rect.y, h2_x - emergency_track_rect.x, emergency_track_rect.height)
            pygame.draw.rect(menu_screen, emergency_color, fill2_rect, border_radius=4)
            
        pygame.draw.circle(menu_screen, (20, 20, 20), (h2_x, emergency_track_rect.centery), 11)
        pygame.draw.circle(menu_screen, emergency_color, (h2_x, emergency_track_rect.centery), 9)
        
        # --- RENDER TEXT SPEED SLIDER ---
        pygame.draw.rect(menu_screen, (45, 45, 45), text_track_rect, border_radius=4)
        # Convert text speed back to tracking slider coordinate layout position
        current_speed_pct = 1.0 - (text_speed / 0.15)
        h3_x = text_track_rect.x + int(current_speed_pct * text_track_rect.width)
        
        text_speed_color = (40, int(100 + (current_speed_pct * 140)), int(180 + (current_speed_pct * 75)))
        if h3_x > text_track_rect.x:
            fill3_rect = pygame.Rect(text_track_rect.x, text_track_rect.y, h3_x - text_track_rect.x, text_track_rect.height)
            pygame.draw.rect(menu_screen, text_speed_color, fill3_rect, border_radius=4)
            
        pygame.draw.circle(menu_screen, (20, 20, 20), (h3_x, text_track_rect.centery), 11)
        pygame.draw.circle(menu_screen, text_speed_color, (h3_x, text_track_rect.centery), 9)
        
        # --- RENDER MUTE CHECKBOX ---
        pygame.draw.rect(menu_screen, (51, 51, 51), checkbox_rect, border_radius=4)
        if is_muted:
            pygame.draw.rect(menu_screen, (0, 255, 0), checkbox_rect.inflate(-8, -8), border_radius=2)
            
        # --- RENDER THE RESET CONFIGURATION INTERFACE ---
        if not show_reset_confirmation:
            # Main State: Draw standard clear button layout
            pygame.draw.rect(menu_screen, (70, 30, 30), reset_btn_rect, border_radius=5)
            reset_txt = menu_font.render("Reset All Settings", True, (240, 160, 160))
            menu_screen.blit(reset_txt, (reset_btn_rect.x + 45, reset_btn_rect.y + 10))
        else:
            # Confirmation State: Render split validation buttons
            pygame.draw.rect(menu_screen, (30, 60, 30), confirm_yes_rect, border_radius=5)
            pygame.draw.rect(menu_screen, (70, 30, 30), confirm_no_rect, border_radius=5)
            
            yes_txt = menu_font.render("CONFIRM", True, (160, 240, 160))
            no_txt = menu_font.render("CANCEL", True, (240, 160, 160))
            
            menu_screen.blit(yes_txt, (confirm_yes_rect.x + 28, confirm_yes_rect.y + 10))
            menu_screen.blit(no_txt, (confirm_no_rect.x + 32, confirm_no_rect.y + 10))
            
        # --- RENDER CLOSE PANEL ACTION BUTTON ---
        pygame.draw.rect(menu_screen, (50, 50, 50), close_btn_rect, border_radius=5)
        menu_screen.blit(close_txt, (close_btn_rect.x + 12, close_btn_rect.y + 10))
        
        pygame.display.flip()
        menu_clock.tick(60)
        
    # Free focus locks and quit layout window context safely
    pygame.event.set_grab(False)
    pygame.display.quit()

def trigger_warning_sound():
    global warning_sound, emergency_volume
    if not warning_sound:
        warning_sound = True
        try:
            ch = pygame.mixer.Channel(1)
            ch.set_volume(emergency_volume)
            sound_obj = pygame.mixer.Sound(warning_file)
            ch.play(sound_obj, loops=-1)
        except Exception:
            pass

def trigger_spacecraft_warning_sound():
    global space_warning_sound, emergency_volume
    if not space_warning_sound:
        space_warning_sound = True
        try:
            ch = pygame.mixer.Channel(2)
            ch.set_volume(emergency_volume)
            sound_obj = pygame.mixer.Sound(space_warning_file)
            ch.play(sound_obj, loops=-1)
        except Exception:
            pass

def trigger_roger_sound():
    try:
        ch = pygame.mixer.Channel(3)
        ch.set_volume(emergency_volume) 
        ch.play(pygame.mixer.Sound(roger_that_file))
    except Exception:
        pass

def trigger_pullup_sound():
    try:
        sound = pygame.mixer.Sound(pull_up_file)
        sound.set_volume(emergency_volume)
        sound.play()
    except Exception:
        pass

def trigger_click_sound():
    try:
        sound = pygame.mixer.Sound(click_file)
        sound.set_volume(emergency_volume)
        sound.play()
    except Exception:
        pass

def trigger_mission_success_sound():
    global emergency_volume
    try:
        ch = pygame.mixer.Channel(4)
        ch.set_volume(round(emergency_volume * 0.5, 2))
        ch.play(pygame.mixer.Sound(mission_success_file))
    except Exception:
        pass

def trigger_mission_failed_sound():
    global emergency_volume
    try:
        ch = pygame.mixer.Channel(5)
        ch.set_volume(round(emergency_volume * 0.5, 2))
        ch.play(pygame.mixer.Sound(mission_failed_file))
    except Exception:
        pass

# Stop all sound function
def stop_all_sounds():
    global space_warning_sound, warning_sound
    space_warning_sound = False
    warning_sound = False
    try:
        pygame.mixer.Channel(1).stop()
        pygame.mixer.Channel(2).stop()
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
try_again_counter = 1

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

# 1. Keep preferred game dimensions
window_width = 950
window_height = 720

# 2. Grab the actual resolution width/height of the user's current screen layout
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 3. Calculate the precise coordinates needed to perfectly center the canvas frame
center_x = int((screen_width / 2) - (window_width / 2))
center_y = int((screen_height / 2) - (window_height / 2))

# 4. Inject the calculated coordinate buffers back into your geometry assignment
root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
 
root.attributes ("-fullscreen", True)
root.update_idletasks()
root.configure(bg=BG_main)

#Exits the game if escape key is pressed
def force_exit_system(event):
    import pygame
    try:
        pygame.quit()
    except:
        pass
    os._exit(0)
root.bind("<Escape>", force_exit_system)

#Exits the game if exit is typed in order
typed_buffer = ""
def check_exit_sequence(event):
    import pygame
    global typed_buffer
        
    typed_buffer += event.char.lower()
           
    if len(typed_buffer) > 10:
        typed_buffer = typed_buffer[-4:]
            
    if typed_buffer.endswith("exit"):
        try: pygame.quit()
        except: pass
        os._exit(0)

root.bind("<Key>", check_exit_sequence)

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
def typewriter(text, text_widget, color=text_color, bold=False, override_speed=None):
    """Animates text into the GUI Text widget safely, checking if it exists first."""
    try:
        if not text_widget.winfo_exists():
            return
    except Exception:
        return

    text_widget.config(state=tk.NORMAL)
    tag_name = f"style_{time.time()}"
    font_style = ("Courier", 14, "bold" if bold else "normal")
    text_widget.tag_configure(tag_name, foreground=color, font=font_style)
    
    # Choose between the custom override speed or the global saved text_speed setting
    current_sleep_delay = override_speed if override_speed is not None else text_speed

    for letter in text:
        try:
            if not text_widget.winfo_exists():
                return
            text_widget.insert(tk.END, letter, tag_name)
            text_widget.see(tk.END)
            text_widget.update()
            
            # Apply the isolated sleep delay
            time.sleep(current_sleep_delay) 
            
        except Exception:
            return
        
    try:
        text_widget.insert(tk.END, "\n")
        text_widget.config(state=tk.DISABLED)
    except Exception:
        return

# Update progress bars function
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

# Making buttons interactive function
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

# First screen after you press try again
def game_restart_screen():
    """Wipes the boot console clean and initializes Chapter 1."""
    trigger_click_sound()
    cancel_all_timers() 
    log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 0)) 
    if not root.winfo_exists():
        return

    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    
    log_container.pack_forget()
    dashboard.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
    log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 0))
    update_gui()
    typewriter(f"This is Try No. {try_again_counter}", output_text, bold=True)
    typewriter("\nThe Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!", output_text)
    typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.", output_text)

    typewriter("\nSTAGE-1: T-MINUS COUNTDOWN", output_text, bold=True)
    typewriter("", output_text)
    typewriter("The Orion-X awaits launch", output_text)

    trigger_warning_sound()

    typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", output_text, color=color_red)
    typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', output_text, color=color_red)
    
    try:
        stage1_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.9)
    except Exception:
        return

# First loading screen when game is booted up   
def run_boot_sequence():
    """Plays the mainframe boot animation with a custom in-place updating console loading bar."""
    trigger_click_sound()
    cancel_all_timers() 
    welcome_frame.pack_forget()  
    log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 0)) 
    
    # Explicit override_speed ensures cinematic timings stay fully matched up
    active_timers.append(root.after(100, lambda: typewriter("CONNECTING TO NASA CENTRAL MAINFRAME...", output_text, color=color_cyan, override_speed=0.01)))
    active_timers.append(root.after(1800, lambda: typewriter("LOADING ORION-X CRITICAL TELEMETRY STACKS... [OK]", output_text, color=color_green, override_speed=0.01)))
    active_timers.append(root.after(4200, lambda: typewriter("ESTABLISHING ENCRYPTED LINK TO LAUNCH PAD... [OK]", output_text, color=color_green, override_speed=0.01)))
    
    # Initialize the Progress Bar header row
    active_timers.append(root.after(6800, lambda: typewriter("\nINITIALIZING MAIN OPERATIONS ARRAY...", output_text, color=color_yellow, bold=True, override_speed=0.01)))
    active_timers.append(root.after(8500, lambda: typewriter("PROGRESS: [███.....................] 15%", output_text, color=color_cyan, override_speed=0.01)))
    active_timers.append(root.after(10000, lambda: update_progress("PROGRESS: [█████████...............] 35%", output_text, color=color_cyan)))
    active_timers.append(root.after(11500, lambda: update_progress("PROGRESS: [██████████████..........] 55%", output_text, color=color_cyan)))
    active_timers.append(root.after(13000, lambda: update_progress("PROGRESS: [███████████████████.....] 75%", output_text, color=color_cyan)))
    
    # Final step finishes the bar, locks it to green, and pushes the cursor down with add_newline=True
    active_timers.append(root.after(14500, lambda: update_progress("PROGRESS: [████████████████████████] 100% [Loading Complete]", output_text, color=color_green, bold=True, add_newline=True)))
    
    # ONLY trigger the game start AFTER the full 17.5 second timeline expires
    active_timers.append(root.after(17500, trigger_game_start))

def trigger_game_start():
    """Wipes the boot console clean and initializes Chapter 1."""
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
        stage1_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.9)
    except Exception:
        return
    
def handle_choice1(choice):
    stop_all_sounds()
    trigger_click_sound()

    stage1_frame.place_forget()
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
        stage2a_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.9)

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
        stage2b_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.9)

def handle_choice2a(choice):
    stage2a_frame.place_forget()
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
    stage3a_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.9)

def handle_landing_choice_branch_2():
    typewriter("", output_text)
    typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", output_text, color="cyan")

    typewriter("\nSTAGE-4: MARS LANDING", output_text, bold=True)
    typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates", output_text)
    typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", output_text, color="red")
    stage3a_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.9)

def handle_choice3a(choice):
    stage3a_frame.place_forget()
    global crew_safety, mission_budget, science_points
        
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        landing_minigame_difficulty()
        if crew_safety == 100:
            crew_safety = 100
        else:
            crew_safety += 10

        science_points += 50
        update_gui()

    elif choice == "2":
        trigger_pullup_sound()
        typewriter("\nCRASH DOWN! The system clips a massive hidden boulder", output_text, color="red")
        typewriter("The lander tips and loses pressure. Space is not forgiving.", output_text, color="red")
        trigger_mission_failed_sound()
        typewriter("MISSION FAILED", output_text, bold=True, color="red")
        crew_safety = 0
        mission_budget = 0
        update_gui()

        end_game_session()

def handle_choice2b(choice):
    stage2b_frame.place_forget()
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
        stage3b_frame.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.9)

    elif choice == "2":
        typewriter("LOST ORBIT! The math is too complex with the light-lag delay", output_text, color="red")
        typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication", output_text, color="red")
        trigger_mission_failed_sound()
        crew_safety = 0
        mission_budget = 0
        update_gui()
        end_game_session()

def handle_choice3b(choice):
    stage3b_frame.place_forget()
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
        typewriter("\nBURN OUT! The extreme cold freezes the fuel valves during descent.", output_text, color="red")
        typewriter("The engines fail 100 meters up. The ship impacts the surface.", output_text, color="red")
        trigger_mission_failed_sound()
        typewriter("MISSION FAILED", output_text, color="red", bold=True)
        crew_safety = 0
        update_gui()
        end_game_session()

#===========================================================================
#LANDING MINI GAME (PYGAME EMBEDDED EDITION)
#===========================================================================

# Landing mini game physics engine
def run_physics_frame():
    global altitude, velocity_y, ship_angle, ship_x, ship_y, game_running, current_difficulty
    global prep_timer_frames
    global move_left_active, move_right_active
    global victory_altitude, pad_screen_y, pad_font, pad_text
    import pygame
    
    if not game_running:
        return
        
    f_w = game_frame.winfo_width()
    f_h = game_frame.winfo_height()
    
    screen_center_x = f_w // 2
    left_wall = screen_center_x - 175
    right_wall = screen_center_x + 175
    
    # As long as the button is down, these execute 60 times a second
    if move_left_active:
        ship_x -= 6  # Adjust this number to change slide speed
        ship_angle = min(25, ship_angle + 3)
    elif move_right_active:
        ship_x += 6  # Adjust this number to change slide speed
        ship_angle = max(-25, ship_angle - 3)
    else:
        # Stabilization dampening when keys are released
        ship_angle *= 0.85
    
    # Symmetrical edge guards to prevent sliding past the dark gray walls
    if ship_x - 25 < left_wall:  ship_x = left_wall + 25
    if ship_x + 25 > right_wall: ship_x = right_wall - 25
        
    # Adjust scrolling speed dynamically depending on active difficulty choice
    if prep_timer_frames > 0:
        altitude += 1.5
        prep_timer_frames -= 1
    else:
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
                
    #Landing Pad
    pad_screen_y = victory_altitude - int(altitude)
    if -100 < pad_screen_y < f_h +100:
        pygame.draw.rect(pg_screen, (0, 255, 100), (left_wall, pad_screen_y, 350, 30))

        pad_font = pygame.font.SysFont ("Courier", 16, bold= True)
        pad_text = pad_font.render("---TOUCHDOWN ZONE---", True, (0, 0, 0))
        pg_screen.blit(pad_text, (screen_center_x - (pad_text.get_width() // 2), pad_screen_y + 6))

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
    
    if prep_timer_frames > 0:
        seconds_left = (prep_timer_frames // 60) + 1
        count_font = pygame.font.SysFont("Courier", 48, bold=True)
        count_string = f"PREPARE: {seconds_left}"
        count_surface = count_font.render(count_string, True, (0, 240, 240))
        
        count_x = screen_center_x - (count_surface.get_width() // 2)
        count_y = (f_h // 2) - 150
        pg_screen.blit(count_surface, (count_x, count_y))

    # Collision Verification Engine 
    if ship_rect.bottom >= pad_screen_y and ship_rect.top < pad_screen_y + 30:
        # Ensure the player is actually centered over the green pad, not hitting side walls
        if left_wall <= ship_rect.centerx <= right_wall:
            game_running = False
            root.unbind("<KeyPress-Left>")
            root.unbind("<KeyRelease-Left>")
            root.unbind("<KeyPress-Right>")
            root.unbind("<KeyRelease-Right>")
            pygame.display.quit()
            game_frame.place_forget()
            landing_success()
            
            return

    crashed = False
    if ship_rect.left <= left_wall or ship_rect.right >= right_wall:
        crashed = True
    else:
        for obs in obstacles:
            screen_y = obs["y"] - int(altitude)
            calculated_height = int(obs["width"] * 0.3)
            
            if -150 < screen_y < f_h + 150:
                if obs["side"] == "LEFT":
                    spike_x = left_wall - 40
                    scaled_spike = pygame.transform.scale(spike_left, (obs["width"], calculated_height))
                    spike_mask = pygame.mask.from_surface(scaled_spike)
                else:
                    spike_x = right_wall + 40 - obs["width"]
                    scaled_spike = pygame.transform.scale(spike_right, (obs["width"], calculated_height))
                    spike_mask = pygame.mask.from_surface(scaled_spike)
                
                offset_x = spike_x - ship_rect.x
                offset_y = screen_y - ship_rect.y
                
                if ship_mask.overlap(spike_mask, (offset_x, offset_y)):
                    crashed = True
                    break

    # 4. Pipeline Refresh Execution
    pygame.display.flip()
    pg_clock.tick(60)
    
    if crashed:
        game_running = False
        # Clean up temporary bindings completely on game over
        root.unbind("<KeyPress-Left>")
        root.unbind("<KeyRelease-Left>")
        root.unbind("<KeyPress-Right>")
        root.unbind("<KeyRelease-Right>")
        pygame.display.quit()
        game_frame.place_forget() 
        space_ship_crash()        
    else:
        root.after(16, run_physics_frame)

# Landing minigame actual user interface
def start_landing_simulation_canvas():
    global game_frame, pg_screen, pg_clock, altitude, velocity_y, ship_angle, game_running
    global ship_x, ship_y, obstacles, ship_surface, ship_mask, spike_left, spike_right, current_difficulty
    global move_left_active, move_right_active, prep_timer_frames, victory_altitude
    import pygame
    import random
    
    # 1. Reset Physics Engine States
    altitude = 0.0
    velocity_y = 0.0
    ship_angle = 0.0
    game_running = True
    
    # Initialize movement trackers to false
    prep_timer_frames = 180
    move_left_active = False
    move_right_active = False
    
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
    
    # 4. Redirect the Pygame pipeline window hook safely across platforms
    try:
        os.environ['SDL_WINDOWID'] = str(game_frame.winfo_id()) 
        if os.name == 'nt':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        elif sys.platform == 'darwin':
            os.environ['SDL_VIDEODRIVER'] = 'cocoa'
        else:
            os.environ['SDL_VIDEODRIVER'] = 'x11'
    except Exception:
        pass
    
    # Initialize Pygame embedded sub-window frame
    pygame.init()
    pg_screen = pygame.display.set_mode((frame_w, frame_h))
    pg_clock = pygame.time.Clock()
        
    # 5. Load and scale 50x90px custom Spaceship design
    try:
        raw_ship = pygame.image.load("Spaceship.png").convert_alpha()
        ship_surface = pygame.transform.scale(raw_ship, (50, 90))
        ship_mask = pygame.mask.from_surface(ship_surface)
    except pygame.error:
        ship_surface = pygame.Surface((50, 90))
        ship_surface.fill((0, 240, 240)) 
        ship_mask = pygame.mask.from_surface(ship_surface)

    # 6. Load single native 200x60px Spike image ("Small Spike.png") & mirror it
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
        small_w = 140
        medium_w = 170
        large_w = 200
        gap_spacing = 180  
    elif current_difficulty == "MEDIUM":
        small_w = 170
        medium_w = 210
        large_w = 240
        gap_spacing = 180  
    else: # HARD MODE
        small_w = 220
        medium_w = 250
        large_w = 270  
        gap_spacing = 220  
    
    # Generate balanced obstacle arrays using a true randomized wall algorithm
    obstacles = []
    current_side = "LEFT"
    repeat_tracker = 0
    
    for i in range(30):
        obs_y = 1000 + (i * gap_spacing)
        chosen_side = random.choice(["LEFT", "RIGHT"])
        
        if chosen_side == current_side:
            repeat_tracker += 1
            if repeat_tracker >= 2:
                chosen_side = "RIGHT" if current_side == "LEFT" else "LEFT"
                repeat_tracker = 0
        else:
            repeat_tracker = 0

        final_spike_y = 900 + (29 * gap_spacing)
        global victory_altitude
        victory_altitude = final_spike_y + 1000
            
        current_side = chosen_side
        width = random.choice([small_w, medium_w, large_w])
        obstacles.append({"y": obs_y, "side": chosen_side, "width": width})
        
    def press_left(event):   global move_left_active;  move_left_active = True
    def release_left(event): global move_left_active;  move_left_active = False
    def press_right(event):  global move_right_active; move_right_active = True
    def release_right(event):global move_right_active; move_right_active = False

    # Bind both keyboard interactions directly
    root.bind("<KeyPress-Left>", press_left)
    root.bind("<KeyRelease-Left>", release_left)
    root.bind("<KeyPress-Right>", press_right)
    root.bind("<KeyRelease-Right>", release_right)
    
    root.focus_set()
    run_physics_frame()

# This is the fuction that controls the difficulty of the landing minigame
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
    global crew_safety, mission_budget
    trigger_mission_failed_sound()
    typewriter ("💥 CRASH: Space shuttle hull compromised!", output_text, color= "red")
    crew_safety = 0
    mission_budget = 0
    end_game_session()

#MISSON SUCCESS SCREEN
def landing_success():
    trigger_mission_success_sound()
    typewriter("HERIOC VICTORY!!!", output_text, color= "green")
    typewriter("You flew beatufully!! the crew and the ship are safe!!!", output_text, color= "green")
    end_game_session()

def end_game_session():
    typewriter(f"\nFinal Session Summary-> Crew Safety: {crew_safety}% | Budget: {mission_budget}% | Science Points: {science_points}", output_text, color=color_cyan)
    restart_frame.place(relx=0.5, rely=0.90, anchor="center")

# 1. Define your new specific restart sequence function
def run_restart_boot_sequence():
    """Launches specifically when retrying the mission, not the first boot."""
    print("Launching specialized restart sequence...")
    # Add your restart-specific logic here (e.g., skip intro cutscenes)
    # run_boot_sequence() # You can still call this inside if needed

# A fuction that activates when you press try again
def reboot_mission():
    global crew_safety, mission_budget, science_points, try_again_counter
    cancel_all_timers()
    restart_frame.place_forget()
    
    # Reset tracking state metrics
    crew_safety = 100
    mission_budget = 100
    science_points = 0
    try_again_counter += 1
    update_gui()
    
    try:
        dashboard.pack_forget()  
        log_container.pack_forget()
        
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.config(state=tk.DISABLED)
    except Exception:
        pass

    game_restart_screen()

# ==========================================
# POPULATE WIDGETS INTO THE FRAMES
# ==========================================

# --- 1. Welcome Screen elements ---
btn_start = tk.Button(welcome_frame, 
                        text="START GAME", 
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

# 2. Stage 1 Elements
tk.Label(stage1_frame, text="AWAITING STRATEGIC DIRECTIVE INSTRUCTIONS...", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold"), width=60).pack(pady=6)
b1_1 = tk.Button(stage1_frame, text="1) Launch Now - Push past high winds and save time", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice1("1"))
b1_1.pack(in_=stage1_frame, pady=4)
b1_2 = tk.Button(stage1_frame, text="2) Delay Launch - Abort current window and wait", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice1("2"))
b1_2.pack(in_=stage1_frame, pady=4)
make_button_interactive(b1_1); make_button_interactive(b1_2)

# 3. Stage 2A Elements
tk.Label(stage2a_frame, text="CRITICAL PRESSURE DROP DETECTED. CHOOSE ROUTE:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold"), width=60).pack(pady=6)
b2a_1 = tk.Button(stage2a_frame, text="1) PUSH ENGINES - Fire second stage anyway to clear orbit", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice2a("1"))
b2a_1.pack(in_=stage2a_frame, pady=4)
b2a_2 = tk.Button(stage2a_frame, text="2) ABORT MISSION - Activate the emergency escape tower", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice2a("2"))
b2a_2.pack(in_=stage2a_frame, pady=4)
make_button_interactive(b2a_1); make_button_interactive(b2a_2)

# 4. Stage 3A Elements
tk.Label(stage3a_frame, text="AUTOMATED LANDING FAILURE! CHOOSE FLIGHT CONTROLS:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold"), width=60).pack(pady=6)
b3a_1 = tk.Button(stage3a_frame, text="1) MANUAL CONTROL - Commander flies manual flight joystick", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice3a("1"))
b3a_1.pack(in_=stage3a_frame, pady=4)
b3a_2 = tk.Button(stage3a_frame, text="2) AUTO-PILOT - Trust flight computer mapping systems", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice3a("2"))
b3a_2.pack(in_=stage3a_frame, pady=4)
make_button_interactive(b3a_1); make_button_interactive(b3a_2)

# 5. Stage 2B (Lost in Space) Elements
tk.Label(stage2b_frame, text="STAGE-2: LOST IN SPACE // ARRAY REBOOT INTERFACE:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold"), width=60).pack(pady=6)
b2b_1 = tk.Button(stage2b_frame, text="1) UPLOAD A PATCH - Push an unverified software fix to reboot the system", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice2b("1"))
b2b_1.pack(in_=stage2b_frame, pady=4)
b2b_2 = tk.Button(stage2b_frame, text="2) MANUAL TRAJECTORY - Force crew to navigate manually using star maps", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice2b("2"))
b2b_2.pack(in_=stage2b_frame, pady=4)
make_button_interactive(b2b_1); make_button_interactive(b2b_2)

# 6. Stage 3B (Low Power Descent) Elements
tk.Label(stage3b_frame, text="STAGE-3: THE LANDING // ROUTE AVAILABLE BATTERY POWER:", bg=BG_main, fg=color_yellow, font=("Courier", 13, "bold"), width=60).pack(pady=6)
b3b_1 = tk.Button(stage3b_frame, text="1) DEPLOY SOLAR SAILS - Wait in orbit for 3 days to charge batteries", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice3b("1"))
b3b_1.pack(in_=stage3b_frame, pady=4)
b3b_2 = tk.Button(stage3b_frame, text="2) EMERGENCY BURN - Cut the life support heaters to power a descent", font=font_console, bg=BG_panel, fg=text_color, bd=0, padx=15, pady=8, highlightthickness=1, highlightbackground="#30363D", width=65, wraplength=550, justify="left", command=lambda: handle_choice3b("2"))
b3b_2.pack(in_=stage3b_frame, pady=4)
make_button_interactive(b3b_1); make_button_interactive(b3b_2)

# 7. Restart Elements
btn_restart = tk.Button(restart_frame, text="TRY AGAIN?", font=("Courier", 13, "bold"), bg=BG_panel, fg=color_cyan, bd=0, padx=25, pady=12, highlightthickness=1, highlightbackground="#30363D", width=25, command=reboot_mission)
btn_restart.pack(in_=restart_frame, pady=15)
btn_exit = tk.Button(restart_frame, text="EXIT?", font=("Courier", 13, "bold"), bg=BG_panel, fg=color_red, bd=0, padx=25, pady=12, highlightthickness=1, highlightbackground="#30363D", width=25, command=root.destroy)
btn_exit.pack(in_=restart_frame, pady=15)
make_button_interactive(btn_restart); make_button_interactive(btn_exit)

# Run structural sync data metrics counters
update_gui()

def on_close_window():
    """Intercepts clicking the 'X' button to kill background timer threads instantly."""
    stop_all_sounds()
    cancel_all_timers()
    root.destroy()

# --- 6. PERMANENT INTERACTION SHORTCUT (Bottom Left Corner) ---
settings_btn = tk.Button(
    root, 
    text="⚙️ Settings", 
    command=open_settings_menu,    # When pressed, spins up our standalone Pygame dashboard sub-window
    font=("Courier", 11, "bold"), 
    bg="#161b22",                 
    fg="#7EE787",                 
    activebackground="#30363D", 
    activeforeground="#7EE787",
    bd=1,
    relief="solid",
    highlightthickness=0
)
settings_btn.place(relx=0.0, rely=1.0, x=15, y=-15, anchor="sw")
settings_btn.lift()


# Tell Tkinter to run our cleanup function when the window closes
root.protocol("WM_DELETE_WINDOW", on_close_window)

root.mainloop()
