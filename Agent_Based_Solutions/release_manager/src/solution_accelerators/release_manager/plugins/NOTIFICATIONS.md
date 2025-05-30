# INSTRUCTIONS.md

## 📬 Setup Instructions for Notification Agent using Microsoft Graph API

This guide describes how to configure a Notification Agent that sends email notifications using the **Microsoft Graph SDK**, authenticated via **DefaultAzureCredential** using **federated identity credentials**.

The agent will send emails from `noreply@releasemanagersa.com` to stakeholders when changes occur in the system.

---

## 1. ✅ Microsoft Entra (Azure AD) Setup

### 1.1 Register an Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID** → **App registrations** → **New registration**
3. Set:

   * **Name**: `NotificationAgent`
   * **Supported account types**: Single tenant (or multi-tenant, based on your org)
   * Click **Register**

### 1.2 Configure Federated Identity Credential (For Workload Identity)

This allows Azure services for e.g. AKS to authenticate without secrets.

1. Go to your registered app → **Certificates & secrets** → **Federated credentials** → **Add credential**
2. Fill in:

   * **Name**: `notification-agent-credential`
   * **Managed Identity**: Use the dropdown to pick the Managed Identity to use
   * **Audience** (pre-selected but confirm): `api://AzureADTokenExchange`

### 1.3 Assign Microsoft Graph API Permissions

1. Go to **API permissions** → **Add a permission**
2. Choose **Microsoft Graph** → **Application permissions**
3. Add the following:

   * `Mail.Send`
4. Click **Grant admin consent** for your tenant.

---

## 2. 📨 Setup [noreply@releasemanagersa.com](mailto:noreply@releasemanagersa.com) Shared Mailbox

### 2.1 Create Shared Mailbox (If not existing)

Go to **Exchange Admin Center** → **Recipients** → **Shared** → **+ Add a shared mailbox**:

* Email: `noreply@releasemanagersa.com`
* Display name: `Release Manager Notifications`

### 2.2 Grant SendAs and FullAccess Rights to the Application

Use **Exchange Online PowerShell** to give your app access:

```powershell
Connect-ExchangeOnline

# Replace with your actual App (Service Principal) object ID
$appObjectId = "<APP_OBJECT_ID>"
$mailbox = "noreply@releasemanagersa.com"

# Full Access
Add-MailboxPermission -Identity $mailbox -User $appObjectId -AccessRights FullAccess -InheritanceType All

# Send As
Add-RecipientPermission -Identity $mailbox -Trustee $appObjectId -AccessRights SendAs
```

> 🔍 You can get the object ID from Azure Portal → App registrations → Your app → Overview → **Object ID**

---

### 3 Install Required Libraries

```bash
pip install azure-identity msgraph-core
```

## 4. ✅ Summary Checklist

* [x] Azure AD app registered
* [x] Federated identity credential configured
* [x] `Mail.Send` application permission granted and consented
* [x] Shared mailbox `noreply@releasemanagersa.com` created
* [x] Application granted `SendAs` and `FullAccess` rights to mailbox
* [x] Notification Agent uses Federated Identity Credentials via `ManagedIdentityCredential` to authenticate

---

## 📚 References

* Microsoft Graph Mail API: [https://learn.microsoft.com/en-us/graph/api/user-sendmail](https://learn.microsoft.com/en-us/graph/api/user-sendmail)
* Federated Credentials: [https://learn.microsoft.com/en-us/entra/identity-platform/workload-identity-federation](https://learn.microsoft.com/en-us/entra/identity-platform/workload-identity-federation)
* Graph Permissions Reference: [https://learn.microsoft.com/en-us/graph/permissions-reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
