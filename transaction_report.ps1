cd "C:\Users\USER\Downloads\BaseCoin\BaseCoin-main\instance"
$date = Get-Date -Format "yyyy-MM-dd"
Write-Host "Transaction Report for $date"
Write-Host "-----------------------------------"

# Export to CSV
sqlite3 db.sqlite3 ".mode csv" ".headers on" ".output report-$date.csv" "SELECT * FROM 'transaction';" ".output stdout"

# Show in terminal
$show = sqlite3 db.sqlite3 "SELECT * FROM 'transaction';"
Write-Host "Transaction Report:`n$show"
# sqlite3 db.sqlite3 "DELETE FROM 'transaction';"
Read-Host "Press Enter to exit..."