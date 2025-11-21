# Test with very different parameters to force cache MISS
$body = @{
    repo = "torvalds/linux"
    team = "kernel-maintainers"
    window_days = 30
} | ConvertTo-Json

Write-Host "Testing with linux kernel repo (should trigger Newman)..."
$response = Invoke-RestMethod -Uri "http://localhost:8000/analyze-workflow" -Method Post -ContentType "application/json" -Body $body

Write-Host "`nPostman Mode: $($response.postman_mode)"
Write-Host "Cache Status: $($response.cache_status)"
if ($response.similarity) {
    Write-Host "Similarity: $($response.similarity)"
}

Write-Host "`nFull Response:"
$response | ConvertTo-Json -Depth 10
