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

# Dark and light them
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

def handle_press(event):
    global key_states
    if event.keysym in key_states:
        key_states[event.keysym] = True

def handle_release(event):
    global key_states
    if event.keysym in key_states:
        key_states[event.keysym] = False

script_directory = os.path.dirname(os.path.abspath(__file__))

# 1. Volume Variables
is_muted = False
pre_mute_music_volume = 0.5
pre_mute_emergency_volume = 0.25
background_music_volume = 0.5
emergency_volume = 0.25 
settings_window = None
DEFAULT_TYPING_SPEED = 0.045

SETTING_FILE = os.path.join(script_directory, "settings.json")

# 2. JSON loader
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

                raw_music = data.get("background_music_volume", 0.5)
                if isinstance(raw_music, (list, tuple)):
                    background_music_volume = float(raw_music[0]) if raw_music else 0.5
                else:
                    background_music_volume = float(raw_music)
                
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

    background_music_volume = max(0.0, min(1.0, float(background_music_volume)))
    emergency_volume = max(0.0, min(1.0, float(emergency_volume)))
    pre_mute_music_volume = max(0.0, min(1.0, float(pre_mute_music_volume)))
    pre_mute_emergency_volume = max(0.0, min(1.0, float(pre_mute_emergency_volume)))
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

load_settings()

# 3. Audio Engine
try:
    pygame.mixer.init()
    pygame.mixer.set_reserved(6) 
except Exception:
    pass

warning_sound = False
space_warning_sound = False

bg_music_file = os.path.join(script_directory, "assets/sounds/Dream Sequence.ogg")
warning_file = os.path.join(script_directory, "assets/sounds/Warning.ogg")
pull_up_file = os.path.join(script_directory, "assets/sounds/Pull Up.ogg")
roger_that_file = os.path.join(script_directory, "assets/sounds/Roger That.ogg")
space_warning_file = os.path.join(script_directory, "assets/sounds/Spacecraft Warning.ogg")
click_file = os.path.join(script_directory, "assets/sounds/Click.ogg")
mission_success_file = os.path.join(script_directory, "assets/sounds/Mission Success.ogg")
mission_failed_file = os.path.join(script_directory, "assets/sounds/Mission Failed.ogg")
ocra_path = os.path.join(script_directory, "assets/fonts/ocra.TTF")
twcen_path = os.path.join(script_directory, "assets/fonts/twcen.TTF")
twcenbold_path = os.path.join(script_directory, "assets/fonts/twcenbold.TTF")

try:
    pygame.mixer.music.load(bg_music_file)
    pygame.mixer.music.set_volume(background_music_volume)
    pygame.mixer.music.play(-1)
except Exception:
    pass

