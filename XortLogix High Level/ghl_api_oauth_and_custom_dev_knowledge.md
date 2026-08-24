# GoHighLevel (GHL) REST API, OAuth 2.0 & Custom Development Comprehensive Knowledge Base

---

## 1. Overview & Architecture Standards

GoHighLevel (HighLevel / LeadConnector) provides a comprehensive API ecosystem and extensibility layer.
* **API Base URL:** `https://services.leadconnectorhq.com`
* **Current API Standard:** REST API v2 (API v1 was deprecated on December 31, 2025).
* **Required Headers:**
  * `Authorization: Bearer <ACCESS_TOKEN_OR_PIT>`
  * `Version: 2021-07-28` (or current API release version)
  * `Content-Type: application/json`
  * `Accept: application/json`

---

## 2. OAuth 2.0 Authorization Flow & Token Management

OAuth 2.0 is required for multi-tenant Marketplace Apps, Agency-wide integrations, and Sub-account level access.

### 2.1 OAuth Endpoints
* **Authorization / Install URL:** `https://marketplace.gohighlevel.com/oauth/chooselocation`
* **Token Exchange / Refresh URL:** `POST https://services.leadconnectorhq.com/oauth/token`

### 2.2 Step 1: User Redirection & Authorization
Direct the user to the GoHighLevel authorization page with required query parameters:
```text
https://marketplace.gohighlevel.com/oauth/chooselocation?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SPACE_SEPARATED_SCOPES}
```
* **Parameters:**
  * `client_id` (string): Your HighLevel App Client ID.
  * `redirect_uri` (string): Pre-configured callback URL in your HighLevel Developer App settings.
  * `response_type` (string): Must be `code`.
  * `scope` (string): Space-separated list of scopes (e.g. `contacts.readonly contacts.write opportunities.write`).

### 2.3 Step 2: Exchange Authorization Code for Tokens
When the user authorizes, HighLevel redirects back to your `redirect_uri` with a `code` query parameter. Send a `POST` request to exchange it:

* **Endpoint:** `POST https://services.leadconnectorhq.com/oauth/token`
* **Content-Type:** `application/x-www-form-urlencoded`
* **Body:**
  * `client_id`: `{CLIENT_ID}`
  * `client_secret`: `{CLIENT_SECRET}`
  * `grant_type`: `authorization_code`
  * `code`: `{AUTHORIZATION_CODE}`
  * `redirect_uri`: `{REDIRECT_URI}`
  * `user_type`: `Location` or `Company`

* **Response Payload (JSON):**
```json
{
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "ref-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "scope": "contacts.readonly contacts.write opportunities.write",
  "userType": "Location",
  "locationId": "ve9EPM428h8vShlRW1KT",
  "companyId": "comp_123456",
  "userId": "user_123456"
}
```

### 2.4 Step 3: Refreshing Expired Access Tokens
Access tokens expire after 24 hours (`expires_in: 86400`). You must use the `refresh_token` to retrieve a new token pair:
* **Endpoint:** `POST https://services.leadconnectorhq.com/oauth/token`
* **Body (`application/x-www-form-urlencoded`):**
  * `client_id`: `{CLIENT_ID}`
  * `client_secret`: `{CLIENT_SECRET}`
  * `grant_type`: `refresh_token`
  * `refresh_token`: `{CURRENT_REFRESH_TOKEN}`
  * `user_type`: `Location` or `Company`

> **Critical Note:** HighLevel uses Refresh Token Rotation. Each refresh generates a new `access_token` AND a new `refresh_token`. Always persist the newly returned refresh token in your database.

### 2.5 Private Integration Tokens (PITs)
For single-location, server-to-server internal integrations where OAuth user flow is not required, use **Private Integration Tokens (PITs)** generated inside Sub-Account Settings -> Integrations / Developer Tools. PITs include scoped permissions and do not expire unless revoked.

### 2.6 Key Scopes Reference
* `contacts.readonly` / `contacts.write` - Contact records, custom fields, tags, tasks, notes.
* `opportunities.readonly` / `opportunities.write` - Pipelines, stages, deal values, lead statuses.
* `locations.readonly` / `locations.write` - Sub-account details, business settings, timezone.
* `locations/customFields.readonly` / `locations/customFields.write` - Schema management for custom fields.
* `locations/customValues.readonly` / `locations/customValues.write` - Manage location custom values.
* `conversations.readonly` / `conversations.write` - Manage message threads.
* `conversations/message.readonly` / `conversations/message.write` - Send SMS, Email, WhatsApp.
* `workflows.readonly` - View workflow triggers and execute contact enrollment.
* `calendars.readonly` / `calendars/events.write` - Appointments, booking slots, schedule calendar events.
* `forms.readonly` / `surveys.readonly` - Form submissions and survey answers.
* `payments.readonly` / `payments/transactions.write` - Invoices, orders, subscriptions, transactions.

