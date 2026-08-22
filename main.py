#Importing packages
import os
import time
import sys
import math
import random
import pygame
import json
import asyncio
import builtins

#Global Variables
current_stage = "welcome"
current_difficulty = "EASY"  
is_boot_completed = False
key_states = {}
terminal_logs = []
thruster_particles = []
starfield_matrix = []
text_speed = 0.045 
is_minigame_unlocked = False
draw_boot_bar = False
boot_bar_pct = 0
is_game_paused = False
is_emergency_active = False
fall_velocity = 0
ship_fuel = 100.0
pad_start_x = -1
_cached_crt_overlay = None
_cached_emergency_glow = None
current_theme = "DARK"

THEMES = {
    "DARK": {
        "BG_MAIN": (11, 14, 20),
        "BG_PANEL": (22, 27, 34),
        "TEXT_COLOR": (230, 237, 243),
        "COLOR_CYAN": (88, 166, 255)
    },
    "LIGHT": {
        "BG_MAIN": (240, 242, 245),
        "BG_PANEL": (255, 255, 255),
        "TEXT_COLOR": (20, 24, 33),
        "COLOR_CYAN": (0, 102, 204)
    }
}

_HIGH_PLASMA = pygame.Surface((3, 3), pygame.SRCALPHA); _HIGH_PLASMA.fill((0, 210, 255, 220))
_LOW_PLASMA = pygame.Surface((3, 3), pygame.SRCALPHA); _LOW_PLASMA.fill((14, 116, 144, 140))
_SMOKE_SURF = pygame.Surface((3, 3), pygame.SRCALPHA); _SMOKE_SURF.fill((71, 85, 105, 80))

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
    global BG_MAIN, BG_PANEL, TEXT_COLOR, COLOR_CYAN

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

                current_theme = data.get("current_theme", "DARK")

                BG_MAIN = THEMES[current_theme]["BG_MAIN"]
                BG_PANEL = THEMES[current_theme]["BG_PANEL"]
                TEXT_COLOR = THEMES[current_theme]["TEXT_COLOR"]
                COLOR_CYAN = THEMES[current_theme]["COLOR_CYAN"]

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
            "is_minigame_unlocked": is_minigame_unlocked,
            "current_theme": current_theme
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
ocra_path = os.path.join(script_directory, "ocra.TTF")
twcen_path = os.path.join(script_directory, "twcen.TTF")
twcenbold_path = os.path.join(script_directory, "twcenbold.TTF")

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

def toggle_theme():
    global current_theme, BG_MAIN, BG_PANEL, TEXT_COLOR, COLOR_CYAN
    current_theme = "LIGHT" if current_theme == "DARK" else "DARK"
    
    # Apply theme variables immediately
    BG_MAIN = THEMES[current_theme]["BG_MAIN"]
    BG_PANEL = THEMES[current_theme]["BG_PANEL"]
    TEXT_COLOR = THEMES[current_theme]["TEXT_COLOR"]
    COLOR_CYAN = THEMES[current_theme]["COLOR_CYAN"]
    save_settings()

def reset_all_settings():
    global background_music_volume, emergency_volume, is_muted
    global pre_mute_emergency_volume, pre_mute_music_volume
    global text_speed, is_minigame_unlocked, current_theme
    global BG_MAIN, BG_PANEL, TEXT_COLOR, COLOR_CYAN
    
    background_music_volume = 0.5
    emergency_volume = 0.25
    is_muted = False
    pre_mute_emergency_volume = 0.25
    pre_mute_music_volume = 0.5
    text_speed = DEFAULT_TYPING_SPEED
    is_minigame_unlocked = False
    
    # Force back to Dark Mode default
    current_theme = "DARK"
    BG_MAIN = THEMES["DARK"]["BG_MAIN"]
    BG_PANEL = THEMES["DARK"]["BG_PANEL"]
    TEXT_COLOR = THEMES["DARK"]["TEXT_COLOR"]
    COLOR_CYAN = THEMES["DARK"]["COLOR_CYAN"]
    
    set_mixer_volumes()
    save_settings()