# 4. Volume Mixer 
def set_mixer_volumes():
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
    
    # Apply theme
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
    global background_music_volume, emergency_volume, is_muted
    global text_speed, is_game_paused
    
    # Temporarily freeze all audio outputs while interacting with controls
    trigger_click_sound()
    is_game_paused = True

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
    
    is_dragging_music = False
    is_dragging_emergency = False
    is_dragging_text = False
    show_reset_confirmation = False
    
    menu_running = True

    while menu_running:
        mouse_pos = pygame.mouse.get_pos()  
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Mouse Click
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
                        
                        # Track dragging activity
                        if music_track_rect.inflate(0, 20).collidepoint(event.pos):
                            is_dragging_music = True
                        elif emergency_track_rect.inflate(0, 20).collidepoint(event.pos):
                            is_dragging_emergency = True
                        elif text_track_rect.inflate(0, 20).collidepoint(event.pos):
                            is_dragging_text = True
                    else:
                        # Process Confirmation Click Responses
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
            # If they are pressing the mouse over a track and weren't dragging yet, let them slide it
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

        menu_bg_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        pygame.draw.rect(main_screen, BG_PANEL, menu_bg_rect, border_radius=8)
        
        border_outline_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)
        pygame.draw.rect(main_screen, border_outline_color, menu_bg_rect, width=2, border_radius=8)

        # Calculate text percentages 
        music_pct = int(background_music_volume * 100)
        emergency_pct = int(emergency_volume * 100)
        
        text_speed_pct = int((1.0 - (text_speed / 0.15)) * 100)
        
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

        track_bg = (45, 45, 45) if current_theme == "DARK" else (210, 214, 219)
        handle_ring = (20, 20, 20) if current_theme == "DARK" else (240, 242, 245)
        button_default_bg = (50, 50, 50) if current_theme == "DARK" else (210, 215, 220)
        checkbox_bg = (51, 51, 51) if current_theme == "DARK" else (190, 195, 200)

        pygame.draw.rect(main_screen, track_bg, music_track_rect, border_radius=4)
        h1_x = music_track_rect.x + int(background_music_volume * music_track_rect.width)
        
        music_color = (int(30 + (background_music_volume * 100)), int(80 + (background_music_volume * 175)), 40)
        if h1_x > music_track_rect.x:
            fill1_rect = pygame.Rect(music_track_rect.x, music_track_rect.y, h1_x - music_track_rect.x, music_track_rect.height)
            pygame.draw.rect(main_screen, music_color, fill1_rect, border_radius=4)
        
        pygame.draw.circle(main_screen, handle_ring, (h1_x, music_track_rect.centery), 11)
        pygame.draw.circle(main_screen, music_color, (h1_x, music_track_rect.centery), 9)

        pygame.draw.rect(main_screen, track_bg, emergency_track_rect, border_radius=4)
        h2_x = emergency_track_rect.x + int(emergency_volume * emergency_track_rect.width)
        
        emergency_color = (int(200 + (emergency_volume * 55)), int(160 - (emergency_volume * 140)), 20)
        if h2_x > emergency_track_rect.x:
            fill2_rect = pygame.Rect(emergency_track_rect.x, emergency_track_rect.y, h2_x - emergency_track_rect.x, emergency_track_rect.height)
            pygame.draw.rect(main_screen, emergency_color, fill2_rect, border_radius=4)
            
        pygame.draw.circle(main_screen, handle_ring, (h2_x, emergency_track_rect.centery), 11)
        pygame.draw.circle(main_screen, emergency_color, (h2_x, emergency_track_rect.centery), 9)
        
        pygame.draw.rect(main_screen, track_bg, text_track_rect, border_radius=4)
        current_speed_pct = 1.0 - (text_speed / 0.15)
        h3_x = text_track_rect.x + int(current_speed_pct * text_track_rect.width)
        
        text_speed_color = (40, int(100 + (current_speed_pct * 140)), int(180 + (current_speed_pct * 75)))
        if h3_x > text_track_rect.x:
            fill3_rect = pygame.Rect(text_track_rect.x, text_track_rect.y, h3_x - text_track_rect.x, text_track_rect.height)
            pygame.draw.rect(main_screen, text_speed_color, fill3_rect, border_radius=4)
            
        pygame.draw.circle(main_screen, handle_ring, (h3_x, text_track_rect.centery), 11)
        pygame.draw.circle(main_screen, text_speed_color, (h3_x, text_track_rect.centery), 9)
        
        pygame.draw.rect(main_screen, checkbox_bg, checkbox_rect, border_radius=4)
        if is_muted:
            pygame.draw.rect(main_screen, (0, 210, 120), checkbox_rect.inflate(-8, -8), border_radius=2)

        if current_theme == "LIGHT":
            pygame.draw.rect(main_screen, (0, 210, 120), theme_box_rect, border_radius=12)
            handle_x = theme_box_rect.right - 14
        else:
            pygame.draw.rect(main_screen, (64, 74, 86), theme_box_rect, border_radius=12)
            handle_x = theme_box_rect.left + 14

        pygame.draw.circle(main_screen, (255, 255, 255), (handle_x, theme_box_rect.centery), 9)

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

        pygame.draw.rect(main_screen, button_default_bg, close_btn_rect, border_radius=5)
        text_x = close_btn_rect.x + (close_btn_rect.width - close_txt.get_width()) // 2
        text_y = close_btn_rect.y + (close_btn_rect.height - close_txt.get_height()) // 2
        main_screen.blit(close_txt, (text_x, text_y))
        
        pygame.display.flip()
        menu_clock.tick(60)
        
        await asyncio.sleep(0)
        
    is_game_paused = False

# ALL AUDIO FUNCTIONS
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


#Game Stats and Points
gamestart="yes"
crew_safety = 100
mission_budget = 100
science_points = 0
try_again_counter = 1

active_timers = []

pygame.font.init()
pygame.init()

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SCALED | pygame.RESIZABLE)
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

# Shakes the screen 
def trigger_screen_shake(intensity=8, duration=15):
    global shake_intensity, shake_duration
    # Only overwrite if the new shake is stronger than a shake currently
    if intensity >= shake_intensity:
        shake_intensity = intensity
        shake_duration = duration

# A CRT line applying function
def apply_global_crt_filter(surface):
    global _cached_crt_overlay
    f_w = surface.get_width()
    f_h = surface.get_height()
    
    if _cached_crt_overlay is None or _cached_crt_overlay.get_size() != (f_w, f_h):
        _cached_crt_overlay = pygame.Surface((f_w, f_h), pygame.SRCALPHA)
        
        for y in range(0, f_h, 4):
            pygame.draw.line(_cached_crt_overlay, (0, 0, 0, 18), (0, y), (f_w, y), width=1)

    surface.blit(_cached_crt_overlay, (0, 0))

# Draws the red glow when there is an emergency
def draw_emergency_ambient_glow(surface):
    global is_emergency_active, _cached_emergency_glow
    if not is_emergency_active:
        return
    scr_w, scr_h = surface.get_size()
    time_ms = pygame.time.get_ticks()

    pulse_wave = (math.sin(time_ms * 0.0035) + 1.0) / 2.0
    breathing_curve = math.pow(pulse_wave, 2.0)
    
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

# The close button on the top right
def draw_close_button(surface, mouse_pos):
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

# The glowing effect on the buttons and screen
def draw_glowing_rect(surface, base_color, rect, glow_radius = 8, max_alpha = 45):
    # Create one surface large enough for the full glow area
    glow_w = rect.width + glow_radius * 2
    glow_h = rect.height + glow_radius * 2
    glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
    
    for i in range(glow_radius, 0, -1):
        alpha = int(max_alpha * (1.0 - (i / glow_radius)))
        glow_color = (base_color[0], base_color[1], base_color[2], alpha)
        
        # Calculate local bounds centered on the single glow surface
        local_x = glow_radius - i
        local_y = glow_radius - i
        local_w = rect.width + i * 2
        local_h = rect.height + i * 2
        
        pygame.draw.rect(glow_surf, glow_color, (local_x, local_y, local_w, local_h), border_radius=4)
        
    surface.blit(glow_surf, (rect.x - glow_radius, rect.y - glow_radius))
    pygame.draw.rect(surface, base_color[:3], rect, border_radius=4)

