param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$BackendEnvFile = Join-Path $BackendDir ".env"
$BackendEnvExample = Join-Path $BackendDir ".env.example"
$BackendVenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Write-Log($Message) {
    Write-Host "[start_dev] $Message"
}

Write-Log "PowerShell startup is a fallback path."
Write-Log "Preferred workflow: move the repo into a WSL-native path and run bash scripts/start_dev.sh from WSL."

function Ensure-BackendEnv {
    if (Test-Path $BackendEnvFile) {
        return
    }

    if (Test-Path $BackendEnvExample) {
        Copy-Item $BackendEnvExample $BackendEnvFile
        throw "Created backend\.env from .env.example. Fill OPENROUTER_API_KEY and rerun."
    }

    throw "backend\.env is missing."
}

function Ensure-BackendVenv {
    if (Test-Path $BackendVenvPython) {
        return
    }

    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCmd) {
        $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
    }
    if (-not $PythonCmd) {
        throw "Python 3 is required but was not found."
    }

    Write-Log "Creating backend virtualenv..."
    & $PythonCmd.Source -m venv (Join-Path $BackendDir ".venv")
    & $BackendVenvPython -m pip install --upgrade pip
    & $BackendVenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

function Get-FrontendRunner {
    $PnpmCmd = Get-Command pnpm -ErrorAction SilentlyContinue
    if ($PnpmCmd) {
        return @{
            Name = "pnpm"
            FilePath = $PnpmCmd.Source
            Args = @("dev", "--host", "0.0.0.0", "--port", $FrontendPort)
            InstallArgs = @("install")
        }
    }

    $NpmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if ($NpmCmd) {
        return @{
            Name = "npm"
            FilePath = $NpmCmd.Source
            Args = @("run", "dev", "--", "--host", "0.0.0.0", "--port", $FrontendPort)
            InstallArgs = @("install")
        }
    }

    throw "pnpm or npm is required but neither was found."
}

function Ensure-FrontendDeps($Runner) {
    $NodeModulesDir = Join-Path $FrontendDir "node_modules"
    if (Test-Path $NodeModulesDir) {
        return
    }

    Write-Log "Installing frontend dependencies..."
    Push-Location $FrontendDir
    try {
        & $Runner.FilePath @($Runner.InstallArgs)
    }
    finally {
        Pop-Location
    }
}

Ensure-BackendEnv
Ensure-BackendVenv
$Runner = Get-FrontendRunner
Ensure-FrontendDeps $Runner

Write-Log "Starting backend on http://localhost:$BackendPort ..."
$BackendProcess = Start-Process -FilePath $BackendVenvPython -ArgumentList @("-m", "uvicorn", "app:app", "--reload", "--port", $BackendPort) -WorkingDirectory $BackendDir -PassThru

Write-Log "Starting frontend on http://localhost:$FrontendPort ..."
$FrontendProcess = Start-Process -FilePath $Runner.FilePath -ArgumentList $Runner.Args -WorkingDirectory $FrontendDir -PassThru

Write-Log "Backend PID: $($BackendProcess.Id)"
Write-Log "Frontend PID: $($FrontendProcess.Id)"
Write-Log "Use Stop-Process on those PIDs when you want to stop them."
