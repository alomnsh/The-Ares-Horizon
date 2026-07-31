#Importing packages
import os
import time
import sys
import math
import random
import pygame
import json
import asyncio

current_stage = "welcome"
current_difficulty = "EASY"  
is_boot_completed = False
key_states = {}
terminal_logs = []
text_speed = 0.045 
is_minigame_unlocked = False

if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"

# If key is pressed it is true, if it is released it is false
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
pre_mute_emergency_volume = 0.25
background_music_volume = 0.5
emergency_volume = 0.25 
settings_window = None
DEFAULT_TYPING_SPEED = 0.045

SETTING_FILE = os.path.join(script_directory, "settings.json")

# 2. Ultra-safe JSON loader that strips any old corrupted tuple data
def load_settings():
    global background_music_volume, emergency_volume, is_muted
    global pre_mute_emergency_volume, pre_mute_music_volume
    global text_speed, is_minigame_unlocked

    if os.path.exists(SETTING_FILE):
        try:
            with open(SETTING_FILE, "r") as f:
                data = json.load(f)
                
                is_muted = data.get("is_muted", False)
                pre_mute_music_volume = float(data.get("pre_mute_music_volume", 0.5))
                pre_mute_emergency_volume = float(data.get("pre_mute_emergency_volume", 0.5))

                text_speed = data.get("text_speed", DEFAULT_TYPING_SPEED)

                is_minigame_unlocked = bool(data.get("is_minigame_unlocked", False))

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
            emergency_volume = 0.25
            is_muted = False
            pre_mute_emergency_volume = 0.25
            pre_mute_music_volume = 0.5
            text_speed = DEFAULT_TYPING_SPEED
            is_minigame_unlocked = False
            
    else:
        background_music_volume = 0.5
        emergency_volume = 0.25
        is_muted = False
        pre_mute_emergency_volume = 0.25
        pre_mute_music_volume = 0.5
        text_speed = DEFAULT_TYPING_SPEED
        is_minigame_unlocked = False

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
            "is_muted" : is_muted,
            "pre_mute_music_volume": pre_mute_music_volume,
            "pre_mute_emergency_volume": pre_mute_emergency_volume,
            "text_speed": text_speed,
            "is_minigame_unlocked": is_minigame_unlocked
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

bg_music_file = os.path.join(script_directory, "Dream Sequence.ogg")
warning_file = os.path.join(script_directory, "Warning.ogg")
pull_up_file = os.path.join(script_directory, "Pull Up.ogg")
roger_that_file = os.path.join(script_directory, "Roger That.ogg")
space_warning_file = os.path.join(script_directory, "Spacecraft Warning.ogg")
click_file = os.path.join(script_directory, "Click.ogg")
mission_success_file = os.path.join(script_directory, "Mission Success.ogg")
mission_failed_file = os.path.join(script_directory, "Mission Failed.ogg")

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
    global text_speed, is_minigame_unlocked

    # Reset all data
    background_music_volume = 0.5
    emergency_volume = 0.25
    is_muted = False
    pre_mute_emergency_volume = 0.25
    pre_mute_music_volume = 0.5
    text_speed = DEFAULT_TYPING_SPEED
    is_minigame_unlocked = False

    set_mixer_volumes()
    save_settings()