# The progress bars to the top
def draw_telemetry_dashboard(surface):
    global crew_safety, mission_budget, science_points
    
    current_w = surface.get_width()
    panel_rect = pygame.Rect(0, 0, current_w, 60)
    pygame.draw.rect(surface, BG_PANEL, panel_rect)
    pygame.draw.rect(surface, (48, 54, 61), panel_rect, width=1)

    col1_center = current_w * 0.18
    col2_center = current_w * 0.45
    col3_center = current_w * 0.75
    
    bar_width = 180
    bar_height = 12
    
    safety_label = ui_font.render("CREW SAFETY STATUS:", True, TEXT_COLOR)
    surface.blit(safety_label, (col1_center - safety_label.get_width() - 10, 23))
    
    # Safety Progress Bar
    safety_track = pygame.Rect(col1_center, 24, bar_width, bar_height)
    pygame.draw.rect(surface, (11, 14, 20), safety_track, border_radius=4)
    
    # Safety Bar Color Shift
    current_safety_color = COLOR_RED if crew_safety <= 40 else COLOR_CYAN

    if crew_safety > 0:
        fill_width = int(bar_width * (max(0, min(100, crew_safety)) / 100.0))
        safety_fill = pygame.Rect(col1_center, 24, fill_width, bar_height)
        draw_glowing_rect(surface, current_safety_color, safety_fill, glow_radius=6, max_alpha=60)

    budget_label = ui_font.render("MISSION BUDGET:", True, TEXT_COLOR)
 
    # 1. Get the totat width of the text
    total_budget_width = budget_label.get_width() + 10 + bar_width
 
    # 2. Find the starting X position that puts the whole group in center
    budget_start_x = (current_w - total_budget_width) // 2
 
    # 3. Draw the text label
    surface.blit(budget_label, (budget_start_x, 23))
 
    # 4. Place the bar right after the text label and the gap
    budget_bar_x = budget_start_x + budget_label.get_width() + 10
 
    budget_track = pygame.Rect(budget_bar_x, 24, bar_width, bar_height)
    pygame.draw.rect(surface, (11, 14, 20), budget_track, border_radius=4)

    fill_width = 0
    if mission_budget > 0:
        fill_width = int(bar_width * (max(0, min(100, mission_budget)) / 100.0))
    budget_fill = pygame.Rect(budget_bar_x, 24, fill_width, bar_height)
    draw_glowing_rect(surface, COLOR_YELLOW, budget_fill, glow_radius=6, max_alpha=60)

    points_str = f"SCIENCE POINTS: {science_points}"
    points_label = ui_font.render(points_str, True, COLOR_GREEN)
    surface.blit(points_label, (col3_center, 23))

# The settings button in the bottom left
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

# The typing function, the typing seen on the screen
async def typewriter(text, color=(126, 231, 135), override_speed=None, bold=False):
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
            
            if current_length + len(word) >= max_chars_per_line:
                terminal_logs[line_index][0] = " ".join(current_line_buffer).strip()
                terminal_logs.append(["", color])
                line_index = len(terminal_logs) - 1
                current_line_buffer.clear()
                current_length = 0
                
            current_line_buffer.append(word)
            current_length += len(word) + 1
            
            # Render updates to reduce blit updates
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
    global terminal_logs, cleaned_text
    
    if not terminal_logs:
        terminal_logs.append(["", color])
        
    # Overwrite text and preserve color
    cleaned_text = text.replace("\u200a", "").strip()
    terminal_logs[-1] = [text, color]
    
    if add_newline:
        terminal_logs.append(["", color])

# The screen after you press try again
async def game_restart_screen():
    global try_again_counter, current_stage, terminal_logs, is_boot_completed, is_emergency_active
    
    trigger_click_sound()

    is_boot_completed = True
    is_emergency_active = False
    
    # 1. Clear the terminal log array completely to prepare a blank canvas
    terminal_logs.clear()
    
    current_stage = "boot_sequence"
    
    # 3. Print flow tracking log
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
    
    current_stage = "stage1"

# Loading screen, needs work
async def run_boot_sequence():
    global draw_boot_bar, boot_bar_pct
    trigger_click_sound()
# TODO ADD A LOADING SCREEN
# TODO ADD A LOADING SCREEN
# TODO ADD A LOADING SCREEN
# TODO ADD A LOADING SCREEN
# TODO ADD A LOADING SCREEN
    await trigger_game_start()

# Start of the story line
async def trigger_game_start():
    global current_stage, terminal_logs, is_boot_completed, is_emergency_active

    is_boot_completed = True
    is_emergency_active = False
    
    terminal_logs.clear()
    
    current_stage = "boot_sequence"

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
    
    current_stage = "stage1"

