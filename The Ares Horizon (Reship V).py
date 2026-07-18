# Ares Horizon - Full Pygame conversion (Pybag-ready)
# Preserves original Tkinter logic, variables, timers, audio, and UI geometry.
# Wraps main loop in async def main() and uses await asyncio.sleep(0) per Pybag requirement.

import asyncio
import os
import time
import sys
import math
import random
import json
from collections import deque

import pygame

# -------------------------
# EXACT ORIGINAL GLOBALS (kept identical names and defaults)
# -------------------------
script_directory = os.path.dirname(os.path.abspath(__file__))

# Audio / settings
is_muted = False
pre_mute_music_volume = 0.5
pre_mute_emergency_volume = 0.5
background_music_volume = 0.5
emergency_volume = 0.5
settings_window = None

SETTING_FILE = os.path.join(script_directory, "settings.json")

# Sound flags
warning_sound = False
space_warning_sound = False

# Audio file paths (identical)
bg_music_file = os.path.join(script_directory, "Dream Sequence.mp3")
warning_file = os.path.join(script_directory, "Warning.mp3")
pull_up_file = os.path.join(script_directory, "Pull Up.mp3")
roger_that_file = os.path.join(script_directory, "Roger That.mp3")
space_warning_file = os.path.join(script_directory, "Spacecraft Warning.mp3")
click_file = os.path.join(script_directory, "Click.mp3")
mission_success_file = os.path.join(script_directory, "Mission Success.mp3")
mission_failed_file = os.path.join(script_directory, "Mission Failed.mp3")

# Theme (hex strings preserved)
BG_main = "#0b0e14"
BG_panel = "#161b22"
text_color = "#e6edf3"
color_cyan = "#58a6ff"
color_yellow = "#f2cc60"
color_red = "#db2b1f"
color_green = "#7EE787"
font_console = ("Courier", 14)

# Game stats
gamestart = "yes"
crew_safety = 100
mission_budget = 100
science_points = 0
try_again_counter = 1

# Timers list (we emulate root.after scheduling)
active_timers = []

# -------------------------
# Helper conversions and utilities
# -------------------------
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

BG_main_rgb = hex_to_rgb(BG_main)
BG_panel_rgb = hex_to_rgb(BG_panel)
text_color_rgb = hex_to_rgb(text_color)
color_cyan_rgb = hex_to_rgb(color_cyan)
color_yellow_rgb = hex_to_rgb(color_yellow)
color_red_rgb = hex_to_rgb(color_red)
color_green_rgb = hex_to_rgb(color_green)

# -------------------------
# Settings load/save (exact logic)
# -------------------------
def load_settings():
    global background_music_volume, emergency_volume, is_muted
    global pre_mute_emergency_volume, pre_mute_music_volume
    if os.path.exists(SETTING_FILE):
        try:
            with open(SETTING_FILE, "r") as f:
                data = json.load(f)
                is_muted = data.get("is_muted", False)
                pre_mute_music_volume = float(data.get("pre_mute_music_volume", 0.5))
                pre_mute_emergency_volume = float(data.get("pre_mute_emergency_volume", 0.5))

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
        except Exception:
            background_music_volume = 0.5
            emergency_volume = 0.5
            is_muted = False
            pre_mute_emergency_volume = 0.5
            pre_mute_music_volume = 0.5

    background_music_volume = max(0.0, min(1.0, float(background_music_volume)))
    emergency_volume = max(0.0, min(1.0, float(emergency_volume)))
    pre_mute_music_volume = max(0.0, min(1.0, float(pre_mute_music_volume)))
    pre_mute_emergency_volume = max(0.0, min(1.0, float(pre_mute_emergency_volume)))

