import streamlit as st
import json

from utils.auth import check_authentication, is_role
from utils.styles import inject_css, render_page_header, format_date, COLORS
from utils.db import (
    get_company, update_company, get_users_by_company,
    get_supabase, SCHEMA_SQL,
)

st.set_page_config(page_title="Settings | ServicePro OS", page_icon="⚙️", layout="wide")

if not check_authentication():
    st.warning("Please log in from the home page.")
    st.stop()

inject_css()

user = st.session_state.user
company = st.session_state.company
company_id = company.get("id", "")
user_role = user.get("role", "crew")

# Only owners and admins can access settings
if not is_role("owner", "admin"):
    st.error("Access denied. Settings requires Owner or Admin role.")
    st.info(f"Your current role: {user_role.title()}")
    st.stop()

render_page_header("Settings", "Configure your ServicePro OS platform")


# ── Helper: reload company from DB and update session ─────────────────────────
def reload_company():
    fresh = get_company(company_id)
    if fresh:
        st.session_state.company = fresh
        return fresh
    return company


# ── Helper: masked key display ────────────────────────────────────────────────
def mask_key(key_val: str, show_prefix: int = 10) -> str:
    if not key_val:
        return ""
    if len(key_val) <= show_prefix:
        return key_val
    return key_val[:show_prefix] + "•" * 8 + key_val[-4:]