async def open_settings_menu(main_screen):
    """Renders a centered settings modal dialog box directly onto the main game canvas."""
    global background_music_volume, emergency_volume, is_muted
    global text_speed
    
    # Temporarily freeze all audio outputs while interacting with controls
    trigger_click_sound()
    
    # Track the main window's dynamic width and height for perfect center positioning
    base_w = main_screen.get_width()
    base_h = main_screen.get_height()
    
    menu_w, menu_h = 320, 470
    menu_x = (base_w - menu_w) // 2
    menu_y = (base_h - menu_h) // 2
    
    menu_clock = pygame.time.Clock()
    menu_font = pygame.font.SysFont("OCR A Extended", 14, bold=True)

    # Component Hitboxes
    music_track_rect = pygame.Rect(menu_x + 40, menu_y + 80, 240, 14)
    emergency_track_rect = pygame.Rect(menu_x + 40, menu_y + 160, 240, 14)
    text_track_rect = pygame.Rect(menu_x + 40, menu_y + 240, 240, 14) 
    
    checkbox_rect = pygame.Rect(menu_x + 40, menu_y + 290, 20, 20)
    reset_btn_rect = pygame.Rect(menu_x + 40, menu_y + 335, 240, 35)
    confirm_yes_rect = pygame.Rect(menu_x + 40, menu_y + 335, 110, 35)
    confirm_no_rect = pygame.Rect(menu_x + 170, menu_y + 335, 110, 35)
    close_btn_rect = pygame.Rect(menu_x + 95, menu_y + 400, 130, 35)
    
    # State tracking variables for explicit holding locks
    is_dragging_music = False
    is_dragging_emergency = False
    is_dragging_text = False
    
    # Confirmation sub-menu processing flag
    show_reset_confirmation = False
    
    menu_running = True

    while menu_running:
        mouse_pos = pygame.mouse.get_pos()  
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Monitor Mouse Click States
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  
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
                        elif text_track_rect.inflate(0, 20).collidepoint(event.pos):
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
                if event.button == 1:  
                    is_dragging_music = False
                    is_dragging_emergency = False
                    is_dragging_text = False
                    save_settings()

        # Safety Backup Check: If the mouse button is not being pressed at all, kill drag states
        if not mouse_pressed[0] or show_reset_confirmation:
            is_dragging_music = False
            is_dragging_emergency = False
            is_dragging_text = False
        else:
            # Fallback Drag Catch: If they are pressing the mouse over a track and weren't dragging yet, let them slide it
            if not is_dragging_music and not is_dragging_emergency and not is_dragging_text:
                if music_track_rect.inflate(0, 20).collidepoint(mouse_pos):
                    is_dragging_music = True
                elif emergency_track_rect.inflate(0, 20).collidepoint(mouse_pos):
                    is_dragging_emergency = True
                elif text_track_rect.inflate(0, 20).collidepoint(mouse_pos):
                    is_dragging_text = True
                    
        if is_dragging_music:
            relative_x = max(0, min(mouse_pos[0] - music_track_rect.x, music_track_rect.width))
            update_music_from_slider(relative_x / music_track_rect.width)
        elif is_dragging_emergency:
            relative_x = max(0, min(mouse_pos[0] - emergency_track_rect.x, emergency_track_rect.width))
            update_emergency_from_slider(relative_x / emergency_track_rect.width)
        elif is_dragging_text: 
            relative_x = max(0, min(mouse_pos[0] - text_track_rect.x, text_track_rect.width))
            percentage = relative_x / text_track_rect.width
            text_speed = max(0.0, 0.15 * (1.0 - percentage))


        # Draw Layout Canvas Frame Window Card Container
        menu_bg_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        pygame.draw.rect(main_screen, (28, 28, 28), menu_bg_rect, border_radius=8)
        pygame.draw.rect(main_screen, (48, 54, 61), menu_bg_rect, width=2, border_radius=8)
        
        # Calculate dynamic text percentages 
        music_pct = int(background_music_volume * 100)
        emergency_pct = int(emergency_volume * 100)
        
        # Invert the display calculation so 0.0s delay prints as "100% speed"
        text_speed_pct = int((1.0 - (text_speed / 0.15)) * 100)
        
        # Generate Text Strings with Percentages appended
        title_txt = menu_font.render("SYSTEM SETTINGS", True, (255, 255, 255))
        music_txt = menu_font.render(f"Background Music: {music_pct}%", True, (180, 180, 180))
        emergency_txt = menu_font.render(f"Sound Effects: {emergency_pct}%", True, (180, 180, 180))
        text_speed_txt = menu_font.render(f"Typewriting Speed: {text_speed_pct}%", True, (180, 180, 180))
        mute_txt = menu_font.render("Mute All Sounds", True, (255, 255, 255))
        close_txt = menu_font.render("Apply Changes", True, (255, 255, 255))
        
        main_screen.blit(title_txt, (menu_x + 95, menu_y + 15))
        main_screen.blit(music_txt, (menu_x + 40, menu_y + 55))
        main_screen.blit(emergency_txt, (menu_x + 40, menu_y + 135))
        main_screen.blit(text_speed_txt, (menu_x + 40, menu_y + 215))
        main_screen.blit(mute_txt, (menu_x + 75, menu_y + 290))

        # --- RENDER MUSIC SLIDER ---
        pygame.draw.rect(main_screen, (45, 45, 45), music_track_rect, border_radius=4)
        h1_x = music_track_rect.x + int(background_music_volume * music_track_rect.width)
        
        music_color = (int(30 + (background_music_volume * 100)), int(80 + (background_music_volume * 175)), 40)
        if h1_x > music_track_rect.x:
            fill1_rect = pygame.Rect(music_track_rect.x, music_track_rect.y, h1_x - music_track_rect.x, music_track_rect.height)
            pygame.draw.rect(main_screen, music_color, fill1_rect, border_radius=4)
        
        pygame.draw.circle(main_screen, (20, 20, 20), (h1_x, music_track_rect.centery), 11)
        pygame.draw.circle(main_screen, music_color, (h1_x, music_track_rect.centery), 9)
        
        # --- RENDER EMERGENCY SLIDER ---
        pygame.draw.rect(main_screen, (45, 45, 45), emergency_track_rect, border_radius=4)
        h2_x = emergency_track_rect.x + int(emergency_volume * emergency_track_rect.width)
        
        emergency_color = (int(200 + (emergency_volume * 55)), int(160 - (emergency_volume * 140)), 20)
        if h2_x > emergency_track_rect.x:
            fill2_rect = pygame.Rect(emergency_track_rect.x, emergency_track_rect.y, h2_x - emergency_track_rect.x, emergency_track_rect.height)
            pygame.draw.rect(main_screen, emergency_color, fill2_rect, border_radius=4)
            
        pygame.draw.circle(main_screen, (20, 20, 20), (h2_x, emergency_track_rect.centery), 11)
        pygame.draw.circle(main_screen, emergency_color, (h2_x, emergency_track_rect.centery), 9)
        
        # --- RENDER TEXT SPEED SLIDER ---
        pygame.draw.rect(main_screen, (45, 45, 45), text_track_rect, border_radius=4)
        current_speed_pct = 1.0 - (text_speed / 0.15)
        h3_x = text_track_rect.x + int(current_speed_pct * text_track_rect.width)
        
        text_speed_color = (40, int(100 + (current_speed_pct * 140)), int(180 + (current_speed_pct * 75)))
        if h3_x > text_track_rect.x:
            fill3_rect = pygame.Rect(text_track_rect.x, text_track_rect.y, h3_x - text_track_rect.x, text_track_rect.height)
            pygame.draw.rect(main_screen, text_speed_color, fill3_rect, border_radius=4)
            
        pygame.draw.circle(main_screen, (20, 20, 20), (h3_x, text_track_rect.centery), 11)
        pygame.draw.circle(main_screen, text_speed_color, (h3_x, text_track_rect.centery), 9)
        
        # --- RENDER MUTE CHECKBOX ---
        pygame.draw.rect(main_screen, (51, 51, 51), checkbox_rect, border_radius=4)
        if is_muted:
            pygame.draw.rect(main_screen, (0, 255, 0), checkbox_rect.inflate(-8, -8), border_radius=2)
            
        # --- RENDER THE RESET CONFIGURATION INTERFACE ---
        if not show_reset_confirmation:
            pygame.draw.rect(main_screen, (70, 30, 30), reset_btn_rect, border_radius=5)
            reset_txt = menu_font.render("Reset All Settings", True, (240, 160, 160))
            main_screen.blit(reset_txt, (reset_btn_rect.x + 45, reset_btn_rect.y + 10))
        else:
            pygame.draw.rect(main_screen, (30, 60, 30), confirm_yes_rect, border_radius=5)
            pygame.draw.rect(main_screen, (70, 30, 30), confirm_no_rect, border_radius=5)
            
            yes_txt = menu_font.render("CONFIRM", True, (160, 240, 160))
            no_txt = menu_font.render("CANCEL", True, (240, 160, 160))
            
            main_screen.blit(yes_txt, (confirm_yes_rect.x + 28, confirm_yes_rect.y + 10))
            main_screen.blit(no_txt, (confirm_no_rect.x + 32, confirm_no_rect.y + 10))
            
        # --- RENDER CLOSE PANEL ACTION BUTTON ---
        pygame.draw.rect(main_screen, (50, 50, 50), close_btn_rect, border_radius=5)
        main_screen.blit(close_txt, (close_btn_rect.x + 12, close_btn_rect.y + 10))
        
        pygame.display.flip()
        menu_clock.tick(60)
        
        # Yield control back to browser compilation system layout safely
        await asyncio.sleep(0)

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
BG_MAIN = (11, 14, 20)
BG_PANEL = (22, 27, 34)      
TEXT_COLOR = (230, 237, 243)  
COLOR_CYAN = (88, 166, 255)   
COLOR_YELLOW = (242, 204, 96) 
COLOR_RED = (219, 43, 31)     
COLOR_GREEN = (126, 231, 135) 


#Game Stats and Point
gamestart="yes"
crew_safety = 100
mission_budget = 100
science_points = 0
try_again_counter = 1

active_timers = []

pygame.font.init()
pygame.init()

screen_info = pygame.display.Info()

# 2. Launch directly into the monitor's native hardware resolution
WINDOW_WIDTH = screen_info.current_w
WINDOW_HEIGHT = screen_info.current_h

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("The Ares Horizon — Mission Control Terminal")

is_fullscreen = True

clock = pygame.time.Clock()

ui_font = pygame.font.SysFont("OCR A Extended", 16, bold = True)

font_console = pygame.font.SysFont("Tw Cen MT", 22, bold=False)

close_btn_rect = pygame.Rect(820, 15, 115, 30)

def draw_close_button(surface, mouse_pos):
    """Renders the close button dynamically pinned to the top right corner."""

    current_w = surface.get_width()
    
    close_btn_rect = pygame.Rect(current_w - 130, 15, 115, 30)
    
    if close_btn_rect.collidepoint(mouse_pos):
        button_color = (170, 40, 30)
        TEXT_COLOR = (255, 255, 255)
    else:
        button_color = (70, 30, 30)
        TEXT_COLOR = (240, 160, 160)
        
    pygame.draw.rect(surface, button_color, close_btn_rect, border_radius=5)
    
    close_text = ui_font.render("CLOSE GAME", True, TEXT_COLOR)
    text_x = close_btn_rect.x + (close_btn_rect.width - close_text.get_width()) // 2
    text_y = close_btn_rect.y + (close_btn_rect.height - close_text.get_height()) // 2
    surface.blit(close_text, (text_x, text_y))
    
    return close_btn_rect