async def open_settings_menu(main_screen):
    """Renders a centered settings modal dialog box directly onto the main game canvas."""
    global background_music_volume, emergency_volume, is_muted
    global text_speed, is_game_paused
    
    # Temporarily freeze all audio outputs while interacting with controls
    trigger_click_sound()
    is_game_paused = True
    
    # Track the main window's dynamic width and height for perfect center positioning
    base_w = main_screen.get_width()
    base_h = main_screen.get_height()
    
    menu_w, menu_h = 320, 470
    menu_x = (base_w - menu_w) // 2
    menu_y = (base_h - menu_h) // 2
    
    menu_clock = pygame.time.Clock()
    menu_font = pygame.font.Font(twcenbold_path, 14)

    # Component Hitboxes
    music_track_rect = pygame.Rect(menu_x + 40, menu_y + 80, 240, 14)
    emergency_track_rect = pygame.Rect(menu_x + 40, menu_y + 160, 240, 14)
    text_track_rect = pygame.Rect(menu_x + 40, menu_y + 240, 240, 14) 
    theme_box_rect = pygame.Rect(menu_x + 40, menu_y + 323, 46, 24)
    checkbox_rect = pygame.Rect(menu_x + 40, menu_y + 290, 20, 20)
    reset_btn_rect = pygame.Rect(menu_x + 40, menu_y + 365, 240, 35)
    confirm_yes_rect = pygame.Rect(menu_x + 40, menu_y + 365, 110, 35)
    confirm_no_rect = pygame.Rect(menu_x + 170, menu_y + 365, 110, 35)
    close_btn_rect = pygame.Rect(menu_x + 95, menu_y + 420, 130, 35)
    
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

                        elif theme_box_rect.collidepoint(event.pos):
                            trigger_click_sound()
                            toggle_theme()

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
        pygame.draw.rect(main_screen, BG_PANEL, menu_bg_rect, border_radius=8)
        
        border_outline_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)
        pygame.draw.rect(main_screen, border_outline_color, menu_bg_rect, width=2, border_radius=8)

        
        # Calculate dynamic text percentages 
        music_pct = int(background_music_volume * 100)
        emergency_pct = int(emergency_volume * 100)
        
        # Invert the display calculation so 0.0s delay prints as "100% speed"
        text_speed_pct = int((1.0 - (text_speed / 0.15)) * 100)
        
        # Generate Text Strings with Percentages appended
        title_txt = menu_font.render("SETTINGS MENU", True, TEXT_COLOR)
        music_txt = menu_font.render("Music Volume", True, TEXT_COLOR)
        emergency_txt = menu_font.render("Emergency Volume", True, TEXT_COLOR)
        text_speed_txt = menu_font.render("Typing Speed", True, TEXT_COLOR)
        mute_txt = menu_font.render("Mute All Sounds", True, TEXT_COLOR)
        theme_txt = menu_font.render("Light Mode", True, TEXT_COLOR)
        close_txt = menu_font.render("Apply Changes", True, TEXT_COLOR)

        main_screen.blit(title_txt, (menu_x + 95, menu_y + 15))
        main_screen.blit(music_txt, (menu_x + 40, menu_y + 55))
        main_screen.blit(emergency_txt, (menu_x + 40, menu_y + 135))
        main_screen.blit(text_speed_txt, (menu_x + 40, menu_y + 215))
        main_screen.blit(mute_txt, (menu_x + 75, menu_y + 290))
        main_screen.blit(theme_txt, (menu_x + 95, menu_y + 325))

                # Determine theme-dependent colors for tracking lanes and outer handle borders
        track_bg = (45, 45, 45) if current_theme == "DARK" else (210, 214, 219)
        handle_ring = (20, 20, 20) if current_theme == "DARK" else (240, 242, 245)
        button_default_bg = (50, 50, 50) if current_theme == "DARK" else (210, 215, 220)
        checkbox_bg = (51, 51, 51) if current_theme == "DARK" else (190, 195, 200)

        # --- RENDER MUSIC SLIDER ---
        pygame.draw.rect(main_screen, track_bg, music_track_rect, border_radius=4)
        h1_x = music_track_rect.x + int(background_music_volume * music_track_rect.width)
        
        music_color = (int(30 + (background_music_volume * 100)), int(80 + (background_music_volume * 175)), 40)
        if h1_x > music_track_rect.x:
            fill1_rect = pygame.Rect(music_track_rect.x, music_track_rect.y, h1_x - music_track_rect.x, music_track_rect.height)
            pygame.draw.rect(main_screen, music_color, fill1_rect, border_radius=4)
        
        pygame.draw.circle(main_screen, handle_ring, (h1_x, music_track_rect.centery), 11)
        pygame.draw.circle(main_screen, music_color, (h1_x, music_track_rect.centery), 9)
        
        # --- RENDER EMERGENCY SLIDER ---
        pygame.draw.rect(main_screen, track_bg, emergency_track_rect, border_radius=4)
        h2_x = emergency_track_rect.x + int(emergency_volume * emergency_track_rect.width)
        
        emergency_color = (int(200 + (emergency_volume * 55)), int(160 - (emergency_volume * 140)), 20)
        if h2_x > emergency_track_rect.x:
            fill2_rect = pygame.Rect(emergency_track_rect.x, emergency_track_rect.y, h2_x - emergency_track_rect.x, emergency_track_rect.height)
            pygame.draw.rect(main_screen, emergency_color, fill2_rect, border_radius=4)
            
        pygame.draw.circle(main_screen, handle_ring, (h2_x, emergency_track_rect.centery), 11)
        pygame.draw.circle(main_screen, emergency_color, (h2_x, emergency_track_rect.centery), 9)
        
        # --- RENDER TEXT SPEED SLIDER ---
        pygame.draw.rect(main_screen, track_bg, text_track_rect, border_radius=4)
        current_speed_pct = 1.0 - (text_speed / 0.15)
        h3_x = text_track_rect.x + int(current_speed_pct * text_track_rect.width)
        
        text_speed_color = (40, int(100 + (current_speed_pct * 140)), int(180 + (current_speed_pct * 75)))
        if h3_x > text_track_rect.x:
            fill3_rect = pygame.Rect(text_track_rect.x, text_track_rect.y, h3_x - text_track_rect.x, text_track_rect.height)
            pygame.draw.rect(main_screen, text_speed_color, fill3_rect, border_radius=4)
            
        pygame.draw.circle(main_screen, handle_ring, (h3_x, text_track_rect.centery), 11)
        pygame.draw.circle(main_screen, text_speed_color, (h3_x, text_track_rect.centery), 9)
        
        # --- RENDER MUTE CHECKBOX ---
        pygame.draw.rect(main_screen, checkbox_bg, checkbox_rect, border_radius=4)
        if is_muted:
            pygame.draw.rect(main_screen, (0, 210, 120), checkbox_rect.inflate(-8, -8), border_radius=2)

        # --- RENDER THEME SWITCH ---
        if current_theme == "LIGHT":
            pygame.draw.rect(main_screen, (0, 210, 120), theme_box_rect, border_radius=12)
            handle_x = theme_box_rect.right - 14
        else:
            pygame.draw.rect(main_screen, (64, 74, 86), theme_box_rect, border_radius=12)
            handle_x = theme_box_rect.left + 14

        pygame.draw.circle(main_screen, (255, 255, 255), (handle_x, theme_box_rect.centery), 9)

        # --- RENDER THE RESET CONFIGURATION INTERFACE ---
        if not show_reset_confirmation:
            btn_bg = (70, 30, 30) if current_theme == "DARK" else (245, 215, 215)
            btn_txt_color = (240, 160, 160) if current_theme == "DARK" else (180, 40, 40)
            pygame.draw.rect(main_screen, btn_bg, reset_btn_rect, border_radius=5)
            reset_txt = menu_font.render("Reset All Settings", True, btn_txt_color)
            text_x = reset_btn_rect.x + (reset_btn_rect.width - reset_txt.get_width()) // 2
            main_screen.blit(reset_txt, (text_x, reset_btn_rect.y + 10))
        else:
            yes_bg = (30, 60, 30) if current_theme == "DARK" else (215, 240, 215)
            yes_txt_color = (160, 240, 160) if current_theme == "DARK" else (30, 130, 30)
            no_bg = (70, 30, 30) if current_theme == "DARK" else (245, 215, 215)
            no_txt_color = (240, 160, 160) if current_theme == "DARK" else (180, 40, 40)
            
            pygame.draw.rect(main_screen, yes_bg, confirm_yes_rect, border_radius=5)
            pygame.draw.rect(main_screen, no_bg, confirm_no_rect, border_radius=5)
            
            yes_txt = menu_font.render("CONFIRM", True, yes_txt_color)
            no_txt = menu_font.render("CANCEL", True, no_txt_color)
            
            main_screen.blit(yes_txt, (confirm_yes_rect.x + 28, confirm_yes_rect.y + 10))
            main_screen.blit(no_txt, (confirm_no_rect.x + 32, confirm_no_rect.y + 10))
            
        # --- RENDER CLOSE PANEL ACTION BUTTON ---
        pygame.draw.rect(main_screen, button_default_bg, close_btn_rect, border_radius=5)
        text_x = close_btn_rect.x + (close_btn_rect.width - close_txt.get_width()) // 2
        text_y = close_btn_rect.y + (close_btn_rect.height - close_txt.get_height()) // 2
        main_screen.blit(close_txt, (text_x, text_y))
        
        pygame.display.flip()
        menu_clock.tick(60)
        
        await asyncio.sleep(0)
        
    is_game_paused = False

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
BG_MAIN = THEMES["DARK"]["BG_MAIN"]
BG_PANEL = THEMES["DARK"]["BG_PANEL"]
TEXT_COLOR = THEMES["DARK"]["TEXT_COLOR"]
COLOR_CYAN = THEMES["DARK"]["COLOR_CYAN"]  
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
WINDOW_WIDTH = screen_info.current_w
WINDOW_HEIGHT = screen_info.current_h

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("The Ares Horizon - Mission Control Terminal")

is_fullscreen = False
clock = pygame.time.Clock()

ui_font = pygame.font.Font(ocra_path, 16)
font_console = pygame.font.Font(twcen_path, 20)

close_btn_rect = pygame.Rect(WINDOW_WIDTH - 140, 15, 115, 30)

game_canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

shake_duration = 0
shake_intensity = 0
camera_offset_x = 0
camera_offset_y = 0

def trigger_screen_shake(intensity=8, duration=15):
    """Activates a camera rattle sequence across a specific frame timeline duration."""
    global shake_intensity, shake_duration
    # Only overwrite if the new shake is stronger than a shake currently active
    if intensity >= shake_intensity:
        shake_intensity = intensity
        shake_duration = duration

def apply_global_crt_filter(surface):
    """A highly optimized, hardware-friendly version of the CRT filter

    that utilizes a pre-rendered cache layer to eliminate CPU loop overhead.
    """
    global _cached_crt_overlay
    f_w = surface.get_width()
    f_h = surface.get_height()
    
    # 1. Generate the surface layer map only once on initial boot
    if _cached_crt_overlay is None or _cached_crt_overlay.get_size() != (f_w, f_h):
        # Create an alpha-transparent canvas surface matched to the display resolution
        _cached_crt_overlay = pygame.Surface((f_w, f_h), pygame.SRCALPHA)
        
        # Write the line matrices to the permanent cache layer memory storage block
        for y in range(0, f_h, 4):
            pygame.draw.line(_cached_crt_overlay, (0, 0, 0, 18), (0, y), (f_w, y), width=1)
            
    # 2. On all subsequent frames, perform a single fast blit operation (No loops executed)
    surface.blit(_cached_crt_overlay, (0, 0))

def draw_emergency_ambient_glow(surface):
    global is_emergency_active, _cached_emergency_glow
    if not is_emergency_active:
        return
    scr_w, scr_h = surface.get_size()
    time_ms = pygame.time.get_ticks()

    pulse_wave = (math.sin(time_ms * 0.0035) + 1.0) / 2.0
    breathing_curve = math.pow(pulse_wave, 2.0)
    
    # Increased alpha range for a brighter glow effect
    max_alpha = int(45 + (breathing_curve * 85))
    vignette_depth = 35

    if _cached_emergency_glow is None or _cached_emergency_glow.get_size() != (scr_w, scr_h):
        _cached_emergency_glow = pygame.Surface((scr_w, scr_h), pygame.SRCALPHA)
        for i in range(vignette_depth):
            factor = (vignette_depth - i) / float(vignette_depth)
            layer_alpha = max(1, int(120 * factor))
            glow_color = (200, 15, 15, layer_alpha)
            pygame.draw.rect(_cached_emergency_glow, glow_color, (i, i, scr_w - i*2, scr_h - i*2), width=1)

    glow_snapshot = _cached_emergency_glow.copy()
    glow_snapshot.set_alpha(max_alpha)

    old_clip = surface.get_clip()
    surface.set_clip(None)
    surface.blit(glow_snapshot, (0, 0))
    surface.set_clip(old_clip)