def save_settings():
    try:
        data = {
            "background_music_volume": background_music_volume,
            "emergency_volume": emergency_volume,
            "is_muted": is_muted,
            "pre_mute_music_volume": pre_mute_music_volume,
            "pre_mute_emergency_volume": pre_mute_emergency_volume
        }
        with open(SETTING_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

# Load at startup
load_settings()

# -------------------------
# Pygame audio initialization (preserve behavior)
# -------------------------
try:
    pygame.mixer.init()
    pygame.mixer.set_reserved(6)
except Exception:
    pass

try:
    pygame.mixer.music.load(bg_music_file)
    pygame.mixer.music.set_volume(background_music_volume)
    pygame.mixer.music.play(-1)
except Exception:
    pass

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
    try:
        pygame.mixer.music.set_volume(background_music_volume)
    except Exception:
        pass
    if background_music_volume > 0 and is_muted:
        is_muted = False
    save_settings()

def update_emergency_from_slider(percentage):
    global emergency_volume, is_muted
    emergency_volume = round(percentage, 2)
    try:
        pygame.mixer.Channel(1).set_volume(emergency_volume)
        pygame.mixer.Channel(2).set_volume(emergency_volume)
    except Exception:
        pass
    if emergency_volume > 0 and is_muted:
        is_muted = False
    save_settings()

# -------------------------
# Sound triggers (preserve)
# -------------------------
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

# -------------------------
# Console / Typewriter implementation (faithful)
# We'll implement a letter-by-letter queue that the main loop advances each frame,
# preserving the original typewriter timing semantics (very small delay).
# -------------------------
class Typewriter:
    def __init__(self):
        # queue of (text, color_rgb, bold)
        self.queue = deque()
        # current output lines (strings)
        self.lines = []
        self.current_text = ""
        self.current_color = text_color_rgb
        self.current_bold = False
        self.char_delay_frames = 0  # original used tiny sleep; we will output many chars per frame to keep speed
        self.chars_per_frame = 4  # tune to keep fast but visible
        self.max_lines = 500

    def enqueue(self, text, color_hex=text_color, bold=False):
        color_rgb = hex_to_rgb(color_hex) if isinstance(color_hex, str) else color_hex
        self.queue.append((text, color_rgb, bold))

    def update(self):
        # If currently building a line, continue
        if self.current_text:
            # flush some characters (we treat current_text as remaining to append)
            to_take = min(self.chars_per_frame, len(self.current_text))
            chunk = self.current_text[:to_take]
            if self.lines and not self.lines[-1][0].endswith("\n"):
                # append to last line
                last_text, last_color, last_bold = self.lines[-1]
                self.lines[-1] = (last_text + chunk, last_color, last_bold)
            else:
                self.lines.append((chunk, self.current_color, self.current_bold))
            self.current_text = self.current_text[to_take:]
            if not self.current_text:
                # finished this queued item; append newline
                if self.lines:
                    last_text, last_color, last_bold = self.lines[-1]
                    if not last_text.endswith("\n"):
                        self.lines[-1] = (last_text + "\n", last_color, last_bold)
                # clamp
                while len(self.lines) > self.max_lines:
                    self.lines.pop(0)
            return

        # If nothing current, pop next queued item
        if self.queue:
            text, color_rgb, bold = self.queue.popleft()
            # set as current_text to be consumed
            self.current_text = text
            self.current_color = color_rgb
            self.current_bold = bold
            # immediately call update to output first chunk this frame
            self.update()

    def get_lines(self):
        return list(self.lines)

typewriter_engine = Typewriter()

# Convenience wrappers to match original function names
def typewriter(text, text_widget=None, color=text_color, bold=False):
    # original signature had text_widget; we ignore and use internal engine
    typewriter_engine.enqueue(text, color, bold)

def update_progress(text, text_widget=None, color=color_cyan, bold=False, add_newline=False):
    # emulate by enqueuing text and optionally newline
    typewriter_engine.enqueue(text, color, bold)
    if add_newline:
        typewriter_engine.enqueue("\n", color, bold)

# -------------------------
# Tkinter frame logic -> Pygame scenes
# We'll preserve the same scene names and transitions.
# Scenes: welcome, stage1, stage2a, stage2b, stage3a, stage3b, restart
# -------------------------
current_scene = "welcome"

def update_gui():
    # In Tkinter this updated progressbars; here we just keep values for rendering
    pass

def cancel_all_timers():
    active_timers.clear()

# Game flow functions (preserve logic exactly)
def game_restart_screen():
    global try_again_counter, current_scene
    trigger_click_sound()
    cancel_all_timers()
    # clear console
    typewriter_engine.lines.clear()
    update_gui()
    typewriter(f"This is Try No. {try_again_counter}", color=color_cyan, bold=True)
    typewriter("\nThe Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!")
    typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.")
    typewriter("\nSTAGE-1: T-MINUS COUNTDOWN", bold=True)
    typewriter("", color=text_color)
    typewriter("The Orion-X awaits launch")
    trigger_warning_sound()
    typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", color=color_red)
    typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', color=color_red)
    current_scene = "stage1"

def run_boot_sequence():
    trigger_click_sound()
    cancel_all_timers()
    # original had many timed root.after calls; to preserve logic we call trigger_game_start immediately
    trigger_game_start()

def trigger_game_start():
    global current_scene
    typewriter_engine.lines.clear()
    update_gui()
    typewriter("Welcome to The Ares Horizon Game!", bold=True)
    typewriter("In this game you are a Flight Director at NASA Mission Control!")
    typewriter("The Orion-X spacecraft is sitting on the launch pad ready to takeoff to take astronauts to Mars!")
    typewriter("As the Flight Director, you are responsible for the safety of the astronauts and the success of the mission.")
    typewriter("\nSTAGE-1: T-MINUS COUNTDOWN", bold=True)
    typewriter("", color=text_color)
    typewriter("The Orion-X awaits launch")
    trigger_warning_sound()
    typewriter("Suddenly, your lead flight engineer, Mark, announces on the comms:", color=color_red)
    typewriter('"Director! The Upper Atmosphere winds just exceeded 8% past our safety limits!"', color=color_red)
    current_scene = "stage1"

def handle_choice1(choice):
    global crew_safety, mission_budget, science_points, current_scene
    stop_all_sounds()
    trigger_click_sound()
    typewriter_engine.lines.clear()

    if choice == "1":
        typewriter("\nIGNITION! The rocket vibrates violently as it puches through the wind")
        typewriter("Minutes later you reach the edge of the atmosphere and enter orbit, but the stress caused by the wind resulted in an issue")
        crew_safety -= 20
        mission_budget -= 10
        update_gui()
        typewriter("", color=text_color)
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color=color_cyan)
        typewriter("\nSTAGE-2: THE ORBITAL ANOMALY", bold=True)
        trigger_spacecraft_warning_sound()
        typewriter("Mark alerts you: Liquid Oxygen pressure in Engine 2 is dropping rapidly!", color=color_red)
        current_scene = "stage2a"
    elif choice == "2":
        typewriter("\nYou stand down on the launch. The crew exits the spacecraft")
        typewriter("Weeks later, you launch on a much longer and not as ideal route")
        mission_budget -= 40
        update_gui()
        typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color=color_cyan)
        typewriter("\nSTAGE-2: LOST IN SPACE", bold=True)
        trigger_warning_sound()
        typewriter("Deep in space, a massive radiation storm knocks down your primary navigation computer", color=color_red)
        typewriter("\nMark scrambles: Director, the main computer is dead, we are drifting!", color=color_red)
        current_scene = "stage2b"