# Global styles setup for progress bars
def draw_telemetry_dashboard(surface):
    global crew_safety, mission_budget, science_points
    
    current_w = surface.get_width()
    
    # 1. Draw the Dashboard Panel Frame Container
    panel_rect = pygame.Rect(0, 0, current_w, 60)
    pygame.draw.rect(surface, BG_PANEL, panel_rect)
    pygame.draw.rect(surface, (48, 54, 61), panel_rect, width=1)

    # 2. Layout Positioning Math (Responsive distribution)
    col1_center = current_w * 0.18
    col2_center = current_w * 0.45
    col3_center = current_w * 0.75
    
    bar_width = 180
    bar_height = 12
    
    # ----------------------------------------------------
    # DRAW CREW SAFETY ELEMENT
    # ----------------------------------------------------
    safety_label = ui_font.render("CREW SAFETY STATUS:", True, TEXT_COLOR)
    surface.blit(safety_label, (col1_center - safety_label.get_width() - 10, 23))
    
    # Safety Progress Bar Background Track
    safety_track = pygame.Rect(col1_center, 24, bar_width, bar_height)
    pygame.draw.rect(surface, (11, 14, 20), safety_track, border_radius=4)
    
    # Dynamic Safety Bar Color Shift
    current_safety_color = COLOR_RED if crew_safety <= 40 else COLOR_CYAN
    
    # Draw Fill
    if crew_safety > 0:
        fill_width = int(bar_width * (max(0, min(100, crew_safety)) / 100.0))
        safety_fill = pygame.Rect(col1_center, 24, fill_width, bar_height)
        pygame.draw.rect(surface, current_safety_color, safety_fill, border_radius=4)

    # ----------------------------------------------------
    # DRAW MISSION BUDGET ELEMENT
    # ----------------------------------------------------
    budget_label = ui_font.render("MISSION BUDGET:", True, TEXT_COLOR)
 
    # 1. Get the total combined width of the text + 10px gap + the bar
    total_budget_width = budget_label.get_width() + 10 + bar_width
 
    # 2. Find the starting X position that puts the whole group dead center
    budget_start_x = (current_w - total_budget_width) // 2
 
    # 3. Draw the text label
    surface.blit(budget_label, (budget_start_x, 23))
 
    # 4. Place the bar right after the text label and the gap
    budget_bar_x = budget_start_x + budget_label.get_width() + 10
 
    # Budget Progress Bar Background Track
    budget_track = pygame.Rect(budget_bar_x, 24, bar_width, bar_height)
    pygame.draw.rect(surface, (11, 14, 20), budget_track, border_radius=4)
 
    # Draw Fill
    if mission_budget > 0:
        fill_width = int(bar_width * (max(0, min(100, mission_budget)) / 100.0))
    budget_fill = pygame.Rect(budget_bar_x, 24, fill_width, bar_height)
    pygame.draw.rect(surface, COLOR_YELLOW, budget_fill, border_radius=4)


    # ----------------------------------------------------
    # DRAW SCIENCE POINTS TEXT ELEMENT
    # ----------------------------------------------------
    points_str = f"SCIENCE POINTS: {science_points}"
    points_label = ui_font.render(points_str, True, COLOR_GREEN)
    surface.blit(points_label, (col3_center, 23))

def draw_settings_button(surface, mouse_pos):
    current_h = surface.get_height()
    
    settings_btn_rect = pygame.Rect(15, current_h - 45, 115, 30)
    
    # Handle hovering states (activebackground equivalent)
    if settings_btn_rect.collidepoint(mouse_pos):
        button_color = (48, 54, 61)   # Original activebackground #30363D
    else:
        button_color = (22, 27, 34)   # Original bg #161b22
        
    # Draw button background card frame with thin border (bd=1, relief="solid")
    pygame.draw.rect(surface, button_color, settings_btn_rect, border_radius=4)
    pygame.draw.rect(surface, (48, 54, 61), settings_btn_rect, width=1, border_radius=4)
    
    # Render original emoji label layout text (#7EE787 text color)
    settings_text = ui_font.render("SETTINGS", True, (126, 231, 135))
    text_x = settings_btn_rect.x + (settings_btn_rect.width - settings_text.get_width()) // 2
    text_y = settings_btn_rect.y + (settings_btn_rect.height - settings_text.get_height()) // 2
    surface.blit(settings_text, (text_x, text_y))
    
    return settings_btn_rect

async def typewriter(text, color=(126, 231, 135), override_speed=None, bold=False):
    """Animates text into the terminal log list while responding instantly to text_speed changes."""
    global terminal_logs, text_speed, screen, clock
    
    current_sleep_delay = override_speed if override_speed is not None else text_speed
    
    # Append an entry holding a blank text canvas paired with color target
    terminal_logs.append(["", color])
    line_index = len(terminal_logs) - 1
    
    max_chars_per_line = 300
    current_line_text = ""
    char_counter = 0
    
    for letter in text:
        try:
            # Handle dynamic word wrapping
            if len(current_line_text) >= max_chars_per_line and letter == " ":
                terminal_logs[line_index][0] = current_line_text.strip()
                terminal_logs.append(["", color])
                line_index = len(terminal_logs) - 1
                current_line_text = ""
                continue
            
            current_line_text += letter + "\u200a"
            terminal_logs[line_index][0] = current_line_text
            char_counter += 1

            if current_sleep_delay < 0.016:
                if char_counter % 3 == 0:
                    await asyncio.sleep(0)
            else:
                await asyncio.sleep(current_sleep_delay)
                
        except Exception:
            return
            
    terminal_logs[line_index][0] = current_line_text.strip()

def update_progress(text, add_newline=False, color=(88, 166, 255)):
    """Updates the terminal log in place, preserving colors."""
    global terminal_logs
    
    if not terminal_logs:
        terminal_logs.append(["", color])
        
    # Overwrite text and preserve color tuple
    terminal_logs[-1] = [text, color]
    
    if add_newline:
        terminal_logs.append(["", color])

async def game_restart_screen():
    """Wipes the boot console clean and launches the initial narrative story text intro sequence."""
    global try_again_counter, current_stage, terminal_logs, is_boot_completed
    
    trigger_click_sound()

    is_boot_completed = True
    
    # 1. Clear the terminal log array completely to prepare a fresh, blank canvas
    terminal_logs.clear()
    
    # 2. Assign the state machine to "boot_sequence" so the terminal log box renders on screen
    current_stage = "boot_sequence"
    
    # 3. Print narrative flow tracking logs chronologically using async typewriter
    await typewriter(f"This is Try No. {try_again_counter}", color=(230, 237, 243))
    
    await typewriter("\nThe Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!", color=(230, 237, 243))
    await typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.", color=(230, 237, 243))
    
    await typewriter("\nSTAGE-1: T-MINUS COUNTDOWN", color=(242, 204, 96))
    await typewriter("", color=(230, 237, 243))
    await typewriter("The Orion-X awaits launch", color=(230, 237, 243))
    
    trigger_warning_sound()
    
    await typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", color=(219, 43, 31)) # Alert Red color
    await typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', color=(219, 43, 31))
    
    # 4. SWAP STATE TO NARRATIVE MODE: Once all text animations complete, show the Stage 1 choice buttons
    current_stage = "stage1"

async def run_boot_sequence():
    """Plays the mainframe boot animation sequentially using clean async sleep pauses."""
    trigger_click_sound()
    # 1. Chronological Timeline Executions (Replacing root.after delay rules)
    await typewriter("CONNECTING TO NASA CENTRAL MAINFRAME...", color=COLOR_CYAN, override_speed=0.01)
    await asyncio.sleep(1.7) # Delays next line until 1800ms mark from boot startup
    
    await typewriter("LOADING ORION-X CRITICAL TELEMETRY STACKS... [OK]", color=COLOR_GREEN, override_speed=0.01)
    await asyncio.sleep(2.3) # Reaches the 4200ms mark chronologically
    
    await typewriter("ESTABLISHING ENCRYPTED LINK TO LAUNCH PAD... [OK]", color=COLOR_GREEN, override_speed=0.01)
    await asyncio.sleep(2.5) # Reaches the 6800ms mark chronologically
    
    # 2. Initialize the Progress Bar header row
    await typewriter("\nINITIALIZING MAIN OPERATIONS ARRAY...", color=COLOR_YELLOW, override_speed=0.01)
    await asyncio.sleep(1.6) # Reaches the 8500ms mark chronologically
    
    # 3. Animate loading updates inside the terminal window log tracking arrays
    await typewriter("PROGRESS: [███.....................] 15%", color=COLOR_CYAN, override_speed=0.01)
    await asyncio.sleep(1.4) # Reaches the 10000ms mark chronologically
    
    update_progress("PROGRESS: [█████████...............] 35%")
    await asyncio.sleep(1.4) # Reaches the 11500ms mark chronologically
    
    update_progress("PROGRESS: [██████████████..........] 55%")
    await asyncio.sleep(1.4) # Reaches the 13000ms mark chronologically
    
    update_progress("PROGRESS: [███████████████████.....] 75%")
    await asyncio.sleep(1.4) # Reaches the 14500ms mark chronologically
    
    update_progress("PROGRESS: [████████████████████████] 100% [Loading Complete]", add_newline=True)
    await asyncio.sleep(2.9) # Reaches the 17500ms full boot sequence timeline constraint
    
    # 4. Safely advance to main operations gameplay setup
    await trigger_game_start()