async def handle_choice1(choice):
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs, is_emergency_active
    
    stop_all_sounds()
    trigger_click_sound()
    is_emergency_active = False

    terminal_logs.clear()
    
    current_stage = "boot_sequence"

    # Launch now path
    if choice == "1":
        await typewriter("\nIGNITION! The rocket vibrates violently as it punches through the wind", color=(230, 237, 243))
        await typewriter("Minutes later you reach the edge of the atmosphere and enter orbit, but the stress caused by the wind resulted in an issue", color=(230, 237, 243))

        crew_safety -= 20
        mission_budget -= 10

        if crew_safety <= 0 or mission_budget <= 0:
            crew_safety = max(0, crew_safety)
            mission_budget = max(0, mission_budget)
            await typewriter("\nCRITICAL FAILURE: Mission parameters compromised! The system cannot continue.", color=(219, 43, 31), bold=True)
            trigger_mission_failed_sound()
            await end_game_session()
            return

        await typewriter("", color=(230, 237, 243))
        await typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color=(88, 166, 255)) 

        await typewriter("\nSTAGE-2: THE ORBITAL ANOMALY", color=(242, 204, 96), bold=True)
        trigger_spacecraft_warning_sound()

        is_emergency_active = True
        

        await typewriter("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!", color=(219, 43, 31))
        
        current_stage = "stage2a"

    # Delay launch path
    elif choice == "2":
        await typewriter("\nYou stand down on the launch. The crew exits the spacecraft", color=(230, 237, 243))
        await typewriter("Weeks later, you launch on a much longer and not as ideal route", color=(230, 237, 243))

        # Security safety, but burns resource
        mission_budget -= 40
        
        if crew_safety <= 0 or mission_budget <= 0:
            crew_safety = max(0, crew_safety)
            mission_budget = max(0, mission_budget)
            await typewriter("\nFINANCIAL BANKRUPTCY: Mission defunded by headquarters!", color=(219, 43, 31), bold=True)
            trigger_mission_failed_sound()
            await end_game_session()
            return

        await typewriter("", color=(230, 237, 243))
        await typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color=(88, 166, 255))

        await typewriter("\nSTAGE-2: LOST IN SPACE", color=(242, 204, 96), bold=True)
        trigger_warning_sound()

        is_emergency_active = True
        

        await typewriter("Deep in space, a massive radiation storm knocks down your primary navigation computer", color=(219, 43, 31))
        await typewriter("\nMark scrambles: Director, the main computer is dead, we are drifting!", color=(219, 43, 31))

        current_stage = "stage2b"

async def handle_choice2a(choice):
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs
    
    stop_all_sounds()
    trigger_click_sound()
    
    terminal_logs.clear()
    current_stage = "boot_sequence"

    # If chose to push engines
    if choice == "1":
        await typewriter("\nRisky Move, the engines fire hard. The pressure stabilizes just in time.", color=(230, 237, 243))
        await typewriter("Months pass in deep space, and the crew finally arrives at the Red Planet", color=(230, 237, 243))

        crew_safety -= 10
        science_points += 30

        if crew_safety <= 0 or mission_budget <= 0:
            crew_safety = max(0, crew_safety)
            mission_budget = max(0, mission_budget)
            await typewriter("\nCRITICAL STRUCTURAL FAILURE: Rocket hull compromised during orbital adjustment!", color=(219, 43, 31), bold=True)
            trigger_mission_failed_sound()
            await end_game_session()
            return
        
        # Call landing function if survived
        await display_mars_landing_sequence(stage_label=3)

    # If chose to abort
    elif choice == "2":
        await typewriter("The emergency escape system rips apart from the capsule", color=(230, 237, 243))
        await typewriter("The crew safely splash down in the Atlantic Ocean", color=(230, 237, 243))
        await typewriter("The mission is over but the crew lives", color=(230, 237, 243))
        
        mission_budget = 0
        await end_game_session()

# Last story line before the mini-game
async def display_mars_landing_sequence(stage_label=3):
    global crew_safety, mission_budget, science_points, current_stage
    
    await typewriter("", color=(230, 237, 243))
    await typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color=(88, 166, 255))

    await typewriter(f"\nSTAGE-{stage_label}: MARS LANDING", color=(242, 204, 96), bold=True)
    await typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates", color=(230, 237, 243))
    await typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", color=(219, 43, 31))

    current_stage = "stage3a"


async def handle_choice3a(choice):
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

    # If chose to trust the computer
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
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs, is_emergency_active
    
    stop_all_sounds()
    trigger_click_sound()

    is_emergency_active = False
    
    terminal_logs.clear()
    current_stage = "boot_sequence"

    # If chose to upload a patch
    if choice == "1":
        await typewriter("The patch works! The navigation is back up again", color=(230, 237, 243))
        await typewriter("However the reboot drained 60% of your spacecraft power reserves", color=(219, 43, 31))
        science_points += 20

        await typewriter("", color=(230, 237, 243))
        await typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color=(88, 166, 255)) # Cyan status
        
        await typewriter("\nSTAGE-3: LOW POWER", color=(242, 204, 96), bold=True) 
        trigger_spacecraft_warning_sound()

        is_emergency_active = True
        

        await typewriter("The crew arrive at Mars in a critically underpowered ship", color=(219, 43, 31))
        await typewriter("With the low power, you cannot run both the heaters and the landing thrusters", color=(219, 43, 31))
        
        current_stage = "stage3b"

    # If chose to let the crew work it out
    elif choice == "2":
        await typewriter("LOST ORBIT! The math is too complex with the light-lag delay", color=(219, 43, 31))
        await typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication", color=(219, 43, 31))
        trigger_mission_failed_sound()
        
        crew_safety = 0
        mission_budget = 0
        
        await end_game_session()


