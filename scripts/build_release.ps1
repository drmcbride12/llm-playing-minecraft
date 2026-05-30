$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = "C:\Users\swage\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$javaHome = "C:\Users\swage\Documents\jdk25-temurin\jdk-25.0.3+9"

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Command $($Arguments -join ' ')"
    }
}

if (!(Test-Path $python)) {
    throw "Python runtime not found at $python"
}

if (!(Test-Path $javaHome)) {
    throw "JDK 25 not found at $javaHome"
}

Push-Location $repo
try {
    $env:PYTHONPATH = (Join-Path $repo "src")
    Invoke-Native $python -m unittest discover -s tests

    $env:PYTHONPATH = "$(Join-Path $repo "build-tools\pyinstaller");$(Join-Path $repo "src")"
    & $python packaging\build_controller_exe.py
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }

    $bridgeJar = "fabric-bridge\build\libs\llm-playing-minecraft-bridge-0.1.0.jar"
    Push-Location "fabric-bridge"
    try {
        $env:JAVA_HOME = $javaHome
        $env:Path = "$env:JAVA_HOME\bin;$env:Path"
        & ".\gradlew.bat" build --stacktrace --console=plain
        if ($LASTEXITCODE -ne 0) {
            throw "Gradle build failed with exit code $LASTEXITCODE"
        }
    } catch {
        if (!(Test-Path (Join-Path $repo $bridgeJar))) {
            throw
        }
        Write-Warning "Gradle build failed in this shell, using existing bridge jar at $bridgeJar"
    } finally {
        Pop-Location
    }

    New-Item -ItemType Directory -Force -Path "dist\release" | Out-Null
    Copy-Item "dist\llm-playing-minecraft-controller.exe" "dist\release\llm-playing-minecraft-controller.exe" -Force
    Copy-Item $bridgeJar "dist\release\llm-playing-minecraft-bridge-0.1.0.jar" -Force
    Copy-Item ".env.example" "dist\release\.env.example" -Force
    Copy-Item "README.md" "dist\release\README.md" -Force

    Write-Host "Release artifacts written to dist\release"
} finally {
    Pop-Location
}
