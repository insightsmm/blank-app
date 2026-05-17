import streamlit as st
from datetime import datetime, date, timedelta

from utils.auth import check_authentication, is_role
from utils.styles import (
    inject_css,
    render_badge,
    render_page_header,
    format_currency,
    format_date,
    COLORS,
)
from utils.db import (
    get_clients,
    get_client,
    create_client,
    get_estimates,
    get_estimate,
    create_estimate,
    update_estimate,
    create_proposal,
    get_proposal_by_estimate,
    update_proposal,
    get_unread_notifications_count,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Estimates | ServicePro OS",
    page_icon="📝",
    layout="wide",
)

# ── Auth guard ───────────────────────────────────────────────────────────────
if not check_authentication():
    st.warning("Please log in from the home page.")
    st.stop()

inject_css()

# ── Convenience vars ─────────────────────────────────────────────────────────
user = st.session_state.user
company = st.session_state.company
role = st.session_state.role
company_id = company["id"]
user_id = user["id"]

TRADE_ICONS = {"painting": "🎨", "electrical": "⚡", "landscaping": "🌿"}

# ── Session state defaults ────────────────────────────────────────────────────
for k, v in {
    "est_trade": None,
    "est_client_id": None,
    "est_step": 1,
    "est_line_items": [],
    "est_subtotal": 0.0,
    "est_total": 0.0,
    "est_tax_rate": 0.0,
    "est_discount": 0.0,
    "est_generated_pdf": None,
    "est_saved_id": None,
    "est_ai_suggestions": None,
    "new_client_inline": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Pre-select client if navigated from clients page
if "estimate_preset_client_id" in st.session_state and st.session_state.estimate_preset_client_id:
    st.session_state.est_client_id = st.session_state.estimate_preset_client_id
    st.session_state.estimate_preset_client_id = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">⚡ ServicePro OS</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div style="margin-bottom:0.5rem;">
            <div style="font-weight:700;font-size:1rem;color:#1F2937;">{company.get('name','My Company')}</div>
            <div style="font-size:0.85rem;color:#6B7280;">{user.get('name','')}</div>
            <div style="margin-top:4px;">{render_badge(role)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        unread = get_unread_notifications_count(user_id)
        if unread > 0:
            st.markdown(
                f'<div style="background:#FEF3C7;color:#92400E;padding:6px 12px;'
                f'border-radius:8px;font-size:0.85rem;font-weight:600;margin-top:8px;">'
                f'🔔 {unread} unread notification{"s" if unread != 1 else ""}</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    st.markdown("---")
    st.markdown("**Navigation**")
    st.page_link("pages/1_Dashboard.py", label="📊 Dashboard")
    st.page_link("pages/2_Clients.py", label="👥 Clients")
    st.page_link("pages/3_Estimates.py", label="📝 Estimates")

render_page_header("📝 Smart Estimator", "Generate professional estimates in minutes")

# ── Load clients ──────────────────────────────────────────────────────────────
all_clients = get_clients(company_id)
client_map = {c["id"]: c for c in all_clients}
client_options = {c["id"]: c["name"] for c in all_clients}

# ─────────────────────────────────────────────────────────────────────────────
# PRICING CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

PAINTING_RATES = {
    "labor_per_sqft": {"Economy": 0.45, "Standard": 0.65, "Premium": 0.90, "Luxury": 1.25},
    "paint_per_sqft": {"Economy": 0.18, "Standard": 0.28, "Premium": 0.45, "Luxury": 0.70},
    "door_unit": 45,
    "window_unit": 25,
    "trim_per_lf": 2.50,
    "prep_washing": 150,
    "prep_drywall_minor": 200,
    "prep_drywall_major": 650,
    "priming_per_sqft": 0.15,
    "ceiling_multiplier": {
        "Standard 8ft": 1.0,
        "9ft": 1.1,
        "10ft": 1.2,
        "Vaulted 12ft+": 1.45,
    },
    "condition_multiplier": {
        "Excellent": 1.0,
        "Good": 1.1,
        "Fair": 1.25,
        "Poor - needs heavy prep": 1.5,
    },
    "cabinet_per_unit": 85,
    "accent_wall": 120,
    "exterior_per_sqft": 0.80,
    "deck_staining": 350,
}

ELECTRICAL_RATES = {
    "service_base": {
        "Residential New": 800,
        "Residential Repair": 250,
        "Commercial": 1500,
        "Emergency": 500,
    },
    "outlet": 125,
    "fixture": 85,
    "ceiling_fan": 150,
    "switch": 65,
    "gfci": 145,
    "panel_upgrade": {
        "100A to 150A": 1200,
        "100A to 200A": 1600,
        "150A to 200A": 1000,
        "Upgrade to 400A": 3800,
    },
    "ev_charger": 850,
    "generator": 1200,
    "smart_home_per_device": 200,
    "security_wiring": 150,
    "permit": 350,
}

LANDSCAPING_RATES = {
    "mowing": {"Weekly": 45, "Bi-weekly": 55, "Monthly": 75},
    "edging_per_visit": 25,
    "fertilization_per_app": 85,
    "aeration_per_sqft": 0.08,
    "mulch_per_yard": 75,
    "hedge_trim": 95,
    "tree_trim_per_tree": 125,
    "leaf_cleanup": 180,
    "seasonal_cleanup": 250,
    "irrigation_per_zone": 800,
    "irrigation_repair": 150,
    "irrigation_winterization": 95,
}


# ─────────────────────────────────────────────────────────────────────────────
# PRICING CALCULATORS
# ─────────────────────────────────────────────────────────────────────────────

def calc_painting(inputs: dict) -> list:
    """Return line items list for painting estimate."""
    items = []
    sqft = inputs.get("sqft", 0)
    quality = inputs.get("quality", "Standard")
    coats = inputs.get("coats", 2)
    ceiling = inputs.get("ceiling", "Standard 8ft")
    condition = inputs.get("condition", "Good")
    doors = inputs.get("doors", 0)
    windows = inputs.get("windows", 0)
    trim_lf = inputs.get("trim_lf", 0)

    ceil_mult = PAINTING_RATES["ceiling_multiplier"].get(ceiling, 1.0)
    cond_mult = PAINTING_RATES["condition_multiplier"].get(condition, 1.0)
    labor_rate = PAINTING_RATES["labor_per_sqft"][quality]
    paint_rate = PAINTING_RATES["paint_per_sqft"][quality]

    if sqft > 0:
        labor = sqft * labor_rate * coats * cond_mult * ceil_mult
        items.append({"description": f"Interior Labor ({quality} — {coats} coat{'s' if coats > 1 else ''}, {condition})", "qty": sqft, "unit_price": round(labor / sqft, 4), "total": round(labor, 2)})

        materials = sqft * paint_rate * coats
        items.append({"description": f"Paint Materials ({quality} grade)", "qty": sqft, "unit_price": paint_rate * coats, "total": round(materials, 2)})

    if doors > 0:
        total = doors * PAINTING_RATES["door_unit"]
        items.append({"description": f"Door Painting", "qty": doors, "unit_price": PAINTING_RATES["door_unit"], "total": total})

    if windows > 0:
        total = windows * PAINTING_RATES["window_unit"]
        items.append({"description": "Window Trim Painting", "qty": windows, "unit_price": PAINTING_RATES["window_unit"], "total": total})

    if trim_lf > 0:
        total = round(trim_lf * PAINTING_RATES["trim_per_lf"], 2)
        items.append({"description": "Trim & Baseboard Painting", "qty": trim_lf, "unit_price": PAINTING_RATES["trim_per_lf"], "total": total})

    if inputs.get("pressure_washing"):
        items.append({"description": "Pressure Washing", "qty": 1, "unit_price": PAINTING_RATES["prep_washing"], "total": PAINTING_RATES["prep_washing"]})

    if inputs.get("drywall_minor"):
        items.append({"description": "Drywall Repair (Minor)", "qty": 1, "unit_price": PAINTING_RATES["prep_drywall_minor"], "total": PAINTING_RATES["prep_drywall_minor"]})

    if inputs.get("drywall_major"):
        items.append({"description": "Drywall Repair (Major)", "qty": 1, "unit_price": PAINTING_RATES["prep_drywall_major"], "total": PAINTING_RATES["prep_drywall_major"]})

    if inputs.get("priming") and sqft > 0:
        primer_total = round(sqft * PAINTING_RATES["priming_per_sqft"], 2)
        items.append({"description": "Primer Coat", "qty": sqft, "unit_price": PAINTING_RATES["priming_per_sqft"], "total": primer_total})

    cabinets = inputs.get("cabinets", 0)
    if inputs.get("cabinet_painting") and cabinets > 0:
        total = cabinets * PAINTING_RATES["cabinet_per_unit"]
        items.append({"description": "Cabinet Painting", "qty": cabinets, "unit_price": PAINTING_RATES["cabinet_per_unit"], "total": total})

    accent_count = inputs.get("accent_count", 0)
    if inputs.get("accent_walls") and accent_count > 0:
        total = accent_count * PAINTING_RATES["accent_wall"]
        items.append({"description": "Accent Wall Painting", "qty": accent_count, "unit_price": PAINTING_RATES["accent_wall"], "total": total})

    ext_sqft = inputs.get("exterior_sqft", 0)
    if inputs.get("exterior_painting") and ext_sqft > 0:
        total = round(ext_sqft * PAINTING_RATES["exterior_per_sqft"], 2)
        items.append({"description": "Exterior Painting", "qty": ext_sqft, "unit_price": PAINTING_RATES["exterior_per_sqft"], "total": total})

    if inputs.get("deck_staining"):
        items.append({"description": "Deck/Fence Staining", "qty": 1, "unit_price": PAINTING_RATES["deck_staining"], "total": PAINTING_RATES["deck_staining"]})

    return items


def calc_electrical(inputs: dict) -> list:
    """Return line items list for electrical estimate."""
    items = []
    service_type = inputs.get("service_type", "Residential Repair")
    emergency_mult = 2.0 if inputs.get("emergency_service") else 1.0
    after_hours_mult = 1.5 if inputs.get("after_hours") else 1.0
    base_mult = max(emergency_mult, after_hours_mult)

    base_cost = ELECTRICAL_RATES["service_base"].get(service_type, 250) * base_mult
    label = service_type
    if inputs.get("emergency_service"):
        label += " (Emergency 2×)"
    elif inputs.get("after_hours"):
        label += " (After Hours 1.5×)"
    items.append({"description": f"Service Call — {label}", "qty": 1, "unit_price": base_cost, "total": round(base_cost, 2)})

    if inputs.get("panel_upgrade") and inputs.get("panel_upgrade_type"):
        cost = ELECTRICAL_RATES["panel_upgrade"].get(inputs["panel_upgrade_type"], 1600)
        items.append({"description": f"Panel Upgrade ({inputs['panel_upgrade_type']})", "qty": 1, "unit_price": cost, "total": cost})

    qty_map = [
        ("outlets", "New Outlet Installation", "outlet"),
        ("fixtures", "Light Fixture Installation", "fixture"),
        ("ceiling_fans", "Ceiling Fan Installation", "ceiling_fan"),
        ("switches", "Switch Installation", "switch"),
        ("gfci_outlets", "GFCI Outlet Installation", "gfci"),
    ]
    for key, label_str, rate_key in qty_map:
        qty = inputs.get(key, 0)
        if qty > 0:
            unit = ELECTRICAL_RATES[rate_key]
            items.append({"description": label_str, "qty": qty, "unit_price": unit, "total": qty * unit})

    if inputs.get("ev_charger"):
        items.append({"description": "EV Charger Installation", "qty": 1, "unit_price": ELECTRICAL_RATES["ev_charger"], "total": ELECTRICAL_RATES["ev_charger"]})

    if inputs.get("generator"):
        items.append({"description": "Generator Hookup", "qty": 1, "unit_price": ELECTRICAL_RATES["generator"], "total": ELECTRICAL_RATES["generator"]})

    smart_devices = inputs.get("smart_home_devices", 0)
    if inputs.get("smart_home") and smart_devices > 0:
        cost = smart_devices * ELECTRICAL_RATES["smart_home_per_device"]
        items.append({"description": "Smart Home Wiring", "qty": smart_devices, "unit_price": ELECTRICAL_RATES["smart_home_per_device"], "total": cost})

    if inputs.get("security_wiring"):
        items.append({"description": "Security System Wiring", "qty": 1, "unit_price": ELECTRICAL_RATES["security_wiring"], "total": ELECTRICAL_RATES["security_wiring"]})

    if inputs.get("permit_required"):
        items.append({"description": "Permit & Inspection Fee", "qty": 1, "unit_price": ELECTRICAL_RATES["permit"], "total": ELECTRICAL_RATES["permit"]})

    return items


def calc_landscaping(inputs: dict) -> list:
    """Return line items list for landscaping estimate."""
    items = []
    lot_sqft = inputs.get("lot_sqft", 0)

    mow_freq = inputs.get("mow_frequency", "Bi-weekly")
    if inputs.get("mowing"):
        visits_per_year = {"Weekly": 48, "Bi-weekly": 24, "Monthly": 12}.get(mow_freq, 24)
        cost_per_visit = LANDSCAPING_RATES["mowing"].get(mow_freq, 55)
        total = visits_per_year * cost_per_visit
        items.append({"description": f"Lawn Mowing ({mow_freq} — {visits_per_year} visits/yr)", "qty": visits_per_year, "unit_price": cost_per_visit, "total": total})

    if inputs.get("edging"):
        visits = {"Weekly": 48, "Bi-weekly": 24, "Monthly": 12}.get(mow_freq, 24)
        cost = visits * LANDSCAPING_RATES["edging_per_visit"]
        items.append({"description": f"Edging ({visits} visits/yr)", "qty": visits, "unit_price": LANDSCAPING_RATES["edging_per_visit"], "total": cost})

    fert_apps = inputs.get("fertilization_apps", 4)
    if inputs.get("fertilization") and fert_apps > 0:
        cost = fert_apps * LANDSCAPING_RATES["fertilization_per_app"]
        items.append({"description": f"Fertilization ({fert_apps} applications)", "qty": fert_apps, "unit_price": LANDSCAPING_RATES["fertilization_per_app"], "total": cost})

    if inputs.get("aeration") and lot_sqft > 0:
        cost = round(lot_sqft * LANDSCAPING_RATES["aeration_per_sqft"], 2)
        items.append({"description": "Lawn Aeration", "qty": lot_sqft, "unit_price": LANDSCAPING_RATES["aeration_per_sqft"], "total": cost})

    mulch_yards = inputs.get("mulch_yards", 0)
    if inputs.get("mulching") and mulch_yards > 0:
        cost = mulch_yards * LANDSCAPING_RATES["mulch_per_yard"]
        items.append({"description": f"Mulching ({mulch_yards} cu yds)", "qty": mulch_yards, "unit_price": LANDSCAPING_RATES["mulch_per_yard"], "total": cost})

    if inputs.get("hedge_trim"):
        items.append({"description": "Hedge Trimming", "qty": 1, "unit_price": LANDSCAPING_RATES["hedge_trim"], "total": LANDSCAPING_RATES["hedge_trim"]})

    tree_count = inputs.get("trim_tree_count", 0)
    if inputs.get("tree_trimming") and tree_count > 0:
        cost = tree_count * LANDSCAPING_RATES["tree_trim_per_tree"]
        items.append({"description": f"Tree Trimming ({tree_count} trees)", "qty": tree_count, "unit_price": LANDSCAPING_RATES["tree_trim_per_tree"], "total": cost})

    if inputs.get("leaf_cleanup"):
        items.append({"description": "Leaf Cleanup", "qty": 1, "unit_price": LANDSCAPING_RATES["leaf_cleanup"], "total": LANDSCAPING_RATES["leaf_cleanup"]})

    if inputs.get("seasonal_cleanup"):
        items.append({"description": "Seasonal Cleanup", "qty": 1, "unit_price": LANDSCAPING_RATES["seasonal_cleanup"], "total": LANDSCAPING_RATES["seasonal_cleanup"]})

    irr_zones = inputs.get("irrigation_zones", 0)
    if inputs.get("new_irrigation") and irr_zones > 0:
        cost = irr_zones * LANDSCAPING_RATES["irrigation_per_zone"]
        items.append({"description": f"New Irrigation System ({irr_zones} zones)", "qty": irr_zones, "unit_price": LANDSCAPING_RATES["irrigation_per_zone"], "total": cost})

    if inputs.get("irrigation_repair"):
        items.append({"description": "Irrigation System Repair", "qty": 1, "unit_price": LANDSCAPING_RATES["irrigation_repair"], "total": LANDSCAPING_RATES["irrigation_repair"]})

    if inputs.get("irrigation_winterization"):
        items.append({"description": "Irrigation Winterization", "qty": 1, "unit_price": LANDSCAPING_RATES["irrigation_winterization"], "total": LANDSCAPING_RATES["irrigation_winterization"]})

    return items


def render_line_items_table(line_items: list, subtotal: float, tax_rate: float, discount: float) -> float:
    """Render the live pricing table and return total."""
    tax_amount = subtotal * (tax_rate / 100)
    total = max(0.0, subtotal + tax_amount - discount)

    if not line_items:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#9CA3AF;">Select options above to see pricing.</div>',
            unsafe_allow_html=True,
        )
        return 0.0

    # Header
    st.markdown(
        """
        <table class="data-table" style="width:100%;">
          <thead>
            <tr>
              <th style="text-align:left;">Description</th>
              <th style="text-align:right;">Qty</th>
              <th style="text-align:right;">Unit Price</th>
              <th style="text-align:right;">Total</th>
            </tr>
          </thead>
          <tbody>
        """,
        unsafe_allow_html=True,
    )
    for li in line_items:
        desc = li.get("description", "")
        qty = li.get("qty", 1)
        unit = li.get("unit_price", 0)
        tot = li.get("total", 0)
        qty_str = f"{qty:,.0f}" if isinstance(qty, (int, float)) and qty == int(qty) else f"{qty:,.2f}"
        st.markdown(
            f"<tr>"
            f"<td>{desc}</td>"
            f"<td style='text-align:right;'>{qty_str}</td>"
            f"<td style='text-align:right;'>{format_currency(unit)}</td>"
            f"<td style='text-align:right;'><strong>{format_currency(tot)}</strong></td>"
            f"</tr>",
            unsafe_allow_html=True,
        )

    # Totals footer
    st.markdown(
        f"""
        <tr style="border-top:2px solid #E5E7EB;">
          <td colspan="3" style="text-align:right;font-weight:600;color:#6B7280;">Subtotal</td>
          <td style="text-align:right;font-weight:600;">{format_currency(subtotal)}</td>
        </tr>
        <tr>
          <td colspan="3" style="text-align:right;color:#6B7280;">Tax ({tax_rate:.1f}%)</td>
          <td style="text-align:right;">{format_currency(tax_amount)}</td>
        </tr>
        <tr>
          <td colspan="3" style="text-align:right;color:#6B7280;">Discount</td>
          <td style="text-align:right;color:#EF4444;">-{format_currency(discount)}</td>
        </tr>
        <tr style="background:#F0FDF4;">
          <td colspan="3" style="text-align:right;font-weight:800;font-size:1.1rem;color:#065F46;">TOTAL</td>
          <td style="text-align:right;font-weight:800;font-size:1.1rem;color:#065F46;">{format_currency(total)}</td>
        </tr>
        </tbody></table>
        """,
        unsafe_allow_html=True,
    )
    return total


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_all, tab_new, tab_proposals = st.tabs(
    ["📋 All Estimates", "✨ New Estimate", "📬 Proposals"]
)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — ALL ESTIMATES
# ═════════════════════════════════════════════════════════════════════════════
with tab_all:
    # Filters
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    with f1:
        filter_status = st.selectbox(
            "Status",
            options=["All", "draft", "sent", "approved", "rejected"],
            key="filter_est_status",
        )
    with f2:
        filter_trade = st.selectbox(
            "Trade Type",
            options=["All", "painting", "electrical", "landscaping"],
            key="filter_est_trade",
        )
    with f3:
        filter_date = st.selectbox(
            "Date Range",
            options=["All Time", "This Month", "Last 30 Days", "Last 90 Days"],
            key="filter_est_date",
        )
    with f4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="refresh_estimates", use_container_width=True):
            st.rerun()

    # Load estimates
    status_arg = None if filter_status == "All" else filter_status
    trade_arg = None if filter_trade == "All" else filter_trade
    estimates = get_estimates(company_id, status=status_arg, trade_type=trade_arg)

    # Date filter
    if filter_date != "All Time" and estimates:
        now = datetime.now()
        if filter_date == "This Month":
            cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif filter_date == "Last 30 Days":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(days=90)
        cutoff_str = cutoff.isoformat()
        estimates = [e for e in estimates if (e.get("created_at") or "") >= cutoff_str]

    # Revenue summary
    draft_total = sum(float(e.get("total", 0) or 0) for e in estimates if e.get("status") == "draft")
    sent_total = sum(float(e.get("total", 0) or 0) for e in estimates if e.get("status") == "sent")
    approved_total = sum(float(e.get("total", 0) or 0) for e in estimates if e.get("status") == "approved")

    st.markdown(
        f"""
        <div style="display:flex;gap:1.5rem;margin-bottom:1rem;flex-wrap:wrap;">
          <div style="background:#F9FAFB;border-radius:10px;padding:0.75rem 1.25rem;border:1px solid #E5E7EB;">
            <span style="color:#6B7280;font-size:0.82rem;font-weight:600;">DRAFT</span>
            <span style="font-weight:700;color:#374151;margin-left:8px;">{format_currency(draft_total)}</span>
          </div>
          <div style="background:#DBEAFE;border-radius:10px;padding:0.75rem 1.25rem;border:1px solid #BFDBFE;">
            <span style="color:#1E40AF;font-size:0.82rem;font-weight:600;">SENT</span>
            <span style="font-weight:700;color:#1E40AF;margin-left:8px;">{format_currency(sent_total)}</span>
          </div>
          <div style="background:#D1FAE5;border-radius:10px;padding:0.75rem 1.25rem;border:1px solid #A7F3D0;">
            <span style="color:#065F46;font-size:0.82rem;font-weight:600;">APPROVED</span>
            <span style="font-weight:700;color:#065F46;margin-left:8px;">{format_currency(approved_total)}</span>
          </div>
          <div style="background:white;border-radius:10px;padding:0.75rem 1.25rem;border:1px solid #E5E7EB;">
            <span style="color:#6B7280;font-size:0.82rem;font-weight:600;">TOTAL RECORDS</span>
            <span style="font-weight:700;color:#374151;margin-left:8px;">{len(estimates)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not estimates:
        st.markdown(
            """
            <div style="text-align:center;padding:4rem 1rem;color:#9CA3AF;
                        background:white;border-radius:12px;border:1px solid #F3F4F6;">
              <div style="font-size:3rem;">📝</div>
              <div style="font-size:1.2rem;font-weight:700;color:#374151;margin-top:0.5rem;">No estimates found</div>
              <div style="font-size:0.9rem;">Create a new estimate using the "New Estimate" tab.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for est in estimates:
            eid = est["id"]
            short_id = str(eid)[:8].upper()
            client_id_e = est.get("client_id")
            client_name = client_map.get(client_id_e, {}).get("name", "Unknown") if client_id_e else "—"
            trade = est.get("trade_type", "")
            trade_icon = TRADE_ICONS.get(trade, "🏠")
            trade_label = f"{trade_icon} {trade.title()}"
            line_items = est.get("line_items", []) or []
            total = format_currency(est.get("total", 0))
            status = est.get("status", "draft")
            badge = render_badge(status)
            date_str = format_date(est.get("created_at", ""))

            with st.expander(f"#{short_id} — {client_name} — {trade_label} — {total}"):
                # Estimate detail
                col_info, col_actions = st.columns([3, 1])

                with col_info:
                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.markdown(f"**Status:** {badge}", unsafe_allow_html=True)
                        st.markdown(f"**Client:** {client_name}")
                    with d2:
                        st.markdown(f"**Trade:** {trade_label}")
                        st.markdown(f"**Line Items:** {len(line_items)}")
                    with d3:
                        st.markdown(f"**Total:** {total}")
                        st.markdown(f"**Created:** {date_str}")

                    if est.get("notes"):
                        st.markdown(f"**Notes:** {est['notes']}")

                    if line_items:
                        st.markdown("**Line Items:**")
                        for li in line_items[:5]:
                            st.markdown(
                                f"- {li.get('description', '')} — {format_currency(li.get('total', 0))}"
                            )
                        if len(line_items) > 5:
                            st.caption(f"…and {len(line_items) - 5} more items")

                with col_actions:
                    client_obj = client_map.get(client_id_e) if client_id_e else None
                    client_email = client_obj.get("email", "") if client_obj else ""

                    # Send estimate
                    if status in ("draft", "sent"):
                        if st.button("📧 Send", key=f"send_est_{eid}", use_container_width=True):
                            if not client_email:
                                st.warning("Client has no email.")
                            else:
                                try:
                                    from utils.gmail_integration import send_proposal_email
                                    gmail_email = company.get("gmail_email", "")
                                    gmail_pass = company.get("gmail_app_password", "")
                                    if not gmail_email:
                                        st.warning("Configure Gmail in company settings first.")
                                    else:
                                        send_proposal_email(
                                            gmail_email=gmail_email,
                                            gmail_app_password=gmail_pass,
                                            client=client_obj,
                                            estimate=est,
                                            company=company,
                                        )
                                        update_estimate(eid, {
                                            "status": "sent",
                                            "sent_at": datetime.utcnow().isoformat(),
                                        })
                                        st.success("✅ Sent!")
                                        st.rerun()
                                except Exception as exc:
                                    st.error(f"Error: {exc}")

                    # Convert to Job
                    if status == "approved":
                        if st.button("🔨 Convert to Job", key=f"convert_{eid}", use_container_width=True):
                            try:
                                from utils.db import create_job
                                job_payload = {
                                    "company_id": company_id,
                                    "client_id": client_id_e,
                                    "estimate_id": eid,
                                    "title": f"{trade.title()} Job — {client_name}",
                                    "description": est.get("notes", ""),
                                    "trade_type": trade,
                                    "status": "scheduled",
                                    "address": client_obj.get("address") if client_obj else None,
                                    "city": client_obj.get("city") if client_obj else None,
                                    "state": client_obj.get("state") if client_obj else None,
                                    "zip": client_obj.get("zip") if client_obj else None,
                                }
                                new_job = create_job(job_payload)
                                if new_job:
                                    st.success(f"✅ Job created! ID: {str(new_job['id'])[:8].upper()}")
                                else:
                                    st.error("Failed to create job.")
                            except Exception as exc:
                                st.error(f"Error: {exc}")

                    # Download PDF
                    if st.button("📄 PDF", key=f"pdf_all_{eid}", use_container_width=True):
                        try:
                            from utils.pdf_generator import generate_proposal_pdf
                            pdf_bytes = generate_proposal_pdf(est, client_obj or {}, company, line_items)
                            st.download_button(
                                "📥 Download PDF",
                                pdf_bytes,
                                f"estimate_{short_id}.pdf",
                                "application/pdf",
                                key=f"dl_all_{eid}",
                            )
                        except Exception as exc:
                            st.error(f"PDF error: {exc}")

                    # Delete
                    if is_role("owner", "admin"):
                        if st.button("🗑️ Delete", key=f"del_est_{eid}", use_container_width=True):
                            try:
                                from utils.db import get_supabase
                                sb = get_supabase()
                                if sb:
                                    sb.table("estimates").delete().eq("id", eid).execute()
                                    st.success("Estimate deleted.")
                                    st.rerun()
                            except Exception as exc:
                                st.error(f"Delete failed: {exc}")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — NEW ESTIMATE
# ═════════════════════════════════════════════════════════════════════════════
with tab_new:
    # ── STEP 1: Client + Trade ──────────────────────────────────────────────
    st.markdown("### Step 1 — Select Client & Trade")

    s1c1, s1c2 = st.columns(2)

    with s1c1:
        st.markdown("**Client**")
        client_ids = list(client_options.keys())
        client_labels = [client_options[cid] for cid in client_ids]

        # Default selection
        default_idx = 0
        if st.session_state.est_client_id and st.session_state.est_client_id in client_ids:
            default_idx = client_ids.index(st.session_state.est_client_id)

        if client_ids:
            selected_label = st.selectbox(
                "Select Client",
                options=["— Select a client —"] + client_labels,
                index=default_idx + 1 if st.session_state.est_client_id else 0,
                key="est_client_select",
                label_visibility="collapsed",
            )
            if selected_label != "— Select a client —":
                idx = client_labels.index(selected_label)
                st.session_state.est_client_id = client_ids[idx]
            else:
                st.session_state.est_client_id = None
        else:
            st.warning("No clients yet. Add a client first.")

        # Inline new client
        with st.expander("➕ Or add a new client"):
            with st.form("inline_new_client"):
                ic1, ic2, ic3 = st.columns(3)
                with ic1:
                    ic_name = st.text_input("Name *", key="ic_name")
                with ic2:
                    ic_email = st.text_input("Email", key="ic_email")
                with ic3:
                    ic_phone = st.text_input("Phone", key="ic_phone")
                ic_submitted = st.form_submit_button("Add Client", use_container_width=True)
                if ic_submitted:
                    if not ic_name.strip():
                        st.error("Name is required.")
                    else:
                        new_c = create_client({
                            "company_id": company_id,
                            "name": ic_name.strip(),
                            "email": ic_email.strip() or None,
                            "phone": ic_phone.strip() or None,
                        })
                        if new_c:
                            st.success(f"✅ Added '{ic_name}'")
                            st.session_state.est_client_id = new_c["id"]
                            st.rerun()
                        else:
                            st.error("Failed to add client.")

    with s1c2:
        st.markdown("**Trade Type**")
        trade_cols = st.columns(3)
        trade_options = [
            ("painting", "🎨 Painting"),
            ("electrical", "⚡ Electrical"),
            ("landscaping", "🌿 Landscaping"),
        ]
        for i, (trade_key, trade_label) in enumerate(trade_options):
            with trade_cols[i]:
                is_selected = st.session_state.est_trade == trade_key
                btn_style = "primary" if is_selected else "secondary"
                if st.button(
                    trade_label,
                    key=f"trade_btn_{trade_key}",
                    use_container_width=True,
                    type=btn_style,
                ):
                    st.session_state.est_trade = trade_key
                    st.rerun()

        if st.session_state.est_trade:
            icon = TRADE_ICONS.get(st.session_state.est_trade, "")
            st.markdown(
                f'<div style="background:#D1FAE5;color:#065F46;padding:8px 16px;border-radius:8px;font-weight:600;">'
                f'{icon} {st.session_state.est_trade.title()} selected</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── STEP 2 + 3: Inputs + Live Calculation ────────────────────────────────
    if not st.session_state.est_trade:
        st.info("Select a trade type above to continue.")
        st.stop()

    if not st.session_state.est_client_id:
        st.info("Select a client above to continue.")
        st.stop()

    selected_client = client_map.get(st.session_state.est_client_id, {})
    selected_client_name = selected_client.get("name", "Unknown Client")

    st.markdown(f"### Step 2 — {TRADE_ICONS.get(st.session_state.est_trade, '')} {st.session_state.est_trade.title()} Estimator")
    st.markdown(f"*Client: **{selected_client_name}***")

    inputs_col, results_col = st.columns([1, 1])

    with inputs_col:
        inputs_data = {}

        # ── PAINTING INPUTS ───────────────────────────────────────────────────
        if st.session_state.est_trade == "painting":
            st.markdown("#### 🏠 Property Details")
            inputs_data["sqft"] = st.number_input("Total Square Footage", min_value=0, max_value=10000, value=1000, step=50, key="p_sqft")
            inputs_data["rooms"] = st.slider("Number of Rooms", 1, 20, 4, key="p_rooms")
            inputs_data["ceiling"] = st.selectbox(
                "Ceiling Height",
                ["Standard 8ft", "9ft", "10ft", "Vaulted 12ft+"],
                key="p_ceiling",
            )
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                inputs_data["doors"] = st.number_input("Doors", 0, 30, 6, key="p_doors")
            with pc2:
                inputs_data["windows"] = st.number_input("Windows", 0, 50, 8, key="p_windows")
            with pc3:
                inputs_data["trim_lf"] = st.number_input("Trim Linear Ft", 0, 500, 0, key="p_trim")

            st.markdown("#### 🎨 Paint Specifications")
            inputs_data["quality"] = st.selectbox(
                "Paint Quality",
                ["Economy", "Standard", "Premium", "Luxury"],
                index=1,
                key="p_quality",
            )
            inputs_data["coats"] = st.selectbox(
                "Number of Coats",
                [1, 2, 3],
                index=1,
                format_func=lambda x: f"{x} coat{'s' if x > 1 else ''}",
                key="p_coats",
            )
            inputs_data["condition"] = st.selectbox(
                "Wall Condition",
                ["Excellent", "Good", "Fair", "Poor - needs heavy prep"],
                index=1,
                key="p_condition",
            )

            st.markdown("#### 🛠️ Prep Work")
            pp1, pp2 = st.columns(2)
            with pp1:
                inputs_data["pressure_washing"] = st.checkbox("Pressure Washing", key="p_pw")
                inputs_data["drywall_minor"] = st.checkbox("Drywall Repair (Minor)", key="p_dw_min")
            with pp2:
                inputs_data["drywall_major"] = st.checkbox("Drywall Repair (Major)", key="p_dw_maj")
                inputs_data["priming"] = st.checkbox("Priming Required", key="p_prime")

            st.markdown("#### ✨ Add-On Services")
            pa1, pa2 = st.columns(2)
            with pa1:
                inputs_data["cabinet_painting"] = st.checkbox("Cabinet Painting", key="p_cab")
                if inputs_data["cabinet_painting"]:
                    inputs_data["cabinets"] = st.number_input("Number of Cabinets", 0, 100, 20, key="p_cab_count")
                else:
                    inputs_data["cabinets"] = 0

                inputs_data["accent_walls"] = st.checkbox("Accent Walls", key="p_accent")
                if inputs_data["accent_walls"]:
                    inputs_data["accent_count"] = st.number_input("Number of Accent Walls", 1, 10, 1, key="p_accent_count")
                else:
                    inputs_data["accent_count"] = 0
            with pa2:
                inputs_data["exterior_painting"] = st.checkbox("Exterior Painting", key="p_ext")
                if inputs_data["exterior_painting"]:
                    inputs_data["exterior_sqft"] = st.number_input("Exterior Sq Ft", 0, 5000, 500, key="p_ext_sqft")
                else:
                    inputs_data["exterior_sqft"] = 0
                inputs_data["deck_staining"] = st.checkbox("Deck/Fence Staining", key="p_deck")

        # ── ELECTRICAL INPUTS ─────────────────────────────────────────────────
        elif st.session_state.est_trade == "electrical":
            st.markdown("#### ⚡ Service Details")
            inputs_data["service_type"] = st.selectbox(
                "Service Type",
                ["Residential New", "Residential Repair", "Commercial", "Emergency"],
                key="e_service",
            )

            st.markdown("#### 🔌 Panel Details")
            inputs_data["panel_upgrade"] = st.checkbox("Panel Upgrade Needed", key="e_panel")
            if inputs_data["panel_upgrade"]:
                inputs_data["panel_upgrade_type"] = st.selectbox(
                    "Upgrade Type",
                    ["100A to 150A", "100A to 200A", "150A to 200A", "Upgrade to 400A"],
                    key="e_panel_type",
                )
                inputs_data["panel_brand"] = st.text_input("Panel Brand", key="e_panel_brand", placeholder="e.g. Square D, Siemens")

            st.markdown("#### 🔆 Fixtures & Outlets")
            eq1, eq2 = st.columns(2)
            with eq1:
                inputs_data["outlets"] = st.number_input("New Outlets", 0, 100, 0, key="e_outlets")
                inputs_data["fixtures"] = st.number_input("Light Fixtures", 0, 100, 0, key="e_fixtures")
                inputs_data["ceiling_fans"] = st.number_input("Ceiling Fans", 0, 30, 0, key="e_fans")
            with eq2:
                inputs_data["switches"] = st.number_input("Switches", 0, 100, 0, key="e_switches")
                inputs_data["gfci_outlets"] = st.number_input("GFCI Outlets", 0, 50, 0, key="e_gfci")

            st.markdown("#### 🏠 Special Services")
            es1, es2 = st.columns(2)
            with es1:
                inputs_data["ev_charger"] = st.checkbox("EV Charger Installation", key="e_ev")
                inputs_data["generator"] = st.checkbox("Generator Hookup", key="e_gen")
            with es2:
                inputs_data["smart_home"] = st.checkbox("Smart Home Wiring", key="e_smart")
                if inputs_data["smart_home"]:
                    inputs_data["smart_home_devices"] = st.number_input("# Devices", 1, 50, 5, key="e_smart_n")
                else:
                    inputs_data["smart_home_devices"] = 0
                inputs_data["security_wiring"] = st.checkbox("Security System Wiring", key="e_security")

            st.markdown("#### 📋 Permits & Scheduling")
            ep1, ep2 = st.columns(2)
            with ep1:
                inputs_data["permit_required"] = st.checkbox("Permit Required", key="e_permit")
                inputs_data["emergency_service"] = st.checkbox("Emergency Service (2× rate)", key="e_emergency")
            with ep2:
                inputs_data["after_hours"] = st.checkbox("After Hours (1.5× rate)", key="e_afterhours")

        # ── LANDSCAPING INPUTS ────────────────────────────────────────────────
        elif st.session_state.est_trade == "landscaping":
            st.markdown("#### 🌿 Property Details")
            lp1, lp2 = st.columns(2)
            with lp1:
                inputs_data["lot_sqft"] = st.number_input("Lot Size (sq ft)", 0, 100000, 5000, step=500, key="l_lot")
                inputs_data["grass_type"] = st.selectbox(
                    "Grass Type",
                    ["Bermuda", "St. Augustine", "Zoysia", "Fescue", "Mixed"],
                    key="l_grass",
                )
            with lp2:
                inputs_data["trees"] = st.number_input("Number of Trees", 0, 50, 0, key="l_trees")
                inputs_data["shrubs"] = st.number_input("Number of Shrubs", 0, 100, 0, key="l_shrubs")

            st.markdown("#### 🌱 Recurring Services")
            ls1, ls2 = st.columns(2)
            with ls1:
                inputs_data["mowing"] = st.checkbox("Lawn Mowing", key="l_mow")
                if inputs_data["mowing"]:
                    inputs_data["mow_frequency"] = st.selectbox(
                        "Frequency",
                        ["Weekly", "Bi-weekly", "Monthly"],
                        index=1,
                        key="l_mow_freq",
                    )
                else:
                    inputs_data["mow_frequency"] = "Bi-weekly"

                inputs_data["edging"] = st.checkbox("Edging", key="l_edge")
                inputs_data["fertilization"] = st.checkbox("Fertilization", key="l_fert")
                if inputs_data["fertilization"]:
                    inputs_data["fertilization_apps"] = st.number_input("Applications per Year", 1, 12, 4, key="l_fert_apps")
                else:
                    inputs_data["fertilization_apps"] = 0
                inputs_data["aeration"] = st.checkbox("Aeration", key="l_aer")

            with ls2:
                inputs_data["mulching"] = st.checkbox("Mulching", key="l_mulch")
                if inputs_data["mulching"]:
                    inputs_data["mulch_yards"] = st.number_input("Cubic Yards", 1, 50, 5, key="l_mulch_yds")
                else:
                    inputs_data["mulch_yards"] = 0
                inputs_data["hedge_trim"] = st.checkbox("Hedge Trimming", key="l_hedge")
                inputs_data["tree_trimming"] = st.checkbox("Tree Trimming", key="l_tree_trim")
                if inputs_data["tree_trimming"]:
                    inputs_data["trim_tree_count"] = st.number_input("# Trees to Trim", 1, 50, 3, key="l_tree_n")
                else:
                    inputs_data["trim_tree_count"] = 0
                inputs_data["leaf_cleanup"] = st.checkbox("Leaf Cleanup", key="l_leaf")
                inputs_data["seasonal_cleanup"] = st.checkbox("Seasonal Cleanup", key="l_seasonal")

            st.markdown("#### 💧 Irrigation")
            li1, li2 = st.columns(2)
            with li1:
                inputs_data["new_irrigation"] = st.checkbox("New Irrigation System", key="l_irr_new")
                if inputs_data["new_irrigation"]:
                    inputs_data["irrigation_zones"] = st.number_input("# Zones", 1, 30, 6, key="l_irr_zones")
                else:
                    inputs_data["irrigation_zones"] = 0
            with li2:
                inputs_data["irrigation_repair"] = st.checkbox("Irrigation Repair", key="l_irr_repair")
                inputs_data["irrigation_winterization"] = st.checkbox("Irrigation Winterization", key="l_irr_winter")

    # ── STEP 3: Live Calculation ───────────────────────────────────────────────
    with results_col:
        st.markdown("### Step 3 — Live Estimate")

        # Calculate line items
        trade = st.session_state.est_trade
        if trade == "painting":
            line_items = calc_painting(inputs_data)
        elif trade == "electrical":
            line_items = calc_electrical(inputs_data)
        elif trade == "landscaping":
            line_items = calc_landscaping(inputs_data)
        else:
            line_items = []

        subtotal = sum(li.get("total", 0) for li in line_items)
        st.session_state.est_line_items = line_items
        st.session_state.est_subtotal = subtotal

        # Tax and discount controls
        td1, td2 = st.columns(2)
        with td1:
            tax_rate = st.number_input("Tax Rate (%)", 0.0, 20.0, 0.0, step=0.5, key="est_tax_rate")
        with td2:
            discount = st.number_input("Discount ($)", 0.0, 50000.0, 0.0, step=25.0, key="est_discount")

        st.session_state.est_tax_rate = tax_rate
        st.session_state.est_discount = discount

        # Render table
        total = render_line_items_table(line_items, subtotal, tax_rate, discount)
        st.session_state.est_total = total

        # ── AI Suggestions ────────────────────────────────────────────────────
        if company.get("anthropic_key"):
            st.markdown("---")
            if st.button("🤖 Get AI Recommendations", key="get_ai_suggestions", use_container_width=True):
                with st.spinner("Consulting AI..."):
                    try:
                        from utils.claude_ai import get_estimate_ai_suggestions
                        suggestions = get_estimate_ai_suggestions(
                            trade_type=trade,
                            inputs=inputs_data,
                            line_items=line_items,
                            total=total,
                            company=company,
                        )
                        st.session_state.est_ai_suggestions = suggestions
                    except Exception as exc:
                        st.error(f"AI error: {exc}")

            if st.session_state.est_ai_suggestions:
                suggestions = st.session_state.est_ai_suggestions
                if isinstance(suggestions, str):
                    st.markdown(
                        f'<div style="background:#F0FDF4;border:1px solid #A7F3D0;border-radius:10px;padding:1rem;color:#065F46;">'
                        f'<strong>🤖 AI Suggestions</strong><br>{suggestions}</div>',
                        unsafe_allow_html=True,
                    )
                elif isinstance(suggestions, list):
                    for s in suggestions:
                        st.markdown(
                            f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;'
                            f'padding:0.75rem;color:#1E40AF;margin-bottom:0.5rem;">💡 {s}</div>',
                            unsafe_allow_html=True,
                        )
                elif isinstance(suggestions, dict):
                    for k, v in suggestions.items():
                        st.markdown(
                            f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;'
                            f'padding:0.75rem;color:#1E40AF;margin-bottom:0.5rem;"><strong>{k}</strong><br>{v}</div>',
                            unsafe_allow_html=True,
                        )

    # ── STEP 4: Notes + Generate ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Step 4 — Notes & Generate")

    n1, n2 = st.columns(2)
    with n1:
        est_notes = st.text_area(
            "Special Instructions / Terms / Notes",
            height=120,
            key="est_notes",
            placeholder="e.g. Two coats guaranteed, touch-up included within 30 days...",
        )
    with n2:
        valid_until_date = st.date_input(
            "Valid Until",
            value=date.today() + timedelta(days=30),
            key="est_valid_until",
        )

    if not line_items:
        st.info("Add services above to generate an estimate.")
    else:
        # Total summary banner
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#10B981,#3B82F6);color:white;
                        border-radius:12px;padding:1.25rem 2rem;display:flex;
                        justify-content:space-between;align-items:center;margin:1rem 0;">
              <div>
                <div style="font-size:0.9rem;opacity:0.9;">{selected_client_name} · {TRADE_ICONS.get(trade,'')} {trade.title()}</div>
                <div style="font-size:0.8rem;opacity:0.8;">{len(line_items)} line items · Valid until {valid_until_date.strftime('%B %d, %Y')}</div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:0.85rem;opacity:0.9;">TOTAL ESTIMATE</div>
                <div style="font-size:2rem;font-weight:800;">{format_currency(st.session_state.est_total)}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action_c1, action_c2, action_c3 = st.columns(3)

        def build_estimate_payload(status: str) -> dict:
            tax_amt = st.session_state.est_subtotal * (st.session_state.est_tax_rate / 100)
            total_final = max(0.0, st.session_state.est_subtotal + tax_amt - st.session_state.est_discount)
            return {
                "company_id": company_id,
                "client_id": st.session_state.est_client_id,
                "created_by": user_id,
                "trade_type": st.session_state.est_trade,
                "inputs": inputs_data,
                "line_items": st.session_state.est_line_items,
                "subtotal": round(st.session_state.est_subtotal, 2),
                "tax": round(tax_amt, 2),
                "discount": round(st.session_state.est_discount, 2),
                "total": round(total_final, 2),
                "status": status,
                "notes": est_notes,
                "valid_until": valid_until_date.isoformat(),
            }

        with action_c1:
            if st.button("💾 Save as Draft", use_container_width=True, key="save_draft"):
                payload = build_estimate_payload("draft")
                saved = create_estimate(payload)
                if saved:
                    st.session_state.est_saved_id = saved["id"]
                    st.success(f"✅ Saved as draft! ID: {str(saved['id'])[:8].upper()}")
                else:
                    st.error("Failed to save estimate.")

        with action_c2:
            if st.button("📄 Generate Proposal", use_container_width=True, key="gen_proposal", type="primary"):
                with st.spinner("Generating proposal..."):
                    # Save estimate
                    payload = build_estimate_payload("draft")
                    saved = create_estimate(payload)
                    if not saved:
                        st.error("Failed to save estimate.")
                    else:
                        eid = saved["id"]
                        st.session_state.est_saved_id = eid

                        # Generate scope of work text
                        scope_text = ""
                        try:
                            from utils.claude_ai import generate_proposal_description
                            scope_text = generate_proposal_description(
                                trade_type=trade,
                                line_items=st.session_state.est_line_items,
                                inputs=inputs_data,
                                company=company,
                            )
                        except Exception:
                            scope_text = f"Professional {trade} services as detailed in the line items above."

                        # Generate PDF
                        try:
                            from utils.pdf_generator import generate_proposal_pdf
                            pdf_estimate = dict(saved)
                            pdf_estimate["scope_text"] = scope_text
                            pdf_bytes = generate_proposal_pdf(
                                pdf_estimate,
                                selected_client,
                                company,
                                st.session_state.est_line_items,
                            )
                            st.session_state.est_generated_pdf = pdf_bytes
                        except Exception as exc:
                            st.error(f"PDF generation failed: {exc}")
                            pdf_bytes = None

                        # Create proposal record
                        create_proposal({"estimate_id": eid, "status": "draft"})
                        st.success("✅ Proposal generated!")

        with action_c3:
            if st.button("🔄 Clear Form", use_container_width=True, key="clear_form"):
                for key in [
                    "est_trade", "est_client_id", "est_line_items",
                    "est_subtotal", "est_total", "est_generated_pdf",
                    "est_saved_id", "est_ai_suggestions",
                ]:
                    if key in st.session_state:
                        st.session_state[key] = None if "id" in key or "trade" in key or "pdf" in key or "suggestions" in key else []
                st.rerun()

        # Show PDF download if available
        if st.session_state.est_generated_pdf:
            st.markdown("---")
            pd1, pd2 = st.columns(2)
            with pd1:
                st.download_button(
                    "📥 Download Proposal PDF",
                    st.session_state.est_generated_pdf,
                    "proposal.pdf",
                    "application/pdf",
                    use_container_width=True,
                    key="dl_proposal_pdf",
                )
            with pd2:
                if st.button("📧 Send to Client", use_container_width=True, key="send_proposal_btn"):
                    client_email = selected_client.get("email", "")
                    if not client_email:
                        st.warning("Client has no email address.")
                    elif not company.get("gmail_email"):
                        st.warning("Gmail not configured in company settings.")
                    else:
                        try:
                            from utils.gmail_integration import send_proposal_email
                            saved_est = get_estimate(st.session_state.est_saved_id) if st.session_state.est_saved_id else {}
                            send_proposal_email(
                                gmail_email=company["gmail_email"],
                                gmail_app_password=company.get("gmail_app_password", ""),
                                client=selected_client,
                                estimate=saved_est or {},
                                company=company,
                            )
                            if st.session_state.est_saved_id:
                                update_estimate(
                                    st.session_state.est_saved_id,
                                    {"status": "sent", "sent_at": datetime.utcnow().isoformat()},
                                )
                                # Update proposal
                                prop = get_proposal_by_estimate(st.session_state.est_saved_id)
                                if prop:
                                    update_proposal(prop["id"], {
                                        "status": "sent",
                                        "sent_at": datetime.utcnow().isoformat(),
                                    })
                            st.success("✅ Proposal sent to client!")
                        except Exception as exc:
                            st.error(f"Failed to send: {exc}")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — PROPOSALS
# ═════════════════════════════════════════════════════════════════════════════
with tab_proposals:
    st.markdown("### 📬 Sent Proposals")

    # Load all sent/approved estimates with proposals
    all_estimates = get_estimates(company_id)
    proposal_estimates = [
        e for e in all_estimates
        if e.get("status") in ("sent", "approved", "draft")
    ]

    if not proposal_estimates:
        st.markdown(
            """
            <div style="text-align:center;padding:4rem 1rem;color:#9CA3AF;
                        background:white;border-radius:12px;border:1px solid #F3F4F6;">
              <div style="font-size:3rem;">📬</div>
              <div style="font-size:1.2rem;font-weight:700;color:#374151;margin-top:0.5rem;">No proposals yet</div>
              <div style="font-size:0.9rem;">Create and send an estimate to see proposals here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Header row
        h1, h2, h3, h4, h5, h6 = st.columns([1, 2, 2, 1, 2, 2])
        with h1:
            st.markdown("**#**")
        with h2:
            st.markdown("**Client**")
        with h3:
            st.markdown("**Trade**")
        with h4:
            st.markdown("**Total**")
        with h5:
            st.markdown("**Status**")
        with h6:
            st.markdown("**Actions**")
        st.markdown('<div style="border-bottom:2px solid #E5E7EB;margin-bottom:0.5rem;"></div>', unsafe_allow_html=True)

        for est in proposal_estimates:
            eid = est["id"]
            short_id = str(eid)[:8].upper()
            client_id_e = est.get("client_id")
            client_obj = client_map.get(client_id_e) if client_id_e else {}
            client_name = client_obj.get("name", "—")
            client_email = client_obj.get("email", "")
            trade = est.get("trade_type", "")
            trade_label = f"{TRADE_ICONS.get(trade, '🏠')} {trade.title()}"
            total = format_currency(est.get("total", 0))
            status = est.get("status", "draft")

            # Get proposal record for additional status
            prop = get_proposal_by_estimate(eid)
            prop_status = prop.get("status", status) if prop else status
            prop_id = prop.get("id") if prop else None
            sent_at = format_date(prop.get("sent_at", "")) if prop else format_date(est.get("sent_at", ""))

            badge = render_badge(prop_status)

            r1, r2, r3, r4, r5, r6 = st.columns([1, 2, 2, 1, 2, 2])
            with r1:
                st.markdown(f"**#{short_id}**")
            with r2:
                st.markdown(client_name)
            with r3:
                st.markdown(trade_label)
            with r4:
                st.markdown(total)
            with r5:
                st.markdown(badge, unsafe_allow_html=True)
                if sent_at:
                    st.caption(f"Sent: {sent_at}")
            with r6:
                act_c1, act_c2 = st.columns(2)
                with act_c1:
                    # Resend
                    if st.button("📧", key=f"prop_resend_{eid}", help="Resend to client"):
                        if not client_email:
                            st.warning("No client email.")
                        elif not company.get("gmail_email"):
                            st.warning("Gmail not configured.")
                        else:
                            try:
                                from utils.gmail_integration import send_proposal_email
                                send_proposal_email(
                                    gmail_email=company["gmail_email"],
                                    gmail_app_password=company.get("gmail_app_password", ""),
                                    client=client_obj,
                                    estimate=est,
                                    company=company,
                                )
                                update_estimate(eid, {"status": "sent", "sent_at": datetime.utcnow().isoformat()})
                                if prop_id:
                                    update_proposal(prop_id, {"status": "sent", "sent_at": datetime.utcnow().isoformat()})
                                st.success("Resent!")
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

                    # Download PDF
                    if st.button("📄", key=f"prop_pdf_{eid}", help="Download PDF"):
                        try:
                            from utils.pdf_generator import generate_proposal_pdf
                            line_items = est.get("line_items", []) or []
                            pdf_bytes = generate_proposal_pdf(est, client_obj or {}, company, line_items)
                            st.download_button(
                                "📥",
                                pdf_bytes,
                                f"proposal_{short_id}.pdf",
                                "application/pdf",
                                key=f"prop_dl_{eid}",
                            )
                        except Exception as exc:
                            st.error(f"PDF error: {exc}")

                with act_c2:
                    # Mark signed
                    if prop_status != "signed":
                        if st.button("✅", key=f"prop_sign_{eid}", help="Mark as Signed"):
                            update_estimate(eid, {"status": "approved"})
                            if prop_id:
                                update_proposal(prop_id, {
                                    "status": "signed",
                                    "signed_at": datetime.utcnow().isoformat(),
                                })
                            else:
                                create_proposal({
                                    "estimate_id": eid,
                                    "status": "signed",
                                    "signed_at": datetime.utcnow().isoformat(),
                                })
                            st.success("Marked as signed!")
                            st.rerun()

                    # Convert to Job
                    if est.get("status") == "approved" or prop_status == "signed":
                        if st.button("🔨", key=f"prop_job_{eid}", help="Convert to Job"):
                            try:
                                from utils.db import create_job
                                job_payload = {
                                    "company_id": company_id,
                                    "client_id": client_id_e,
                                    "estimate_id": eid,
                                    "title": f"{trade.title()} Job — {client_name}",
                                    "description": est.get("notes", ""),
                                    "trade_type": trade,
                                    "status": "scheduled",
                                    "address": client_obj.get("address") if client_obj else None,
                                    "city": client_obj.get("city") if client_obj else None,
                                    "state": client_obj.get("state") if client_obj else None,
                                    "zip": client_obj.get("zip") if client_obj else None,
                                }
                                new_job = create_job(job_payload)
                                if new_job:
                                    st.success(f"✅ Job created: {str(new_job['id'])[:8].upper()}")
                                else:
                                    st.error("Failed to create job.")
                            except Exception as exc:
                                st.error(f"Error: {exc}")

            st.markdown('<div style="border-bottom:1px solid #F3F4F6;margin:4px 0;"></div>', unsafe_allow_html=True)