async def handle_choice3b(choice):
    global crew_safety, mission_budget, science_points, current_stage, terminal_logs
          
    stop_all_sounds()
    trigger_click_sound()
    
    terminal_logs.clear()
    current_stage = "boot_sequence"

    # Wait for charge
    if choice == "1":
        await typewriter("The solar sails catch enough sunlight to recharge", color=(126, 231, 135))
        science_points += 40
        
        await display_mars_landing_sequence(stage_label=4)

    # Do emergency burn
    elif choice == "2":
        await typewriter("\nBURN OUT! The extreme cold freezes the fuel valves during descent.", color=(219, 43, 31))
        await typewriter("The engines fail 100 meters up. The ship impacts the surface.", color=(219, 43, 31))
        trigger_mission_failed_sound()
        await typewriter("MISSION FAILED", color=(219, 43, 31), bold=True)
        
        crew_safety = 0
        
        await end_game_session()

#LANDING MINI GAME!! 

# The background stars
def space_starfield(count=60):
    global starfield_matrix
    starfield_matrix.clear()
    
    for _ in range(count):
        # Pick random placement
        starfield_matrix.append({
            "x": random.uniform(0, 1.0),
            "y": random.uniform(-0.1, 1.1),
            "speed_multiplier": random.uniform(0.3, 1.4),
            "size": random.choice([1, 1, 2, 3])
        })

def update_and_draw_starfield(surface, current_altitude, left_bound, right_bound):
    global starfield_matrix
    
    scr_w, scr_h = surface.get_size()
    
    for star in starfield_matrix:
        # Compute vertical positions
        scroll_offset = int(current_altitude * star["speed_multiplier"])
        pixel_y = int((star["y"] * scr_h) - scroll_offset) % scr_h
        
        lane_width = right_bound - left_bound
        pixel_x = int(left_bound + (star["x"] * lane_width))
        
        # Determine brightness based on depth
        brightness = int(100 + (star["speed_multiplier"] * 110))

        r_val = min(255, max(0, int(brightness)))
        g_val = min(255, max(0, int(brightness)))
        b_val = min(255, max(0, int(brightness * 1.15)))
        star_color = (r_val, g_val, b_val)

        pygame.draw.rect(surface, star_color, (pixel_x, pixel_y, star["size"], star["size"]))

# Thrust particles
def spawn_thruster_spark(ship_x, ship_y, ship_width=50, ship_height=90):
    global thruster_particles
    # Calculate the exact nozzle area of the spaceship
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
    global thruster_particles
    
    surviving_particles = []
    
    for p in thruster_particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 14
        
        if p["life"] <= 0:
            continue
            
        # Blit pre-cached surfaces
        if p["life"] > 160:
            surface.blit(_HIGH_PLASMA, (int(p["x"]), int(p["y"])))
        elif p["life"] > 80:
            surface.blit(_LOW_PLASMA, (int(p["x"]), int(p["y"])))
        else:
            surface.blit(_SMOKE_SURF, (int(p["x"]), int(p["y"])))
            
        surviving_particles.append(p)
        
    thruster_particles = surviving_particles

