## Onboarding Project

This project is designed to help new software members become comfortable creating and
running software in the team's development environment. By the end, you should have:

- created a small ROS 2 package with a publisher and subscriber;
- built and run your code inside the dev container; and
- launched the simulator and watched the drone fly in QGroundControl and Gazebo.

## Before You Start

Meeting 1 covers the prerequisites: your GitHub account, collaborator access, an SSH key,
and cloning the repository. If you need help with the development environment, follow
[SETUP.md](SETUP.md) for your operating system. The [GitHub Wiki](https://github.com/Queen-s-Aerospace-Design-Team/AeroSAE2027/wiki)
contains additional learning resources and troubleshooting information.

## 1. Create an Onboarding Branch

From the repository, create a branch using your first and last name:

```bash
git checkout main
git pull origin main
git checkout -b onboarding_YOURFIRSTNAME_YOURLASTNAME
```

Onboarding branches must use this naming format so they are distinguishable from project
branches. Replace with your first and last name.

After creating your branch, switch to the branch and open the code.
```bash
git switch onboarding_YOURFIRSTNAME_YOURLASTNAME #your branch name
```

Open the directory in VSCode after switching to your branch using this command: 
```bash
code . #opens the directory in VSCode
```
When opening VSCode, you should see a prompt asking to **Reopen in Container**, select yes. If you do not, you can trigger the same action by opening VSCode's command palette with `Ctrl/Command + Shift + P` and typing `>Dev Containers: Rebuild and Reopen in Container` then selecting that option.

## 2. Build a ROS 2 Publisher and Subscriber

Create your ROS 2 package in the designated onboarding folder. Follow the ROS 2 guide for
[creating a package](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.html#what-is-a-ros-2-package).

Your package must contain:

1. A publisher node that publishes a message to a topic.
2. A subscriber node that receives and prints messages from that topic.

Use the [ROS 2 publisher and subscriber tutorial](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html)
as your guide. Build and run the package inside the dev container, then commit and push
your work:

```bash
git add .
git commit -m "Add onboarding publisher and subscriber"
git push
```

Open a pull request from your branch for practice. For the team's normal branch, commit, and review workflow, see
[CONTRIBUTING.md](CONTRIBUTING.md).

## 3. Fly the Simulated Drone

Follow [Running the Sim](SETUP.md#running-the-sim) in `SETUP.md` to build the workspace,
start Gazebo, and open QGroundControl. Use `simulateDepth.sh`; wait for the simulator to
start, then arm and take off from QGroundControl. Gazebo will take a while to load, be patient when loading it for the first time

If you get stuck, check [SETUP.md](SETUP.md), [CONTRIBUTING.md](CONTRIBUTING.md), and the
[GitHub Wiki](https://github.com/Queen-s-Aerospace-Design-Team/AeroSAE2027/wiki)

If you have any questions, do not hesitate to reach out the managers! We are here to help!
