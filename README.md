# The Ares Horizon-Adventure Game
A choice python adventure game where the player takes a high-stake role of a Flight Director at NASA. Their objective is to successfully launch, navigate and land a spacecraft on the surface of Mars

<img width="1918" height="983" alt="Image" src="https://github.com/user-attachments/assets/37832fe0-860f-4aac-8f54-0d5724ae079d" />

## How to Play

### Option 1: Quick Play (Windows Only - No Setup Required)
1. Head over to the **[Releases](https://github.com/alomnsh/The-Ares-Horizon-Adventure-Game/releases/tag/v2.0.0)** page.
2. Download the `The.Ares.Horizon.exe` file from the latest release assets.
3. Double-click to run and play instantly!

### Option 2: Run via Source Code (Cross-Platform Setup)

The game runs locally using a Pygame-based desktop GUI interface. To prevent graphic rendering breaks or installation blockades on Unix environments, follow these precise environment setup steps:

#### 1. Install System Dependencies
Open your **Terminal** and install the underlying graphic and audio system libraries required to render the Pygame display wrapper:

* **macOS:** Ensure you have [Homebrew](https://brew.sh) installed, then copy and paste:
  ```bash
  brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf pkg-config portmidi
  ```
* **Linux (Ubuntu/Debian/Mint):** Update your package registries and install the native multimedia core:
  ```bash
  sudo apt update
  sudo apt install build-essential python3-dev python3-venv python3-pip libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev libportmidi-dev -y
  ```

#### 2. Clone the Repository & Configure Environment
Clone your branch and initialize an isolated execution loop to sidestep "Externally Managed Environment" (`PEP 668`) system blocks:

```bash
# Clone and enter the repository folder
git clone https://github.com
cd The-Ares-Horizon-Adventure-Game

# Create and boot up a clean local virtual environment
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python Dependencies
With your virtual environment initialized, run your installation tree:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*Note for Python 3.14+ Users:* If standard installation errors out due to uncompiled upstream structures, install the community-managed release directly into your active virtual environment:
```bash
pip install pygame --ce
```

#### 4. Launch the Game
Execute the main script layout from your shell:
```bash
python "The Ares Horizon.py"
```

> ⚠️ **VOLUME WARNING:** The game comes with default volume settings, you can adjust them too your need, it may me too loud for some people

## Features
* **Real-Time Progress Bars:** The code uses `ttk.Progressbar` to track the crew safety points and the mission budget remaining
* **Audio Integration:** Uses `pygame` audio engine to handle sounds.
* **Typewriter Effect:** The text streams onto the screen character-by-character to replicate an authentic, old-school Mission Control terminal.
* **Mini-Game:** A 60 FPS `Pygame` canvas embedded inside the Tkinter window for the final descent phase.
* **Interactive UI:** Old choice nodes and story text are cleared between transitions, and feautures custom hover transformations on gameplay buttons.
* **Setting Menu:** The user can change the volumes of sounds, how fast the typewriter types, mute all sounds, or reset every setting to default. Menu build with `pygame` and integrated with `tkinter`

## How it Works
* **Hybrid Tkinter & Pygame Engine:** The application connects Tkinter's geometric window manager with an active Pygame physics loop using cross-process OS window hooks.
* **Non-Blocking GUI Loop:** Instead of using `time.sleep()` which blocks the exectution loop and cause crashes, the text-scrolling updates the text frame by frame using the tkinter (`root.after`)
* **Machine Branching:** Each phase is isolated in a state block. When a player make their choice a function is triggred that wipes out the old buttons, and text and calculates the score, updates the labels and starts the next choice branch

## Credits
* GUI concepts and layout inspiration from the [Hack Club Jams Guide](https://jams.hackclub.com/jam/story-game).

## AI Disclosure
* The work that AI did was supervised by me and completely understood before implementation
* Used Google's AI to help with fixing bugs with my function and bugs with my boot sequence
* Used Gemini for help with learning Pygame and trying to implement into my mini-game
* Used Gemini for help in converting my code into `pygame` for publishing purposes
* AI usage was less than 15% of the code
