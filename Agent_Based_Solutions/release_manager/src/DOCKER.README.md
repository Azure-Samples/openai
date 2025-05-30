# Release Manager - Docker Execution

This repository includes Visual Studio Code tasks for building and running the **Release Manager** solution in Docker using the PowerShell script `Run-SolutionAcceleratorInDocker.ps1`.

## Overview

Two VSCode tasks are available to run the Release Manager solution:

1. **Standard Build and Run**  
2. **Forced Rebuild and Run (`-Recreate` mode)**

Both tasks rely on the same PowerShell script but differ in whether Docker containers are forcibly rebuilt.

---

## 📂 Script: `Run-SolutionAcceleratorInDocker.ps1`

This PowerShell script automates Docker image builds and container launches for solution accelerators. It accepts a range of parameters to specify services, ports, and credentials.

---

## 🔧 Tasks

### 1. `Release Manager: Build and Run in Docker`

Runs the services in Docker using cached layers when available. Ideal for day-to-day development.

```json
Label: "Release Manager: Build and Run in Docker"
```

**Command Summary**:
```powershell
../src/Run-SolutionAcceleratorInDocker.ps1 `
    -SolutionName "ReleaseManager" `
    -DockerfilePaths "services/session_manager/Dockerfile solution_accelerators/release_manager/Dockerfile" `
    -ServiceNames "session_manager release_manager" `
    -ServicePorts "5000 6000" `
    -SubscriptionId "" `
    -TenantId ""
```

> This mode **does not** include the `-Recreate` flag, so it will reuse existing Docker containers if possible.

---

### 2. `Release Manager: Build and Run Docker Images [FORCE INSTALL]`

Forces Docker images to be rebuilt and containers recreated. Use this when dependencies or Dockerfiles change and you need a clean slate.

```json
Label: "Release Manager: Build and Run Docker Images [FORCE INSTALL]"
```

**Command Summary**:
```powershell
../src/Run-SolutionAcceleratorInDocker.ps1 `
    -SolutionName "ReleaseManager" `
    -DockerfilePaths "services/session_manager/Dockerfile solution_accelerators/release_manager/Dockerfile" `
    -ServiceNames "session_manager release_manager" `
    -ServicePorts "5000 6000" `
    -SubscriptionId "" `
    -TenantId "" `
    -Recreate
```

> This mode **includes** the `-Recreate` flag, which will clean up and rebuild containers even if they already exist.

---

## ✅ Prerequisites

- PowerShell (Core recommended)
- Docker runtime
- Visual Studio Code (with Tasks support)
- `-SubscriptionId` and `-TenantId` if used for cloud-based configuration

---

## 🏃 Usage

To run either task:

1. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
2. Select **Tasks: Run Task**.
3. Choose one of the following:
   - `Release Manager: Build and Run in Docker`
   - `Release Manager: Build and Run Docker Images [FORCE INSTALL]`
4. Wait for the tasks to finish. Once the docker containers are up and running, you should see the following containers up and running:
   - `Release Manager`
   - `Session Manager`
   - `Redis` (acts as a message broker between Session Manager and Release Manager)
5. For `Release Manager` and `Session Manager`, there's an additional step to allow Azure Cloud access - **az login**.
   Right-click on the container, select `View Logs`, and switch to the terminal to complete the authentication with Azure.
6. After successful login, `Session Manager` can be accessed at `http://127.0.0.1:5000` (or use the web client at `frontend/index.html` to create the request for Session Manager and use the chat interface.)

---

## ℹ Notes

- The working directory is set to `src/`, so relative paths in the script are resolved from there.
- If you encounter build issues, try the **FORCE INSTALL** task to clear any stale container state.