# The main physics engine
def run_physics_frame(surface):
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

    if pad_start_x < 0:
        pad_start_x = random.randint(int(f_w * 0.1), int(f_w * 0.8))

    # HORIZONTAL MOVEMENT AND EDGE SCREEN WRAPPING
    if move_left_active:
        ship_x -= 6.5
        ship_angle = min(28, ship_angle + 3.5)
    elif move_right_active:
        ship_x += 6.5
        ship_angle = max(-28, ship_angle - 3.5)
    else:
        ship_angle *= 0.82

    # Infinite wrap around screen borders
    if ship_x < 0: ship_x += f_w
    elif ship_x > f_w: ship_x -= f_w

    # Calculate horizontal camera center offset
    camera_offset_x = ship_x - (f_w // 2)

    # DESCENT AND THRUSTER PHYSICS
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
                # Apply braking forces, consume fuel, and spawn particles
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
                # Apply vertical thrust
                fall_velocity += gravity * 2.2
                ship_fuel = max(0.0, ship_fuel - 0.18)
            else:
                # Natural acceleration with gravity
                fall_velocity += gravity
        else:
            # Out of fuel
            fall_velocity += gravity

        altitude += fall_velocity

    # MARs TERRAIN RENDERING
    surface.fill((10, 12, 18))
    update_and_draw_starfield(surface, altitude, int(camera_offset_x * 0.25), f_w)

    pad_screen_y = victory_altitude - int(altitude)
    ground_level_y = pad_screen_y + 20
    pad_width = int(f_w * 0.12)
    scr_pad_x = pad_start_x - camera_offset_x
    target_center_x = pad_start_x + (pad_width // 2)

    if ground_level_y < f_h + 400:
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
        
        for i in range(1, len(terrain_points) - 2):
            p1_x, p1_y = terrain_points[i]
            p2_x, p2_y = terrain_points[i+1]
            pygame.draw.line(surface, (28, 22, 32), (p1_x, p1_y + 30), (p2_x, p2_y + 30), width=1)
            pygame.draw.line(surface, (22, 18, 26), (p1_x, p1_y + 60), (p2_x, p2_y + 60), width=1)

        pygame.draw.lines(surface, (145, 65, 52), False, terrain_points[1:-1], width=3)

        pad_glow = pygame.Surface((pad_width, 15), pygame.SRCALPHA)
        pygame.draw.rect(pad_glow, (0, 255, 150, 25), (0, 0, pad_width, 15))
        surface.blit(pad_glow, (scr_pad_x, ground_level_y))
        
        pygame.draw.line(surface, (0, 255, 150), (scr_pad_x, ground_level_y), (scr_pad_x + pad_width, ground_level_y), width=5)
        pygame.draw.line(surface, (0, 255, 150), (scr_pad_x, ground_level_y), (scr_pad_x, ground_level_y - 12), width=2)
        pygame.draw.line(surface, (0, 255, 150), (scr_pad_x + pad_width, ground_level_y), (scr_pad_x + pad_width, ground_level_y - 12), width=2)


    time_ms = pygame.time.get_ticks()
    bobbing_offset = int(math.sin(time_ms * 0.008) * 6)
    arrow_center_y = ship_y - 110 + bobbing_offset

    target_y = ground_level_y if ground_level_y < f_h else f_h
    scr_target_center_x = scr_pad_x + (pad_width // 2)
    
    # Calculate shortest horizontal screen distance distance to target
    wrapped_dx = scr_target_center_x - ship_x
    if wrapped_dx > (f_w / 2): wrapped_dx -= f_w
    elif wrapped_dx < -(f_w / 2): wrapped_dx += f_w
        
    heading_angle = math.atan2(target_y - ship_y, wrapped_dx)
    
    # Pre cache trig
    cos_val = math.cos(heading_angle)
    sin_val = math.sin(heading_angle)
    
    base_arrow_vertices = [(22, 0), (-2, -8), (2, 0), (-2, 8)]
    rotated_vertices = [
        (int(ship_x + (vx * cos_val - vy * sin_val)), int(arrow_center_y + (vx * sin_val + vy * cos_val)))
        for vx, vy in base_arrow_vertices
    ]
        
    is_aligned = abs(wrapped_dx) <= (pad_width // 2)
    arrow_color = (0, 255, 150) if is_aligned else (0, 200, 255)
    
    if not is_aligned:
        for dash_y in range(arrow_center_y + 20, f_h - 40, 22):
            pygame.draw.line(surface, (0, 200, 255, 30), (ship_x, dash_y), (ship_x, dash_y + 10), width=1)

    pygame.draw.polygon(surface, arrow_color, rotated_vertices)
    pygame.draw.polygon(surface, (255, 255, 255, 200), rotated_vertices, width=1)

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

    ship_rect = pygame.Rect(ship_x - 25, ship_y - 45, 50, 90)
    rotated_ship = pygame.transform.rotate(ship_surface, ship_angle)
    surface.blit(rotated_ship, rotated_ship.get_rect(center=ship_rect.center).topleft)

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

    gauge_x, gauge_y = 740, 24
    pygame.draw.rect(surface, (25, 30, 45), (gauge_x, gauge_y, 140, 14), border_radius=3)
    fill_width = int(min(140, (display_v_speed / 90.0) * 140))
    pygame.draw.rect(surface, speed_color, (gauge_x, gauge_y, fill_width, 14), border_radius=3)

    safety_tick_x = gauge_x + int((45.0 / 90.0) * 140)
    pygame.draw.line(surface, (255, 255, 255), (safety_tick_x, gauge_y - 2), (safety_tick_x, gauge_y + 16), width=2)

    if prep_timer_frames > 0:
        seconds_left = (prep_timer_frames // 60) + 1
        count_font = pygame.font.Font(twcenbold_path, 40)
        count_surface = count_font.render(f"CALIBRATING SYSTEMS: {seconds_left}", True, (0, 200, 255))
        surface.blit(count_surface, (f_w // 2 - count_surface.get_width() // 2, (f_h // 2) - 140))

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

# TODO Clean this up and remove no essential things
def start_landing_simulation_canvas():
    global current_stage, altitude, velocity_y, ship_angle, game_running
    global ship_x, ship_y, obstacles, ship_surface, ship_mask, spike_left, spike_right, current_difficulty
    global move_left_active, move_right_active, prep_timer_frames, victory_altitude, is_emergency_active, ship_fuel, pad_start_x

    is_emergency_active = False
    
    # 1. Reset Physics Engine
    altitude = 0.0
    velocity_y = 0.0
    ship_angle = 0.0
    game_running = True
    ship_fuel = 100.0
    pad_start_x = random.randint(int(screen.get_width() * 0.1), int(screen.get_width() * 0.8))
    thruster_particles.clear()
    
    # Start countdown
    prep_timer_frames = 180
    move_left_active = False
    move_right_active = False
    
    # 2. Pull dimensions 
    frame_w = screen.get_width()
    frame_h = screen.get_height()

    # 3. Load and scale up or down Spaceship
    try:
        raw_ship = pygame.image.load("assets/images/Spaceship.png").convert_alpha()
        ship_surface = pygame.transform.scale(raw_ship, (50, 90))
        ship_mask = pygame.mask.from_surface(ship_surface)
    except pygame.error:
        ship_surface = pygame.Surface((50, 90))
        ship_surface.fill((0, 240, 240)) 
        ship_mask = pygame.mask.from_surface(ship_surface)

    try:
        raw_spike = pygame.image.load("assets/images/Small Spike.png").convert_alpha()
        spike_left = pygame.transform.scale(raw_spike, (200, 60))
        spike_right = pygame.transform.flip(spike_left, True, False)
    except pygame.error:
        spike_left = pygame.Surface((200, 60))
        spike_left.fill((130, 45, 45))
        spike_right = pygame.Surface((200, 60))
        spike_right.fill((130, 45, 45))
    
    # 5. Ship Coordinates
    ship_x = frame_w // 2
    ship_y = frame_h // 2

    if current_difficulty == "EASY":
        small_w, medium_w, large_w = 140, 170, 200
        gap_spacing = 180  
    elif current_difficulty == "MEDIUM":
        small_w, medium_w, large_w = 170, 210, 240
        gap_spacing = 180  
    else: # HARD MODE
        small_w, medium_w, large_w = 220, 250, 270  
        gap_spacing = 220  
    
    # Generate obstacle using the randomized wall algorithm
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

    space_starfield(count=65)

    current_stage = "landing_simulation"

# The difficulty menu
def draw_difficulty_menu(surface, mouse_pos):
    global current_difficulty, BG_PANEL, TEXT_COLOR, current_theme
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    # 1. Define container sizes
    card_w, card_h = 400, 400
    card_x = (scr_w - card_w) // 2
    card_y = (scr_h - card_h) // 2
    
    # 2. Draw base box frame 
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
    pygame.draw.rect(surface, BG_PANEL, card_rect, border_radius=8)
    
    border_outline_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)
    pygame.draw.rect(surface, border_outline_color, card_rect, width=2, border_radius=8)
    
    title_font = pygame.font.Font(twcenbold_path, 16)
    title_surf = title_font.render("CHOOSE DIFFICULTY", True, TEXT_COLOR)
    title_x = card_x + (card_w - title_surf.get_width()) // 2
    surface.blit(title_surf, (title_x, card_y + 35))
    
    btn_w, btn_h = 220, 40
    btn_x = card_x + (card_w - btn_w) // 2
    easy_rect = pygame.Rect(btn_x, card_y + 110, btn_w, btn_h)
    med_rect = pygame.Rect(btn_x, card_y + 180, btn_w, btn_h)
    hard_rect = pygame.Rect(btn_x, card_y + 250, btn_w, btn_h)
    
    btn_text_color = (11, 14, 20) if current_theme == "DARK" else (255, 255, 255)
    
    is_easy_hover = easy_rect.collidepoint(mouse_pos)
    if current_theme == "DARK":
        easy_bg = (130, 200, 255) if is_easy_hover else (88, 166, 255)
    else:
        easy_bg = (0, 76, 153) if is_easy_hover else (0, 102, 204)
        
    pygame.draw.rect(surface, easy_bg, easy_rect, border_radius=4)
    easy_txt = font_console.render("EASY MODE", True, btn_text_color)
    surface.blit(easy_txt, (easy_rect.x + (btn_w - easy_txt.get_width()) // 2, easy_rect.y + (btn_h - easy_txt.get_height()) // 2))
    
    is_med_hover = med_rect.collidepoint(mouse_pos)
    if current_theme == "DARK":
        med_bg = (255, 220, 120) if is_med_hover else (242, 204, 96)
    else:
        med_bg = (204, 153, 0) if is_med_hover else (219, 165, 32)
        
    pygame.draw.rect(surface, med_bg, med_rect, border_radius=4)
    med_txt = font_console.render("MEDIUM MODE", True, btn_text_color)
    surface.blit(med_txt, (med_rect.x + (btn_w - med_txt.get_width()) // 2, med_rect.y + (btn_h - med_txt.get_height()) // 2))
    
    is_hard_hover = hard_rect.collidepoint(mouse_pos)
    if current_theme == "DARK":
        hard_bg = (255, 80, 70) if is_hard_hover else (219, 43, 31)
    else:
        hard_bg = (153, 15, 10) if is_hard_hover else (185, 25, 15)
        
    pygame.draw.rect(surface, hard_bg, hard_rect, border_radius=4)
    hard_txt = font_console.render("HARD MODE", True, btn_text_color)
    surface.blit(hard_txt, (hard_rect.x + (btn_w - hard_txt.get_width()) // 2, hard_rect.y + (btn_h - hard_txt.get_height()) // 2))

    return easy_rect, med_rect, hard_rect

# Call for the mini game difficulty mene
def landing_minigame_difficulty():
    global current_stage
    current_stage = "difficulty_menu"

# Track if the player won the game in their last run
was_last_run_victory = False
is_playing_standalone_minigame = False

# If you crashed the ship
async def space_ship_crash():
    global crew_safety, mission_budget
    trigger_screen_shake(intensity=16, duration=25)
    trigger_mission_failed_sound()
    
    await typewriter("CRASH: Space shuttle hull compromised!", color=(219, 43, 31))
    crew_safety = 0
    mission_budget = 0
    await end_game_session()

# If the landing is a success
async def landing_success():
    global is_minigame_unlocked, was_last_run_victory

    is_minigame_unlocked = True
    was_last_run_victory = True

    save_settings()
    trigger_mission_success_sound()

    terminal_logs.clear()

    trigger_mission_success_sound()
    await typewriter("HEROIC VICTORY!!!", color=(126, 231, 135))
    await typewriter("You flew beautifully!! The crew and the ship are safe!!!", color=(126, 231, 135))
    await end_game_session()

# End Session Function
async def end_game_session():
    global is_playing_standalone_minigame, current_stage, crew_safety, mission_budget, science_points, was_last_run_victory

    if crew_safety < 100:
        trigger_screen_shake(intensity=10, duration=25)

    await typewriter(f"\nFinal Session Summary-> Crew Safety: {crew_safety}% | Budget: {mission_budget}% | Science Points: {science_points}", color=(88, 166, 255)) # Cyan

    current_stage = "restart"

    await asyncio.sleep(0)


def reboot_mission():
    global crew_safety, mission_budget, science_points, try_again_counter, was_last_run_victory, current_stage
    
    # Reset back to defaults
    crew_safety = 100
    mission_budget = 100
    science_points = 0
    try_again_counter += 1

    current_stage = "welcome"

# Either launch the story or the mini game
def launch_story_mode():
    global is_playing_standalone_minigame
    is_playing_standalone_minigame = False 

    asyncio.create_task(game_restart_screen())

# Launch the mini game instead of the story mode
def launch_standalone_minigame():
    global is_playing_standalone_minigame
    is_playing_standalone_minigame = True  

    landing_minigame_difficulty()

# Draw the start screen
def draw_welcome_screen(surface, mouse_pos):
    global is_minigame_unlocked, current_stage, current_theme, BG_PANEL, TEXT_COLOR
    
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    title_font = pygame.font.Font(twcenbold_path, 26)
    sub_font = pygame.font.Font(twcenbold_path, 13)
    
    title_surf = title_font.render("THE ARES HORIZON", True, (126, 231, 135))
    subtitle_surf = sub_font.render("MISSION CONTROL TERMINAL", True, TEXT_COLOR)
    
    surface.blit(title_surf, ((scr_w - title_surf.get_width()) // 2, scr_h // 2 - 160))
    surface.blit(subtitle_surf, ((scr_w - subtitle_surf.get_width()) // 2, scr_h // 2 - 120))
    
    btn_start_rect = None
    btn_story_rect = None
    btn_minigame_rect = None

    border_outline_color = (48, 54, 61) if current_theme == "DARK" else (180, 185, 190)

    if not is_minigame_unlocked:
        w, h = 240, 65
        btn_start_rect = pygame.Rect((scr_w - w) // 2, scr_h // 2 - 20, w, h)
        
        # Hover or Idle check
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

    else:
        lbl_surf = ui_font.render("CHOOSE YOUR PATHWAY:", True, (242, 204, 96))
        surface.blit(lbl_surf, ((scr_w - lbl_surf.get_width()) // 2, scr_h // 2 - 50))
        
        w, h = 210, 55
        center_gap = 30
        
        btn_story_rect = pygame.Rect(scr_w // 2 - w - center_gap, scr_h // 2, w, h)
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
        
        pygame.draw.rect(surface, bg_mini, btn_minigame_rect, border_radius=4)
        pygame.draw.rect(surface, border_outline_color, btn_minigame_rect, width=1, border_radius=4)
        
        mini_color = (88, 166, 255) if current_theme == "DARK" else (0, 102, 204)
        mini_txt = ui_font.render("LAUNCH MINIGAME", True, mini_color)
        surface.blit(mini_txt, (btn_minigame_rect.x + (w - mini_txt.get_width()) // 2, 
                                btn_minigame_rect.y + (h - mini_txt.get_height()) // 2))

    return btn_start_rect, btn_story_rect, btn_minigame_rect

# Buttons and there lables
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

# Draw the buttons
def draw_choice_interface(surface, mouse_pos):
    global current_stage
    
    if current_stage not in STAGE_CONTENT:
        return None, None

    scr_w = surface.get_width()
    scr_h = surface.get_height()
    content = STAGE_CONTENT[current_stage]
    
    console_rect = pygame.Rect(25, 80, scr_w - 50, scr_h - 170)
    
    # title color based on current mode
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

# Draw the terminal where the typewriter types
def draw_terminal_console(surface):
    global terminal_logs, current_stage, current_theme, BG_MAIN, BG_PANEL, TEXT_COLOR, COLOR_CYAN
    
    scr_w = surface.get_width()
    scr_h = surface.get_height()
    
    console_rect = pygame.Rect(25, 80, scr_w - 50, scr_h - 170)
    glow_radius = 12

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
        
        if current_theme == "LIGHT" and (line_color == (255, 255, 255) or line_color == (230, 237, 243)):
            line_color = TEXT_COLOR
            
        text_surface = font_console.render(line_text, True, line_color)
        surface.blit(text_surface, (console_rect.x + padding_x, start_y + (i * line_spacing)))



close_btn_rect = pygame.Rect(820, 15, 115, 30)
mute_btn_rect  = pygame.Rect(695, 15, 115, 30)

# The main root
async def main():
    global screen, is_fullscreen, current_stage, move_left_active, move_right_active
    
    load_settings()
    set_mixer_volumes()
    
    running = True
    while running:
        # Track the position of the user mouse
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    is_fullscreen = not is_fullscreen
                    pygame.display.toggle_fullscreen()

                elif event.type == pygame.K_ESCAPE and is_fullscreen:
                    is_fullscreen = False
                    pygame.display.toggle_fullscreen()
                
                # Check keys if thelanding simulator is active
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

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    current_close_rect = pygame.Rect(screen.get_width() - 130, 15, 115, 30)
                    if current_close_rect.collidepoint(event.pos):
                        running = False
                        continue

                    if mute_btn_rect.collidepoint(event.pos):
                        toggle_mute()
                        continue

                    current_h = screen.get_height()
                    current_settings_rect = pygame.Rect(15, current_h - 45, 115, 30)
                    if current_settings_rect.collidepoint(event.pos):
                        await open_settings_menu(screen)
                        continue

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

        game_canvas.fill(BG_MAIN) 
    
        if current_stage not in ["welcome"]:
            draw_telemetry_dashboard(game_canvas)

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
            camera_offset_x = random.randint(-shake_intensity, shake_intensity)
            camera_offset_y = random.randint(-shake_intensity, shake_intensity)
            shake_duration -= 1
            
            # Decrease the intensity as the shake gets near the end
            if shake_duration == 0:
                shake_intensity = 0
                camera_offset_x = 0
                camera_offset_y = 0
        else:
            camera_offset_x = 0
            camera_offset_y = 0
        
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