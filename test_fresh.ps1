# Clear Redis cache
$clearResponse = Invoke-RestMethod -Uri "http://localhost:8000/clear-cache" -Method Post
Write-Host "Cache cleared: $($clearResponse.message)"

# Test with a different repo to avoid cache hit
$body = @{
    repo = "facebook/react"
    team = "frontend"
    window_days = 7
} | ConvertTo-Json

Write-Host "`nTesting with fresh request (facebook/react)..."
$response = Invoke-RestMethod -Uri "http://localhost:8000/analyze-workflow" -Method Post -ContentType "application/json" -Body $body

Write-Host "`nResponse:"
$response | ConvertTo-Json -Depth 10
