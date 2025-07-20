# PowerShell script to set up permissions for semi-machine-to-machine authentication
# This script configures delegated permissions for shared mailbox access

param(
    [Parameter(Mandatory=$true)]
    [string]$AuthUser,  # e.g., "danny.v@yourdomain.com"
    
    [Parameter(Mandatory=$true)]
    [string]$SharedMailbox,  # e.g., "noreply@yourdomain.com"
    
    [Parameter(Mandatory=$false)]
    [string]$TenantId = "",  # Optional: specify tenant ID
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf
)

Write-Host "Setting up permissions for semi-machine-to-machine authentication..." -ForegroundColor Green
Write-Host "Auth User: $AuthUser" -ForegroundColor Yellow
Write-Host "Shared Mailbox: $SharedMailbox" -ForegroundColor Yellow
Write-Host ""

# Check if Exchange Online PowerShell module is installed
if (-not (Get-Module -ListAvailable -Name ExchangeOnlineManagement)) {
    Write-Host "Installing Exchange Online PowerShell module..." -ForegroundColor Yellow
    Install-Module -Name ExchangeOnlineManagement -Force -AllowClobber
}

# Connect to Exchange Online
Write-Host "Connecting to Exchange Online..." -ForegroundColor Yellow
try {
    Connect-ExchangeOnline -ErrorAction Stop
    Write-Host "✅ Connected to Exchange Online successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to connect to Exchange Online: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please make sure you have the necessary permissions and try again." -ForegroundColor Yellow
    exit 1
}

# Step 1: Check if shared mailbox exists
Write-Host ""
Write-Host "Step 1: Checking shared mailbox..." -ForegroundColor Cyan
try {
    $mailbox = Get-Mailbox -Identity $SharedMailbox -ErrorAction Stop
    Write-Host "✅ Shared mailbox found: $($mailbox.DisplayName)" -ForegroundColor Green
} catch {
    Write-Host "❌ Shared mailbox not found: $SharedMailbox" -ForegroundColor Red
    Write-Host "Please create the shared mailbox first or check the email address." -ForegroundColor Yellow
    Disconnect-ExchangeOnline -Confirm:$false
    exit 1
}

# Step 2: Check if auth user exists
Write-Host ""
Write-Host "Step 2: Checking auth user..." -ForegroundColor Cyan
try {
    $user = Get-User -Identity $AuthUser -ErrorAction Stop
    Write-Host "✅ Auth user found: $($user.DisplayName)" -ForegroundColor Green
} catch {
    Write-Host "❌ Auth user not found: $AuthUser" -ForegroundColor Red
    Write-Host "Please check the user email address or create the user first." -ForegroundColor Yellow
    Disconnect-ExchangeOnline -Confirm:$false
    exit 1
}

# Step 3: Add auth user as member of shared mailbox
Write-Host ""
Write-Host "Step 3: Adding auth user as member of shared mailbox..." -ForegroundColor Cyan
try {
    $existingMembers = Get-MailboxPermission -Identity $SharedMailbox | Where-Object {$_.User -eq $AuthUser}
    
    if ($existingMembers) {
        Write-Host "ℹ️  Auth user is already a member of the shared mailbox" -ForegroundColor Yellow
    } else {
        if ($WhatIf) {
            Write-Host "WhatIf: Would add $AuthUser as member of $SharedMailbox" -ForegroundColor Gray
        } else {
            Add-MailboxPermission -Identity $SharedMailbox -User $AuthUser -AccessRights FullAccess -InheritanceType All
            Write-Host "✅ Added $AuthUser as member of $SharedMailbox" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Failed to add user as member: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 4: Grant SendAs permission
Write-Host ""
Write-Host "Step 4: Granting SendAs permission..." -ForegroundColor Cyan
try {
    $existingSendAs = Get-RecipientPermission -Identity $SharedMailbox | Where-Object {$_.Trustee -eq $AuthUser}
    
    if ($existingSendAs) {
        Write-Host "ℹ️  SendAs permission already granted to $AuthUser" -ForegroundColor Yellow
    } else {
        if ($WhatIf) {
            Write-Host "WhatIf: Would grant SendAs permission to $AuthUser for $SharedMailbox" -ForegroundColor Gray
        } else {
            Add-RecipientPermission -Identity $SharedMailbox -Trustee $AuthUser -AccessRights SendAs
            Write-Host "✅ Granted SendAs permission to $AuthUser for $SharedMailbox" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Failed to grant SendAs permission: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 5: Verify permissions
Write-Host ""
Write-Host "Step 5: Verifying permissions..." -ForegroundColor Cyan
try {
    $membership = Get-MailboxPermission -Identity $SharedMailbox | Where-Object {$_.User -eq $AuthUser}
    $sendAs = Get-RecipientPermission -Identity $SharedMailbox | Where-Object {$_.Trustee -eq $AuthUser}
    
    Write-Host "Membership permissions:" -ForegroundColor White
    if ($membership) {
        Write-Host "  ✅ $AuthUser has $($membership.AccessRights) access to $SharedMailbox" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $AuthUser has no membership access to $SharedMailbox" -ForegroundColor Red
    }
    
    Write-Host "SendAs permissions:" -ForegroundColor White
    if ($sendAs) {
        Write-Host "  ✅ $AuthUser has SendAs permission for $SharedMailbox" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $AuthUser has no SendAs permission for $SharedMailbox" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to verify permissions: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Azure AD App Configuration Instructions
Write-Host ""
Write-Host "Step 6: Azure AD App Configuration" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "IMPORTANT: Configure your Azure AD app with DELEGATED permissions:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Go to Azure Portal > Azure Active Directory > App registrations" -ForegroundColor White
Write-Host "2. Select your application" -ForegroundColor White
Write-Host "3. Go to 'API permissions'" -ForegroundColor White
Write-Host "4. Add these DELEGATED permissions:" -ForegroundColor White
Write-Host "   - Microsoft Graph > Mail.Send" -ForegroundColor White
Write-Host "   - Microsoft Graph > User.Read" -ForegroundColor White
Write-Host "5. Grant admin consent for your organization" -ForegroundColor White
Write-Host "6. Configure redirect URI: http://localhost:8000/auth/callback" -ForegroundColor White
Write-Host ""

# Step 7: OAuth2 Setup Instructions
Write-Host "Step 7: OAuth2 Setup Instructions" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "After configuring Azure AD, run these commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Set up OAuth2 configuration:" -ForegroundColor White
Write-Host "   python manage.py setup_oauth2_authorization --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --tenant-id YOUR_TENANT_ID --auth-user $AuthUser --from-email $SharedMailbox" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Complete OAuth2 authorization in browser" -ForegroundColor White
Write-Host ""
Write-Host "3. Exchange authorization code for tokens:" -ForegroundColor White
Write-Host "   python manage.py exchange_auth_code --auth-code YOUR_AUTH_CODE" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test the configuration:" -ForegroundColor White
Write-Host "   python manage.py test_oauth2_authentication --test-email $AuthUser" -ForegroundColor Gray
Write-Host ""

# Disconnect from Exchange Online
Write-Host "Disconnecting from Exchange Online..." -ForegroundColor Yellow
Disconnect-ExchangeOnline -Confirm:$false
Write-Host "✅ Disconnected from Exchange Online" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Setup complete! Follow the Azure AD configuration steps above." -ForegroundColor Green
Write-Host "This semi-machine-to-machine approach will work with shared mailboxes using delegated permissions." -ForegroundColor Green 