---

## 3. Core REST API v2 Endpoints & Implementation

All requests must include `Authorization: Bearer <TOKEN>` and `Version: 2021-07-28`.

### 3.1 Contacts API

#### Create / Upsert Contact
* **Method & Route:** `POST /contacts/`
* **Payload:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+15551234567",
  "locationId": "ve9EPM428h8vShlRW1KT",
  "gender": "male",
  "address1": "123 Main Street",
  "city": "Austin",
  "state": "TX",
  "postalCode": "78701",
  "country": "US",
  "timezone": "America/Chicago",
  "tags": ["lead", "web-inquiry", "hot"],
  "customFields": [
    {
      "id": "custom_field_id_123",
      "field_value": "VIP Client"
    }
  ]
}
```

#### Update Contact
* **Method & Route:** `PUT /contacts/{contactId}`
* **Payload:** Include only the fields to update (e.g. tags, phone, custom field values).

#### Search / Filter Contacts
* **Method & Route:** `GET /contacts/`
* **Query Parameters:** `locationId={locationId}&query={email_or_phone_or_name}&limit=20`

#### Upsert Contact (Find by email/phone or Create)
* **Method & Route:** `POST /contacts/upsert`
* Deduplicates based on email or phone number in the sub-account.

---

### 3.2 Opportunities & Pipelines API

#### Get Pipelines for Location
* **Method & Route:** `GET /opportunities/pipelines?locationId={locationId}`

#### Create / Move Opportunity
* **Method & Route:** `POST /opportunities/`
* **Payload:**
```json
{
  "pipelineId": "pipeline_abc123",
  "locationId": "ve9EPM428h8vShlRW1KT",
  "name": "Acme Corp Deal",
  "pipelineStageId": "stage_xyz789",
  "status": "open",
  "contactId": "contact_id_999",
  "monetaryValue": 5000,
  "assignedTo": "user_id_456"
}
```

#### Update Opportunity Stage / Status
* **Method & Route:** `PUT /opportunities/{opportunityId}`
* **Payload:** `{"pipelineStageId": "stage_won_111", "status": "won"}`

---

### 3.3 Workflows API

#### Execute / Add Contact to Workflow
* **Method & Route:** `POST /workflows/{workflowId}/execute`
* **Payload:**
```json
{
  "contactId": "contact_id_999",
  "eventStartTime": "2026-03-01T10:00:00Z"
}
```

---

### 3.4 Custom Values & Custom Fields API

#### Get All Custom Values
* **Method & Route:** `GET /locations/{locationId}/customValues`

#### Update Custom Value
* **Method & Route:** `PUT /locations/{locationId}/customValues/{customValueId}`
* **Payload:** `{"name": "Support Email", "value": "support@xortlogix.com"}`

#### Get Custom Fields Schema
* **Method & Route:** `GET /locations/{locationId}/customFields`

---

### 3.5 Outbound & Inbound Webhooks

* **HighLevel Webhook Triggers:** Contact Created, Contact Updated, Tag Added, Opportunity Stage Changed, Form Submitted, Inbound SMS, Appointment Booked.
* **Webhook Payload Structure:** Includes `locationId`, `contact_id`, full contact object, triggered workflow ID, and custom field values.
* **Verification:** Verify webhook authenticity using the webhook signature or custom auth header in your middleware.

---

## 4. Front-End Custom Development Deliverables (Company Standards)

When a requirement is **not available as built-in native GoHighLevel functionality**, our front-end development team builds custom solutions using **HTML, CSS, and JavaScript**.

### 4.1 Custom GoHighLevel Features
We develop custom features within GoHighLevel that are not natively supported:
1. **Custom Dashboard Widgets:**
   * Dynamic stats widgets injected into the HighLevel dashboard using JavaScript and CSS.
   * Fetching real-time external analytics, custom charts (Chart.js / ApexCharts), or database stats.
2. **Custom Data Displays:**
   * Custom tables, modal popups, data grids, and client portal views rendered directly inside GHL sub-accounts or funnels.
3. **Custom Interactions & Workflows:**
   * Dynamic field validation, multi-step calculation forms, conditional UI hiding/showing, and external API calls directly from funnel pages.

### 4.2 Custom GoHighLevel Dashboard Theme & CSS Styling
Since HighLevel does not offer complete white-label visual theme flexibility natively, we customize the dashboard appearance using **Custom CSS**:
* **Theme Colors & Palettes:** Overriding default colors with the client's corporate brand colors.
* **Background & Surface Colors:** Dark mode implementation, gradient headers, custom cards, and sidebar styling.
* **Typography & UI Element Styling:** Custom font integration (Google Fonts), modern button borders, glow effects, badge customization, and rounded corners.
* **Implementation Location:** Agency Settings -> Company -> Custom CSS, or Sub-Account Settings -> Custom CSS.

```css
/* Example: Custom Dashboard CSS Theme */
:root {
  --ghl-primary: #6366f1;
  --ghl-bg-dark: #0f172a;
  --ghl-card-bg: #1e293b;
  --ghl-text: #f8fafc;
}