async def trigger_game_start():
    """Wipes the boot console clean and initializes Chapter 1 narrative introduction sequence."""
    global current_stage, terminal_logs, is_boot_completed

    is_boot_completed = True
    
    # 1. Clear the terminal logs array completely to prepare a fresh, blank canvas
    terminal_logs.clear()
    
    # 2. Assign the state tracker to "boot_sequence" so the terminal log box renders on screen
    current_stage = "boot_sequence"

    # 3. Print narrative flow logs chronologically using async typewriter
    await typewriter("Welcome to The Ares Horizon Game!", color=(230, 237, 243))
    await typewriter("In this game you are a Flight Director at NASA Mission Control!", color=(230, 237, 243))
    await typewriter("The Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!", color=(230, 237, 243))
    await typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.", color=(230, 237, 243))

    await typewriter("\nSTAGE-1: T-MINUS COUNTDOWN", color=(242, 204, 96)) 
    await typewriter("", color=(230, 237, 243))
    await typewriter("The Orion-X awaits launch", color=(230, 237, 243))

    trigger_warning_sound()

    await typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", color=(219, 43, 31))
    await typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', color=(219, 43, 31))
    
    # 4. SWAP STATE TO NARRATIVE MODE: Once all text animations finish, instantly show Stage 1 choice buttons
    current_stage = "stage1"

async def handle_choice1(choice):
    """Processes choice inputs for Stage 1, applying penalties and animating dynamic story outcomes."""
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs
    
    stop_all_sounds()
    trigger_click_sound()

    # 1. Clear the terminal log array completely to prepare a fresh narrative backdrop canvas
    terminal_logs.clear()
    
    # 2. Assign state to "boot_sequence" so the terminal draws text while typing
    current_stage = "boot_sequence"

    # ==========================================
    # NARRATIVE PATHWAY 1: PUSH PAST THE WINDS
    # ==========================================
    if choice == "1":
        await typewriter("\nIGNITION! The rocket vibrates violently as it punches through the wind", color=(230, 237, 243))
        await typewriter("Minutes later you reach the edge of the atmosphere and enter orbit, but the stress caused by the wind resulted in an issue", color=(230, 237, 243))

        # Risk penalties: Deduct stats from global tracking metrics pools
        crew_safety -= 20
        mission_budget -= 10

        # --- CRITICAL SAFETY / BUDGET SYSTEM GUARD RAIL ---
        if crew_safety <= 0 or mission_budget <= 0:
            crew_safety = max(0, crew_safety)
            mission_budget = max(0, mission_budget)
            await typewriter("\nCRITICAL FAILURE: Mission parameters compromised! The system cannot continue.", color=(219, 43, 31), bold=True)
            trigger_mission_failed_sound()
            await end_game_session()
            return

        # Display Live Metric Indicators
        await typewriter("", color=(230, 237, 243))
        await typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color=(88, 166, 255)) 

        # Transition cleanly into the Stage 2A plot fork setup
        await typewriter("\nSTAGE-2: THE ORBITAL ANOMALY", color=(242, 204, 96), bold=True)
        trigger_spacecraft_warning_sound()
        await typewriter("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!", color=(219, 43, 31))
        
        # 3a. SWAP STATE TO SHOW STAGE 2A BUTTONS: Once text finishes animating
        current_stage = "stage2a"

    # ==========================================
    # NARRATIVE PATHWAY 2: DELAY THE LAUNCH
    # ==========================================
    elif choice == "2":
        await typewriter("\nYou stand down on the launch. The crew exits the spacecraft", color=(230, 237, 243))
        await typewriter("Weeks later, you launch on a much longer and not as ideal route", color=(230, 237, 243))

        # Security safety safeguards cash balances but burns timeline resource windows
        mission_budget -= 40
        
        # --- CRITICAL BUDGET SYSTEM GUARD RAIL ---
        if crew_safety <= 0 or mission_budget <= 0:
            crew_safety = max(0, crew_safety)
            mission_budget = max(0, mission_budget)
            await typewriter("\nFINANCIAL BANKRUPTCY: Mission defunded by headquarters!", color=(219, 43, 31), bold=True)
            trigger_mission_failed_sound()
            await end_game_session()
            return

        # Display Live Metric Indicators
        await typewriter("", color=(230, 237, 243))
        await typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color=(88, 166, 255))

        # Transition cleanly into the Stage 2B plot fork setup
        await typewriter("\nSTAGE-2: LOST IN SPACE", color=(242, 204, 96), bold=True)
        trigger_warning_sound()
        await typewriter("Deep in space, a massive radiation storm knocks down your primary navigation computer", color=(219, 43, 31))
        await typewriter("\nMark scrambles: Director, the main computer is dead, we are drifting!", color=(219, 43, 31))
        
        # 3b. SWAP STATE TO SHOW STAGE 2B BUTTONS: Once text finishes animating
        current_stage = "stage2b"

async def handle_choice2a(choice):
    """Processes narrative choice inputs for Stage 2A with immediate safety failure checks."""
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs
    
    stop_all_sounds()
    trigger_click_sound()
    
    # 1. Clear text log stack and assign temporary typing state
    terminal_logs.clear()
    current_stage = "boot_sequence"

    if choice == "1":
        await typewriter("\nRisky Move, the engines fire hard. The pressure stabilizes just in time.", color=(230, 237, 243))
        await typewriter("Months pass in deep space, and the crew finally arrives at the Red Planet", color=(230, 237, 243))
        
        # Apply metric change
        crew_safety -= 10
        science_points += 30
        
        # --- CRITICAL VALUE FAILURE GUARD ---
        if crew_safety <= 0 or mission_budget <= 0:
            crew_safety = max(0, crew_safety)
            mission_budget = max(0, mission_budget)
            await typewriter("\nCRITICAL STRUCTURAL FAILURE: Rocket hull compromised during orbital adjustment!", color=(219, 43, 31), bold=True)
            trigger_mission_failed_sound()
            await end_game_session()
            return
        
        # Call unified landing sequence handler if survived
        await display_mars_landing_sequence(stage_label=3)

    elif choice == "2":
        await typewriter("The emergency escape system rips apart from the capsule", color=(230, 237, 243))
        await typewriter("The crew safely splash down in the Atlantic Ocean", color=(230, 237, 243))
        await typewriter("The mission is over but the crew lives", color=(230, 237, 243))
        
        mission_budget = 0
        await end_game_session()


async def display_mars_landing_sequence(stage_label=3):
    """Consolidates your landing branch layouts into a single async template."""
    global crew_safety, mission_budget, science_points, current_stage
    
    await typewriter("", color=(230, 237, 243))
    await typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color=(88, 166, 255))

    await typewriter(f"\nSTAGE-{stage_label}: MARS LANDING", color=(242, 204, 96), bold=True)
    await typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates", color=(230, 237, 243))
    await typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", color=(219, 43, 31))
    
    # Enable Stage 3A layout choice buttons
    current_stage = "stage3a"


async def handle_choice3a(choice):
    """Processes choice inputs for Stage 3A (Mars Automated Landing Crisis)."""
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs
        
    stop_all_sounds()
    trigger_click_sound()
    
    terminal_logs.clear()
    current_stage = "boot_sequence"

    if choice == "1":
        # Fires up the minigame
        landing_minigame_difficulty()
        
        if crew_safety >= 100:
            crew_safety = 100
        else:
            crew_safety += 10

        science_points += 50

    elif choice == "2":
        trigger_pullup_sound()
        await typewriter("\nCRASH DOWN! The system clips a massive hidden boulder", color=(219, 43, 31))
        await typewriter("The lander tips and loses pressure. Space is not forgiving.", color=(219, 43, 31))
        
        trigger_mission_failed_sound()
        await typewriter("MISSION FAILED", color=(219, 43, 31), bold=True)
        
        crew_safety = 0
        mission_budget = 0
        
        await end_game_session()