def draw_close_button(surface, mouse_pos):
    """Renders the close button dynamically pinned to the top right corner."""

    current_w = surface.get_width()
    
    close_btn_rect = pygame.Rect(current_w - 130, 15, 115, 30)
    
    if close_btn_rect.collidepoint(mouse_pos):
        button_color = (170, 40, 30)
        TEXT_COLOR = (255, 255, 255)
        glow_color = (230, 50, 40)
        glow_max_alpha = 55
        glow_radius = 8
    else:
        button_color = (70, 30, 30)
        TEXT_COLOR = (240, 160, 160)
        glow_color = (120, 40, 40)
        glow_max_alpha = 25
        glow_radius = 5

    for i in builtins.range(glow_radius, 0, -1):
        glow_surf = pygame.Surface((close_btn_rect.width + i*2, close_btn_rect.height + i*2), pygame.SRCALPHA)
        alpha = int(glow_max_alpha * (1.0 - (i / glow_radius)))
        
        pygame.draw.rect(glow_surf, (*glow_color, alpha), glow_surf.get_rect())
        surface.blit(glow_surf, (close_btn_rect.x - i, close_btn_rect.y - i))
        
    pygame.draw.rect(surface, button_color, close_btn_rect, border_radius=5)
    
    close_text = ui_font.render("CLOSE GAME", True, TEXT_COLOR)
    text_x = close_btn_rect.x + (close_btn_rect.width - close_text.get_width()) // 2
    text_y = close_btn_rect.y + (close_btn_rect.height - close_text.get_height()) // 2
    surface.blit(close_text, (text_x, text_y))
    
    return close_btn_rect

def draw_glowing_rect(surface, base_color, rect, glow_radius = 8, max_alpha = 45):
    """Draws a core interface shape surrounded by an ambient alpha-gradient bloom"""
    # Create one surface large enough for the full glow area instead of recreating it inside the loop
    glow_w = rect.width + glow_radius * 2
    glow_h = rect.height + glow_radius * 2
    glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
    
    for i in range(glow_radius, 0, -1):
        alpha = int(max_alpha * (1.0 - (i / glow_radius)))
        glow_color = (base_color[0], base_color[1], base_color[2], alpha)
        
        # Calculate dynamic local bounds centered on our single glow surface
        local_x = glow_radius - i
        local_y = glow_radius - i
        local_w = rect.width + i * 2
        local_h = rect.height + i * 2
        
        pygame.draw.rect(glow_surf, glow_color, (local_x, local_y, local_w, local_h), border_radius=4)
        
    surface.blit(glow_surf, (rect.x - glow_radius, rect.y - glow_radius))
    pygame.draw.rect(surface, base_color[:3], rect, border_radius=4)

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
        draw_glowing_rect(surface, current_safety_color, safety_fill, glow_radius=6, max_alpha=60)

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
    fill_width = 0
    if mission_budget > 0:
        fill_width = int(bar_width * (max(0, min(100, mission_budget)) / 100.0))
    budget_fill = pygame.Rect(budget_bar_x, 24, fill_width, bar_height)
    draw_glowing_rect(surface, COLOR_YELLOW, budget_fill, glow_radius=6, max_alpha=60)


    # ----------------------------------------------------
    # DRAW SCIENCE POINTS TEXT ELEMENT
    # ----------------------------------------------------
    points_str = f"SCIENCE POINTS: {science_points}"
    points_label = ui_font.render(points_str, True, COLOR_GREEN)
    surface.blit(points_label, (col3_center, 23))

def draw_settings_button(surface, mouse_pos):
    global current_theme, BG_PANEL
    current_h = surface.get_height()
    
    settings_btn_rect = pygame.Rect(15, current_h - 45, 115, 30)
    
    if settings_btn_rect.collidepoint(mouse_pos):
        button_color = (48, 54, 61) if current_theme == "DARK" else (210, 215, 220)
        glow_color = (126, 231, 135) if current_theme == "DARK" else (50, 180, 70)
        glow_max_alpha = 50           
        glow_radius = 8
    else:
        button_color = BG_PANEL
        glow_color = (46, 117, 52) if current_theme == "DARK" else (220, 230, 220)
        glow_max_alpha = 20           
        glow_radius = 4

    for i in range(glow_radius, 0, -1):
        glow_surf = pygame.Surface((settings_btn_rect.width + i*2, settings_btn_rect.height + i*2), pygame.SRCALPHA)
        alpha = int(glow_max_alpha * (1.0 - (i / glow_radius)))
        pygame.draw.rect(glow_surf, (*glow_color, alpha), glow_surf.get_rect())
        surface.blit(glow_surf, (settings_btn_rect.x - i, settings_btn_rect.y - i))
        
    border_outline_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)

    pygame.draw.rect(surface, button_color, settings_btn_rect, border_radius=4)
    pygame.draw.rect(surface, border_outline_color, settings_btn_rect, width=1, border_radius=4)
    
    text_color = (126, 231, 135) if current_theme == "DARK" else (30, 140, 50)
    settings_text = ui_font.render("SETTINGS", True, text_color)
    text_x = settings_btn_rect.x + (settings_btn_rect.width - settings_text.get_width()) // 2
    text_y = settings_btn_rect.y + (settings_btn_rect.height - settings_text.get_height()) // 2
    surface.blit(settings_text, (text_x, text_y))
    
    return settings_btn_rect

async def typewriter(text, color=(126, 231, 135), override_speed=None, bold=False):
    """Animates text into the terminal log list while responding instantly to text_speed changes."""
    global terminal_logs, text_speed, screen, clock, is_game_paused
    
    terminal_logs.append(["", color])
    line_index = len(terminal_logs) - 1
    max_chars_per_line = 300
    
    words = text.split(" ")
    current_line_buffer = []
    current_length = 0
    char_counter = 0
    
    for word in words:
        try:
            while is_game_paused:
                await asyncio.sleep(0.05)
                
            current_sleep_delay = override_speed if override_speed is not None else text_speed
            
            # Smart conditional lookahead bounds check
            if current_length + len(word) >= max_chars_per_line:
                terminal_logs[line_index][0] = " ".join(current_line_buffer).strip()
                terminal_logs.append(["", color])
                line_index = len(terminal_logs) - 1
                current_line_buffer.clear()
                current_length = 0
                
            current_line_buffer.append(word)
            current_length += len(word) + 1
            
            # Render updates systematically to reduce blit updates
            terminal_logs[line_index][0] = " ".join(current_line_buffer)
            char_counter += len(word)
            
            if current_sleep_delay < 0.016:
                if char_counter % 9 == 0:
                    await asyncio.sleep(0)
            else:
                await asyncio.sleep(current_sleep_delay)
        except Exception:
            return
            
    terminal_logs[line_index][0] = " ".join(current_line_buffer).strip()

def update_progress(text, add_newline=False, color=(88, 166, 255)):
    """Updates the terminal log in place, preserving colors."""
    global terminal_logs, cleaned_text
    
    if not terminal_logs:
        terminal_logs.append(["", color])
        
    # Overwrite text and preserve color tuple
    cleaned_text = text.replace("\u200a", "").strip()
    terminal_logs[-1] = [text, color]
    
    if add_newline:
        terminal_logs.append(["", color])

async def game_restart_screen():
    """Wipes the boot console clean and launches the initial narrative story text intro sequence."""
    global try_again_counter, current_stage, terminal_logs, is_boot_completed, is_emergency_active
    
    trigger_click_sound()

    is_boot_completed = True
    is_emergency_active = False
    
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

    is_emergency_active = True
    

    await typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", color=(219, 43, 31))
    await typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', color=(219, 43, 31))
    
    # 4. SWAP STATE TO NARRATIVE MODE: Once all text animations complete, show the Stage 1 choice buttons
    current_stage = "stage1"

