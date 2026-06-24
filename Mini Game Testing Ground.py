import tkinter as tk
import random
import math
root = tk.Tk()

def landing_minigame_difficulty():
    
    # 2. Create the master full-screen backdrop frame
    menu_backdrop = tk.Frame(root, bg="#0d0d1a")
    menu_backdrop.pack(fill=tk.BOTH, expand=True)

    # 3. Create the tight inner container for your elements
    button_container = tk.Frame(menu_backdrop, bg="#0d0d1a")
    # Pin the exact middle of the container to the exact middle of the screen
    button_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    # 4. Add your centered title text
    title_label = tk.Label(
        button_container, 
        text="SELECT LANDING DIFFICULTY", 
        font=("Courier", 18, "bold"), 
        fg="white", 
        bg="#0d0d1a"
    )
    title_label.pack(pady=(0, 30))

    # 5. Define your inner click handler right inside the function.
    # This reads the difficulty string, sets your global variables, and shifts screens.
    def select_mode(mode):
        global current_gravity, current_pad_width, ship_fuel, max_safe_speed, max_safe_angle
        
        if mode == "EASY":
            current_gravity = 0.08
            current_pad_width = 120
            ship_fuel = 150
            max_safe_speed = 3.0
            max_safe_angle = 15
            
        elif mode == "MEDIUM":
            current_gravity = 0.15
            current_pad_width = 80
            ship_fuel = 100
            max_safe_speed = 2.0
            max_safe_angle = 10

        elif mode == "HARD":
            current_gravity = 0.25
            current_pad_width = 45
            ship_fuel = 75
            max_safe_speed = 1.2
            max_safe_angle = 5

        # Tear down the menu frame so the buttons vanish
        menu_backdrop.pack_forget()

    # 6. Build and pack the buttons vertically inside the centered container
    btn_easy = tk.Button(button_container, text="EASY MODE", font=("Courier", 12, "bold"), 
                         bg="#00ffcc", fg="black", command=lambda: select_mode("EASY"))
    btn_easy.pack(pady=10, fill=tk.X, ipady=5)

    btn_medium = tk.Button(button_container, text="MEDIUM MODE", font=("Courier", 12, "bold"), 
                           bg="#ffcc00", fg="black", command=lambda: select_mode("MEDIUM"))
    btn_medium.pack(pady=10, fill=tk.X, ipady=5)

    btn_hard = tk.Button(button_container, text="HARD MODE", font=("Courier", 12, "bold"), 
                         bg="#ff3333", fg="white", command=lambda: select_mode("HARD"))
    btn_hard.pack(pady=10, fill=tk.X, ipady=5)