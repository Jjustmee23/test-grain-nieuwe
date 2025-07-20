# PowerShell script to fix shared mailbox permissions
# Run this script as an administrator with Microsoft 365 PowerShell module installed

Write-Host "Microsoft 365 Shared Mailbox Permission Fix" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Configuration
$AuthUser = "danny.v@nexonsolutions.be"
$SharedMailbox = "noreply@nexonsolutions.be"

Write-Host "Auth User: $AuthUser" -ForegroundColor Yellow
Write-Host "Shared Mailbox: $SharedMailbox" -ForegroundColor Yellow
Write-Host ""

# Check if Exchange Online PowerShell module is installed
try {
    Import-Module ExchangeOnlineManagement -ErrorAction Stop
    Write-Host "✓ Exchange Online PowerShell module found" -ForegroundColor Green
} catch {
    Write-Host "✗ Exchange Online PowerShell module not found" -ForegroundColor Red
    Write-Host "Please install it with: Install-Module -Name ExchangeOnlineManagement -Force" -ForegroundColor Yellow
    exit 1
}

# Connect to Exchange Online
Write-Host "Connecting to Exchange Online..." -ForegroundColor Yellow
try {
    Connect-ExchangeOnline -ErrorAction Stop
    Write-Host "✓ Connected to Exchange Online" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to connect to Exchange Online" -ForegroundColor Red
    Write-Host "Please ensure you have the necessary permissions and try again" -ForegroundColor Yellow
    exit 1
}

# Check if shared mailbox exists
Write-Host "Checking if shared mailbox exists..." -ForegroundColor Yellow
try {
    $mailbox = Get-Mailbox -Identity $SharedMailbox -ErrorAction Stop
    Write-Host "✓ Shared mailbox found: $($mailbox.DisplayName)" -ForegroundColor Green
} catch {
    Write-Host "✗ Shared mailbox not found: $SharedMailbox" -ForegroundColor Red
    Write-Host "Please create the shared mailbox first in Microsoft 365 Admin Center" -ForegroundColor Yellow
    exit 1
}

# Check current permissions
Write-Host "Checking current permissions..." -ForegroundColor Yellow
try {
    $currentPermissions = Get-RecipientPermission -Identity $SharedMailbox -Trustee $AuthUser -ErrorAction SilentlyContinue
    if ($currentPermissions) {
        Write-Host "✓ Current permissions found:" -ForegroundColor Green
        foreach ($permission in $currentPermissions) {
            Write-Host "  - $($permission.AccessRights)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "✗ No permissions found for $AuthUser" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Error checking permissions" -ForegroundColor Red
}

# Grant Send As permission
Write-Host "Granting Send As permission..." -ForegroundColor Yellow
try {
    Add-RecipientPermission -Identity $SharedMailbox -Trustee $AuthUser -AccessRights SendAs -ErrorAction Stop
    Write-Host "✓ Send As permission granted successfully" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "✓ Send As permission already exists" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to grant Send As permission: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Verify the permission was granted
Write-Host "Verifying permissions..." -ForegroundColor Yellow
try {
    $newPermissions = Get-RecipientPermission -Identity $SharedMailbox -Trustee $AuthUser -ErrorAction Stop
    if ($newPermissions) {
        Write-Host "✓ Permissions verified:" -ForegroundColor Green
        foreach ($permission in $newPermissions) {
            Write-Host "  - $($permission.AccessRights)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "✗ Permissions not found after granting" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Error verifying permissions" -ForegroundColor Red
}

# Disconnect from Exchange Online
Write-Host "Disconnecting from Exchange Online..." -ForegroundColor Yellow
try {
    Disconnect-ExchangeOnline -Confirm:$false
    Write-Host "✓ Disconnected from Exchange Online" -ForegroundColor Green
} catch {
    Write-Host "✗ Error disconnecting" -ForegroundColor Red
}

Write-Host ""
Write-Host "Permission fix completed!" -ForegroundColor Green
Write-Host "Please wait 15-30 minutes for permissions to propagate before testing." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Wait 15-30 minutes for permissions to propagate" -ForegroundColor White
Write-Host "2. Test the email functionality in your application" -ForegroundColor White
Write-Host "3. If still not working, check Azure AD app permissions" -ForegroundColor White 