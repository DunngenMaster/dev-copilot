# Test with completely unique parameters to force cache MISS
$body = @{
    repo = "golang/go"
    team = "go-team"
    window_days = 21
} | ConvertTo-Json

Write-Host "Testing with unique repo (golang/go) - should trigger Newman..."
Write-Host "Check your backend terminal for [Postman] log messages!`n"

$response = Invoke-RestMethod -Uri "http://localhost:8000/analyze-workflow" -Method Post -ContentType "application/json" -Body $body

Write-Host "Postman Mode: $($response.postman_mode)"
Write-Host "Cache Status: $($response.cache_status)"
Write-Host "Similarity: $($response.similarity)"
Write-Host "`nBottlenecks:"
$response.bottlenecks | ForEach-Object { Write-Host "  - $_" }