async def handle_choice2b(choice):
    """Processes narrative choice inputs for Stage 2B (Lost in Space)."""
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs
    
    stop_all_sounds()
    trigger_click_sound()
    
    # 1. Clear text log stack and assign temporary typing state
    terminal_logs.clear()
    current_stage = "boot_sequence"

    if choice == "1":
        await typewriter("The patch works! The navigation is back up again", color=(230, 237, 243))
        await typewriter("However the reboot drained 60% of your spacecraft power reserves", color=(219, 43, 31))
        science_points += 20

        # Display Live Metric Indicators
        await typewriter("", color=(230, 237, 243))
        await typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color=(88, 166, 255)) # Cyan status
        
        # Transition into Stage 3B low power plot line
        await typewriter("\nSTAGE-3: LOW POWER", color=(242, 204, 96), bold=True) 
        trigger_spacecraft_warning_sound()
        await typewriter("The crew arrive at Mars in a critically underpowered ship", color=(219, 43, 31))
        await typewriter("With the low power, you cannot run both the heaters and the landing thrusters", color=(219, 43, 31))
        
        # Enable Stage 3B layout choice buttons
        current_stage = "stage3b"

    elif choice == "2":
        await typewriter("LOST ORBIT! The math is too complex with the light-lag delay", color=(219, 43, 31))
        await typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication", color=(219, 43, 31))
        trigger_mission_failed_sound()
        
        crew_safety = 0
        mission_budget = 0
        
        await end_game_session()


async def handle_choice3b(choice):
    """Processes choice inputs for Stage 3B (Low Power Descent)."""
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs
          
    stop_all_sounds()
    trigger_click_sound()
    
    terminal_logs.clear()
    current_stage = "boot_sequence"

    if choice == "1":
        await typewriter("The solar sails catch enough sunlight to recharge", color=(126, 231, 135))
        science_points += 40
        
        # Pulls up Stage 4 Mars Landing text and routes to Stage 3A buttons automatically
        await display_mars_landing_sequence(stage_label=4)

    elif choice == "2":
        await typewriter("\nBURN OUT! The extreme cold freezes the fuel valves during descent.", color=(219, 43, 31))
        await typewriter("The engines fail 100 meters up. The ship impacts the surface.", color=(219, 43, 31))
        trigger_mission_failed_sound()
        await typewriter("MISSION FAILED", color=(219, 43, 31), bold=True)
        
        crew_safety = 0
        
        await end_game_session()

#===========================================================================
#LANDING MINI GAME 
#===========================================================================

