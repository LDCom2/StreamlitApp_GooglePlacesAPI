import streamlit as st
import requests
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

API_KEY = ""



def get_location(place_name):
    """
    :param place_name: named location on Google Maps
    :return: Coordinate location in latitaude and longitude
    """

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": place_name, "key": API_KEY}
    res = requests.get(url, params=params).json()

    if not res["results"]:
        st.error("Location not found!")
        return None, None

    loc = res["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


def get_places(lat, lng, radius=1000, place_type="restaurant", n_random=3):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": place_type,
        "key": API_KEY
    }

    res = requests.get(url, params=params).json()
    res = res.get("results", [])
    if not res:
        return pd.DataFrame()
    df = pd.DataFrame(res)

    # If we found more than our target, pick random ones
    if len(df) > n_random:
        df = df.sample(n=n_random).reset_index(drop=True)

    return df

def build_map(lat, lng, places):
    m = folium.Map(location=[lat, lng], zoom_start=15)
    cluster = MarkerCluster().add_to(m)

    # Center marker
    folium.Marker(
        [lat, lng],
        popup="Search Center",
        icon=folium.Icon(color="red", icon="star")
    ).add_to(m)

    for _,place in places.iterrows():
        loc = place["geometry"]["location"]
        name = place.get("name", "Unknown")
        rating = place.get("rating", "N/A")

        folium.Marker(
            location=[loc["lat"], loc["lng"]],
            popup=f"<b>{name}</b><br>Rating: {rating}",
        ).add_to(cluster)

    return m



st.set_page_config(layout="wide")

st.markdown("""
<div style="
    background-color: #1E1E1E; 
    padding: 20px 40px; 
    border-radius: 10px; 
    display: flex; 
    justify-content: space-between; 
    align-items: baseline; 
    margin-bottom: 30px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
">
    <h2 style="font-size: 24px; font-weight: 400; letter-spacing: -0.5px; margin: 0; color: white; opacity: 0.7;">
        Find food near you <span style="font-weight: 800; opacity: 1; color: #FFFFFF;">(Randomly chosen)</span>
    </h2>
    <h1 style="font-size: 55px; font-weight: 900; letter-spacing: -3px; margin: 0; line-height: 1;">
        <span style="color: #FF4B4B;">NEAR ME</span><span style="color: white; opacity: 0.2;">al</span>
    </h1>
</div>
""", unsafe_allow_html=True)


if "map_html" not in st.session_state:
    st.session_state.map_html = None

col1, col2 = st.columns([2,5])

with col1:
    with st.form(key="search_form"):
        location_name = st.text_input("Where are you now?", "Seneca Polytechnic")
        place_type = st.selectbox("Place type", ["restaurant", "cafe", "bar", "museum", "park"])
        radius = st.slider("How far are you willing to walk/travel? (m)", 100, 5000, 500)
        max_results = st.slider("Number of places to show", 1, 5, 3)
        submit_button = st.form_submit_button("Search")

with col2:
    if submit_button:
        lat, lng = get_location(location_name)
        if lat and lng:
            places = get_places(lat, lng, radius, place_type, max_results)
            if places.empty:
                st.warning("No places found in this area. Just have something delivered")
                st.session_state.map_html = None
            else:
                m = build_map(lat, lng, places)
                st.session_state.map_html = m._repr_html_()

    if st.session_state.map_html:
        st.components.v1.html(st.session_state.map_html, height=500, scrolling=True)

st.markdown("""
<h2 style='font-weight: 300; margin-top: 10px; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px;'>
    <span style='opacity: 0.4;'>Here are your</span> <b>Options</b>
</h2>
""", unsafe_allow_html=True)

row2 = st.columns(1)[0]
with row2:
    if submit_button:
        if places.empty:
            st.warning("No results found. Just have something delivered")
        else:
            places['Open Now?'] = places['opening_hours'].str['open_now'].apply(lambda x: 'Yes' if x else 'No')

            st.dataframe(places[['name','rating', 'Open Now?','types','vicinity']], use_container_width=True)
    else:
        st.info("Run a search to see results.")
