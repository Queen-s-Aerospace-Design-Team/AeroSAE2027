# Dev container

Detail behind the "Development environment" section in [AGENTS.md](../../AGENTS.md).

## The image

```yaml
image: ghcr.io/queen-s-aerospace-design-team/devcontainer-px4:latest
pull_policy: always
```

(`.devcontainer/compose.base.yml`)

**The image is not built from this repo — there is no Dockerfile here.** It is built and pushed
from a separate container repository under the same GitHub org, and this repo only consumes it.
The production counterpart is `ghcr.io/queen-s-aerospace-design-team/deployment-px4:latest`
(`deployment/compose.deployment.yml`).

The tag is `:latest`, not a pinned digest. That's a deliberate trade — everyone gets fixes without
touching this repo — but it means **the image can change under you with no commit here**. ROS 2
Jazzy and the bundled `~/PX4-Autopilot` are whatever that tag currently ships.

(`ci.yml:174` carries a related comment — `# Canary: the image is tracked as :latest and can grow
without warning.` — but in context it sits above a `df -h /` pair and is about the image growing in
**size** and exhausting runner disk, not about its behaviour drifting. Don't cite it as evidence
for the behavioural risk.)

> `TODO:` record the exact name and URL of the image repo. Git history refers to it as
> `containers2027` (commit `f7b730f`) and earlier as `containersfork` (commit `8f6efe2`), but the
> name appears in **no tracked file** in this repo, so neither has been verified as current.

## Identity and layout

| Thing | Value |
| --- | --- |
| Container user | `qadt` |
| Home | `/home/qadt` |
| Workspace | `/home/qadt/AeroSAE2027` |
| ROS workspace | `/home/qadt/AeroSAE2027/ros_ws` |
| Compose project / container name | `qadt-devcontainer` |
| Devcontainer display name | `QADT Dev Container (PX4)` |

Two bind mounts in `compose.base.yml`:

- the repo (`source: ..`) → `/home/qadt/AeroSAE2027`
- `${HOME}/.ssh` → `/home/qadt/.ssh`, **read-only**, so git push works inside the container using
  your host key

### Why the workspace path is a fixed literal

Quoting `compose.base.yml`'s header comment:

> it binds THIS working directory into /home/qadt/AeroSAE2027, regardless of what the local clone
> directory is actually named on disk (a fork, a rename, etc.) ... This path is deliberately a
> fixed literal, not templated: docker compose does not resolve devcontainer.json-only variables
> like `${localWorkspaceFolderBasename}` (that's a devcontainers-CLI-only substitution), and a
> fixed path keeps every team member's container laid out identically, matching devcontainer.json's
> "workspaceFolder" and the workspace layout documented in docs/context/devcontainer.md.

So your clone can be named anything on the host; inside the container it is always
`/home/qadt/AeroSAE2027`. This is why the CMake-cache gotcha in `AGENTS.md` is about the *mount
path* changing, not your local folder name.

## Compose profile selection

`.devcontainer/initialize.sh` runs **before** the container starts (`initializeCommand`). It
detects the host platform and **copies** the matching profile to `compose.active.yml`:

| Profile | File |
| --- | --- |
| linux-NVIDIA | `compose.linux-NVIDIA.yml` |
| linux-nonNVIDIA | `compose.linux-nonNVIDIA.yml` |
| macos | `compose.macos.yml` |
| wsl | `compose.wsl.yml` |

`devcontainer.json` then composes `["compose.base.yml", "compose.active.yml"]`.

`compose.active.yml` is **gitignored**, and it is a one-time **copy, not a symlink** — editing a
`compose.<profile>.yml` does nothing until you rerun `initialize.sh` or re-trigger "Reopen in
Container". This is the single most common way a devcontainer edit silently fails to take effect.

On the Linux profiles `initialize.sh` requires a working X11 display for GUI passthrough (Gazebo,
rviz2), but accepts XWayland: it checks for either `XDG_SESSION_TYPE=x11` or a live socket at
`/tmp/.X11-unix/X<N>`, so Wayland-default hosts work as long as XWayland is running.

`postStartCommand` runs `.devcontainer/postStart.sh`, which starts the Micro XRCE-DDS Agent — see
[px4-integration.md](px4-integration.md).

`./scripts/manualCompose.sh` does the same thing from a terminal (`initialize.sh` →
`docker compose up -d` → exec a shell) if you'd rather not use VSCode's "Reopen in Container".

## The `qadt-dev` → `qadt` rename, and why CI checks container identity

`qadt-dev` appears in **no config, script, or source file** — the only hits for that string outside
these context docs are substrings of `qadt-devcontainer`. It is history, and it's worth knowing
because it explains a CI check that otherwise looks redundant.

Per commit `8f6efe2`, the image's Dockerfile "renamed its build-time user from qadt-dev to qadt so
it matches devcontainer.json's `remoteUser`". Before that fix, the mismatch meant "VS Code's
common-utils feature was creating an empty `qadt` user disconnected from everything the image
actually built" — a container that comes up looking fine but has none of the toolchain on the
user's path.

That failure lives in the **image**, which this repo doesn't build. So CI checks it from both ends:

1. **`Devcontainer config check`** greps `devcontainer.json`'s `remoteUser` / `workspaceFolder` and
   `compose.base.yml`'s `working_dir` / bind `target`, asserting all four against
   `EXPECTED_CONTAINER_USER: qadt` and `CONTAINER_WORKSPACE: /home/qadt/AeroSAE2027`. This only
   proves the config *claims* the right user.
2. **`Verify container identity`**, a step inside the `Colcon build (ROS2 workspace)` job, actually
   `docker run`s the image and asserts `whoami` is `qadt`, `$HOME` is `/home/qadt`, and something
   exists under `/opt/ros`. Its comment says why: "The only check that the image actually RUNS as
   `qadt` - devcontainer-config can only confirm devcontainer.json claims it, which misses an
   upstream rename. Runs before the build so failure is fast and legible."

Because the tag is `:latest`, that second check guards a moving target: it can start failing on a
PR that changed nothing relevant, and that failure is real information about the image, not about
the PR.

## `qadt` vs `qadt-deploy`

Different users, different stacks — don't copy paths between them.

| | Dev container | Deployment container |
| --- | --- | --- |
| User | `qadt` | `qadt-deploy` |
| Workspace | `/home/qadt/AeroSAE2027` | `/home/qadt-deploy/AeroSAE2027` |
| Compose | `.devcontainer/compose.*.yml` | `deployment/compose.*.yml` |
| Image | `devcontainer-px4:latest` | `deployment-px4:latest` |

## Other devcontainer.json facts

- `"service": "dev"`, `"overrideCommand": true`, `"shutdownAction": "stopCompose"`
- Feature `ghcr.io/devcontainers/features/common-utils:2` with `configureZshAsDefaultShell: true`
  and `upgradePackages: false`, pinned in `devcontainer-lock.json` to `2.5.7`
- Editor settings hardcode `jazzy` and `python3.12` in the ROS paths
- `compose.linux-nonNVIDIA.yml` is the only profile that pins `user: "1000:1000"`. CI has to
  `sudo chown -R 1000:1000` the checkout because the GitHub runner checks out as uid 1001 while
  the container user is uid 1000.
