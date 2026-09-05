# The Ares Horizon-Adventure Game
A choice python adventure game where the player is a Flight Director at NASA tyring to get the spaceship to Mars
<img width="1918" height="983" alt="Image" src="https://github.com/user-attachments/assets/37832fe0-860f-4aac-8f54-0d5724ae079d" />

## How to Play

### Option 1 (Beta Testing Demo, for stardance raters)
[Link](https://alomnsh.github.io/The-Ares-Horizon/)

### Option 2: Quick Play (Windows Only - No Setup Required)
1. Go to the **[Releases](https://github.com/alomnsh/The-Ares-Horizon-Adventure-Game/releases/tag/v2.0.0)** page.
2. Download the `The.Ares.Horizon.exe` double-click the file to start playing

### Option 3: Run via Source Code (Cross-Platform Setup)

The game is run using a Tkinter and Pygame desktop GUI. So to avoid graphic rendering issues and installation freezes on your Unix PC, please follow these setup steps:

#### 1. Install System Dependencies
Open your **Terminal** and install the graphic and audio libraries required that the Pygame display wrapper depends on:

* **macOS:** Ensure you have [Homebrew](https://brew.sh) installed, then copy and paste:
  ```bash
  brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf pkg-config portmidi
  ```
* **Linux (Ubuntu/Debian/Mint):**
  ```bash
  sudo apt update
  sudo apt install build-essential python3-dev python3-venv python3-pip libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev libportmidi-dev -y
  ```

#### 2. Clone the Repository & Setupt
After cloning the repository, create a separate virtual environment to isolate the game's execution context from your system Python to avoid "Externally managed environment" (PEP 668) issues:
```bash
git clone https://github.com
cd The-Ares-Horizon-Adventure-Game

python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python Dependencies
With the virtual environment activated, run the following command to install the Python packages listed in requirements.txt
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*Note for Python 3.14+ Users:* If you're running Python 3.14+, and pip fails to install the dependencies due to a missing d binary, install pygame directly into your virtual environment using the community pygame distribution:
```bash
pip install pygame --ce
```

#### 4. Launch the Game
Run this command to play the game:
```bash
python "The Ares Horizon.py"
```

> ⚠️ **VOLUME WARNING:** The game has default volume settings, you can change them to your likings, it may be too loud for some people

## Features
* **Progress Bars:** The code uses `ttk.Progressbar` to indicate the crew safety points and the mission budgetleft
* **Audio Integration:** Uses `pygame` audio engine to handle sounds.
* **Typewriter Effect:** TText scrolls on the screen character by character to give a retro look of a real mission control
* **Mini-Game:** A 60 FPS `Pygame` window is launched inside the Tkinter window for the game
* **UI:** The old choice and story text are cleared in the new branch, and added unique hover effect on the buttons
* **Setting Menu:** The user can change the volumes of the game sounds, how fast the typewriter scrolls, mute all the sounds, or restore all the default settings. The menu is built with pygame

## How it Works
* The game engine uses a hybrid approach of Tkinter and Pygame, which communicates with the OS windowing system. The text is scrolled frame-by-frame with the tkinter root.after() method instead of using the standard time.sleep() function to prevent freezing issues that would happen when using the event loop
Each game stage consists of a set of decision nodes when selecting one of the choices, the function clears the Tkinter widgets, calculates the choice points, updates the UI elements, and branches the decision tree onto the next set of nodes

## Credits
* GUI concepts and layout inspiration from the [Hack Club Jams Guide](https://jams.hackclub.com/jam/story-game).

## AI Disclosure
* TThe AI-assisted contributions to this project were made under my supervision and fully understood before being committed to version control

* Google's AI was used to fix the bugs in my functions and in the boot process

* Gemini was used to learn Pygame and practice implementing it into my game

* The AI-assisted coding was less than 15% of the final code
