param (
    [Parameter(Mandatory=$true)]
    [string]$SolutionName,
    [Parameter(Mandatory=$true)]
    [string]$DockerfilePaths,     # Space-separated string
    [Parameter(Mandatory=$true)]
    [string]$ServiceNames,        # Space-separated string
    [Parameter(Mandatory=$true)]
    [string]$ServicePorts,        # Space-separated string (new)
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    [Parameter(Mandatory=$true)]
    [string]$TenantId,
    [switch]$Recreate              # Optional flag: if set, rebuild/restart everything
)

$DockerfileList = $DockerfilePaths -split '\s+'
$ServiceNameList = $ServiceNames -split '\s+'
$PortList = $ServicePorts -split '\s+'

if ($DockerfileList.Count -ne $ServiceNameList.Count -or $ServiceNameList.Count -ne $PortList.Count) {
    Write-Error "DockerfilePaths, ServiceNames, and ServicePorts must have the same number of elements."
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ─────────────────────────────────────────────
# Step 1: Create Shared Docker Network
# ─────────────────────────────────────────────
$networkName = "app-network"
$networkExists = docker network ls --filter name=^$networkName$ --format "{{.Name}}"
if (-not $networkExists) {
    Write-Host "Creating Docker network '$networkName'..."
    docker network create $networkName | Out-Null
} else {
    Write-Host "✅ Docker network '$networkName' already exists."
}

# ─────────────────────────────────────────────
# Step 2: Redis Container
# ─────────────────────────────────────────────
$redisContainer = "my-redis"
$redisImage = "redis:7.2-alpine"
$redisPassword = "redis_password"

$redisIsRunning = docker ps --filter "name=^$redisContainer$" --format "{{.Names}}" | Where-Object { $_ -eq $redisContainer }

if ($Recreate -or -not $redisIsRunning) {
    if (docker ps -a --filter "name=^$redisContainer$" --format "{{.Names}}" | Where-Object { $_ -eq $redisContainer }) {
        Write-Host "Removing existing Redis container..."
        docker rm -f $redisContainer | Out-Null
    }

    Write-Host "`n🚀 Starting Redis container ($redisContainer)..."
    docker run -d `
        --name $redisContainer `
        --network $networkName `
        -p 6379:6379 `
        -e REDIS_PASSWORD=$redisPassword `
        $redisImage `
        redis-server --requirepass $redisPassword

    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to start Redis container."
        exit 1
    }

    Write-Host "✅ Redis container '$redisContainer' is running."
} else {
    Write-Host "✅ Redis container '$redisContainer' is already running. Skipping."
}

# ─────────────────────────────────────────────
# Step 3: Service Containers
# ─────────────────────────────────────────────
for ($i = 0; $i -lt $DockerfileList.Count; $i++) {
    $relativePath = Join-Path -Path $scriptDir -ChildPath $DockerfileList[$i]
    $dockerfilePath = Resolve-Path $relativePath
    $contextDir = Split-Path $dockerfilePath -Parent
    $serviceName = $ServiceNameList[$i]
    $containerName = "${serviceName}-container"
    $imageName = $serviceName
    $port = $PortList[$i]

    $isRunning = docker ps --filter "name=^$containerName$" --format "{{.Names}}" | Where-Object { $_ -eq $containerName }
    $imageExists = docker images --format "{{.Repository}}" | Where-Object { $_ -eq $imageName }

    if ($Recreate -or -not $isRunning) {
        if (docker ps -a --filter "name=^$containerName$" --format "{{.Names}}" | Where-Object { $_ -eq $containerName }) {
            Write-Host "Removing stopped container '$containerName'..."
            docker rm -f $containerName | Out-Null
        }

        if ($Recreate -or -not $imageExists) {
            Write-Host "`n🔨 Building image: $imageName from $dockerfilePath"
            docker build -f $dockerfilePath -t $imageName $scriptDir
            if ($LASTEXITCODE -ne 0) {
                Write-Error "❌ Failed to build Docker image for $imageName"
                continue
            }
        } else {
            Write-Host "✅ Image '$imageName' already exists. Skipping build."
        }

        $envFilePath = Join-Path -Path $contextDir -ChildPath ".env"
        $useEnv = Test-Path $envFilePath

        if (-not $useEnv) {
            Write-Error "⚠️  No .env file found at $envFilePath."
            exit 1
        }
        Write-Host "🔧 Found .env file at $envFilePath"

        docker run -d `
            --name $containerName `
            --network $networkName `
            -p "${port}:${port}" `
            --env AZURE_TENANT_ID=$TenantId `
            --env AZURE_SUBSCRIPTION_ID=$SubscriptionId `
            --env-file $envFilePath `
            $imageName

        if ($LASTEXITCODE -ne 0) {
            Write-Error "❌ Failed to start container $containerName"
            continue
        } else {
            Write-Host "✅ $containerName is ready. Please head over to container logs to complete authentication [right-click on container --> View Logs]."
        }
    } else {
        Write-Host "`n✅ Container '$containerName' is already running. Skipping."
    }
}

Write-Host "`n🎉 All services and Redis are up and running."
