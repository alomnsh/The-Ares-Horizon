# The Ares Horizon-Adventure Game
A choice python adventure game where the player takes a high-stake role of a Flight Director at NASA. There objective is to successfully launch, navigate and land a spacecraft on the surface of Mars

<!Gameplay Screenshot>

**[Download and Play the Game](link)**

## Quick Start
Play the game on your own computer by doing the following steps:

1. **Clone the repository**
   ```bash
   git clone https://github.com
   cd The-Ares-Horizon-Adventure-Game
   ```
   
2. **Install the Packages**
   ```bash
   pip install playsound==1.2.2 termcolor
   ```
   (Note: Version 1.2.2 of playsound is recommended to play the audio and the termcolor package is for colors!!)

3. **Launch the game**
   ```bash
   python "The Ares Horizon.py"
   ```
   (If you are on MacOS or linux, use:)
   ```bash
   python3 "The Ares Horizon.py"
   ``` 

## Feature
* **Real-Time Progress Bars:** The code uses `ttk.Progressbar` to track the crew saftey points and the mission budget remaining
* **Background Audio:** The code has `playsound` to automatically play a custom made background music when the game is being played
* **Typewriter Effect:** It feels like someone is typing on your screen letter-by-letter to give a cinematic feels to the game
* **The Interface:** Old text and choice are automatically removed and the color of the buttons change when hovering over them

## How it Works
* The game uses tkinter for the GUI. It is a custom made GUI
* **Non-Blocking GUI Loop:** Instead of using `time.sleep()` which blocks the exectution loop and cause crashes, the text-scrolling updates the text frame by frame using the tkinter (`root.after`)
* **Machine Branching:** Each phase is isolated in a state block. When a player make thier choice a function is triggred that wipes out the old buttons, and text and calculates the score, updates the labels and starts the next choice branch

## Credits
* How to get started and how to make the GUI from [Jams](https://jams.hackclub.com/jam/story-game)
