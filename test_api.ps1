$body = @{
    repo = "microsoft/typescript"
    team = "engineering"
    window_days = 14
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/analyze-workflow" -Method Post -ContentType "application/json" -Body $body

$response | ConvertTo-Json -Depth 10