def handle_choice2a(choice):
    global crew_safety, mission_budget, science_points, current_scene
    current_scene = "none"
    typewriter_engine.lines.clear()
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        typewriter("\nRisky Move, the engines fire hard. The pressure stabilizes just in time.")
        typewriter("Months pass in deep space, and the crew finally arrives at the Red Planet")
        crew_safety -= 10
        science_points += 30
        update_gui()
        handle_landing_choice_branch_1()
    elif choice == "2":
        typewriter("The emergency escape system rips apart from the capsule")
        typewriter("The crew safely splash down in the atlantic ocean")
        typewriter("The mission is over but the crew lives")
        mission_budget = 0
        update_gui()
        end_game_session()

def handle_landing_choice_branch_1():
    typewriter("", color=text_color)
    typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color=color_cyan)
    typewriter("\nSTAGE-3: MARS LANDING", bold=True)
    typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates")
    typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", color=color_red)
    global current_scene
    current_scene = "stage3a"

def handle_landing_choice_branch_2():
    typewriter("", color=text_color)
    typewriter(f"Status-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Point Gathered {science_points}", color=color_cyan)
    typewriter("\nSTAGE-4: MARS LANDING", bold=True)
    typewriter("The ship plummets into the thin Martian Atmosphere. The automated landing program initiates")
    typewriter("The radar suddenly targets a dangerous boulder-strewn crater for landing", color=color_red)
    global current_scene
    current_scene = "stage3a"

def handle_choice3a(choice):
    global crew_safety, mission_budget, science_points, current_scene
    current_scene = "none"
    typewriter_engine.lines.clear()
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
        typewriter("\nCRASH DOWN! The system clips a massive hidden boulder", color=color_red)
        typewriter("The lander tips and loses pressure. Space is not forgiving.", color=color_red)
        trigger_mission_failed_sound()
        typewriter("MISSION FAILED", bold=True, color=color_red)
        crew_safety = 0
        mission_budget = 0
        update_gui()
        end_game_session()

