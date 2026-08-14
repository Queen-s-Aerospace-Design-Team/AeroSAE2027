Hey! Want to get our team's dev environment for this year's QADT season kicks off. Should take ~20-30 min depending on your internet (there's a ~15GB download).

**Before you start:**
- You'll get a GitHub collaborator invite for `Queen-s-Aerospace-Design-Team/AeroSAE2027` — accept it first (check email or https://github.com/notifications)
- Make sure you have a GitHub SSH key set up (test with `ssh -T git@github.com` — if that doesn't say "Hi [username]!", set one up first)
- Install **Docker** (Docker Desktop on Windows/Mac, or Docker Engine on Linux) 
    - Type the following commands to verify both Docker and Docker-Compose are installed:
    ```bash
    docker version
    docker compose version
    ``` 
- Install **VS Code**
    - Install the **"Dev Containers"** extension (search it in the Extensions tab)

**Steps:**
1. Clone the repo:
   ```bash
   git clone git@github.com:Queen-s-Aerospace-Design-Team/AeroSAE2027.git
   ```
2. Open the folder in VS Code. Run:
    ```bash
    cd AeroSAE2027
    code .
    ```
3. When VS Code prompts "Reopen in Container," click it (or Command Palette → "Dev Containers: Reopen in Container") — *(If this doesnt show up, do (CTRL + SHIFT + P) and search "Dev Containers: Reopen in Container")*
4. First time will take a while — it's pulling a ~15GB image. In your terminal you will see a few specifications that is being gathered to run the container.
5. Once you see "Starting Micro XRCE Agent...", it's open. Run this in a new integrated terminal (CTRL + SHIFT + `):
   ```bash
   pwd
   echo $AMENT_PREFIX_PATH
   ls -ld ~/PX4-Autopilot
   which register-python-argcomplete
   ```

   The output of the previous lines should look something like this: 
   ```bash
   qadt ➜ ~/AeroSAE2027 (main) $ pwd
   /home/qadt/AeroSAE2027
   qadt ➜ ~/AeroSAE2027 (main) $ echo $AMENT_PREFIX_PATH 
   /opt/ros/jazzy
   qadt ➜ ~/AeroSAE2027 (main) $ ls -ld ~/PX4-Autopilot 
   drwxr-xr-x 1 qadt qadt 4096 Aug  8 22:58 /home/qadt/PX4-Autopilot
   qadt ➜ ~/AeroSAE2027 (main) $ which register-python-argcomplete 
   /usr/bin/register-python-argcomplete
   qadt ➜ ~/AeroSAE2027 (main) $ 
   ```

**A couple of OS-specific notes** (also covered in the repo's `readme.md` if you hit any issues):
- **Windows**: needs WSL2 + Ubuntu, with Docker Desktop's WSL2 integration enabled
- **macOS**: needs XQuartz for GUI passthrough — Gazebo's 3D simulation view specifically won't work well on Mac (known limitation, driver mismatch), but the rest should
- **Linux**: needs an X11 session (not pure Wayland) for GUI apps to display

**Bonus round — if all that works, try flying the sim:**
1. Build the ROS workspace (takes a few minutes the first time, mainly compiling PX4's message definitions):
   ```bash
   cd ~/AeroSAE2027/ros_ws
   colcon build --symlink-install
   source install/setup.zsh
   ```
2. Launch the sim (opens a tmux session with PX4 SITL, Gazebo, and a couple viewer panes):
   ```bash
   cd ~/AeroSAE2027
   ./scripts/simulateDepth.sh
   ```
3. Give it 30-60 seconds to spin up, then in a **new** terminal launch QGroundControl:
   ```bash
   ./scripts/launchQGC.sh
   ```
4. Once QGC shows **"Ready"** next to the logo (top-left), try arming and taking off from its UI. If the drone lifts off in the Gazebo window, that's a full pass!
