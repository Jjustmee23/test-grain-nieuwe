# PowerShell script to fix M2M (Machine-to-Machine) permissions
# Run this script as an administrator with Microsoft 365 PowerShell module installed

Write-Host "Microsoft 365 M2M Permission Fix" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Configuration
$AppName = "grainsmtp"
$SharedMailbox = "noreply@nexonsolutions.be"
$TenantId = "52c7588b-0477-4341-bc4b-52aeb1c1af2e"

Write-Host "M2M Configuration:" -ForegroundColor Yellow
Write-Host "  App Name: $AppName" -ForegroundColor White
Write-Host "  Shared Mailbox: $SharedMailbox" -ForegroundColor White
Write-Host "  Tenant ID: $TenantId" -ForegroundColor White
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

# Check current permissions for the application
Write-Host "Checking current M2M permissions..." -ForegroundColor Yellow
try {
    # For M2M, we need to check application permissions
    # This is more complex as we need to check Azure AD app permissions
    Write-Host "  Note: M2M permissions are managed in Azure AD, not Exchange Online" -ForegroundColor Cyan
    Write-Host "  Please ensure the following in Azure AD:" -ForegroundColor Cyan
    Write-Host "    1. App '$AppName' has 'Mail.Send' APPLICATION permission" -ForegroundColor White
    Write-Host "    2. Admin consent has been granted" -ForegroundColor White
    Write-Host "    3. App has 'Send As' permission for shared mailbox" -ForegroundColor White
} catch {
    Write-Host "✗ Error checking M2M permissions" -ForegroundColor Red
}

# Provide M2M setup instructions
Write-Host ""
Write-Host "M2M Setup Instructions:" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host ""

Write-Host "1. Azure AD App Configuration:" -ForegroundColor Yellow
Write-Host "   - Go to: https://portal.azure.com" -ForegroundColor White
Write-Host "   - Navigate to: Azure Active Directory > App registrations" -ForegroundColor White
Write-Host "   - Select app: $AppName" -ForegroundColor White
Write-Host "   - Go to: API permissions" -ForegroundColor White
Write-Host "   - Remove all existing permissions" -ForegroundColor White
Write-Host "   - Add permission: Microsoft Graph > Application permissions > Mail.Send" -ForegroundColor White
Write-Host "   - Click: 'Grant admin consent for [tenant]'" -ForegroundColor White
Write-Host ""

Write-Host "2. Shared Mailbox Permissions:" -ForegroundColor Yellow
Write-Host "   - Go to: https://admin.microsoft.com" -ForegroundColor White
Write-Host "   - Navigate to: Groups > Shared mailboxes" -ForegroundColor White
Write-Host "   - Select: $SharedMailbox" -ForegroundColor White
Write-Host "   - Go to: Members tab" -ForegroundColor White
Write-Host "   - Add the application as a member" -ForegroundColor White
Write-Host "   - Grant 'Send As' permission to the application" -ForegroundColor White
Write-Host ""

Write-Host "3. Alternative PowerShell Commands:" -ForegroundColor Yellow
Write-Host "   # Grant Send As permission to application" -ForegroundColor White
Write-Host "   Add-RecipientPermission -Identity '$SharedMailbox' -Trustee '$AppName' -AccessRights SendAs" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. Verify M2M Configuration:" -ForegroundColor Yellow
Write-Host "   # Check application permissions" -ForegroundColor White
Write-Host "   Get-RecipientPermission -Identity '$SharedMailbox' -Trustee '$AppName'" -ForegroundColor Cyan
Write-Host ""

# Disconnect from Exchange Online
Write-Host "Disconnecting from Exchange Online..." -ForegroundColor Yellow
try {
    Disconnect-ExchangeOnline -Confirm:$false
    Write-Host "✓ Disconnected from Exchange Online" -ForegroundColor Green
} catch {
    Write-Host "✗ Error disconnecting" -ForegroundColor Red
}

Write-Host ""
Write-Host "M2M permission setup instructions completed!" -ForegroundColor Green
Write-Host "Please follow the Azure AD and Microsoft 365 Admin Center steps above." -ForegroundColor Yellow
Write-Host "After configuration, wait 15-30 minutes for permissions to propagate." -ForegroundColor Yellow
Write-Host ""
Write-Host "Test the configuration with:" -ForegroundColor Cyan
Write-Host "  python manage.py test_m2m_authentication --email danny.v@nexonsolutions.be" -ForegroundColor White 