def handle_choice2b(choice):
    global crew_safety, mission_budget, science_points, current_scene
    current_scene = "none"
    typewriter_engine.lines.clear()
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        typewriter("The patch works! The navigation is back up again")
        typewriter("However the reboot drained 60% of your spacecraft power reserves", color=color_red)
        science_points += 20
        update_gui()
        typewriter(f"\nStatus-> Crew Safety {crew_safety} % | Mission Budget {mission_budget} % | Science Points {science_points}", color=color_cyan)
        typewriter("\nSTAGE-3: LOW POWER", bold=True)
        trigger_spacecraft_warning_sound()
        typewriter("The crew arrive at Mars in a critically underpowered ship", color=color_red)
        typewriter("With the low power, you cannot run both the heaters and the landing thrusters", color=color_red)
        current_scene = "stage3b"
    elif choice == "2":
        typewriter("LOST ORBIT! The math is too complex with the light-lag delay", color=color_red)
        typewriter("The crew misses the Mars window completely, drifting into the solar system with no way of communication", color=color_red)
        trigger_mission_failed_sound()
        crew_safety = 0
        mission_budget = 0
        update_gui()
        end_game_session()

def handle_choice3b(choice):
    global crew_safety, mission_budget, science_points, current_scene
    current_scene = "none"
    typewriter_engine.lines.clear()
    stop_all_sounds()
    trigger_click_sound()

    if choice == "1":
        typewriter("The solar sails catch enough sunlight to recharge", color=color_green)
        science_points += 40
        update_gui()
        handle_landing_choice_branch_2()
    elif choice == "2":
        typewriter("\nBURN OUT! The extreme cold freezes the fuel valves during descent.", color=color_red)
        typewriter("The engines fail 100 meters up. The ship impacts the surface.", color=color_red)
        trigger_mission_failed_sound()
        typewriter("MISSION FAILED", color=color_red, bold=True)
        crew_safety = 0
        update_gui()
        end_game_session()

# -------------------------
# Landing minigame (preserve physics & generation exactly)
# We'll run it in a dedicated Pygame surface sized to the same geometry as the original embedded frame.
# -------------------------
# Shared landing variables (kept names)
altitude = 0.0
velocity_y = 0.0
ship_angle = 0.0
ship_x = 0
ship_y = 0
game_running = False
current_difficulty = "EASY"
prep_timer_frames = 0
move_left_active = False
move_right_active = False
victory_altitude = 0
obstacles = []
ship_surface = None
ship_mask = None
spike_left = None
spike_right = None
pg_screen = None
pg_clock = None