/* Custom Sidebar Styling */
.sidebar-v2, .hl_navbar {
  background-color: var(--ghl-bg-dark) !important;
  border-right: 1px solid #334155 !important;
}

/* Custom Modern Card Theme */
.card, .hl_card {
  background-color: var(--ghl-card-bg) !important;
  border-radius: 12px !important;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;
}
```

---

## 5. Decision Framework: Native vs. Custom Solutions

When answering user queries, the assistant must evaluate whether a requirement is possible **Natively** or requires **Custom Development**:

| Requirement | Native GHL Capability | Custom Solution Blueprint |
| :--- | :--- | :--- |
| **Dashboard Color & Theme Styling** | ❌ Not available natively beyond basic logo | ✅ Inject **Custom CSS** in Agency/Location settings to override UI styles, fonts, and dark mode. |
| **Custom Analytics Widgets on Dashboard** | ❌ Standard built-in widgets only | ✅ Build **Custom HTML/JS Widget** that fetches API data and renders via Custom Code or iFrame app. |
| **Complex Math / Dynamic Pricing in Forms** | ❌ Basic fixed form fields only | ✅ Inject **Custom JavaScript** in Funnel/Form to dynamically calculate prices and update custom fields. |
| **Multi-System Database Sync (ERP / Custom DB)** | ❌ Limited to native marketplace integrations | ✅ Use **GHL Outbound Webhook** $\rightarrow$ Middleware (Python/Node.js/Laravel) $\rightarrow$ **GHL REST API v2** update. |
| **Multi-Location Agency Management App** | ❌ Manual navigation in dashboard | ✅ Build a **Custom OAuth 2.0 Marketplace App** with `locations.readonly` and `contacts.write` scopes. |
| **Custom Customer Portal / Dynamic Data View** | ❌ Standard client portal with limited UI | ✅ Build an external React/Vue/HTML frontend that authenticates via **OAuth 2.0 / REST API v2** and embeds via HighLevel Custom Menu Link. |

---

## 6. Full Code Implementation Examples

### 6.1 Python: Create Contact & Move to Pipeline via REST API v2
```python
import requests

API_TOKEN = "your_access_token_or_pit"
LOCATION_ID = "ve9EPM428h8vShlRW1KT"
BASE_URL = "https://services.leadconnectorhq.com"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Version": "2021-07-28",
    "Content-Type": "application/json"
}

# 1. Create Contact
contact_payload = {
    "firstName": "Alex",
    "lastName": "Rivera",
    "email": "alex.rivera@example.com",
    "phone": "+15559876543",
    "locationId": LOCATION_ID,
    "tags": ["enterprise-lead"]
}

contact_res = requests.post(f"{BASE_URL}/contacts/", json=contact_payload, headers=headers)
contact_data = contact_res.json()
contact_id = contact_data.get("contact", {}).get("id")

# 2. Create Opportunity in Pipeline
opp_payload = {
    "pipelineId": "your_pipeline_id",
    "locationId": LOCATION_ID,
    "name": "Alex Rivera - Enterprise Plan",
    "pipelineStageId": "your_stage_id",
    "status": "open",
    "contactId": contact_id,
    "monetaryValue": 12000
}

opp_res = requests.post(f"{BASE_URL}/opportunities/", json=opp_payload, headers=headers)
print("Opportunity Created:", opp_res.json())
```

### 6.2 JavaScript (Front-End Custom Interaction in GHL Funnel)
```javascript
// Custom JavaScript injected into GHL Funnel Step Settings
window.addEventListener('DOMContentLoaded', () => {
  // Listen for custom form input to calculate dynamic price
  const quantityInput = document.querySelector('#custom-quantity-input');
  const displayTotal = document.querySelector('#custom-total-price');

  if (quantityInput && displayTotal) {
    quantityInput.addEventListener('input', (e) => {
      const qty = parseInt(e.target.value) || 0;
      const unitPrice = 49.99;
      const total = (qty * unitPrice).toFixed(2);
      displayTotal.innerText = `$${total}`;
    });
  }
});
```