async def run_boot_sequence():
    """Plays a clean, friendly, and non-overwhelming terminal welcome sequence."""
    global draw_boot_bar, boot_bar_pct
    trigger_click_sound()
    
    # Ensure progress bar state starts fresh
    #draw_boot_bar = False
    #boot_bar_pct = 0

    # --- STAGE 1: WELCOME BANNER ---
    #await typewriter("THE ARES HORIZON // TERMINAL BOOT SEQUENCE", color=COLOR_YELLOW, override_speed=0.005)
    #await asyncio.sleep(0.3)
    
    #dump_lines = [
    #    "  > USER PROFILE LOADED... WELCOME COMMANDER",
    #    "  > SECURE SATELLITE CONNECTION STATUS... [ONLINE]",
    #    "  > LIFE SUPPORT & CABIN SYSTEMS CHECK... [SAFE]"
    #]
    #for line in dump_lines:
    #    await typewriter(line, color=COLOR_CYAN, override_speed=0.002)
    #    trigger_click_sound()
    #    await asyncio.sleep(0.12)
        
    #await asyncio.sleep(0.3)

    # --- STAGE 2: SIMPLE SHIP HEALTH CHECK ---
    #await typewriter("\nPRE-FLIGHT HARDWARE INTEGRITY TEST:", color=COLOR_YELLOW, override_speed=0.005)
    #await asyncio.sleep(0.15)
    
    #systems = [
    #    ("STEERING GYROS", "CALIBRATED"),
    #    ("ENGINE THRUSTERS", "STABLE"),
    #    ("HEAT SHIELDS", "READY")
    #]
    #for name, status in systems:
    #    # Padded dots for columns alignment matrix
    #    dots = "." * (25 - len(name))
    #    msg = f"  >> {name} {dots} [{status}]"
    #    await typewriter(msg, color=COLOR_GREEN, override_speed=0.003)
    #    trigger_click_sound()
    #    await asyncio.sleep(0.15)

    #await asyncio.sleep(0.3)

    # --- STAGE 3: GAME LOAD INITIATION ---
    #await typewriter("\nSETTING UP FLIGHT DEEP MONITOR INTERFACE PANEL...", color=COLOR_YELLOW, override_speed=0.005)
    
    # 1. Turn on the graphics flag so main engine loop handles drawing the bar safely
    #draw_boot_bar = True
    
    # 2. Smoothly increment the tracker step-by-step using async delays
    #while boot_bar_pct < 100:
    #    boot_bar_pct += 1
        
    #    if boot_bar_pct % 15 == 0 or boot_bar_pct > 96:
    #        trigger_click_sound()
            
        # Realistic processing timeline variations
    #    if 42 <= boot_bar_pct <= 48:
    #        await asyncio.sleep(0.05)
    #    elif 88 <= boot_bar_pct <= 93:
    #        await asyncio.sleep(0.04)
    #    else:
    #        await asyncio.sleep(0.015)

    # 3. Hold at 100% briefly, then shut off the progress bar graphics container frame
    #await asyncio.sleep(0.4)
    #draw_boot_bar = False

    # --- STAGE 4: MAIN GAME TRANSITION ---
    #await typewriter("\nINTERFACE SETUP COMPLETED SUCCESSFULLY.", color=COLOR_CYAN, override_speed=0.005)
    #await typewriter("ALL MODULES ACTIVE. OPENING MAIN DASHBOARD...", color=COLOR_GREEN, override_speed=0.003)
    #trigger_click_sound()
    #await asyncio.sleep(1.0)
    
    # Advance to main screen
    await trigger_game_start()

async def trigger_game_start():
    """Wipes the boot console clean and initializes Chapter 1 narrative introduction sequence."""
    global current_stage, terminal_logs, is_boot_completed, is_emergency_active

    is_boot_completed = True
    is_emergency_active = False
    
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

    is_emergency_active = True
    

    await typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", color=(219, 43, 31))
    await typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', color=(219, 43, 31))
    
    # 4. SWAP STATE TO NARRATIVE MODE: Once all text animations finish, instantly show Stage 1 choice buttons
    current_stage = "stage1"

async def handle_choice1(choice):
    """Processes choice inputs for Stage 1, applying penalties and animating dynamic story outcomes."""
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs, is_emergency_active
    
    stop_all_sounds()
    trigger_click_sound()
    is_emergency_active = False

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

        is_emergency_active = True
        

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

        is_emergency_active = True
        

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
        loop = asyncio.get_event_loop()
        loop.call_soon(landing_minigame_difficulty)
        
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
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs, is_emergency_active
    
    stop_all_sounds()
    trigger_click_sound()

    is_emergency_active = False
    
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

        is_emergency_active = True
        

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

def initialize_space_starfield(count=60):
    """Bakes a randomized collection of coordinate points to map your background deep space depth."""
    global starfield_matrix
    starfield_matrix.clear()
    
    for _ in range(count):
        # Pick random placement across standard coordinate space layouts
        starfield_matrix.append({
            "x": random.uniform(0, 1.0),
            "y": random.uniform(-0.1, 1.1),
            "speed_multiplier": random.uniform(0.3, 1.4),
            "size": random.choice([1, 1, 2, 3])
        })

def update_and_draw_starfield(surface, current_altitude, left_bound, right_bound):
    """Updates background space vectors and renders parallax stars inside your central flight lane."""
    global starfield_matrix
    
    scr_w, scr_h = surface.get_size()
    
    for star in starfield_matrix:
        # Compute dynamic vertical positions using your game's current upward altitude progression
        scroll_offset = int(current_altitude * star["speed_multiplier"])
        pixel_y = int((star["y"] * scr_h) - scroll_offset) % scr_h
        
        lane_width = right_bound - left_bound
        pixel_x = int(left_bound + (star["x"] * lane_width))
        
        # Determine brightness based on layer depth
        brightness = int(100 + (star["speed_multiplier"] * 110))

        r_val = min(255, max(0, int(brightness)))
        g_val = min(255, max(0, int(brightness)))
        b_val = min(255, max(0, int(brightness * 1.15)))
        star_color = (r_val, g_val, b_val)
        
        # Draw a clean, hardware pixel block square matching console layout grid styles
        pygame.draw.rect(surface, star_color, (pixel_x, pixel_y, star["size"], star["size"]))

