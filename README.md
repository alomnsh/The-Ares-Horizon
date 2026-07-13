# The Ares Horizon-Adventure Game
A choice python adventure game where the player takes a high-stake role of a Flight Director at NASA. Their objective is to successfully launch, navigate and land a spacecraft on the surface of Mars

<img width="1918" height="983" alt="Image" src="https://github.com/user-attachments/assets/37832fe0-860f-4aac-8f54-0d5724ae079d" />

## How to Play

### Option 1: Quick Play (Windows Only - No Setup Required)
1. Head over to the **[Releases](https://github.com/alomnsh/The-Ares-Horizon-Adventure-Game/releases/tag/v1.0.1)** page.
2. Download the `The Ares Horizon (Reship V).exe` file from the latest release assets.
3. Double-click to run and play instantly!

### Option 2: Run via Source Code (Cross-Platform Setup)

Play the game on your own computer by doing the following steps (The game is a desktop based GUI, so it has to be hosted on your computer and cannot run on cloud):

1. **Install System Dependencies (For Mac & Linux Users)**
   Open your **Terminal** and run the command matching your operating system so your computer can handle Python window graphics:

   * **macOS:** Make sure you have Homebrew installed, then run:
     ```bash
     brew install python tcl-tk
     ```
   * **Linux (Ubuntu/Debian/Mint):** Run:
     ```bash
     sudo apt update && sudo apt install python3-tk python3-pip -y
     ```

2. **Clone the repository**
   ```bash
   git clone https://github.com
   cd The-Ares-Horizon-Adventure-Game
   ```

3. **Install the Packages**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Launch the game**
   ```bash
   python3 "The Ares Horizon (Reship V).py"
   ```
> ⚠️ **VOLUME WARNING:** Please set your system audio to around **30%** before starting. The terminal features cinematic alarms and emergency sound effects that may be loud!

## Features
* **Real-Time Progress Bars:** The code uses `ttk.Progressbar` to track the crew safety points and the mission budget remaining
* **Audio Integration:** Uses `pygame` audio engine to handle sounds.
* **Typewriter Effect:** The text streams onto the screen character-by-character to replicate an authentic, old-school Mission Control terminal.
* **Mini-Game:** A 60 FPS `Pygame` canvas embedded inside the Tkinter window for the final descent phase.
* **Interactive UI:** Old choice nodes and story text are cleared between transitions, and feautures custom hover transformations on gameplay buttons.

## How it Works
* **Hybrid Tkinter & Pygame Engine:** The application connects Tkinter's geometric window manager with an active Pygame physics loop using cross-process OS window hooks.
* **Non-Blocking GUI Loop:** Instead of using `time.sleep()` which blocks the exectution loop and cause crashes, the text-scrolling updates the text frame by frame using the tkinter (`root.after`)
* **Machine Branching:** Each phase is isolated in a state block. When a player make their choice a function is triggred that wipes out the old buttons, and text and calculates the score, updates the labels and starts the next choice branch

## Credits
* GUI concepts and layout inspiration from the [Hack Club Jams Guide](https://jams.hackclub.com/jam/story-game).

## AI Disclosure
* Used Google's AI to help with fixing bugs with my typewriter function and bugs with my boot sequence
* Used Gemini for help with learning Pygame and trying to implement into my mini-game
* AI usage was less than 10% of the code
