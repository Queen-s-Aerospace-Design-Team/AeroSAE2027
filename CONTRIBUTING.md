# Contributing

`main` is protected: every change lands via a pull request with at least one approving review — no direct pushes, including from repo admins.

## Workflow

1. **Branch off `main`.** Name it `<yourname>/<short-description>` or `fix/...` / `feature/...` — whatever's clear at a glance in the branch list.
   ```bash
   git checkout main
   git pull origin main
   git checkout -b yourname/short-description
   ```
2. **Commit and push your branch.**
   ```bash
   git push -u origin yourname/short-description
   ```
3. **Open a pull request** into `main` (GitHub will print a direct link after the push, or use the "Compare & pull request" button on the repo page). Describe what changed and why — especially anything a reviewer can't infer just from the diff (why this approach, what you tested, what you didn't).
4. **Get one approval.** Anyone else with repo access can review — it doesn't have to be a specific person. Address feedback with more commits on the same branch; they show up on the PR automatically.
5. **Merge once approved.** Prefer "Squash and merge" for branches with messy/WIP commit history, or a regular merge if the commit history itself is worth keeping (e.g. a few clean, logically separate commits).
6. **Delete the branch** after merging (GitHub offers a button right there) to keep the branch list from accumulating cruft.

## Before opening a PR

- If your change touches `.devcontainer/` or anything else that affects the whole team's dev environment, actually test it — rebuild the container yourself, don't just eyeball the diff. See `CLAUDE.md` for the one-time `rm -rf ros_ws/{build,install,log}` gotcha if you've changed the workspace mount path.
- If your change touches `ros_ws/`, make sure `colcon build --symlink-install` succeeds before pushing.

## Reviewing someone else's PR

You don't need to be an expert in the exact file changed to leave a useful review — flag anything unclear, anything that looks untested, or anything you'd have done differently and want explained. "Looks fine, tested it and it builds" is a legitimate, sufficient approval for most changes here; save deep scrutiny for anything touching flight-critical logic (`flight_missions/`, `mission_core/`) or the shared devcontainer/deployment config.