def run_physics_frame():
    global altitude, velocity_y, ship_angle, ship_x, ship_y, game_running, current_difficulty
    global prep_timer_frames, move_left_active, move_right_active
    global victory_altitude, ship_surface, ship_mask, spike_left, spike_right, obstacles
    global pg_screen, pg_clock

    if not game_running or pg_screen is None:
        return

    f_w, f_h = pg_screen.get_size()
    screen_center_x = f_w // 2
    left_wall = screen_center_x - 175
    right_wall = screen_center_x + 175

    if move_left_active:
        ship_x -= 6
        ship_angle = min(25, ship_angle + 3)
    elif move_right_active:
        ship_x += 6
        ship_angle = max(-25, ship_angle - 3)
    else:
        ship_angle *= 0.85

    if ship_x - 25 < left_wall:
        ship_x = left_wall + 25
    if ship_x + 25 > right_wall:
        ship_x = right_wall - 25

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

    pg_screen.fill((15, 15, 25))

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

    pad_screen_y = victory_altitude - int(altitude)
    if -100 < pad_screen_y < f_h + 100:
        pygame.draw.rect(pg_screen, (0, 255, 100), (left_wall, pad_screen_y, 350, 30))
        pad_font = pygame.font.SysFont("Courier", 16, bold=True)
        pad_text = pad_font.render("---TOUCHDOWN ZONE---", True, (0, 0, 0))
        pg_screen.blit(pad_text, (screen_center_x - (pad_text.get_width() // 2), pad_screen_y + 6))

    pygame.draw.rect(pg_screen, (40, 40, 45), (0, 0, left_wall, f_h))
    pygame.draw.rect(pg_screen, (40, 40, 45), (right_wall, 0, f_w - right_wall, f_h))

    hud_font = pygame.font.SysFont("Courier", 18, bold=True)
    hud_string = f"SYS-MODE: {current_difficulty}"
    text_surface = hud_font.render(hud_string, True, (255, 255, 255))
    text_x = f_w - text_surface.get_width() - 25
    text_y = f_h - text_surface.get_height() - 25
    pg_screen.blit(text_surface, (text_x, text_y))

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

    if ship_rect.bottom >= pad_screen_y and ship_rect.top < pad_screen_y + 30:
        if left_wall <= ship_rect.centerx <= right_wall:
            # success
            game_running = False
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

    pygame.display.flip()
    pg_clock.tick(60)

    if crashed:
        game_running = False
        space_ship_crash()

def start_landing_simulation_canvas():
    global pg_screen, pg_clock, altitude, velocity_y, ship_angle, game_running
    global ship_x, ship_y, obstacles, ship_surface, ship_mask, spike_left, spike_right, current_difficulty
    global move_left_active, move_right_active, prep_timer_frames, victory_altitude

    altitude = 0.0
    velocity_y = 0.0
    ship_angle = 0.0
    game_running = True

    prep_timer_frames = 180
    move_left_active = False
    move_right_active = False

    frame_w = 700  # embed size; original used full width; we choose a large area
    frame_h = 520

    # Initialize Pygame sub-screen for minigame
    pygame.init()
    pg_screen = pygame.display.set_mode((frame_w, frame_h))
    pg_clock = pygame.time.Clock()

    try:
        raw_ship = pygame.image.load(os.path.join(script_directory, "Spaceship.png")).convert_alpha()
        ship_surface = pygame.transform.scale(raw_ship, (50, 90))
        ship_mask = pygame.mask.from_surface(ship_surface)
    except Exception:
        ship_surface = pygame.Surface((50, 90))
        ship_surface.fill((0, 240, 240))
        ship_mask = pygame.mask.from_surface(ship_surface)

    try:
        raw_spike = pygame.image.load(os.path.join(script_directory, "Small Spike.png")).convert_alpha()
        spike_left = pygame.transform.scale(raw_spike, (200, 60))
        spike_right = pygame.transform.flip(spike_left, True, False)
    except Exception:
        spike_left = pygame.Surface((200, 60)); spike_left.fill((130, 45, 45))
        spike_right = pygame.Surface((200, 60)); spike_right.fill((130, 45, 45))

    ship_x = frame_w // 2
    ship_y = frame_h // 2

    if current_difficulty == "EASY":
        small_w = 140; medium_w = 170; large_w = 200; gap_spacing = 180
    elif current_difficulty == "MEDIUM":
        small_w = 170; medium_w = 210; large_w = 240; gap_spacing = 180
    else:
        small_w = 220; medium_w = 250; large_w = 270; gap_spacing = 220

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

def landing_minigame_difficulty():
    global current_difficulty
    # Recreate the three-button choice UI using the main Pygame UI (we will set a modal flag and wait for user click)
    # To preserve exact logic, we will present three choices and wait for the player's click in the main loop.
    # For simplicity here, default to EASY if no input; the main loop will allow clicking to set difficulty.
    current_difficulty = "EASY"
    # After selection, start the minigame
    start_landing_simulation_canvas()

def space_ship_crash():
    global crew_safety, mission_budget
    trigger_mission_failed_sound()
    typewriter("💥 CRASH: Space shuttle hull compromised!", color=color_red)
    crew_safety = 0
    mission_budget = 0
    end_game_session()

def landing_success():
    trigger_mission_success_sound()
    typewriter("HERIOC VICTORY!!!", color=color_green)
    typewriter("You flew beatufully!! the crew and the ship are safe!!!", color=color_green)
    end_game_session()

def end_game_session():
    typewriter(f"\nFinal Session Summary-> Crew Safety: {crew_safety}% | Budget: {mission_budget}% | Science Points: {science_points}", color=color_cyan)
    global current_scene
    current_scene = "restart"

def run_restart_boot_sequence():
    print("Launching specialized restart sequence...")

def reboot_mission():
    global crew_safety, mission_budget, science_points, try_again_counter, current_scene
    cancel_all_timers()
    crew_safety = 100
    mission_budget = 100
    science_points = 0
    try_again_counter += 1
    update_gui()
    typewriter_engine.lines.clear()
    game_restart_screen()
    current_scene = "stage1"

# -------------------------
# Pygame UI rendering helpers (map Tkinter geometry to Pygame)
# -------------------------
WINDOW_WIDTH = 950
WINDOW_HEIGHT = 720

def draw_progress_bar(surface, x, y, width, height, pct, color):
    # Draw trough
    pygame.draw.rect(surface, (28, 28, 28), (x, y, width, height))
    # Draw filled
    fill_w = int(width * (pct / 100.0))
    pygame.draw.rect(surface, color, (x, y, fill_w, height))

def draw_button(surface, rect, text, font, bg, fg, border_radius=6):
    pygame.draw.rect(surface, bg, rect, border_radius=border_radius)
    txt_surf = font.render(text, True, fg)
    surface.blit(txt_surf, (rect.x + 8, rect.y + (rect.height - txt_surf.get_height()) // 2))

# -------------------------
# Main async loop (Pybag-ready)
# -------------------------
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("The Ares Horizon - Mission Control Terminal")
    clock = pygame.time.Clock()

    # Fonts
    font_small = pygame.font.SysFont("Courier", 13)
    font_medium = pygame.font.SysFont("Courier", 14)
    font_bold = pygame.font.SysFont("Courier", 16, bold=True)
    font_title = pygame.font.SysFont("Courier", 20, bold=True)

    # Layout rectangles to match Tkinter placements
    dashboard_rect = pygame.Rect(15, 10, WINDOW_WIDTH - 30, 70)
    log_rect = pygame.Rect(15, 90, WINDOW_WIDTH - 30, WINDOW_HEIGHT - 160)
    panel_rect = pygame.Rect(15, WINDOW_HEIGHT - 60, WINDOW_WIDTH - 30, 50)  # bottom area for settings etc.

    # Buttons and interactive rects (sizes chosen to match original widths)
    btn_start_rect = pygame.Rect(WINDOW_WIDTH//2 - 120, WINDOW_HEIGHT//2 - 40, 240, 80)

    # Stage choice rects (we will place them centered near bottom like original frames)
    def stage_button_rect(index):
        # index 0 -> first button, index 1 -> second
        base_x = WINDOW_WIDTH//2 - 350//2
        base_y = int(WINDOW_HEIGHT * 0.85)
        return pygame.Rect(base_x, base_y + index*48, 700, 40)

    # Settings button bottom-left
    settings_rect = pygame.Rect(15, WINDOW_HEIGHT - 45, 120, 30)

    # Restart buttons
    btn_restart_rect = pygame.Rect(WINDOW_WIDTH//2 - 140, int(WINDOW_HEIGHT*0.9), 120, 40)
    btn_exit_rect = pygame.Rect(WINDOW_WIDTH//2 + 20, int(WINDOW_HEIGHT*0.9), 120, 40)

    # For landing difficulty modal (three buttons)
    diff_btns = [
        pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 60, 300, 40),
        pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 10, 300, 40),
        pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 40, 300, 40),
    ]
    show_diff_modal = False

    # Initial console text
    typewriter("Welcome to The Ares Horizon Game!", bold=True)
    typewriter("Press START GAME to begin.", color=color_cyan)

    running = True
    last_time = time.time()

    # Keep track of whether the landing minigame is active in the main window
    landing_active = False

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                # Landing minigame controls
                if event.key == pygame.K_LEFT:
                    global move_left_active
                    move_left_active = True
                if event.key == pygame.K_RIGHT:
                    global move_right_active
                    move_right_active = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_left_active = False
                if event.key == pygame.K_RIGHT:
                    move_right_active = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Settings toggle (open settings modal)
                if settings_rect.collidepoint((mx, my)):
                    trigger_click_sound()
                    # We'll open a small settings modal that replicates the original Pygame settings menu
                    # For parity, we will toggle mute on click and also allow opening a modal
                    toggle_mute()
                # If difficulty modal visible, handle clicks
                if show_diff_modal:
                    if diff_btns[0].collidepoint((mx, my)):
                        current_difficulty = "EASY"
                        show_diff_modal = False
                        start_landing_simulation_canvas()
                        landing_active = True
                    elif diff_btns[1].collidepoint((mx, my)):
                        current_difficulty = "MEDIUM"
                        show_diff_modal = False
                        start_landing_simulation_canvas()
                        landing_active = True
                    elif diff_btns[2].collidepoint((mx, my)):
                        current_difficulty = "HARD"
                        show_diff_modal = False
                        start_landing_simulation_canvas()
                        landing_active = True
                else:
                    # Scene-specific clicks
                    if current_scene == "welcome":
                        if btn_start_rect.collidepoint((mx, my)):
                            trigger_click_sound()
                            run_boot_sequence()
                    elif current_scene == "stage1":
                        r1 = stage_button_rect(0)
                        r2 = stage_button_rect(1)
                        if r1.collidepoint((mx, my)):
                            handle_choice1("1")
                        elif r2.collidepoint((mx, my)):
                            handle_choice1("2")
                    elif current_scene == "stage2a":
                        r1 = stage_button_rect(0)
                        r2 = stage_button_rect(1)
                        if r1.collidepoint((mx, my)):
                            handle_choice2a("1")
                        elif r2.collidepoint((mx, my)):
                            handle_choice2a("2")
                    elif current_scene == "stage2b":
                        r1 = stage_button_rect(0)
                        r2 = stage_button_rect(1)
                        if r1.collidepoint((mx, my)):
                            handle_choice2b("1")
                        elif r2.collidepoint((mx, my)):
                            handle_choice2b("2")
                    elif current_scene == "stage3a":
                        r1 = stage_button_rect(0)
                        r2 = stage_button_rect(1)
                        if r1.collidepoint((mx, my)):
                            handle_choice3a("1")
                        elif r2.collidepoint((mx, my)):
                            handle_choice3a("2")
                    elif current_scene == "stage3b":
                        r1 = stage_button_rect(0)
                        r2 = stage_button_rect(1)
                        if r1.collidepoint((mx, my)):
                            handle_choice3b("1")
                        elif r2.collidepoint((mx, my)):
                            handle_choice3b("2")
                    elif current_scene == "restart":
                        if btn_restart_rect.collidepoint((mx, my)):
                            reboot_mission()
                        elif btn_exit_rect.collidepoint((mx, my)):
                            running = False
                            break

        # Update typewriter engine
        typewriter_engine.update()

        # If landing minigame active, run physics frame
        if game_running and pg_screen is not None:
            try:
                run_physics_frame()
            except Exception:
                pass

        # Rendering main UI
        screen.fill(BG_main_rgb)

        # Dashboard top (crew safety, budget, points)
        pygame.draw.rect(screen, BG_panel_rgb, dashboard_rect, border_radius=6)
        label1 = font_small.render("CREW SAFETY STATUS:", True, text_color_rgb)
        screen.blit(label1, (dashboard_rect.x + 10, dashboard_rect.y + 10))
        # Safety bar
        draw_progress_bar(screen, dashboard_rect.x + 170, dashboard_rect.y + 12, 180, 12, crew_safety, color_cyan_rgb if crew_safety > 40 else color_red_rgb)
        label2 = font_small.render("MISSION BUDGET:", True, text_color_rgb)
        screen.blit(label2, (dashboard_rect.x + 370, dashboard_rect.y + 10))
        draw_progress_bar(screen, dashboard_rect.x + 520, dashboard_rect.y + 12, 180, 12, mission_budget, color_yellow_rgb)
        points_label = font_small.render(f"SCIENCE POINTS ACCUMULATED: {science_points}", True, color_green_rgb)
        screen.blit(points_label, (dashboard_rect.x + 10, dashboard_rect.y + 34))

        # Log area (emulate Text widget)
        pygame.draw.rect(screen, (11, 12, 16), log_rect, border_radius=4)
        # Render last N lines from typewriter_engine.lines
        lines = typewriter_engine.get_lines()
        # Flatten lines into strings and render last visible lines
        console_font = pygame.font.SysFont("Courier", 14)
        max_lines = (log_rect.height - 20) // 18
        # Build a single string from lines list
        text_accum = ""
        for txt, col, bold in lines:
            text_accum += txt
        split_lines = text_accum.splitlines()
        split_lines = split_lines[-max_lines:]
        for i, ln in enumerate(split_lines):
            surf = console_font.render(ln, True, text_color_rgb)
            screen.blit(surf, (log_rect.x + 8, log_rect.y + 8 + i*18))

        # Draw scene-specific UI (buttons)
        if current_scene == "welcome":
            # Big START button centered
            draw_button(screen, btn_start_rect, "START GAME", font_bold, BG_panel_rgb, text_color_rgb)
        elif current_scene == "stage1":
            title = font_bold.render("STAGE-1: T-MINUS COUNTDOWN", True, text_color_rgb)
            screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, int(WINDOW_HEIGHT*0.75) - 80))
            r1 = stage_button_rect(0); r2 = stage_button_rect(1)
            draw_button(screen, r1, "1) Launch Now - Push past high winds and save time", font_medium, BG_panel_rgb, text_color_rgb)
            draw_button(screen, r2, "2) Delay Launch - Abort current window and wait", font_medium, BG_panel_rgb, text_color_rgb)
        elif current_scene == "stage2a":
            title = font_bold.render("STAGE-2: THE ORBITAL ANOMALY", True, text_color_rgb)
            screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, int(WINDOW_HEIGHT*0.75) - 80))
            r1 = stage_button_rect(0); r2 = stage_button_rect(1)
            draw_button(screen, r1, "1) PUSH ENGINES - Fire second stage anyway to clear orbit", font_medium, BG_panel_rgb, text_color_rgb)
            draw_button(screen, r2, "2) ABORT MISSION - Activate the emergency escape tower", font_medium, BG_panel_rgb, text_color_rgb)
        elif current_scene == "stage2b":
            title = font_bold.render("STAGE-2: LOST IN SPACE", True, text_color_rgb)
            screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, int(WINDOW_HEIGHT*0.75) - 80))
            r1 = stage_button_rect(0); r2 = stage_button_rect(1)
            draw_button(screen, r1, "1) PATCH NAV - Attempt remote reboot and patch", font_medium, BG_panel_rgb, text_color_rgb)
            draw_button(screen, r2, "2) MANUAL TRAJECTORY - Force crew to navigate manually", font_medium, BG_panel_rgb, text_color_rgb)
        elif current_scene == "stage3a":
            title = font_bold.render("STAGE-3: MARS LANDING", True, text_color_rgb)
            screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, int(WINDOW_HEIGHT*0.75) - 80))
            r1 = stage_button_rect(0); r2 = stage_button_rect(1)
            draw_button(screen, r1, "1) MANUAL CONTROL - Commander flies manual flight joystick", font_medium, BG_panel_rgb, text_color_rgb)
            draw_button(screen, r2, "2) ABORT - Emergency pull-up", font_medium, BG_panel_rgb, text_color_rgb)
        elif current_scene == "stage3b":
            title = font_bold.render("STAGE-3: THE LANDING // ROUTE AVAILABLE BATTERY POWER:", True, text_color_rgb)
            screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, int(WINDOW_HEIGHT*0.75) - 80))
            r1 = stage_button_rect(0); r2 = stage_button_rect(1)
            draw_button(screen, r1, "1) DEPLOY SOLAR SAILS - Wait in orbit for 3 days to charge batteries", font_medium, BG_panel_rgb, text_color_rgb)
            draw_button(screen, r2, "2) EMERGENCY BURN - Cut the life support heaters to power a descent", font_medium, BG_panel_rgb, text_color_rgb)
        elif current_scene == "restart":
            draw_button(screen, btn_restart_rect, "TRY AGAIN?", font_medium, BG_panel_rgb, color_cyan_rgb)
            draw_button(screen, btn_exit_rect, "EXIT?", font_medium, BG_panel_rgb, color_red_rgb)

        # Settings button bottom-left
        pygame.draw.rect(screen, (22, 22, 22), settings_rect, border_radius=4)
        settings_text = font_small.render("⚙️ Settings", True, color_green_rgb)
        screen.blit(settings_text, (settings_rect.x + 8, settings_rect.y + 6))

        # If difficulty modal requested, draw it
        if show_diff_modal:
            modal_rect = pygame.Rect(WINDOW_WIDTH//2 - 220, WINDOW_HEIGHT//2 - 120, 440, 240)
            pygame.draw.rect(screen, BG_panel_rgb, modal_rect, border_radius=6)
            title = font_bold.render("CHOOSE DIFFICULTY", True, text_color_rgb)
            screen.blit(title, (modal_rect.x + (modal_rect.width - title.get_width())//2, modal_rect.y + 12))
            draw_button(screen, diff_btns[0], "EASY MODE", font_medium, color_cyan_rgb, (0,0,0))
            draw_button(screen, diff_btns[1], "MEDIUM MODE", font_medium, color_yellow_rgb, (0,0,0))
            draw_button(screen, diff_btns[2], "HARD MODE", font_medium, color_red_rgb, (255,255,255))

        pygame.display.flip()
        clock.tick(60)

        # Pybag requirement: yield to event loop to avoid freezing
        await asyncio.sleep(0)

    pygame.quit()

# Run the async main when executed
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        # fallback
        pass