def run_physics_frame(surface):
    """Updates game mechanics and handles collisions directly on the primary screen canvas."""
    global altitude, velocity_y, ship_angle, ship_x, ship_y, game_running, current_difficulty
    global prep_timer_frames, current_stage
    global move_left_active, move_right_active
    global victory_altitude, pad_screen_y

    if not game_running:
        return
        
    # 1. Pull dynamic window geometry parameters from main surface
    f_w = surface.get_width()
    f_h = surface.get_height()
    
    screen_center_x = f_w // 2
    left_wall = screen_center_x - 175
    right_wall = screen_center_x + 175
    
    # 2. Continuous Input Slide and Tilt Physics Calculations
    if move_left_active:
        ship_x -= 6  
        ship_angle = min(25, ship_angle + 3)
    elif move_right_active:
        ship_x += 6  
        ship_angle = max(-25, ship_angle - 3)
    else:
        ship_angle *= 0.85
    
    # Symmetrical edge guards to prevent sliding past the dark gray walls
    if ship_x - 25 < left_wall:  ship_x = left_wall + 25
    if ship_x + 25 > right_wall: ship_x = right_wall - 25
        
    # Scroll layout speed modifiers based on active difficulty choice
    if prep_timer_frames > 0:
        altitude += 1.5
        prep_timer_frames -= 1
    else:
        if current_difficulty == "EASY":
            altitude += 2.0
        elif current_difficulty == "MEDIUM":
            altitude += 3.2
        else: # HARD
            altitude += 4.5   
    
    # 3. Graphics Rendering Operations
    surface.fill((15, 15, 25)) 
    
    # Loop and draw moving spike segments dynamically
    for obs in obstacles:
        screen_y = obs["y"] - int(altitude)
        if -150 < screen_y < f_h + 150:
            calculated_height = int(obs["width"] * 0.3)
            
            if obs["side"] == "LEFT":
                scaled_spike = pygame.transform.scale(spike_left, (obs["width"], calculated_height))
                surface.blit(scaled_spike, (left_wall - 40, screen_y))
            else:
                scaled_spike = pygame.transform.scale(spike_right, (obs["width"], calculated_height))
                surface.blit(scaled_spike, (right_wall + 40 - obs["width"], screen_y))
                
    # Render Green Touchdown Landing Pad
    pad_screen_y = victory_altitude - int(altitude)
    if -100 < pad_screen_y < f_h + 100:
        pygame.draw.rect(surface, (0, 255, 100), (left_wall, pad_screen_y, 350, 30))
        pad_font = pygame.font.SysFont("OCR A Extended", 16, bold=True)
        pad_text = pad_font.render("---TOUCHDOWN ZONE---", True, (0, 0, 0))
        surface.blit(pad_text, (screen_center_x - (pad_text.get_width() // 2), pad_screen_y + 6))

    # Mask trailing spike bases using side column frames
    pygame.draw.rect(surface, (40, 40, 45), (0, 0, left_wall, f_h))
    pygame.draw.rect(surface, (40, 40, 45), (right_wall, 0, f_w - right_wall, f_h))
    
    # Render Bottom Right Heads-Up Display (HUD Mode Label)
    hud_font = pygame.font.SysFont("OCR A Extended", 18, bold=True)
    hud_string = f"SYS-MODE: {current_difficulty}"
    text_surface = hud_font.render(hud_string, True, (255, 255, 255))
    surface.blit(text_surface, (f_w - text_surface.get_width() - 25, f_h - text_surface.get_height() - 25))
    
    # 4. Spaceship Modeling & Rendering Matrix
    ship_rect = pygame.Rect(ship_x - 25, ship_y - 45, 50, 90)
    surface.blit(ship_surface, (ship_rect.x, ship_rect.y))
    
    # Draw Countdown Prepare Overlay Strings
    if prep_timer_frames > 0:
        seconds_left = (prep_timer_frames // 60) + 1
        count_font = pygame.font.SysFont("OCR A Extended", 48, bold=True)
        count_string = f"PREPARE: {seconds_left}"
        count_surface = count_font.render(count_string, True, (0, 240, 240))
        surface.blit(count_surface, (screen_center_x - (count_surface.get_width() // 2), (f_h // 2) - 150))

    # 5. Collision Verification Engine Check Routine
    if ship_rect.bottom >= pad_screen_y and ship_rect.top < pad_screen_y + 30:
        if left_wall <= ship_rect.centerx <= right_wall:
            game_running = False
            # Instead of destroying modules wrap handlers into background task engines
            asyncio.create_task(landing_success())
            return

    # Check for boundary or mask-based spike collisions
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
                else:
                    spike_x = right_wall + 40 - obs["width"]
                    scaled_spike = pygame.transform.scale(spike_right, (obs["width"], calculated_height))
                
                spike_mask = pygame.mask.from_surface(scaled_spike)
                offset_x = spike_x - ship_rect.x
                offset_y = screen_y - ship_rect.y
                
                if ship_mask.overlap(spike_mask, (offset_x, offset_y)):
                    crashed = True
                    break

    # 6. Evaluate Endgame Redirect Routing States
    if crashed:
        game_running = False
        asyncio.create_task(space_ship_crash())

def start_landing_simulation_canvas():
    """Initializes the physics engine properties and obstacles natively inside the global state machine."""
    global current_stage, altitude, velocity_y, ship_angle, game_running
    global ship_x, ship_y, obstacles, ship_surface, ship_mask, spike_left, spike_right, current_difficulty
    global move_left_active, move_right_active, prep_timer_frames, victory_altitude
    
    # 1. Reset Physics Engine States
    altitude = 0.0
    velocity_y = 0.0
    ship_angle = 0.0
    game_running = True
    
    # Initialize countdown and movement trackers
    prep_timer_frames = 180
    move_left_active = False
    move_right_active = False
    
    # 2. Pull runtime canvas dimensions directly from unified screen object
    frame_w = screen.get_width()
    frame_h = screen.get_height()

    # 3. Load and scale custom Spaceship design
    try:
        raw_ship = pygame.image.load("Spaceship.png").convert_alpha()
        ship_surface = pygame.transform.scale(raw_ship, (50, 90))
        ship_mask = pygame.mask.from_surface(ship_surface)
    except pygame.error:
        ship_surface = pygame.Surface((50, 90))
        ship_surface.fill((0, 240, 240)) 
        ship_mask = pygame.mask.from_surface(ship_surface)

    # 4. Load single native 200x60px Spike image & mirror it
    try:
        raw_spike = pygame.image.load("Small Spike.png").convert_alpha()
        spike_left = pygame.transform.scale(raw_spike, (200, 60))
        spike_right = pygame.transform.flip(spike_left, True, False)
    except pygame.error:
        spike_left = pygame.Surface((200, 60))
        spike_left.fill((130, 45, 45))
        spike_right = pygame.Surface((200, 60))
        spike_right.fill((130, 45, 45))
    
    # 5. Core Ship Coordinates
    ship_x = frame_w // 2
    ship_y = frame_h // 2
    
    # 6. Symmetrical Dense Spacing Properties based on selection difficulty
    if current_difficulty == "EASY":
        small_w, medium_w, large_w = 140, 170, 200
        gap_spacing = 180  
    elif current_difficulty == "MEDIUM":
        small_w, medium_w, large_w = 170, 210, 240
        gap_spacing = 180  
    else: # HARD MODE
        small_w, medium_w, large_w = 220, 250, 270  
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
        victory_altitude = final_spike_y + 1000
            
        current_side = chosen_side
        width = random.choice([small_w, medium_w, large_w])
        obstacles.append({"y": obs_y, "side": chosen_side, "width": width})

    # 7. ROUTE ENGINE STATE MACHINE: Advance instantly into active minigame loop context
    current_stage = "landing_simulation"

def draw_difficulty_menu(surface, mouse_pos):
    """Renders a responsive centered difficulty selection card mimicking your Tkinter styles."""
    global current_difficulty
    
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    # 1. Define container sizes
    card_w, card_h = 400, 400
    card_x = (scr_w - card_w) // 2
    card_y = (scr_h - card_h) // 2
    
    # 2. Draw base dialog bounding box frame
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
    pygame.draw.rect(surface, (22, 27, 34), card_rect, border_radius=8)
    pygame.draw.rect(surface, (48, 54, 61), card_rect, width=2, border_radius=8) 
    
    # 3. Draw Title Label Text Header
    title_font = pygame.font.SysFont("OCR A Extended", 16, bold=True)
    title_surf = title_font.render("CHOOSE DIFFICULTY", True, (230, 237, 243))
    title_x = card_x + (card_w - title_surf.get_width()) // 2
    surface.blit(title_surf, (title_x, card_y + 35))
    
    # 4. Button Geometry Constants
    btn_w, btn_h = 220, 40
    btn_x = card_x + (card_w - btn_w) // 2
    
    easy_rect = pygame.Rect(btn_x, card_y + 110, btn_w, btn_h)
    med_rect  = pygame.Rect(btn_x, card_y + 180, btn_w, btn_h)
    hard_rect = pygame.Rect(btn_x, card_y + 250, btn_w, btn_h)
    
    # --- RENDER EASY MODE BUTTON (COLOR_CYAN) ---
    is_easy_hover = easy_rect.collidepoint(mouse_pos)
    easy_bg = (130, 200, 255) if is_easy_hover else (88, 166, 255) # Hover highlight logic
    pygame.draw.rect(surface, easy_bg, easy_rect, border_radius=4)
    easy_txt = font_console.render("EASY MODE", True, (11, 14, 20))
    surface.blit(easy_txt, (easy_rect.x + (btn_w - easy_txt.get_width()) // 2, easy_rect.y + (btn_h - easy_txt.get_height()) // 2))
    
    # --- RENDER MEDIUM MODE BUTTON (YELLOW) ---
    is_med_hover = med_rect.collidepoint(mouse_pos)
    med_bg = (255, 255, 140) if is_med_hover else (242, 204, 96)
    pygame.draw.rect(surface, med_bg, med_rect, border_radius=4)
    med_txt = font_console.render("MEDIUM MODE", True, (11, 14, 20))
    surface.blit(med_txt, (med_rect.x + (btn_w - med_txt.get_width()) // 2, med_rect.y + (btn_h - med_txt.get_height()) // 2))
    
    # --- RENDER HARD MODE BUTTON (COLOR_RED) ---
    is_hard_hover = hard_rect.collidepoint(mouse_pos)
    hard_bg = (255, 90, 80) if is_hard_hover else (219, 43, 31)
    pygame.draw.rect(surface, hard_bg, hard_rect, border_radius=4)
    hard_txt = font_console.render("HARD MODE", True, (255, 255, 255))
    surface.blit(hard_txt, (hard_rect.x + (btn_w - hard_txt.get_width()) // 2, hard_rect.y + (btn_h - hard_txt.get_height()) // 2))
    
    # Return button hitboxes so mouse click handlers can intercept selections
    return easy_rect, med_rect, hard_rect


def landing_minigame_difficulty():
    """Triggers the responsive difficulty selection layout screen state."""
    global current_stage
    current_stage = "difficulty_menu"

# Track if the player won the game in their last run
was_last_run_victory = False
# Add a routing flag right above the end_game_session function
is_playing_standalone_minigame = False

async def space_ship_crash():
    """Triggers the crash animation sequences and forces endgame stat calculations."""
    global crew_safety, mission_budget
    trigger_mission_failed_sound()
    
    await typewriter("CRASH: Space shuttle hull compromised!", color=(219, 43, 31))
    crew_safety = 0
    mission_budget = 0
    await end_game_session()


async def landing_success():
    """Unlocks standalone shortcuts, updates victory states, and handles summaries."""
    global is_minigame_unlocked, was_last_run_victory

    is_minigame_unlocked = True
    was_last_run_victory = True

    # Commit the true value of is_minigame_unlocked cleanly to storage
    save_settings()

    trigger_mission_success_sound()
    await typewriter("HEROIC VICTORY!!!", color=(126, 231, 135))
    await typewriter("You flew beautifully!! The crew and the ship are safe!!!", color=(126, 231, 135))
    await end_game_session()


async def end_game_session():
    """Prints a rolling metric evaluation log and routes users to choice screens."""
    global is_playing_standalone_minigame, current_stage
    
    await typewriter(f"\nFinal Session Summary-> Crew Safety: {crew_safety}% | Budget: {mission_budget}% | Science Points: {science_points}", color=(88, 166, 255)) # Cyan
    
    # Check if they came from the standalone button path shortcut
    if is_playing_standalone_minigame:
        # Redirect directly back to the minigame difficulty choice panel selection
        landing_minigame_difficulty()
    else:
        current_stage = "restart"


def reboot_mission():
    """Wipes active session data and determines narrative progression paths."""
    global crew_safety, mission_budget, science_points, try_again_counter, was_last_run_victory, current_stage
    
    # Reset tracking state metrics back to standard defaults
    crew_safety = 100
    mission_budget = 100
    science_points = 0
    try_again_counter += 1

    if was_last_run_victory:
        # Bounce winners back out to the main menu screen to view their newly unlocked pathway buttons
        was_last_run_victory = False 
        current_stage = "welcome"
    else:
        # Players failed/crashed: skip the welcome screens and launch directly into Chapter 1
        # Trigger async typing animation timeline smoothly inside background task queues
        asyncio.create_task(game_restart_screen())


def launch_story_mode():
    """Initializes a normal chronological gameplay campaign playthrough."""
    global is_playing_standalone_minigame
    is_playing_standalone_minigame = False 
    
    # Swaps state to trigger typing strings letter-by-letter
    asyncio.create_task(game_restart_screen())


def launch_standalone_minigame():
    """Bypasses introductory story frames and skips straight to testing flight metrics."""
    global is_playing_standalone_minigame
    is_playing_standalone_minigame = True  
    
    # Direct route into minigame difficulty prompt state layout
    landing_minigame_difficulty()

def draw_welcome_screen(surface, mouse_pos):
    """Draws a responsive welcome canvas menu layout with dynamic minigame branching states."""
    global is_minigame_unlocked, current_stage
    
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    # 1. RENDER RETRO MISSION TITLE HEADERS
    title_font = pygame.font.SysFont("OCR A Extended", 26, bold=True)
    sub_font = pygame.font.SysFont("OCR A Extended", 13, bold=False)
    
    title_surf = title_font.render("THE ARES HORIZON", True, (126, 231, 135))
    subtitle_surf = sub_font.render("MISSION CONTROL TERMINAL", True, (230, 237, 243))
    
    surface.blit(title_surf, ((scr_w - title_surf.get_width()) // 2, scr_h // 2 - 160))
    surface.blit(subtitle_surf, ((scr_w - subtitle_surf.get_width()) // 2, scr_h // 2 - 120))
    
    # Initialize target rect parameters to return back to the mouse event listener loop
    btn_start_rect = None
    btn_story_rect = None
    btn_minigame_rect = None

    # ----------------------------------------------------
    # BRANCH A: SINGLE BIG START BUTTON LAYOUT (LOCKED STATE)
    # ----------------------------------------------------
    if not is_minigame_unlocked:
        w, h = 240, 65
        btn_start_rect = pygame.Rect((scr_w - w) // 2, scr_h // 2 - 20, w, h)
        
        # Hover vs Idle highlighting check
        bg_color = (48, 54, 61) if btn_start_rect.collidepoint(mouse_pos) else (22, 27, 34)
        
        pygame.draw.rect(surface, bg_color, btn_start_rect, border_radius=4)
        pygame.draw.rect(surface, (48, 54, 61), btn_start_rect, width=1, border_radius=4)
        
        text_surf = ui_font.render("START GAME", True, (230, 237, 243))
        surface.blit(text_surf, (btn_start_rect.x + (w - text_surf.get_width()) // 2, 
                                 btn_start_rect.y + (h - text_surf.get_height()) // 2))

    # ----------------------------------------------------
    # BRANCH B: SPLIT MULTI-CHOICE SELECTION MENU (UNLOCKED STATE)
    # ----------------------------------------------------
    else:
        # Prompt Label
        lbl_surf = ui_font.render("CHOOSE YOUR PATHWAY:", True, (242, 204, 96))
        surface.blit(lbl_surf, ((scr_w - lbl_surf.get_width()) // 2, scr_h // 2 - 50))
        
        w, h = 210, 55
        center_gap = 30
        
        # Left button position (Play Story)
        btn_story_rect = pygame.Rect(scr_w // 2 - w - center_gap, scr_h // 2, w, h)
        # Right button position (Launch Minigame)
        btn_minigame_rect = pygame.Rect(scr_w // 2 + center_gap, scr_h // 2, w, h)
        
        # Draw Play Story Button Frame
        bg_story = (48, 54, 61) if btn_story_rect.collidepoint(mouse_pos) else (22, 27, 34)
        pygame.draw.rect(surface, bg_story, btn_story_rect, border_radius=4)
        pygame.draw.rect(surface, (48, 54, 61), btn_story_rect, width=1, border_radius=4)
        
        story_txt = ui_font.render("PLAY STORY", True, (230, 237, 243))
        surface.blit(story_txt, (btn_story_rect.x + (w - story_txt.get_width()) // 2, 
                                 btn_story_rect.y + (h - story_txt.get_height()) // 2))
        
        # Draw Launch Minigame Button Frame
        bg_mini = (48, 54, 61) if btn_minigame_rect.collidepoint(mouse_pos) else (22, 27, 34)
        pygame.draw.rect(surface, bg_mini, btn_minigame_rect, border_radius=4)
        pygame.draw.rect(surface, (48, 54, 61), btn_minigame_rect, width=1, border_radius=4)
        
        mini_txt = ui_font.render("LAUNCH MINIGAME", True, (88, 166, 255))
        surface.blit(mini_txt, (btn_minigame_rect.x + (w - mini_txt.get_width()) // 2, 
                                btn_minigame_rect.y + (h - mini_txt.get_height()) // 2))

    # Return hitboxes to allow the main mouse event click listener to evaluate them
    return btn_start_rect, btn_story_rect, btn_minigame_rect

# A centralized data dictionary mapping game choices to their strings
STAGE_CONTENT = {
    "stage1": {
        "title": "AWAITING STRATEGIC DIRECTIVE INSTRUCTIONS...",
        "c1": "1) Launch Now - Push past high winds and save time",
        "c2": "2) Delay Launch - Abort current window and wait"
    },
    "stage2a": {
        "title": "CRITICAL PRESSURE DROP DETECTED. CHOOSE ROUTE:",
        "c1": "1) PUSH ENGINES - Fire second stage anyway to clear orbit",
        "c2": "2) ABORT MISSION - Activate the emergency escape tower"
    },
    "stage3a": {
        "title": "AUTOMATED LANDING FAILURE! CHOOSE FLIGHT CONTROLS:",
        "c1": "1) MANUAL CONTROL - (INTERACTIVE)",
        "c2": "2) AUTO-PILOT - Trust flight computer mapping systems"
    },
    "stage2b": {
        "title": "STAGE-2: LOST IN SPACE // ARRAY REBOOT INTERFACE:",
        "c1": "1) UPLOAD A PATCH - Push an unverified software fix to reboot the system",
        "c2": "2) MANUAL TRAJECTORY - Force crew to navigate manually using star maps"
    },
    "stage3b": {
        "title": "STAGE-3: THE LANDING // ROUTE AVAILABLE BATTERY POWER:",
        "c1": "1) DEPLOY SOLAR SAILS - Wait in orbit for 3 days to charge batteries",
        "c2": "2) EMERGENCY BURN - Cut the life support heaters to power a descent"
    },
    "restart": {
        "title": "MISSION TERMINATED",
        "c1": "TRY AGAIN?",
        "c2": "EXIT SYSTEM?"
    }
}

def draw_choice_interface(surface, mouse_pos):
    """Draws narrative choices stacked neatly above the bottom margin of the terminal window, with fully centered, letter-spaced labels and choice title."""
    global current_stage
    
    if current_stage not in STAGE_CONTENT:
        return None, None

    scr_w = surface.get_width()
    scr_h = surface.get_height()
    content = STAGE_CONTENT[current_stage]
    
    # 1. Capture Main Terminal Bounding Box Position Math
    console_rect = pygame.Rect(25, 80, scr_w - 50, scr_h - 170)
    
    title_color = (219, 43, 31) if current_stage == "restart" else (242, 204, 96)
    
    # FIX: Add letter-spacing padding to the choice title string
    padded_title = "".join([char + "\u200a" for char in content["title"]])
    title_surface = ui_font.render(padded_title, True, title_color)
    
    title_x = console_rect.x + (console_rect.width - title_surface.get_width()) // 2
    title_y = console_rect.bottom - 130 
    surface.blit(title_surface, (title_x, title_y))
    
    # 3. Dynamic Button Geometry Constants
    btn_w = console_rect.width - 40 
    btn_h = 35
    btn_x = console_rect.x + 20
    
    b1_rect = pygame.Rect(btn_x, title_y + 25, btn_w, btn_h) 
    b2_rect = pygame.Rect(btn_x, title_y + 65, btn_w, btn_h) 
    
    active_font = ui_font if current_stage == "restart" else font_console
    
    # ----------------------------------------------------
    # --- RENDER CHOICE BUTTON 1 ---
    # ----------------------------------------------------
    if b1_rect.collidepoint(mouse_pos):
        bg1, fg1 = (48, 54, 61), (255, 255, 255)
    else:
        bg1 = (22, 27, 34)
        fg1 = content.get("color1", (100, 200, 255))
        
    pygame.draw.rect(surface, bg1, b1_rect, border_radius=4)
    pygame.draw.rect(surface, (48, 54, 61), b1_rect, width=1, border_radius=4)
    
    # FIX: Add letter-spacing padding to choice 1 string before measuring width
    padded_c1 = "".join([char + "\u200a" for char in content["c1"]])
    text1_surf = active_font.render(padded_c1, True, fg1)
    text1_x = b1_rect.x + (btn_w - text1_surf.get_width()) // 2
    text1_y = b1_rect.y + (btn_h - text1_surf.get_height()) // 2
    surface.blit(text1_surf, (text1_x, text1_y))

    # ----------------------------------------------------
    # --- RENDER CHOICE BUTTON 2 ---
    # ----------------------------------------------------
    if b2_rect.collidepoint(mouse_pos):
        bg2, fg2 = (48, 54, 61), (255, 255, 255)
    else:
        bg2 = (22, 27, 34)
        fg2 = content.get("color2", (245, 210, 110))
        
    pygame.draw.rect(surface, bg2, b2_rect, border_radius=4)
    pygame.draw.rect(surface, (48, 54, 61), b2_rect, width=1, border_radius=4)
    
    # FIX: Add letter-spacing padding to choice 2 string before measuring width
    padded_c2 = "".join([char + "\u200a" for char in content["c2"]])
    text2_surf = active_font.render(padded_c2, True, fg2)
    text2_x = b2_rect.x + (btn_w - text2_surf.get_width()) // 2
    text2_y = b2_rect.y + (btn_h - text2_surf.get_height()) // 2
    surface.blit(text2_surf, (text2_x, text2_y))
    
    return b1_rect, b2_rect

# Holds a running list of string messages displayed on the screen console
terminal_logs = [
    ["ARES HORIZON OPERATING SYSTEM v4.6.0", (126, 231, 135)],
]

def draw_terminal_console(surface):
    """Renders a responsive text log console container, leaving bottom padding space for choices."""
    global terminal_logs, current_stage
    
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    # 1. Main Terminal Window Rectangle Layout Container
    console_rect = pygame.Rect(25, 80, scr_w - 50, scr_h - 170)
    
    # Draw backdrop card graphics
    pygame.draw.rect(surface, (15, 18, 23), console_rect)          
    pygame.draw.rect(surface, (48, 54, 61), console_rect, width=1) 
    
    line_spacing = 30
    padding_x, padding_y = 15, 15
    
    # 110 pixels from the vertical ceiling space to protect text lines from button
    usable_height = console_rect.height if current_stage not in STAGE_CONTENT else console_rect.height - 110
    
    max_visible_lines = (usable_height - (padding_y * 2)) // line_spacing
    visible_lines = terminal_logs[-max_visible_lines:] if len(terminal_logs) > max_visible_lines else terminal_logs
    
    start_y = console_rect.y + padding_y
    for i, line_data in enumerate(visible_lines):
        line_text = line_data[0]
        line_color = line_data[1]
        
        text_surface = font_console.render(line_text, True, line_color)
        surface.blit(text_surface, (console_rect.x + padding_x, start_y + (i * line_spacing)))

# --- GLOBAL HITBOX BOUNDS ---
close_btn_rect = pygame.Rect(820, 15, 115, 30)
mute_btn_rect  = pygame.Rect(695, 15, 115, 30)

async def main():
    global screen, is_fullscreen, current_stage, move_left_active, move_right_active
    
    # Initialize data parameters and background soundtracks on startup
    load_settings()
    set_mixer_volumes()
    
    running = True
    while running:
        # Track the absolute grid position coordinates of the user mouse pointer
        mouse_pos = pygame.mouse.get_pos()
        
        # --- PYGAME EVENT LOOP ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # ----------------------------------------------------
            # 1. KEYBOARD CONTINUOUS INPUT TRACKING LAYER
            # ----------------------------------------------------
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    
                elif event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                    else:
                        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SCALED)
                
                # Check directional maneuvers if the immersive landing simulator is active
                elif current_stage == "landing_simulation":
                    if event.key == pygame.K_LEFT:
                        move_left_active = True
                    elif event.key == pygame.K_RIGHT:
                        move_right_active = True

            elif event.type == pygame.KEYUP:
                if current_stage == "landing_simulation":
                    if event.key == pygame.K_LEFT:
                        move_left_active = False
                    elif event.key == pygame.K_RIGHT:
                        move_right_active = False

            # ----------------------------------------------------
            # 2. UNIFIED MOUSE CLICK TARGET HANDLING LAYER
            # ----------------------------------------------------
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Close Game Titlebar Button Box Check
                    current_close_rect = pygame.Rect(screen.get_width() - 130, 15, 115, 30)
                    if current_close_rect.collidepoint(event.pos):
                        running = False
                        continue

                    # Mute Sound Toggle Button Box Check
                    if mute_btn_rect.collidepoint(event.pos):
                        toggle_mute()
                        continue

                    # Responsive Bottom-Left Settings Menu Action Box Check
                    current_h = screen.get_height()
                    current_settings_rect = pygame.Rect(15, current_h - 45, 115, 30)
                    if current_settings_rect.collidepoint(event.pos):
                        await open_settings_menu(screen)
                        continue

                    # --- SCENE SPECIFIC ROUTING INTERCEPTS ---
                    # Welcome Menu Clicks
                    if current_stage == "welcome":
                        start_r, story_r, mini_r = draw_welcome_screen(screen, mouse_pos)
                        if start_r and start_r.collidepoint(event.pos):
                            trigger_click_sound()
                            current_stage = "boot_sequence"
                            asyncio.create_task(run_boot_sequence())
                        elif story_r and story_r.collidepoint(event.pos):
                            trigger_click_sound()
                            launch_story_mode()
                        elif mini_r and mini_r.collidepoint(event.pos):
                            trigger_click_sound()
                            launch_standalone_minigame()
                    
                    # Difficulty Selector Window Menu Clicks
                    elif current_stage == "difficulty_menu":
                        easy_r, med_r, hard_r = draw_difficulty_menu(screen, mouse_pos)
                        if easy_r.collidepoint(event.pos):
                            trigger_click_sound()
                            current_difficulty = "EASY"
                            start_landing_simulation_canvas()
                        elif med_r.collidepoint(event.pos):
                            trigger_click_sound()
                            current_difficulty = "MEDIUM"
                            start_landing_simulation_canvas()
                        elif hard_r.collidepoint(event.pos):
                            trigger_click_sound()
                            current_difficulty = "HARD"
                            start_landing_simulation_canvas()
                    
                    # Core Narrative Branch Choices Click Checks
                    elif current_stage in STAGE_CONTENT:
                        b1_rect, b2_rect = draw_choice_interface(screen, mouse_pos)
                        if b1_rect and b2_rect:
                            if b1_rect.collidepoint(event.pos):
                                trigger_click_sound()
                                if current_stage == "stage1": asyncio.create_task(handle_choice1("1"))
                                elif current_stage == "stage2a": asyncio.create_task(handle_choice2a("1"))
                                elif current_stage == "stage3a": asyncio.create_task(handle_choice3a("1"))
                                elif current_stage == "stage2b": asyncio.create_task(handle_choice2b("1"))
                                elif current_stage == "stage3b": asyncio.create_task(handle_choice3b("1"))
                                elif current_stage == "restart": reboot_mission()
                            elif b2_rect.collidepoint(event.pos):
                                trigger_click_sound()
                                if current_stage == "stage1": asyncio.create_task(handle_choice1("2"))
                                elif current_stage == "stage2a": asyncio.create_task(handle_choice2a("2"))
                                elif current_stage == "stage3a": asyncio.create_task(handle_choice3a("2"))
                                elif current_stage == "stage2b": asyncio.create_task(handle_choice2b("2"))
                                elif current_stage == "stage3b": asyncio.create_task(handle_choice3b("2"))
                                elif current_stage == "restart": 
                                    pygame.quit()
                                    sys.exit()

        # ----------------------------------------------------
        # 3. DRAWING / RENDERING STATE MACHINE ROUTING LAYER
        # ----------------------------------------------------
        screen.fill(BG_MAIN) 
    
        if current_stage not in ["welcome"]:
            draw_telemetry_dashboard(screen)

        # STATE MAPPING ENGINES
        if current_stage == "welcome":
            draw_welcome_screen(screen, mouse_pos)
            
        elif current_stage == "boot_sequence":
            draw_terminal_console(screen)
            
        elif current_stage == "difficulty_menu":
            draw_difficulty_menu(screen, mouse_pos)
            
        elif current_stage in STAGE_CONTENT:
            draw_terminal_console(screen)
            draw_choice_interface(screen, mouse_pos)
            
        elif current_stage == "landing_simulation":
            run_physics_frame(screen)

        if current_stage != "landing_simulation":
            draw_settings_button(screen, mouse_pos)
        
        # Keep close game handle alive in all layers as an absolute application recovery bypass
        draw_close_button(screen, mouse_pos)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())