# ── Helper: integration status badge ─────────────────────────────────────────
def status_badge(configured: bool) -> str:
    if configured:
        return '<span style="background:#D1FAE5;color:#065F46;padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:600;">✅ Connected</span>'
    return '<span style="background:#FEE2E2;color:#991B1B;padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:600;">❌ Not Configured</span>'


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏢 Company Profile",
    "🔑 API Keys & Integrations",
    "💲 Pricing Templates",
    "👥 User Management",
    "🗄️ Database Setup",
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — COMPANY PROFILE
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Company Profile")

    with st.form("company_profile_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            comp_name = st.text_input("Company Name *", value=company.get("name", ""))
            comp_email = st.text_input("Email", value=company.get("email", "") or "")
            comp_address = st.text_input("Address", value=company.get("address", "") or "")
            comp_logo = st.text_input("Logo URL", value=company.get("logo_url", "") or "", help="URL to your company logo image")
        with col_b:
            comp_phone = st.text_input("Phone", value=company.get("phone", "") or "")
            comp_website = st.text_input("Website", value=company.get("website", "") or "", placeholder="https://yourcompany.com")
            st.text_input("Company ID (read-only)", value=company_id, disabled=True, help="Use this ID when contacting support")
            created_at = company.get("created_at", "")
            st.text_input("Account Created", value=format_date(created_at[:10] if created_at else "") or "—", disabled=True)

        save_profile = st.form_submit_button("💾 Save Changes", use_container_width=False)

    if save_profile:
        if not comp_name.strip():
            st.error("Company name is required.")
        else:
            with st.spinner("Saving..."):
                result = update_company(company_id, {
                    "name": comp_name.strip(),
                    "email": comp_email.strip() or None,
                    "phone": comp_phone.strip() or None,
                    "address": comp_address.strip() or None,
                    "website": comp_website.strip() or None,
                    "logo_url": comp_logo.strip() or None,
                })
            if result:
                st.session_state.company = reload_company()
                st.success("Company profile saved successfully!")
            else:
                st.error("Failed to save. Check your database connection.")

    if company.get("logo_url"):
        st.markdown("**Current Logo Preview:**")
        st.image(company["logo_url"], width=200)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — API KEYS & INTEGRATIONS
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("API Keys & Integrations")
    st.warning("🔒 API keys are stored securely in your database. Never share your secret keys.")

    # ── Status overview ────────────────────────────────────────────────────
    st.markdown("**Integration Status:**")
    status_cols = st.columns(5)
    integrations = [
        ("Claude AI", bool(company.get("anthropic_key"))),
        ("Stripe", bool(company.get("stripe_secret_key"))),
        ("Gmail", bool(company.get("gmail_email") and company.get("gmail_app_password"))),
        ("Google Maps", bool(company.get("google_maps_key"))),
        ("Twilio SMS", bool(company.get("twilio_sid") and company.get("twilio_auth"))),
    ]
    for i, (name, configured) in enumerate(integrations):
        with status_cols[i]:
            st.markdown(f"**{name}**<br>{status_badge(configured)}", unsafe_allow_html=True)

    st.markdown("---")

    # ── Claude AI ─────────────────────────────────────────────────────────
    with st.expander("🤖 Claude AI (Anthropic)", expanded=not bool(company.get("anthropic_key"))):
        st.markdown("**Used for:** AI estimates, chatbot, job summaries, photo analysis")
        st.markdown(f"**Model:** `claude-opus-4-7`")

        current_anthropic = company.get("anthropic_key", "") or ""
        if current_anthropic:
            st.info(f"Current key: `{mask_key(current_anthropic)}`")

        with st.form("anthropic_form"):
            new_anthropic = st.text_input(
                "Anthropic API Key",
                type="password",
                placeholder="sk-ant-api03-...",
                help="Get your API key at console.anthropic.com",
            )
            col_test, col_save = st.columns([1, 1])
            with col_test:
                test_anthropic = st.form_submit_button("🔌 Test Connection")
            with col_save:
                save_anthropic = st.form_submit_button("💾 Save Key")

        if test_anthropic:
            key_to_test = new_anthropic.strip() or current_anthropic
            if not key_to_test:
                st.warning("Enter an API key to test.")
            else:
                try:
                    import anthropic as _anthropic
                    test_client = _anthropic.Anthropic(api_key=key_to_test)
                    with st.spinner("Testing Claude API..."):
                        resp = test_client.messages.create(
                            model="claude-opus-4-7",
                            max_tokens=20,
                            messages=[{"role": "user", "content": "Say: OK"}],
                        )
                    st.success(f"Claude AI connected! Response: {resp.content[0].text.strip()}")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")

        if save_anthropic and new_anthropic.strip():
            with st.spinner("Saving..."):
                result = update_company(company_id, {"anthropic_key": new_anthropic.strip()})
            if result:
                st.session_state.company = reload_company()
                st.success("Anthropic API key saved!")
            else:
                st.error("Failed to save.")

    # ── Stripe ────────────────────────────────────────────────────────────
    with st.expander("💳 Stripe (Payments)", expanded=not bool(company.get("stripe_secret_key"))):
        st.markdown("**Used for:** Payment links, invoicing, online payments")
        st.info("Use test keys (`sk_test_...`) during development. Switch to live keys (`sk_live_...`) for production.")

        current_stripe_secret = company.get("stripe_secret_key", "") or ""
        current_stripe_pub = company.get("stripe_publishable_key", "") or ""
        if current_stripe_secret:
            st.info(f"Current secret key: `{mask_key(current_stripe_secret)}`")
        if current_stripe_pub:
            st.info(f"Current publishable key: `{mask_key(current_stripe_pub)}`")

        with st.form("stripe_form"):
            new_stripe_secret = st.text_input(
                "Stripe Secret Key",
                type="password",
                placeholder="sk_test_... or sk_live_...",
                help="Found in Stripe Dashboard → Developers → API Keys",
            )
            new_stripe_pub = st.text_input(
                "Stripe Publishable Key",
                placeholder="pk_test_... or pk_live_...",
                help="The public key safe to share in frontend code",
            )
            col_test_s, col_save_s = st.columns([1, 1])
            with col_test_s:
                test_stripe = st.form_submit_button("🔌 Test Connection")
            with col_save_s:
                save_stripe = st.form_submit_button("💾 Save Keys")

        if test_stripe:
            key_to_test = new_stripe_secret.strip() or current_stripe_secret
            if not key_to_test:
                st.warning("Enter a Stripe Secret Key to test.")
            else:
                try:
                    import stripe as _stripe
                    _stripe.api_key = key_to_test
                    with st.spinner("Testing Stripe connection..."):
                        account = _stripe.Account.retrieve()
                    st.success(f"Stripe connected! Account: {account.get('email', account.get('id', 'OK'))}")
                except Exception as e:
                    st.error(f"Stripe connection failed: {str(e)}")

        if save_stripe:
            updates = {}
            if new_stripe_secret.strip():
                updates["stripe_secret_key"] = new_stripe_secret.strip()
            if new_stripe_pub.strip():
                updates["stripe_publishable_key"] = new_stripe_pub.strip()
            if updates:
                with st.spinner("Saving..."):
                    result = update_company(company_id, updates)
                if result:
                    st.session_state.company = reload_company()
                    st.success("Stripe keys saved!")
                else:
                    st.error("Failed to save.")
            else:
                st.warning("Enter at least one key to save.")

    # ── Gmail ─────────────────────────────────────────────────────────────
    with st.expander("📧 Gmail (Email)", expanded=not bool(company.get("gmail_email"))):
        st.markdown("**Used for:** Sending proposals, invoices, appointment reminders")

        current_gmail = company.get("gmail_email", "") or ""
        if current_gmail:
            st.info(f"Current Gmail: `{current_gmail}`")

        with st.expander("📖 How to get a Gmail App Password"):
            st.markdown("""
**Step-by-step instructions:**

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification** and enable it if not already
4. After enabling 2-Step Verification, go back to Security
5. Search for **"App passwords"** or scroll down to find it
6. Click **App passwords**
7. Select app: **"Mail"**, select device: **"Other (Custom name)"**
8. Enter a name like "ServicePro OS" and click **Generate**
9. Copy the 16-character password (shown once — save it!)
10. Paste it in the field below

**Important:** This is NOT your regular Gmail password. It's a special app-specific password.
""")

        with st.form("gmail_form"):
            new_gmail_email = st.text_input(
                "Gmail Email Address",
                value=current_gmail,
                placeholder="yourname@gmail.com",
            )
            new_gmail_pass = st.text_input(
                "Gmail App Password",
                type="password",
                placeholder="xxxx xxxx xxxx xxxx",
                help="16-character app password from Google Account → Security → App Passwords",
            )
            col_test_g, col_save_g = st.columns([1, 1])
            with col_test_g:
                test_gmail = st.form_submit_button("🔌 Test Connection")
            with col_save_g:
                save_gmail = st.form_submit_button("💾 Save")

        if test_gmail:
            email_to_test = new_gmail_email.strip() or current_gmail
            pass_to_test = new_gmail_pass.strip() or company.get("gmail_app_password", "")
            if not email_to_test or not pass_to_test:
                st.warning("Enter both Gmail email and App Password to test.")
            else:
                try:
                    import smtplib
                    with st.spinner("Testing Gmail SMTP connection..."):
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(email_to_test, pass_to_test)
                        server.quit()
                    st.success(f"Gmail connected successfully for {email_to_test}!")
                except smtplib.SMTPAuthenticationError:
                    st.error("Authentication failed. Check your Gmail email and App Password.")
                except Exception as e:
                    st.error(f"Gmail connection failed: {str(e)}")

        if save_gmail:
            updates_g = {}
            if new_gmail_email.strip():
                updates_g["gmail_email"] = new_gmail_email.strip()
            if new_gmail_pass.strip():
                updates_g["gmail_app_password"] = new_gmail_pass.strip()
            if updates_g:
                with st.spinner("Saving..."):
                    result = update_company(company_id, updates_g)
                if result:
                    st.session_state.company = reload_company()
                    st.success("Gmail credentials saved!")
                else:
                    st.error("Failed to save.")
            else:
                st.warning("Enter credentials to save.")

    # ── Google Maps ────────────────────────────────────────────────────────
    with st.expander("🗺️ Google Maps", expanded=not bool(company.get("google_maps_key"))):
        st.markdown("**Used for:** Job location mapping, crew route planning, driving directions")

        current_maps = company.get("google_maps_key", "") or ""
        if current_maps:
            st.info(f"Current key: `{mask_key(current_maps)}`")

        with st.expander("📖 How to get a Google Maps API Key"):
            st.markdown("""
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Go to **APIs & Services → Library**
4. Search and enable:
   - **Maps JavaScript API**
   - **Geocoding API**
   - **Directions API** (for route planning)
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API Key**
7. Copy the key and paste it below
8. (Recommended) Restrict the key to your app's domain for security
""")

        with st.form("maps_form"):
            new_maps_key = st.text_input(
                "Google Maps API Key",
                type="password",
                placeholder="AIza...",
            )
            col_test_m, col_save_m = st.columns([1, 1])
            with col_test_m:
                test_maps = st.form_submit_button("🔌 Test Connection")
            with col_save_m:
                save_maps = st.form_submit_button("💾 Save")

        if test_maps:
            key_to_test = new_maps_key.strip() or current_maps
            if not key_to_test:
                st.warning("Enter a Google Maps API key to test.")
            else:
                try:
                    import urllib.request
                    test_url = (
                        f"https://maps.googleapis.com/maps/api/geocode/json"
                        f"?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key={key_to_test}"
                    )
                    with st.spinner("Testing Google Maps API..."):
                        with urllib.request.urlopen(test_url, timeout=10) as resp:
                            data = json.loads(resp.read())
                    if data.get("status") == "OK":
                        st.success("Google Maps API connected! Geocoding works.")
                    elif data.get("status") == "REQUEST_DENIED":
                        st.error("API key is invalid or Maps Geocoding API is not enabled.")
                    else:
                        st.warning(f"Unexpected status: {data.get('status')} — {data.get('error_message', '')}")
                except Exception as e:
                    st.error(f"Test failed: {str(e)}")

        if save_maps and new_maps_key.strip():
            with st.spinner("Saving..."):
                result = update_company(company_id, {"google_maps_key": new_maps_key.strip()})
            if result:
                st.session_state.company = reload_company()
                st.success("Google Maps API key saved!")
            else:
                st.error("Failed to save.")

    # ── Twilio ────────────────────────────────────────────────────────────
    with st.expander("📱 Twilio (SMS)", expanded=False):
        st.markdown("**Used for:** SMS appointment reminders, crew alerts *(coming soon)*")

        current_twilio_sid = company.get("twilio_sid", "") or ""
        current_twilio_auth = company.get("twilio_auth", "") or ""
        current_twilio_phone = company.get("twilio_phone", "") or ""

        if current_twilio_sid:
            st.info(f"Account SID: `{mask_key(current_twilio_sid)}`")
        if current_twilio_phone:
            st.info(f"Twilio Phone: `{current_twilio_phone}`")

        with st.form("twilio_form"):
            new_twilio_sid = st.text_input(
                "Account SID",
                value=current_twilio_sid,
                placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                help="Found in Twilio Console Dashboard",
            )
            new_twilio_auth = st.text_input(
                "Auth Token",
                type="password",
                placeholder="Your Twilio Auth Token",
            )
            new_twilio_phone = st.text_input(
                "Twilio Phone Number",
                value=current_twilio_phone,
                placeholder="+15551234567",
                help="Must be in E.164 format: +1XXXXXXXXXX",
            )
            col_test_t, col_save_t = st.columns([1, 1])
            with col_test_t:
                test_twilio = st.form_submit_button("🔌 Test Connection")
            with col_save_t:
                save_twilio = st.form_submit_button("💾 Save")

        if test_twilio:
            sid_to_test = new_twilio_sid.strip() or current_twilio_sid
            auth_to_test = new_twilio_auth.strip() or current_twilio_auth
            if not sid_to_test or not auth_to_test:
                st.warning("Enter Account SID and Auth Token to test.")
            else:
                try:
                    from twilio.rest import Client as TwilioClient
                    with st.spinner("Testing Twilio connection..."):
                        t_client = TwilioClient(sid_to_test, auth_to_test)
                        account = t_client.api.accounts(sid_to_test).fetch()
                    st.success(f"Twilio connected! Account: {account.friendly_name}")
                except ImportError:
                    st.warning("Twilio package not installed. Add 'twilio' to requirements.txt.")
                except Exception as e:
                    st.error(f"Twilio connection failed: {str(e)}")

        if save_twilio:
            updates_t = {}
            if new_twilio_sid.strip():
                updates_t["twilio_sid"] = new_twilio_sid.strip()
            if new_twilio_auth.strip():
                updates_t["twilio_auth"] = new_twilio_auth.strip()
            if new_twilio_phone.strip():
                updates_t["twilio_phone"] = new_twilio_phone.strip()
            if updates_t:
                with st.spinner("Saving..."):
                    result = update_company(company_id, updates_t)
                if result:
                    st.session_state.company = reload_company()
                    st.success("Twilio settings saved!")
                else:
                    st.error("Failed to save.")
            else:
                st.warning("Enter at least one field to save.")

    # ── Save All ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.info("Tip: Each integration section has its own Save button. Use them individually or use the form at the top.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — PRICING TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Default Pricing Templates")
    st.markdown("Set your default labor and material rates. These pre-fill your estimator for faster quoting.")

    # Load current pricing config
    pricing_raw = company.get("pricing_config") or {}
    if isinstance(pricing_raw, str):
        try:
            pricing_raw = json.loads(pricing_raw)
        except Exception:
            pricing_raw = {}

    painting_defaults = pricing_raw.get("painting", {})
    electrical_defaults = pricing_raw.get("electrical", {})
    landscaping_defaults = pricing_raw.get("landscaping", {})

    paint_tab, elec_tab, land_tab = st.tabs(["🎨 Painting Rates", "⚡ Electrical Rates", "🌿 Landscaping Rates"])

    # ── Painting Rates ─────────────────────────────────────────────────────
    with paint_tab:
        st.markdown("**Labor Rates (per sq ft)**")
        with st.form("painting_rates_form"):
            pc1, pc2 = st.columns(2)
            with pc1:
                p_labor_economy = st.number_input("Economy Labor ($/sqft)", value=float(painting_defaults.get("labor_economy", 0.50)), step=0.05, format="%.2f")
                p_labor_standard = st.number_input("Standard Labor ($/sqft)", value=float(painting_defaults.get("labor_standard", 0.75)), step=0.05, format="%.2f")
                p_labor_premium = st.number_input("Premium Labor ($/sqft)", value=float(painting_defaults.get("labor_premium", 1.10)), step=0.05, format="%.2f")
                p_labor_luxury = st.number_input("Luxury Labor ($/sqft)", value=float(painting_defaults.get("labor_luxury", 1.60)), step=0.05, format="%.2f")
            with pc2:
                p_material = st.number_input("Paint Material ($/sqft)", value=float(painting_defaults.get("material_per_sqft", 0.35)), step=0.05, format="%.2f")
                p_primer = st.number_input("Primer ($/sqft)", value=float(painting_defaults.get("primer_per_sqft", 0.15)), step=0.05, format="%.2f")
                p_door = st.number_input("Door Unit Price ($)", value=float(painting_defaults.get("door_unit_price", 75.0)), step=5.0, format="%.2f")
                p_window = st.number_input("Window Unit Price ($)", value=float(painting_defaults.get("window_unit_price", 45.0)), step=5.0, format="%.2f")
                p_baseboard = st.number_input("Baseboard ($/linear ft)", value=float(painting_defaults.get("baseboard_per_lf", 2.50)), step=0.25, format="%.2f")

            save_painting = st.form_submit_button("💾 Save Painting Rates", use_container_width=False)

        if save_painting:
            pricing_raw["painting"] = {
                "labor_economy": p_labor_economy,
                "labor_standard": p_labor_standard,
                "labor_premium": p_labor_premium,
                "labor_luxury": p_labor_luxury,
                "material_per_sqft": p_material,
                "primer_per_sqft": p_primer,
                "door_unit_price": p_door,
                "window_unit_price": p_window,
                "baseboard_per_lf": p_baseboard,
            }
            with st.spinner("Saving painting rates..."):
                result = update_company(company_id, {"pricing_config": pricing_raw})
            if result:
                st.session_state.company = reload_company()
                st.success("Painting rates saved!")
            else:
                st.error("Failed to save.")

    # ── Electrical Rates ────────────────────────────────────────────────────
    with elec_tab:
        st.markdown("**Electrical Base Rates**")
        with st.form("electrical_rates_form"):
            ec1, ec2 = st.columns(2)
            with ec1:
                e_labor_hour = st.number_input("Labor Rate ($/hour)", value=float(electrical_defaults.get("labor_per_hour", 95.0)), step=5.0, format="%.2f")
                e_outlet = st.number_input("Outlet Install ($)", value=float(electrical_defaults.get("outlet_install", 85.0)), step=5.0, format="%.2f")
                e_switch = st.number_input("Switch Install ($)", value=float(electrical_defaults.get("switch_install", 75.0)), step=5.0, format="%.2f")
                e_light_fixture = st.number_input("Light Fixture Install ($)", value=float(electrical_defaults.get("light_fixture_install", 125.0)), step=10.0, format="%.2f")
            with ec2:
                e_panel_upgrade = st.number_input("Panel Upgrade ($/unit)", value=float(electrical_defaults.get("panel_upgrade", 1800.0)), step=100.0, format="%.2f")
                e_circuit = st.number_input("New Circuit ($)", value=float(electrical_defaults.get("new_circuit", 350.0)), step=25.0, format="%.2f")
                e_gfci = st.number_input("GFCI Outlet ($)", value=float(electrical_defaults.get("gfci_outlet", 110.0)), step=5.0, format="%.2f")
                e_service_call = st.number_input("Service Call / Diagnostic ($)", value=float(electrical_defaults.get("service_call", 150.0)), step=10.0, format="%.2f")

            save_electrical = st.form_submit_button("💾 Save Electrical Rates", use_container_width=False)

        if save_electrical:
            pricing_raw["electrical"] = {
                "labor_per_hour": e_labor_hour,
                "outlet_install": e_outlet,
                "switch_install": e_switch,
                "light_fixture_install": e_light_fixture,
                "panel_upgrade": e_panel_upgrade,
                "new_circuit": e_circuit,
                "gfci_outlet": e_gfci,
                "service_call": e_service_call,
            }
            with st.spinner("Saving electrical rates..."):
                result = update_company(company_id, {"pricing_config": pricing_raw})
            if result:
                st.session_state.company = reload_company()
                st.success("Electrical rates saved!")
            else:
                st.error("Failed to save.")

    # ── Landscaping Rates ───────────────────────────────────────────────────
    with land_tab:
        st.markdown("**Landscaping Base Rates**")
        with st.form("landscaping_rates_form"):
            lc1, lc2 = st.columns(2)
            with lc1:
                l_labor_hour = st.number_input("Labor Rate ($/hour)", value=float(landscaping_defaults.get("labor_per_hour", 65.0)), step=5.0, format="%.2f")
                l_mowing = st.number_input("Mowing ($/1000 sqft)", value=float(landscaping_defaults.get("mowing_per_1000sqft", 35.0)), step=5.0, format="%.2f")
                l_mulch = st.number_input("Mulch Install ($/yard)", value=float(landscaping_defaults.get("mulch_per_yard", 95.0)), step=5.0, format="%.2f")
                l_planting = st.number_input("Plant Install ($/plant)", value=float(landscaping_defaults.get("planting_per_plant", 25.0)), step=5.0, format="%.2f")
            with lc2:
                l_sod = st.number_input("Sod Installation ($/sqft)", value=float(landscaping_defaults.get("sod_per_sqft", 2.50)), step=0.25, format="%.2f")
                l_irrigation = st.number_input("Irrigation Head ($)", value=float(landscaping_defaults.get("irrigation_head", 85.0)), step=5.0, format="%.2f")
                l_cleanup = st.number_input("Cleanup / Hauling ($/hour)", value=float(landscaping_defaults.get("cleanup_per_hour", 55.0)), step=5.0, format="%.2f")
                l_hardscape = st.number_input("Hardscape Labor ($/sqft)", value=float(landscaping_defaults.get("hardscape_labor_per_sqft", 12.0)), step=1.0, format="%.2f")

            save_landscaping = st.form_submit_button("💾 Save Landscaping Rates", use_container_width=False)

        if save_landscaping:
            pricing_raw["landscaping"] = {
                "labor_per_hour": l_labor_hour,
                "mowing_per_1000sqft": l_mowing,
                "mulch_per_yard": l_mulch,
                "planting_per_plant": l_planting,
                "sod_per_sqft": l_sod,
                "irrigation_head": l_irrigation,
                "cleanup_per_hour": l_cleanup,
                "hardscape_labor_per_sqft": l_hardscape,
            }
            with st.spinner("Saving landscaping rates..."):
                result = update_company(company_id, {"pricing_config": pricing_raw})
            if result:
                st.session_state.company = reload_company()
                st.success("Landscaping rates saved!")
            else:
                st.error("Failed to save.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — USER MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("User Management")

    if not is_role("owner", "admin"):
        st.error("Only owners and admins can manage users.")
    else:
        with st.spinner("Loading users..."):
            all_users = get_users_by_company(company_id)

        # Role descriptions
        with st.expander("ℹ️ Role Descriptions"):
            st.markdown("""
| Role | Access Level |
|------|-------------|
| **Owner** | Full access including billing and all settings |
| **Admin** | All features except billing and ownership transfer |
| **Estimator** | Create/edit estimates, view clients and jobs |
| **Crew** | View assigned jobs, check in/out, upload photos |
| **Client** | View their own jobs and proposals only |
""")

        st.markdown(f"**{len(all_users)} user(s) in your company**")

        # ── Users table ────────────────────────────────────────────────────
        if all_users:
            for u in all_users:
                u_id = u.get("id", "")
                u_name = u.get("name", "Unknown")
                u_email = u.get("email", "")
                u_role = u.get("role", "crew")
                u_active = u.get("is_active", True)
                is_current_user = u_id == user["id"]

                role_colors = {
                    "owner": "#7C3AED",
                    "admin": "#2563EB",
                    "estimator": "#059669",
                    "crew": "#D97706",
                    "client": "#6B7280",
                }
                role_color = role_colors.get(u_role, "#6B7280")

                with st.container():
                    uc1, uc2, uc3, uc4, uc5 = st.columns([2.5, 2.5, 1.5, 1, 2])
                    with uc1:
                        you_label = " (You)" if is_current_user else ""
                        st.markdown(f"**{u_name}**{you_label}")
                        st.caption(u_email)
                    with uc2:
                        st.markdown(
                            f'<span style="background:{role_color}22;color:{role_color};'
                            f'padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:600;">'
                            f'{u_role.title()}</span>',
                            unsafe_allow_html=True,
                        )
                    with uc3:
                        if u_active:
                            st.markdown('<span style="color:#10B981;font-size:0.85rem;">● Active</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span style="color:#EF4444;font-size:0.85rem;">● Inactive</span>', unsafe_allow_html=True)
                    with uc4:
                        # Edit role
                        if not is_current_user and is_role("owner"):
                            new_role = st.selectbox(
                                "Role",
                                ["owner", "admin", "estimator", "crew", "client"],
                                index=["owner", "admin", "estimator", "crew", "client"].index(u_role) if u_role in ["owner", "admin", "estimator", "crew", "client"] else 3,
                                key=f"role_select_{u_id}",
                                label_visibility="collapsed",
                            )
                    with uc5:
                        action_cols = st.columns(2)
                        with action_cols[0]:
                            if not is_current_user and is_role("owner"):
                                if st.button(
                                    "Save Role",
                                    key=f"save_role_{u_id}",
                                    use_container_width=True,
                                ):
                                    from utils.db import update_user
                                    with st.spinner("Updating..."):
                                        update_user(u_id, {"role": new_role})
                                    st.success(f"Role updated to {new_role}!")
                                    st.rerun()
                        with action_cols[1]:
                            if not is_current_user:
                                toggle_label = "Deactivate" if u_active else "Activate"
                                if st.button(toggle_label, key=f"toggle_user_{u_id}", use_container_width=True):
                                    from utils.db import update_user
                                    with st.spinner("Updating..."):
                                        update_user(u_id, {"is_active": not u_active})
                                    st.success(f"User {'deactivated' if u_active else 'activated'}!")
                                    st.rerun()
                    st.markdown("---")

        # ── Invite New User ────────────────────────────────────────────────
        st.subheader("➕ Invite New User")
        with st.form("invite_user_form"):
            inv_col1, inv_col2 = st.columns(2)
            with inv_col1:
                inv_name = st.text_input("Full Name *")
                inv_email = st.text_input("Email *")
            with inv_col2:
                inv_phone = st.text_input("Phone (optional)")
                inv_role = st.selectbox("Role", ["crew", "estimator", "admin", "client"])
            inv_password = st.text_input("Temporary Password *", type="password", help="User should change this after first login")
            invite_btn = st.form_submit_button("Send Invite / Create User", use_container_width=False)

        if invite_btn:
            if not inv_name.strip() or not inv_email.strip() or not inv_password.strip():
                st.error("Name, email, and password are required.")
            else:
                from utils.db import create_user as db_create_user
                with st.spinner("Creating user..."):
                    new_user = db_create_user({
                        "company_id": company_id,
                        "name": inv_name.strip(),
                        "email": inv_email.strip().lower(),
                        "password": inv_password.strip(),
                        "role": inv_role,
                        "phone": inv_phone.strip() or None,
                        "is_active": True,
                    })
                if new_user:
                    st.success(f"User '{inv_name}' created with role '{inv_role}'! They can log in with their email and the temporary password.")
                    st.rerun()
                else:
                    st.error("Failed to create user. Email may already be in use.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 — DATABASE SETUP
# ──────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Database Setup — Supabase")

    # ── Connection status ───────────────────────────────────────────────────
    sb_client = get_supabase()
    if sb_client:
        st.markdown(
            '<div style="background:#D1FAE5;border-left:4px solid #10B981;'
            'padding:1rem;border-radius:8px;margin-bottom:1rem;">'
            '<strong>✅ Database Connected</strong> — Supabase connection is active.'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#FEE2E2;border-left:4px solid #EF4444;'
            'padding:1rem;border-radius:8px;margin-bottom:1rem;">'
            '<strong>❌ Database Not Connected</strong> — Follow the setup steps below.'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Step-by-step guide ─────────────────────────────────────────────────
    st.markdown("### 🛠️ Step-by-Step Supabase Setup")

    with st.expander("Step 1 — Create Supabase Project", expanded=not sb_client):
        st.markdown("""
**1.** Go to [supabase.com](https://supabase.com) and create a free account.

**2.** Click **"New Project"** and fill in:
   - Project name (e.g., "ServicePro OS")
   - Database password (save this!)
   - Region (choose nearest to you)

**3.** Wait for the project to initialize (~2 minutes). You'll see a progress indicator.
""")

    with st.expander("Step 2 — Get Your Credentials", expanded=not sb_client):
        st.markdown("""
**4.** In your Supabase project dashboard, click **"Project Settings"** (gear icon in sidebar).

**5.** Click **"API"** in the settings menu.

**6.** You'll see two important values:
   - **Project URL** — looks like `https://abcdefghijklm.supabase.co`
   - **service_role key** — a long JWT token (use this, NOT the anon key)

⚠️ Use the **service_role** key, not the **anon** key. The service_role key bypasses Row Level Security which is needed for the app to function.
""")

    with st.expander("Step 3 — Add to Streamlit Secrets", expanded=not sb_client):
        st.markdown("**7.** In Streamlit Cloud: go to your app → **Settings** → **Secrets**")
        st.markdown("**8.** Paste the following (replacing with your actual values):")
        st.code(
            'SUPABASE_URL = "https://your-project-id.supabase.co"\n'
            'SUPABASE_KEY = "your-service-role-key-here"',
            language="toml",
        )
        st.markdown("**9.** Click **Save** and wait for the app to restart.")

    with st.expander("Step 4 — Run Database Schema", expanded=not sb_client):
        st.markdown("**10.** In your Supabase project, go to **SQL Editor** → **New Query**")
        st.markdown("**11.** Paste and run the following SQL to create all required tables:")
        st.code(SCHEMA_SQL, language="sql")
        st.success("This creates all required tables: companies, users, clients, estimates, jobs, payments, messages, and more.")

    with st.expander("Step 5 — Restart App", expanded=not sb_client):
        st.markdown("""
**12.** After adding secrets and running the schema:
   - In Streamlit Cloud: click **Reboot app** in the app menu
   - Or wait ~60 seconds for automatic restart

**13.** Return to this Settings page and click **"Test Database Connection"** below to verify.
""")

    st.markdown("---")

    # ── Connection test ─────────────────────────────────────────────────────
    st.markdown("### 🔌 Test Database Connection")

    if st.button("🔌 Test Database Connection", use_container_width=False):
        with st.spinner("Testing connection..."):
            try:
                test_sb = get_supabase()
                if not test_sb:
                    st.error("Could not create Supabase client. Check that SUPABASE_URL and SUPABASE_KEY are set in Streamlit secrets.")
                else:
                    # Try to count tables
                    tables_to_check = ["companies", "users", "clients", "jobs", "estimates", "payments", "messages"]
                    found_tables = []
                    missing_tables = []
                    for table in tables_to_check:
                        try:
                            result = test_sb.table(table).select("id", count="exact").limit(1).execute()
                            found_tables.append(f"✅ `{table}` ({result.count or 0} records)")
                        except Exception:
                            missing_tables.append(f"❌ `{table}` — not found or not accessible")

                    st.success("Supabase connection successful!")
                    st.markdown("**Table Status:**")
                    for t in found_tables:
                        st.markdown(t)
                    for t in missing_tables:
                        st.warning(t)

                    if missing_tables:
                        st.info("Some tables are missing. Run the SQL schema in Step 4 above to create them.")
            except Exception as e:
                st.error(f"Connection test failed: {str(e)}")

    # ── Show current secrets status ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔐 Secrets Status")
    try:
        url_set = bool(st.secrets.get("SUPABASE_URL", ""))
        key_set = bool(st.secrets.get("SUPABASE_KEY", ""))
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if url_set:
                st.success("SUPABASE_URL is set")
            else:
                st.error("SUPABASE_URL is not set")
        with col_s2:
            if key_set:
                st.success("SUPABASE_KEY is set")
            else:
                st.error("SUPABASE_KEY is not set")
    except Exception:
        st.warning("Could not check secrets. This is normal in local development — add secrets to .streamlit/secrets.toml.")
