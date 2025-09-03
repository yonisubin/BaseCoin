cd "C:\Users\USER\Downloads\BaseCoin\BaseCoin-main"

# Get user input
$userName = Read-Host "Enter the name of the user"
$amount = Read-Host "Enter the amount to add to the user's balance"

# Validate amount is numeric
if (-not [double]::TryParse($amount, [ref]0)) {
    Write-Host "Error: '$amount' is not a valid number."
    Read-Host "`nPress Enter to exit..."
    exit
}

# Check if user exists
$exists = sqlite3 "C:\Users\USER\Downloads\BaseCoin\BaseCoin-main\instance\db.sqlite3" "SELECT COUNT(*) FROM user WHERE lower(name)=lower('$userName');"
$exists = $exists.Trim()

if ($exists -eq "0") {
    Write-Host "User $userName does not exist. Please create the user first."
    Read-Host "`nPress Enter to exit..."
    exit
}

# Show balance before
Write-Host "Before:`n"
sqlite3 "C:\Users\USER\Downloads\BaseCoin\BaseCoin-main\instance\db.sqlite3" "SELECT id, name, balance FROM user WHERE lower(name)=lower('$userName');"

# Update balance
Write-Host "`nAdding $amount to the balance of user $userName..."
sqlite3 "C:\Users\USER\Downloads\BaseCoin\BaseCoin-main\instance\db.sqlite3" "UPDATE user SET balance = balance + $amount WHERE lower(name) = lower('$userName');"

# Show balance after
Write-Host "`n`nAfter:`n"
sqlite3 "C:\Users\USER\Downloads\BaseCoin\BaseCoin-main\instance\db.sqlite3" "SELECT id, name, balance FROM user WHERE lower(name)=lower('$userName');"

Write-Host "You entered user name: $userName and amount: $amount"

Read-Host "`nPress Enter to exit..."
