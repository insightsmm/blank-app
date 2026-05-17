import requests
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from typing import Optional, Tuple, List, Dict
import urllib.parse


def get_maps_key() -> Optional[str]:
    """Return the Google Maps API key from company settings, or None."""
    try:
        company = st.session_state.get("company", {}) or {}
        key = company.get("google_maps_key", "")
        return key if key else None
    except Exception as e:
        print(f"get_maps_key error: {e}")
        return None


def geocode_address(
    address: str,
    city: str = "",
    state: str = "",
    zip_code: str = "",
) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode a street address using the Google Geocoding API.
    Returns (lat, lng) or (None, None) if geocoding fails.
    """
    api_key = get_maps_key()
    if not api_key:
        return None, None

    # Build full address string
    parts = [p for p in [address, city, state, zip_code] if p]
    full_address = ", ".join(parts)
    if not full_address.strip():
        return None, None

    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": full_address, "key": api_key}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return float(location["lat"]), float(location["lng"])

        print(f"Geocoding failed for '{full_address}': {data.get('status')}")
        return None, None

    except Exception as e:
        print(f"geocode_address error: {e}")
        return None, None


# Status → Folium marker color mapping
_STATUS_COLORS = {
    "scheduled": "blue",
    "in_progress": "green",
    "on_hold": "orange",
    "completed": "gray",
    "cancelled": "red",
}


def create_jobs_map(
    jobs: List[Dict],
    center_lat: float = None,
    center_lng: float = None,
) -> folium.Map:
    """
    Create a Folium map with colored markers for each job.
    Falls back to a US-centered map if no job coordinates are available.
    """
    # Default US center
    default_lat, default_lng, default_zoom = 39.5, -98.35, 4

    # Find usable coordinates
    valid_jobs = [
        j for j in jobs
        if j.get("lat") is not None and j.get("lng") is not None
    ]

    if center_lat is None or center_lng is None:
        if valid_jobs:
            center_lat = sum(j["lat"] for j in valid_jobs) / len(valid_jobs)
            center_lng = sum(j["lng"] for j in valid_jobs) / len(valid_jobs)
            zoom = 10 if len(valid_jobs) > 1 else 13
        else:
            center_lat, center_lng, zoom = default_lat, default_lng, default_zoom
    else:
        zoom = 12

    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom, tiles="OpenStreetMap")

    if not valid_jobs:
        return m

    cluster = MarkerCluster().add_to(m)

    for job in valid_jobs:
        lat = job["lat"]
        lng = job["lng"]
        status = job.get("status", "scheduled")
        color = _STATUS_COLORS.get(status, "blue")

        title = job.get("title", "Untitled Job")
        client_name = job.get("client_name", "")
        trade_type = (job.get("trade_type") or "").title()
        start_date = job.get("start_date", "")
        job_address = ", ".join(
            filter(None, [job.get("address", ""), job.get("city", ""), job.get("state", "")])
        )

        popup_html = f"""
        <div style="min-width:180px; font-family:Arial,sans-serif;">
            <strong style="font-size:1rem;">{title}</strong><br>
            <span style="color:#6B7280; font-size:0.8rem;">{trade_type}</span><br>
            {"<b>Client:</b> " + client_name + "<br>" if client_name else ""}
            {"<b>Date:</b> " + str(start_date) + "<br>" if start_date else ""}
            {"<b>Address:</b> " + job_address + "<br>" if job_address else ""}
            <span style="background:{'#DBEAFE' if status=='scheduled' else '#D1FAE5'};
                padding:2px 8px; border-radius:10px; font-size:0.75rem;">
                {status.replace('_', ' ').title()}
            </span>
        </div>
        """

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=title,
            icon=folium.Icon(color=color, icon="wrench", prefix="fa"),
        ).add_to(cluster)

    return m


def create_route_map(
    origin_address: str,
    destination_address: str,
    waypoints: List[str] = None,
) -> folium.Map:
    """
    Create a Folium map showing origin and destination markers.
    Draws a simple polyline if both addresses can be geocoded.
    """
    origin_lat, origin_lng = geocode_address(origin_address)
    dest_lat, dest_lng = geocode_address(destination_address)

    # Default map centered between points or fallback
    if origin_lat and dest_lat:
        center_lat = (origin_lat + dest_lat) / 2
        center_lng = (origin_lng + dest_lng) / 2
        zoom = 11
    elif dest_lat:
        center_lat, center_lng, zoom = dest_lat, dest_lng, 13
    elif origin_lat:
        center_lat, center_lng, zoom = origin_lat, origin_lng, 13
    else:
        center_lat, center_lng, zoom = 39.5, -98.35, 4

    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom, tiles="OpenStreetMap")

    if origin_lat:
        folium.Marker(
            location=[origin_lat, origin_lng],
            popup="Origin: " + origin_address,
            tooltip="Start",
            icon=folium.Icon(color="green", icon="home", prefix="fa"),
        ).add_to(m)

    if dest_lat:
        folium.Marker(
            location=[dest_lat, dest_lng],
            popup="Destination: " + destination_address,
            tooltip="Job Site",
            icon=folium.Icon(color="red", icon="flag", prefix="fa"),
        ).add_to(m)

    # Waypoint markers
    if waypoints:
        for i, wp in enumerate(waypoints):
            wp_lat, wp_lng = geocode_address(wp)
            if wp_lat:
                folium.Marker(
                    location=[wp_lat, wp_lng],
                    popup=f"Stop {i+1}: {wp}",
                    tooltip=f"Stop {i+1}",
                    icon=folium.Icon(color="blue", icon="circle", prefix="fa"),
                ).add_to(m)

    # Draw a dashed line between origin and destination if both available
    if origin_lat and dest_lat:
        points = [[origin_lat, origin_lng], [dest_lat, dest_lng]]
        if waypoints:
            wp_coords = []
            for wp in waypoints:
                wp_lat, wp_lng = geocode_address(wp)
                if wp_lat:
                    wp_coords.append([wp_lat, wp_lng])
            if wp_coords:
                points = [[origin_lat, origin_lng]] + wp_coords + [[dest_lat, dest_lng]]

        folium.PolyLine(
            locations=points,
            color="#10B981",
            weight=4,
            opacity=0.7,
            dash_array="10",
        ).add_to(m)

    return m


def get_google_maps_url(destination: str, origin: str = None) -> str:
    """
    Build a Google Maps directions URL for the given destination.
    Optionally include an origin.
    """
    base = "https://www.google.com/maps/dir/?api=1"
    dest_encoded = urllib.parse.quote(destination)
    url = f"{base}&destination={dest_encoded}"
    if origin:
        origin_encoded = urllib.parse.quote(origin)
        url += f"&origin={origin_encoded}"
    return url


def get_directions_html(job: dict) -> str:
    """
    Return an HTML 'Get Directions' button linking to Google Maps for a job's address.
    """
    parts = [
        job.get("address", ""),
        job.get("city", ""),
        job.get("state", ""),
        job.get("zip", ""),
    ]
    address = ", ".join(p for p in parts if p)
    if not address.strip():
        return "<p style='color:#9CA3AF;font-size:0.85rem;'>No address on file</p>"

    maps_url = get_google_maps_url(address)
    return (
        f'<a href="{maps_url}" target="_blank" style="'
        f"display:inline-block; background:#3B82F6; color:white; "
        f"padding:0.5rem 1.25rem; border-radius:8px; text-decoration:none; "
        f"font-weight:600; font-size:0.9rem;"
        f'">🗺️ Get Directions</a>'
        f'<div style="font-size:0.8rem;color:#6B7280;margin-top:4px;">{address}</div>'
    )