def spawn_thruster_spark(ship_x, ship_y, ship_width=50, ship_height=90):
    """Spawns an energetic engine exhaust spark at the base of the lander."""
    global thruster_particles
    # Calculate the exact center-bottom nozzle area of the spaceship
    engine_x = ship_x + (ship_width // 2)
    engine_y = ship_y + ship_height -8
    
    thruster_particles.append({
        "x": float(engine_x + random.randint(-18, 18)),
        "y": float(engine_y),
        "vx": random.uniform(-1.2, 1.2),
        "vy": random.uniform(4.0, 7.5),
        "life": 255
    })

def update_and_draw_thrusters(surface):
    """Updates active exhaust particle physics matrices and renders them to the screen canvas."""
    global thruster_particles
    
    # Fast in-place filtering loop to avoid list shifting overheads
    surviving_particles = []
    
    for p in thruster_particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 14
        
        if p["life"] <= 0:
            continue
            
        # Blit pre-cached structural surfaces instantly instead of instantiating new templates
        if p["life"] > 160:
            surface.blit(_HIGH_PLASMA, (int(p["x"]), int(p["y"])))
        elif p["life"] > 80:
            surface.blit(_LOW_PLASMA, (int(p["x"]), int(p["y"])))
        else:
            surface.blit(_SMOKE_SURF, (int(p["x"]), int(p["y"])))
            
        surviving_particles.append(p)
        
    thruster_particles = surviving_particles

def run_physics_frame(surface):
    """Updates game mechanics, handles infinite horizontal screen wrapping, 
    and generates a scrolling camera-relative vector terrain layout.
    """
    global altitude, ship_angle, ship_x, ship_y, game_running, current_difficulty
    global prep_timer_frames, current_stage, fall_velocity, ship_fuel, pad_start_x
    global move_left_active, move_right_active
    global victory_altitude, pad_screen_y, is_emergency_active
    global thruster_particles
    
    is_emergency_active = False
    if not game_running:
        return

    f_w = surface.get_width()
    f_h = surface.get_height()

    # Generate landing pad horizontal position if not initialized
    if pad_start_x < 0:
        pad_start_x = random.randint(int(f_w * 0.1), int(f_w * 0.8))

    # =========================================================================
    # HORIZONTAL MOVEMENT AND EDGE SCREEN WRAPPING
    # =========================================================================
    if move_left_active:
        ship_x -= 6.5
        ship_angle = min(28, ship_angle + 3.5)
    elif move_right_active:
        ship_x += 6.5
        ship_angle = max(-28, ship_angle - 3.5)
    else:
        ship_angle *= 0.82

    # Infinite wrap coordinates around screen borders
    if ship_x < 0: ship_x += f_w
    elif ship_x > f_w: ship_x -= f_w

    # Calculate horizontal camera center offset relative to the ship position
    camera_offset_x = ship_x - (f_w // 2)

    # =========================================================================
    # VERTICAL DESCENT AND THRUSTER INPUT PHYSICS
    # =========================================================================
    up_arrow_pressed = pygame.key.get_pressed()[pygame.K_UP]
    down_arrow_pressed = pygame.key.get_pressed()[pygame.K_DOWN]

    if current_difficulty == "EASY":
        gravity = 0.022
        engine_brake = 0.088
    elif current_difficulty == "MEDIUM":
        gravity = 0.038
        engine_brake = 0.078
    else:
        gravity = 0.052
        engine_brake = 0.065

    if prep_timer_frames > 0:
        altitude += 1.5
        fall_velocity = 1.2
        prep_timer_frames -= 1
    else:
        if ship_fuel > 0:
            if up_arrow_pressed:
                # Apply retro braking forces, consume fuel, and spawn exhaust particles
                fall_velocity = max(0.2, fall_velocity - engine_brake)
                ship_fuel = max(0.0, ship_fuel - 0.28)
                
                for _ in range(3):
                    engine_x = ship_x + random.randint(-8, 8)
                    engine_y = ship_y + 40
                    p_vx = -ship_angle * 0.1 + random.uniform(-1.5, 1.5)
                    thruster_particles.append({
                        "x": float(engine_x), "y": float(engine_y),
                        "vx": p_vx, "vy": random.uniform(5.0, 9.5),
                        "life": 255, "type": random.choice(["plasma", "fire", "smoke"])
                    })
            elif down_arrow_pressed:
                # Apply vertical downward overdrive thrust
                fall_velocity += gravity * 2.2
                ship_fuel = max(0.0, ship_fuel - 0.18)
            else:
                # Natural acceleration under gravity
                fall_velocity += gravity
        else:
            # Out of fuel: pure gravity fall
            fall_velocity += gravity

        altitude += fall_velocity

    # =========================================================================
    # MARTIAN TERRAIN SCROLL RENDERING
    # =========================================================================
    surface.fill((10, 12, 18))
    update_and_draw_starfield(surface, altitude, int(camera_offset_x * 0.25), f_w)

    pad_screen_y = victory_altitude - int(altitude)
    ground_level_y = pad_screen_y + 20
    pad_width = int(f_w * 0.12)
    scr_pad_x = pad_start_x - camera_offset_x
    target_center_x = pad_start_x + (pad_width // 2)

    if ground_level_y < f_h + 400:
        # Background mountain silhouette coordinates for depth simulation
        bg_points = [
            (-f_w, f_h), (-f_w, ground_level_y + 120),
            (pad_start_x * 0.5 - camera_offset_x, ground_level_y + 160),
            (scr_pad_x - 80, ground_level_y + 90),
            (scr_pad_x + pad_width // 2, ground_level_y + 100),
            (scr_pad_x + pad_width + 80, ground_level_y + 80),
            (f_w * 2, ground_level_y + 140), (f_w * 2, f_h)
        ]
        pygame.draw.polygon(surface, (24, 20, 26), bg_points)
        pygame.draw.lines(surface, (36, 30, 40), False, bg_points[1:-1], width=1)

        # Foreground terrain coordinates matching the randomized landing pad location
        terrain_points = [
            (-f_w, f_h), (-f_w, ground_level_y + 70),
            (pad_start_x * 0.5 - camera_offset_x, ground_level_y + 110),
            (scr_pad_x - 40, ground_level_y + 45),
            (scr_pad_x, ground_level_y),
            (scr_pad_x + pad_width, ground_level_y),
            (scr_pad_x + pad_width + 40, ground_level_y + 35),
            (scr_pad_x + pad_width + (f_w - pad_start_x) * 0.4 - camera_offset_x, ground_level_y + 95),
            (f_w * 0.95 - camera_offset_x, ground_level_y + 50),
            (f_w * 2, ground_level_y + 85), (f_w * 2, f_h)
        ]
        pygame.draw.polygon(surface, (18, 15, 22), terrain_points)
        
        # Render a structural topographic line grid underneath the mountainsides
        for i in range(1, len(terrain_points) - 2):
            p1_x, p1_y = terrain_points[i]
            p2_x, p2_y = terrain_points[i+1]
            pygame.draw.line(surface, (28, 22, 32), (p1_x, p1_y + 30), (p2_x, p2_y + 30), width=1)
            pygame.draw.line(surface, (22, 18, 26), (p1_x, p1_y + 60), (p2_x, p2_y + 60), width=1)

        # High-contrast edge surface outline stroke
        pygame.draw.lines(surface, (145, 65, 52), False, terrain_points[1:-1], width=3)

        # Glowing target platform system overlays
        pad_glow = pygame.Surface((pad_width, 15), pygame.SRCALPHA)
        pygame.draw.rect(pad_glow, (0, 255, 150, 25), (0, 0, pad_width, 15))
        surface.blit(pad_glow, (scr_pad_x, ground_level_y))
        
        pygame.draw.line(surface, (0, 255, 150), (scr_pad_x, ground_level_y), (scr_pad_x + pad_width, ground_level_y), width=5)
        pygame.draw.line(surface, (0, 255, 150), (scr_pad_x, ground_level_y), (scr_pad_x, ground_level_y - 12), width=2)
        pygame.draw.line(surface, (0, 255, 150), (scr_pad_x + pad_width, ground_level_y), (scr_pad_x + pad_width, ground_level_y - 12), width=2)

    # -------------------------------------------------------------------------
    # DYNAMIC RADAR TARGET TRACKING ARROW (Camera-Relative Screen Space Vector)
    # -------------------------------------------------------------------------
    time_ms = pygame.time.get_ticks()
    bobbing_offset = int(math.sin(time_ms * 0.008) * 6)
    arrow_center_y = ship_y - 110 + bobbing_offset

    target_y = ground_level_y if ground_level_y < f_h else f_h
    scr_target_center_x = scr_pad_x + (pad_width // 2)
    
    # Calculate shortest wrapping horizontal screen distance vector to target
    wrapped_dx = scr_target_center_x - ship_x
    if wrapped_dx > (f_w / 2): wrapped_dx -= f_w
    elif wrapped_dx < -(f_w / 2): wrapped_dx += f_w
        
    heading_angle = math.atan2(target_y - ship_y, wrapped_dx)
    
    # Pre-cache trigonometry vector multipliers to avoid costly real-time loops
    cos_val = math.cos(heading_angle)
    sin_val = math.sin(heading_angle)
    
    base_arrow_vertices = [(22, 0), (-2, -8), (2, 0), (-2, 8)]
    rotated_vertices = [
        (int(ship_x + (vx * cos_val - vy * sin_val)), int(arrow_center_y + (vx * sin_val + vy * cos_val)))
        for vx, vy in base_arrow_vertices
    ]
        
    is_aligned = abs(wrapped_dx) <= (pad_width // 2)
    arrow_color = (0, 255, 150) if is_aligned else (0, 200, 255)
    
    # Draw vertical radar lock guidance track markers when misaligned
    if not is_aligned:
        for dash_y in range(arrow_center_y + 20, f_h - 40, 22):
            pygame.draw.line(surface, (0, 200, 255, 30), (ship_x, dash_y), (ship_x, dash_y + 10), width=1)

    pygame.draw.polygon(surface, arrow_color, rotated_vertices)
    pygame.draw.polygon(surface, (255, 255, 255, 200), rotated_vertices, width=1)

    # =========================================================================
    # MULTI-TIER VEHICLE EXHAUST PARTICLE ARRAY MANAGEMENT
    # =========================================================================
    # Cap active particle buffer capacity to optimize rendering on low-end hardware
    if len(thruster_particles) > 35:
        thruster_particles = thruster_particles[-35:]

    for p in thruster_particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 12
        if p["life"] <= 0:
            thruster_particles.remove(p)
            continue
        
        radius = 2 if p["type"] == "plasma" else (3 if p["type"] == "fire" else 4)
        p_color = (0, 240, 255, p["life"]) if p["type"] == "plasma" else ((255, 120, 40, p["life"]) if p["type"] == "fire" else (60, 65, 80, int(p["life"] * 0.4)))
        
        pygame.draw.circle(surface, p_color, (int(p["x"]), int(p["y"])), radius)

    # Blit ship asset structure onto frame coordinate positions
    ship_rect = pygame.Rect(ship_x - 25, ship_y - 45, 50, 90)
    rotated_ship = pygame.transform.rotate(ship_surface, ship_angle)
    surface.blit(rotated_ship, rotated_ship.get_rect(center=ship_rect.center).topleft)

    # =========================================================================
    # GLASS-MORPHISM FLIGHT OVERLAY HUD PANEL & MECHANICAL SPEED TAPE GAUGE
    # =========================================================================
    hud_surf = pygame.Surface((f_w, 80), pygame.SRCALPHA)
    pygame.draw.rect(hud_surf, (14, 16, 24, 220), (0, 0, f_w, 75)) 
    pygame.draw.line(hud_surf, (40, 48, 68), (0, 75), (f_w, 75), width=2) 
    surface.blit(hud_surf, (0, 0))

    hud_font = pygame.font.Font(twcenbold_path, 13)
    display_v_speed = round(fall_velocity * 12.5, 1)
    is_fatal_speed = display_v_speed > 45.0
    
    speed_color = (255, 60, 60) if is_fatal_speed else (0, 255, 150)
    fuel_color = (255, 60, 60) if ship_fuel < 25.0 else (0, 200, 255)

    lbl_alt = hud_font.render(f"RADAR ALTITUDE: {int(max(0, victory_altitude - altitude))} M", True, (160, 175, 195))
    lbl_vel = hud_font.render(f"DESCENT VECTOR: -{display_v_speed} M/S", True, speed_color)
    lbl_fuel = hud_font.render(f"FUEL LEVEL: {int(ship_fuel)}%", True, fuel_color)
    
    surface.blit(lbl_alt, (45, 28))
    surface.blit(lbl_vel, (260, 28))
    surface.blit(lbl_fuel, (520, 28))

    # Progress width fill calculations for the visual speed bar gauge
    gauge_x, gauge_y = 740, 24
    pygame.draw.rect(surface, (25, 30, 45), (gauge_x, gauge_y, 140, 14), border_radius=3)
    fill_width = int(min(140, (display_v_speed / 90.0) * 140))
    pygame.draw.rect(surface, speed_color, (gauge_x, gauge_y, fill_width, 14), border_radius=3)
    
    # White structural threshold marker indicating fatal touchdown landing velocities
    safety_tick_x = gauge_x + int((45.0 / 90.0) * 140)
    pygame.draw.line(surface, (255, 255, 255), (safety_tick_x, gauge_y - 2), (safety_tick_x, gauge_y + 16), width=2)

    if prep_timer_frames > 0:
        seconds_left = (prep_timer_frames // 60) + 1
        count_font = pygame.font.Font(twcenbold_path, 40)
        count_surface = count_font.render(f"CALIBRATING SYSTEMS: {seconds_left}", True, (0, 200, 255))
        surface.blit(count_surface, (f_w // 2 - count_surface.get_width() // 2, (f_h // 2) - 140))

    # =========================================================================
    # TOUCHDOWN LOCATION ACCURACY AND SPEED CRITERIA METRICS
    # =========================================================================
    if ship_rect.bottom >= ground_level_y:
        ship_center_x = ship_rect.centerx + camera_offset_x
        pad_center_x = pad_start_x + (pad_width // 2)

        world_dx = pad_center_x - ship_center_x
        if world_dx > (f_w /2): world_dx -= f_w
        elif world_dx < -(f_w /2): world_dx += f_w

        is_on_pad = abs(world_dx) <= (pad_width // 2)

        game_running= False

        if is_on_pad and not is_fatal_speed:
            asyncio.create_task(landing_success())
        else:
            asyncio.create_task(space_ship_crash())

        return

def start_landing_simulation_canvas():
    """Initializes the physics engine properties and obstacles natively inside the global state machine."""
    global current_stage, altitude, velocity_y, ship_angle, game_running
    global ship_x, ship_y, obstacles, ship_surface, ship_mask, spike_left, spike_right, current_difficulty
    global move_left_active, move_right_active, prep_timer_frames, victory_altitude, is_emergency_active, ship_fuel, pad_start_x

    is_emergency_active = False
    
    # 1. Reset Physics Engine States
    altitude = 0.0
    velocity_y = 0.0
    ship_angle = 0.0
    game_running = True
    ship_fuel = 100.0
    pad_start_x = random.randint(int(screen.get_width() * 0.1), int(screen.get_width() * 0.8))
    thruster_particles.clear()
    
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

    initialize_space_starfield(count=65)

    # 7. ROUTE ENGINE STATE MACHINE: Advance instantly into active minigame loop context
    current_stage = "landing_simulation"

def draw_difficulty_menu(surface, mouse_pos):
    """Renders a responsive centered difficulty selection card using dynamic themes."""
    global current_difficulty, BG_PANEL, TEXT_COLOR, current_theme
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    # 1. Define container sizes
    card_w, card_h = 400, 400
    card_x = (scr_w - card_w) // 2
    card_y = (scr_h - card_h) // 2
    
    # 2. Draw base dialog box frame (DYNAMIC BG)
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
    pygame.draw.rect(surface, BG_PANEL, card_rect, border_radius=8)
    
    # Dynamic border color selection based on active theme
    border_outline_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)
    pygame.draw.rect(surface, border_outline_color, card_rect, width=2, border_radius=8)
    
    # 3. Draw Title Label Text Header (DYNAMIC TEXT)
    title_font = pygame.font.Font(twcenbold_path, 16)
    title_surf = title_font.render("CHOOSE DIFFICULTY", True, TEXT_COLOR)
    title_x = card_x + (card_w - title_surf.get_width()) // 2
    surface.blit(title_surf, (title_x, card_y + 35))
    
    # 4. Button Geometry Constants
    btn_w, btn_h = 220, 40
    btn_x = card_x + (card_w - btn_w) // 2
    easy_rect = pygame.Rect(btn_x, card_y + 110, btn_w, btn_h)
    med_rect = pygame.Rect(btn_x, card_y + 180, btn_w, btn_h)
    hard_rect = pygame.Rect(btn_x, card_y + 250, btn_w, btn_h)
    
    # Dynamic font text color matching button content clarity
    btn_text_color = (11, 14, 20) if current_theme == "DARK" else (255, 255, 255)
    
    # --- RENDER EASY MODE BUTTON (COLOR_CYAN Variations) ---
    is_easy_hover = easy_rect.collidepoint(mouse_pos)
    if current_theme == "DARK":
        easy_bg = (130, 200, 255) if is_easy_hover else (88, 166, 255)
    else:
        easy_bg = (0, 76, 153) if is_easy_hover else (0, 102, 204)
        
    pygame.draw.rect(surface, easy_bg, easy_rect, border_radius=4)
    easy_txt = font_console.render("EASY MODE", True, btn_text_color)
    surface.blit(easy_txt, (easy_rect.x + (btn_w - easy_txt.get_width()) // 2, easy_rect.y + (btn_h - easy_txt.get_height()) // 2))
    
    # --- RENDER MEDIUM MODE BUTTON (YELLOW Variations) ---
    is_med_hover = med_rect.collidepoint(mouse_pos)
    if current_theme == "DARK":
        med_bg = (255, 220, 120) if is_med_hover else (242, 204, 96)
    else:
        med_bg = (204, 153, 0) if is_med_hover else (219, 165, 32)
        
    pygame.draw.rect(surface, med_bg, med_rect, border_radius=4)
    med_txt = font_console.render("MEDIUM MODE", True, btn_text_color)
    surface.blit(med_txt, (med_rect.x + (btn_w - med_txt.get_width()) // 2, med_rect.y + (btn_h - med_txt.get_height()) // 2))
    
    # --- RENDER HARD MODE BUTTON (RED Variations) ---
    is_hard_hover = hard_rect.collidepoint(mouse_pos)
    if current_theme == "DARK":
        hard_bg = (255, 80, 70) if is_hard_hover else (219, 43, 31)
    else:
        hard_bg = (153, 15, 10) if is_hard_hover else (185, 25, 15)
        
    pygame.draw.rect(surface, hard_bg, hard_rect, border_radius=4)
    hard_txt = font_console.render("HARD MODE", True, btn_text_color)
    surface.blit(hard_txt, (hard_rect.x + (btn_w - hard_txt.get_width()) // 2, hard_rect.y + (btn_h - hard_txt.get_height()) // 2))

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
    trigger_screen_shake(intensity=16, duration=25)
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

    terminal_logs.clear()

    trigger_mission_success_sound()
    await typewriter("HEROIC VICTORY!!!", color=(126, 231, 135))
    await typewriter("You flew beautifully!! The crew and the ship are safe!!!", color=(126, 231, 135))
    await end_game_session()


async def end_game_session():
    """Prints a rolling metric evaluation log and routes users to choice screens."""
    global is_playing_standalone_minigame, current_stage, crew_safety, mission_budget, science_points, was_last_run_victory

    if crew_safety < 100:
        trigger_screen_shake(intensity=10, duration=25)

    await typewriter(f"\nFinal Session Summary-> Crew Safety: {crew_safety}% | Budget: {mission_budget}% | Science Points: {science_points}", color=(88, 166, 255)) # Cyan

    current_stage = "restart"

    await asyncio.sleep(0)


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
    global is_minigame_unlocked, current_stage, current_theme, BG_PANEL, TEXT_COLOR
    
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    # 1. RENDER RETRO MISSION TITLE HEADERS
    title_font = pygame.font.Font(twcenbold_path, 26)
    sub_font = pygame.font.Font(twcenbold_path, 13)
    
    title_surf = title_font.render("THE ARES HORIZON", True, (126, 231, 135))
    subtitle_surf = sub_font.render("MISSION CONTROL TERMINAL", True, TEXT_COLOR)
    
    surface.blit(title_surf, ((scr_w - title_surf.get_width()) // 2, scr_h // 2 - 160))
    surface.blit(subtitle_surf, ((scr_w - subtitle_surf.get_width()) // 2, scr_h // 2 - 120))
    
    # Initialize target rect parameters to return back to the mouse event listener loop
    btn_start_rect = None
    btn_story_rect = None
    btn_minigame_rect = None

    border_outline_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)

    # ----------------------------------------------------
    # BRANCH A: SINGLE BIG START BUTTON LAYOUT (LOCKED STATE)
    # ----------------------------------------------------
    if not is_minigame_unlocked:
        w, h = 240, 65
        btn_start_rect = pygame.Rect((scr_w - w) // 2, scr_h // 2 - 20, w, h)
        
        # Hover vs Idle highlighting check
        if btn_start_rect.collidepoint(mouse_pos):
            bg_color = (48, 54, 61) if current_theme == "DARK" else (210, 215, 220)
            glow_color = (0, 180, 216) if current_theme == "DARK" else (0, 130, 200)
            glow_max_alpha, glow_radius = 65, 12
        else:
            bg_color = BG_PANEL
            glow_color = (14, 116, 144) if current_theme == "DARK" else (200, 205, 210)
            glow_max_alpha, glow_radius = 25, 6

        for i in range(glow_radius, 0, -1):
            glow_surf = pygame.Surface((btn_start_rect.width + i*2, btn_start_rect.height + i*2), pygame.SRCALPHA)
            alpha = int(glow_max_alpha * (1.0 - (i / glow_radius)))
            pygame.draw.rect(glow_surf, (*glow_color, alpha), glow_surf.get_rect())
            surface.blit(glow_surf, (btn_start_rect.x - i, btn_start_rect.y - i))
        
        pygame.draw.rect(surface, bg_color, btn_start_rect, border_radius=4)
        pygame.draw.rect(surface, border_outline_color, btn_start_rect, width=1, border_radius=4)
        
        text_surf = ui_font.render("START GAME", True, TEXT_COLOR)
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

        if btn_story_rect.collidepoint(mouse_pos):
            bg_story = (48, 54, 61) if current_theme == "DARK" else (210, 215, 220)
            glow_story_color = (247, 127, 0) if current_theme == "DARK" else (210, 105, 0)
            g_story_alpha, g_story_radius = 55, 8
        else:
            bg_story = BG_PANEL
            glow_story_color = (130, 70, 10) if current_theme == "DARK" else (230, 220, 210)
            g_story_alpha, g_story_radius = 20, 4

        for i in range(g_story_radius, 0, -1):
            glow_surf = pygame.Surface((btn_story_rect.width + i*2, btn_story_rect.height + i*2), pygame.SRCALPHA)
            alpha = int(g_story_alpha * (1.0 - (i / g_story_radius)))
            pygame.draw.rect(glow_surf, (*glow_story_color, alpha), glow_surf.get_rect())
            surface.blit(glow_surf, (btn_story_rect.x - i, btn_story_rect.y - i))
        
        # Draw Play Story Button Frame
        pygame.draw.rect(surface, bg_story, btn_story_rect, border_radius=4)
        pygame.draw.rect(surface, border_outline_color, btn_story_rect, width=1, border_radius=4)
        
        story_txt = ui_font.render("PLAY STORY", True, TEXT_COLOR)
        surface.blit(story_txt, (btn_story_rect.x + (w - story_txt.get_width()) // 2, 
                                 btn_story_rect.y + (h - story_txt.get_height()) // 2))

        if btn_minigame_rect.collidepoint(mouse_pos):
            bg_mini = (48, 54, 61) if current_theme == "DARK" else (210, 215, 220)
            glow_mini_color = (0, 180, 216) if current_theme == "DARK" else (0, 130, 200)
            g_mini_alpha, g_mini_radius = 60, 10
        else:
            bg_mini = BG_PANEL
            glow_mini_color = (14, 116, 144) if current_theme == "DARK" else (210, 215, 220)
            g_mini_alpha, g_mini_radius = 20, 4
            
        for i in range(g_mini_radius, 0, -1):
            glow_surf = pygame.Surface((btn_minigame_rect.width + i*2, btn_minigame_rect.height + i*2), pygame.SRCALPHA)
            alpha = int(g_mini_alpha * (1.0 - (i / g_mini_radius)))
            pygame.draw.rect(glow_surf, (*glow_mini_color, alpha), glow_surf.get_rect())
            surface.blit(glow_surf, (btn_minigame_rect.x - i, btn_minigame_rect.y - i))
        
        # Draw Launch Minigame Button Frame
        pygame.draw.rect(surface, bg_mini, btn_minigame_rect, border_radius=4)
        pygame.draw.rect(surface, border_outline_color, btn_minigame_rect, width=1, border_radius=4)
        
        mini_color = (88, 166, 255) if current_theme == "DARK" else (0, 102, 204)
        mini_txt = ui_font.render("LAUNCH MINIGAME", True, mini_color)
        surface.blit(mini_txt, (btn_minigame_rect.x + (w - mini_txt.get_width()) // 2, 
                                btn_minigame_rect.y + (h - mini_txt.get_height()) // 2))

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
    global current_stage
    
    if current_stage not in STAGE_CONTENT:
        return None, None

    scr_w = surface.get_width()
    scr_h = surface.get_height()
    content = STAGE_CONTENT[current_stage]
    
    console_rect = pygame.Rect(25, 80, scr_w - 50, scr_h - 170)
    
    # Adapt choice title color based on current mode
    if current_stage == "restart":
        title_color = (219, 43, 31)
    else:
        title_color = (242, 204, 96) if current_theme == "DARK" else (204, 153, 0)
    
    padded_title = "".join([char + "\u200a" for char in content["title"]])
    title_surface = ui_font.render(padded_title, True, title_color)
    
    title_x = console_rect.x + (console_rect.width - title_surface.get_width()) // 2
    title_y = console_rect.bottom - 130 
    surface.blit(title_surface, (title_x, title_y))
    
    btn_w = console_rect.width - 40 
    btn_h = 35
    btn_x = console_rect.x + 20
    
    b1_rect = pygame.Rect(btn_x, title_y + 25, btn_w, btn_h) 
    b2_rect = pygame.Rect(btn_x, title_y + 65, btn_w, btn_h) 
    
    active_font = ui_font if current_stage == "restart" else font_console

    if current_stage == "restart":
        glow_base_color = (219, 43, 31)
    else:
        glow_base_color = (247, 127, 0)
    
    # --- RENDER CHOICE BUTTON 1 ---
    if b1_rect.collidepoint(mouse_pos):
        bg1 = (48, 54, 61) if current_theme == "DARK" else (210, 215, 220)
        fg1 = (255, 255, 255) if current_theme == "DARK" else (20, 24, 33)
        g1_max_alpha, g1_radius = 55, 8
    else:
        bg1 = BG_PANEL
        fg1 = content.get("color2", (245, 210, 110)) if current_theme == "DARK" else (140, 100, 10)
        g1_max_alpha, g1_radius = 20, 4

    glow1_w, glow1_h = b1_rect.width + g1_radius * 2, b1_rect.height + g1_radius * 2
    glow1_surf = pygame.Surface((glow1_w, glow1_h), pygame.SRCALPHA)
    for i in range(g1_radius, 0, -1):
        alpha = int(g1_max_alpha * (1.0 - (i / g1_radius)))
        pygame.draw.rect(glow1_surf, (*glow_base_color, alpha), (g1_radius - i, g1_radius - i, b1_rect.width + i * 2, b1_rect.height + i * 2), border_radius=4)
    surface.blit(glow1_surf, (b1_rect.x - g1_radius, b1_rect.y - g1_radius))
        
    pygame.draw.rect(surface, bg1, b1_rect, border_radius=4)
    pygame.draw.rect(surface, (48, 54, 61) if current_theme == "DARK" else (180, 185, 190), b1_rect, width=1, border_radius=4)
    padded_c1 = "".join([char + "\u200a" for char in content["c1"]])
    text1_surf = active_font.render(padded_c1, True, fg1)
    text1_x = b1_rect.x + (btn_w - text1_surf.get_width()) // 2
    text1_y = b1_rect.y + (btn_h - text1_surf.get_height()) // 2
    surface.blit(text1_surf, (text1_x, text1_y))

    # --- RENDER CHOICE BUTTON 2 ---
    if b2_rect.collidepoint(mouse_pos):
        bg2 = (48, 54, 61) if current_theme == "DARK" else (210, 215, 220)
        fg2 = (255, 255, 255) if current_theme == "DARK" else (20, 24, 33)
        g2_max_alpha, g2_radius = 55, 8
    else:
        bg2 = BG_PANEL
        fg2 = content.get("color2", (245, 210, 110)) if current_theme == "DARK" else (140, 100, 10)
        g2_max_alpha, g2_radius = 20, 4

    glow2_w, glow2_h = b2_rect.width + g2_radius * 2, b2_rect.height + g2_radius * 2
    glow2_surf = pygame.Surface((glow2_w, glow2_h), pygame.SRCALPHA)
    for i in range(g2_radius, 0, -1):
        alpha = int(g2_max_alpha * (1.0 - (i / g2_radius)))
        pygame.draw.rect(glow2_surf, (*glow_base_color, alpha), (g2_radius - i, g2_radius - i, b2_rect.width + i * 2, b2_rect.height + i * 2), border_radius=4)
    surface.blit(glow2_surf, (b2_rect.x - g2_radius, b2_rect.y - g2_radius))
    
    pygame.draw.rect(surface, bg2, b2_rect, border_radius=4)
    pygame.draw.rect(surface, (48, 54, 61) if current_theme == "DARK" else (180, 185, 190), b2_rect, width=1, border_radius=4)
    
    padded_c2 = "".join([char + "\u200a" for char in content["c2"]])
    text2_surf = active_font.render(padded_c2, True, fg2)
    text2_x = b2_rect.x + (btn_w - text2_surf.get_width()) // 2 
    text2_y = b2_rect.y + (btn_h - text2_surf.get_height()) // 2
    surface.blit(text2_surf, (text2_x, text2_y))
    
    return b1_rect, b2_rect

def draw_terminal_console(surface):
    global terminal_logs, current_stage, current_theme, BG_MAIN, BG_PANEL, TEXT_COLOR, COLOR_CYAN
    
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    console_rect = pygame.Rect(25, 80, scr_w - 50, scr_h - 170)
    glow_radius = 12

    # Fast single-surface glow allocation
    glow_w, glow_h = console_rect.width + glow_radius * 2, console_rect.height + glow_radius * 2
    glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
    
    for i in range(glow_radius, 0, -1):
        alpha = int(35 * (1.0 - (i / glow_radius)))
        glow_color = (*COLOR_CYAN, alpha)
        local_x = glow_radius - i
        local_y = glow_radius - i
        local_w = console_rect.width + i * 2
        local_h = console_rect.height + i * 2
        pygame.draw.rect(glow_surf, glow_color, (local_x, local_y, local_w, local_h), border_radius=4)
        
    surface.blit(glow_surf, (console_rect.x - glow_radius, console_rect.y - glow_radius))
        
    # Adaptive theme backgrounds and borders
    pygame.draw.rect(surface, BG_PANEL, console_rect, border_radius=4)          
    border_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)
    pygame.draw.rect(surface, border_color, console_rect, width=1, border_radius=4) 
    
    line_spacing = 30
    padding_x, padding_y = 15, 15
    
    usable_height = console_rect.height if current_stage not in STAGE_CONTENT else console_rect.height - 110
    
    max_visible_lines = (usable_height - (padding_y * 2)) // line_spacing
    visible_lines = terminal_logs[-max_visible_lines:] if len(terminal_logs) > max_visible_lines else terminal_logs
    
    start_y = console_rect.y + padding_y
    for i, line_data in enumerate(visible_lines):
        line_text = line_data[0]
        line_color = line_data[1]
        
        # Invert default white text when using light mode layout
        if current_theme == "LIGHT" and (line_color == (255, 255, 255) or line_color == (230, 237, 243)):
            line_color = TEXT_COLOR
            
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
                if event.key == pygame.K_F11:
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

        game_canvas.fill(BG_MAIN) 
    
        if current_stage not in ["welcome"]:
            draw_telemetry_dashboard(game_canvas)

        # STATE MAPPING ENGINES
        if current_stage == "welcome":
            draw_welcome_screen(game_canvas, mouse_pos)
            
        elif current_stage == "boot_sequence":
            draw_terminal_console(game_canvas)
            
            global draw_boot_bar, boot_bar_pct
            if draw_boot_bar:
                bar_width, bar_height = 450, 24
                bar_x = (game_canvas.get_width() - bar_width) // 2
                bar_y = game_canvas.get_height() - 220 
                pygame.draw.rect(game_canvas, (48, 54, 61), (bar_x, bar_y, bar_width, bar_height), width=1)
                pygame.draw.rect(game_canvas, (22, 27, 34), (bar_x + 3, bar_y + 3, bar_width - 6, bar_height - 6))
                current_fill_width = int((bar_width - 6) * (boot_bar_pct / 100.0))
                if current_fill_width > 0:
                    pygame.draw.rect(game_canvas, (0, 180, 216), (bar_x + 3, bar_y + 3, current_fill_width, bar_height - 6))
                pct_text = font_console.render(f"SYSTEM SETUP CONTEXT: {boot_bar_pct}%", True, (0, 180, 216))
                game_canvas.blit(pct_text, ((game_canvas.get_width() - pct_text.get_width()) // 2, bar_y + bar_height + 12))
            
        elif current_stage == "difficulty_menu":
            draw_difficulty_menu(game_canvas, mouse_pos)
            
        elif current_stage in STAGE_CONTENT:
            draw_terminal_console(game_canvas)
            draw_choice_interface(game_canvas, mouse_pos)
            
        elif current_stage == "landing_simulation":
            run_physics_frame(game_canvas)

        if current_stage != "landing_simulation":
            draw_settings_button(game_canvas, mouse_pos)
        
        draw_close_button(game_canvas, mouse_pos)

        screen.fill(BG_MAIN)

        global shake_duration, shake_intensity, camera_offset_x, camera_offset_y
        if shake_duration > 0:
            # Generate random pixel displacements bounded by the active intensity power scale
            camera_offset_x = random.randint(-shake_intensity, shake_intensity)
            camera_offset_y = random.randint(-shake_intensity, shake_intensity)
            shake_duration -= 1
            
            # Smoothly damp down the rumble intensity as the shake nears its timeline end
            if shake_duration == 0:
                shake_intensity = 0
                camera_offset_x = 0
                camera_offset_y = 0
        else:
            camera_offset_x = 0
            camera_offset_y = 0
        
        # Blit the entire finished game canvas onto the screen applying the shaking displacements
        screen.blit(game_canvas, (camera_offset_x, camera_offset_y))

        global is_emergency_active
        if is_emergency_active:
            draw_emergency_ambient_glow(screen)

        apply_global_crt_filter(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())