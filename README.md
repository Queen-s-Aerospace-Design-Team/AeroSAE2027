# QADT AeroSAE 2027 Software Repository

Welcome! You've landed in the software home of Queen's Aerospace Design Team (QADT)'s entry for AeroSAE 2027! This repo contains drone autonomy, computer vision, hardware control, and the containers that tie it all together. Whether you're here for your first commit or your fiftieth, glad to have you.

This page is short on purpose, it's just here to point you the right way:

## Setting up your dev environment?

→ [SETUP.md](docs/markdowns/SETUP.md) walks you through setting up the developer environment such as: installing prerequisites, cloning the repo, getting the devcontainer running, and flying the drone in simulation.
If you do not have a windows machine don't worry! There are instructions for MacOS and Linux users.

## Just want to run the simulator?

Once Docker and VS Code are installed ([SETUP.md](docs/markdowns/SETUP.md)):

```bash
git clone git@github.com:Queen-s-Aerospace-Design-Team/AeroSAE2027.git && code AeroSAE2027
# In VS Code: "Reopen in Container", then open a terminal (Ctrl/Cmd + Shift + `)
./sim/launch.sh            # --headless for no Gazebo window, --world aeac for the team world
```

That starts PX4 SITL, Gazebo and the ROS 2 ↔ Gazebo bridge. **One Ctrl-C stops all of it.** To check it starts and shuts down cleanly: `./sim/smoke_test.sh`.

## Starting the onboarding project?

→ [ONBOARDING.md](docs/markdowns/ONBOARDING.md) contains all the information needed for the onboarding project. If you have any questions about it, don't hesitate to reach out the managers!

## Ready to contribute?

→ [CONTRIBUTING.md](docs/markdowns/CONTRIBUTING.md) covers the workflow such as branching, PRs, review, and what to check before you touch a Dockerfile or the ROS workspace. The main branch is protected, so every change lands through it.

## Looking for what to work on?

→ The [project board](https://github.com/orgs/Queen-s-Aerospace-Design-Team/projects/8/views/1) tracks the different tasks. It displays what's up for grabs, what's in progress, and what's done.

## Stuck, or looking for something else?

→ The [GitHub Wiki](https://github.com/Queen-s-Aerospace-Design-Team/AeroSAE2027/wiki) is where team resources and common sources of pain are located. There, learning material and the fixes people reach for most often can be found. If you hit something that isn't there yet, add it once you've solved it so the next person doesn't have to re-solve it.

Questions that aren't answered by any of the above? Reach out to a manager!

## Software Executive Team (2026/27)

- **Ben Roytblat** $-$ *Director*
- **Jacob Wong** $-$ *Manager*
- **Liam Shannon** $-$ *Manager*
