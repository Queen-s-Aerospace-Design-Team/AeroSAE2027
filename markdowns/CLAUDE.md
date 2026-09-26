# CLAUDE.md

@AGENTS.md

The import above pulls in the canonical project context — project summary, stack, development
environment, build commands, repo layout, coding conventions, and CI. **This file covers
Claude-Code-specific workflow only.** Put facts about the codebase in `AGENTS.md`, so every
agent and every teammate reads the same thing; put "how Claude Code should operate here" below.

## Where to run Claude Code

**Inside the dev container** you have the full toolchain — ROS 2 Jazzy, the PX4 SITL setup at
`~/PX4-Autopilot`, `colcon build` / `colcon test`, `./scripts/format-all.sh`, and the
`./scripts/simulate*.sh` tmux harnesses. This is the only place a change to `ros_ws/` can
actually be verified.

**On the bare host, or in a cloud session,** none of that exists — there is no supported
host-native build. Reading, searching, editing, and writing docs all work fine; anything that
needs a build, a test, or a sim run does not. In that case, make the edit, say plainly that it
is unverified, and leave verification to a container session or to CI on the PR.

Either way, follow the branch/PR/review workflow in [CONTRIBUTING.md](./CONTRIBUTING.md) —
`main` is protected and every change lands via a reviewed PR. Two checks from that file are
worth repeating because they are easy for an agent to skip: if you touch `.devcontainer/`,
rebuild the container rather than eyeballing the diff; if you touch `ros_ws/`, confirm
`colcon build --symlink-install` succeeds before pushing.

## Local settings

`.claude/` is gitignored, so local permissions and session state don't carry over between
teammates, or between a host session and a container session. Anything that should apply to
everyone belongs in this file or in `AGENTS.md` — not in `.claude/`.
