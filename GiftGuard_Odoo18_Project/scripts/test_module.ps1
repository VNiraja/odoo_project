$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot "compose.yml"

docker compose -f $composeFile --profile test run --rm odoo-test
if ($LASTEXITCODE -ne 0) {
    throw "GiftGuard Odoo tests failed with exit code $LASTEXITCODE."
}
