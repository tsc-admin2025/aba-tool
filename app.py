"""Main Streamlit application for ABA Competitor Analysis Tool."""

import logging
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.api.google_maps import GoogleMapsClient
from src.config import DEFAULT_SEARCH_KEYWORDS, GOOGLE_MAPS_API_KEY, STREAMLIT_CONFIG
from src.exceptions import ConfigurationError
from src.models import GeocodeStatus, SearchParameters
from src.services.analysis import CompetitorAnalysisService
from src.services.batch_validation import BatchValidationService
from src.services.competitor_search import CompetitorSearchService
from src.services.geocoding import GeocodingService
from src.ui import components

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_password() -> bool:
    """Gate the app behind a password stored in Streamlit secrets.

    Returns True if the user has entered the correct password.
    Skips the gate entirely if no APP_PASSWORD secret is configured
    (so local dev without a password still works).
    """
    try:
        correct_password = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        # No password configured — skip gate (local dev)
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Show login form
    st.markdown(
        """
        <div style="text-align: center; margin-top: 4rem;">
            <h2 style="color: #ED8B00; font-family: 'Inter', sans-serif;">
                tuscany<span style="color: #1A1A1A;">strategy</span>
            </h2>
            <p style="color: #666; font-size: 0.875rem;">ABA Competitor Analysis Tool</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter password", type="password", key="password_input")
        if st.button("Sign in", type="primary", use_container_width=True):
            if password == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")

    return False

# US States list
US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]


@st.cache_resource  # type: ignore[misc]
def init_services() -> (
    tuple[
        GeocodingService,
        CompetitorSearchService,
        CompetitorAnalysisService,
        BatchValidationService,
    ]
):
    """Initialize all services (cached for performance)."""
    try:
        if not GOOGLE_MAPS_API_KEY:
            raise ConfigurationError("Google Maps API key not configured")

        logger.info(
            f"API Key loaded: {GOOGLE_MAPS_API_KEY[:10]}..."
            f"{GOOGLE_MAPS_API_KEY[-4:] if GOOGLE_MAPS_API_KEY else 'None'}"
        )

        gmaps_client = GoogleMapsClient(GOOGLE_MAPS_API_KEY)
        geocoding_service = GeocodingService(gmaps_client)
        search_service = CompetitorSearchService(gmaps_client)
        analysis_service = CompetitorAnalysisService()
        batch_validation_service = BatchValidationService(geocoding_service)

        logger.info("All services initialized successfully")
        return (
            geocoding_service,
            search_service,
            analysis_service,
            batch_validation_service,
        )

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


def main() -> None:
    """Run the main application."""
    st.set_page_config(**STREAMLIT_CONFIG)

    # Password gate — blocks everything until authenticated
    if not check_password():
        st.stop()

    # Tuscany Strategy CSS (same branding as ECE tool)
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --tuscany-orange: #ED8B00;
            --tuscany-orange-hover: #D47A00;
            --tuscany-red: #A4514D;
            --tuscany-dark: #1A1A1A;
            --tuscany-gray: #666666;
            --tuscany-light-gray: #F8F8F8;
            --tuscany-white: #FFFFFF;
        }

        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--tuscany-white);
        }

        ::selection { background-color: var(--tuscany-orange); color: white; }
        ::-moz-selection { background-color: var(--tuscany-orange); color: white; }

        .stMarkdown a { color: var(--tuscany-orange); }
        .stMarkdown a:hover { color: var(--tuscany-orange-hover); text-decoration: underline; }

        .stSlider > div > div > div > div[role="slider"] {
            background-color: var(--tuscany-orange) !important;
            border-color: var(--tuscany-orange) !important;
        }

        *:focus { outline-color: var(--tuscany-orange) !important; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        .main { padding-top: 2rem; }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif;
            color: var(--tuscany-dark);
            font-weight: 600;
        }

        .stButton > button {
            background-color: var(--tuscany-orange);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            font-weight: 600;
            border-radius: 25px;
            transition: all 0.3s ease;
            font-family: 'Inter', sans-serif;
        }

        .stButton > button:hover {
            background-color: var(--tuscany-orange-hover);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(237, 139, 0, 0.3);
        }

        .stDownloadButton > button {
            background-color: transparent;
            color: var(--tuscany-orange);
            border: 2px solid var(--tuscany-orange);
            padding: 0.75rem 2rem;
            font-weight: 600;
            border-radius: 25px;
            transition: all 0.3s ease;
        }

        .stDownloadButton > button:hover {
            background-color: var(--tuscany-orange);
            color: white;
        }

        [data-testid="stSidebar"] {
            background-color: var(--tuscany-light-gray);
            padding: 2rem 1rem;
        }

        [data-testid="stSidebar"] h1 {
            color: var(--tuscany-orange);
            font-size: 1.5rem;
            margin-bottom: 2rem;
        }

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            padding: 0.75rem;
            font-family: 'Inter', sans-serif;
        }

        .stTextInput > div > div > input:focus {
            border-color: var(--tuscany-orange);
            box-shadow: 0 0 0 2px rgba(237, 139, 0, 0.1);
        }

        [data-testid="metric-container"] {
            background-color: var(--tuscany-white);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease;
        }

        [data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        }

        .stTabs [data-baseweb="tab"] {
            font-family: 'Inter', sans-serif;
            font-weight: 500;
        }

        .stTabs [aria-selected="true"] {
            background-color: var(--tuscany-orange);
            color: white;
        }

        .stProgress > div > div > div {
            background-color: var(--tuscany-orange);
        }

        [data-testid="stFileUploadDropzone"] {
            background-color: var(--tuscany-light-gray);
            border: 2px dashed #E0E0E0;
            border-radius: 12px;
            padding: 2rem;
        }

        [data-testid="stFileUploadDropzone"]:hover {
            border-color: var(--tuscany-orange);
        }

        .block-container {
            padding-top: 3rem;
            max-width: 1200px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Initialize services
    try:
        (
            geocoding_service,
            search_service,
            analysis_service,
            batch_validation_service,
        ) = init_services()
    except ConfigurationError:
        st.error("Please set GOOGLE_MAPS_API_KEY in your .env file")
        st.stop()
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.stop()

    # Header
    st.markdown(
        """
        <div style="background-color: white; padding: 1rem 2rem; margin: -3rem -3rem 2rem -3rem; border-bottom: 1px solid #E0E0E0;">
            <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: baseline;">
                <span style="font-size: 2.5rem; font-weight: 700; color: #ED8B00; font-family: 'Inter', sans-serif;">tuscany</span>
                <span style="font-size: 2.5rem; font-weight: 700; color: #A4514D; font-family: 'Inter', sans-serif;">strategy</span>
                <span style="font-size: 1rem; color: #999999; margin-left: 1rem; font-family: 'Inter', sans-serif; letter-spacing: 0.1em;">CONSULTING</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Hero
    st.markdown(
        """
        <div style="background-color: #F8F8F8; padding: 3rem; border-radius: 12px; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem; font-weight: 700; color: #1A1A1A; margin-bottom: 1rem; font-family: 'Inter', sans-serif;">
                ABA Competitor Analysis Tool
            </h1>
            <p style="font-size: 1.25rem; color: #666666; font-weight: 400; font-family: 'Inter', sans-serif;">
                Enabling leaders to make high stakes decisions <strong>with confidence</strong>
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Analysis mode
    analysis_mode = st.selectbox(
        "Choose Analysis Mode",
        ["Single Location", "Batch Analysis (CSV Upload)"],
        help="Select single location for individual analysis or batch for multiple locations",
    )

    if analysis_mode == "Single Location":
        handle_single_location_analysis(
            geocoding_service, search_service, analysis_service
        )
    else:
        handle_batch_analysis(
            batch_validation_service, search_service, analysis_service
        )


def handle_single_location_analysis(
    geocoding_service: GeocodingService,
    search_service: CompetitorSearchService,
    analysis_service: CompetitorAnalysisService,
) -> None:
    """Handle single location analysis workflow."""
    search_params = components.render_sidebar(US_STATES)

    if search_params:
        with st.container():
            st.header(f"Analysis Results for {search_params.location_name}")
            st.subheader(f"Location: {search_params.city}, {search_params.state}")

            # Step 1: Geocoding
            with st.spinner("Finding location coordinates..."):
                geocode_result = geocoding_service.geocode_ece_location(
                    search_params.location_name,
                    search_params.city,
                    search_params.state,
                )

            if geocode_result.status != GeocodeStatus.SUCCESS:
                st.error(
                    f"Could not find location: "
                    f"{geocode_result.error or 'Location not found'}"
                )
                return

            center_location = geocode_result.location
            if center_location is None:
                st.error("Location coordinates not available")
                return
            st.success(f"Location found: {center_location.formatted_address}")

            # Step 2: Search + enrich (distances + place details)
            st.subheader("Searching for ABA Competitors")

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current: int, total: int, message: str) -> None:
                progress_bar.progress(current / total if total > 0 else 0)
                status_text.text(message)

            with st.spinner("Searching for competitors..."):
                enhanced_competitors = search_service.search_and_enhance_competitors(
                    center_location,
                    search_params.radius_miles,
                    search_terms=search_params.search_keywords,
                    progress_callback=update_progress,
                )

            progress_bar.empty()
            status_text.empty()

            if not enhanced_competitors:
                st.warning("No competitors found in the specified radius")
                return

            # Step 3: Analyze (service type detection + sorting)
            result = analysis_service.analyze_competitors(
                enhanced_competitors, search_params, center_location
            )

            # Display
            components.render_metrics(result)

            tab1, tab2, tab3 = st.tabs(
                ["All Competitors", "Map View", "Analysis"]
            )

            with tab1:
                components.render_all_competitors_tab(
                    result.competitors, search_params
                )

            with tab2:
                components.render_map_view(result)

            with tab3:
                components.render_analysis_tab(result)


def handle_batch_analysis(
    batch_validation_service: BatchValidationService,
    search_service: CompetitorSearchService,
    analysis_service: CompetitorAnalysisService,
) -> None:
    """Handle batch analysis workflow."""
    locations = components.render_csv_upload()

    if locations:
        st.divider()

        with st.spinner("Validating locations and geocoding..."):
            validation_summary = batch_validation_service.validate_locations(locations)

        components.render_validation_summary(validation_summary)

        if validation_summary.success_count > 0:
            st.divider()

            radius_miles = st.slider(
                "Search Radius (miles)",
                min_value=1,
                max_value=6,
                value=2,
                help="Radius to search for competitors around each location",
            )

            # Search keywords for batch
            keywords_text = st.text_area(
                "Search Keywords (comma-separated)",
                value=", ".join(DEFAULT_SEARCH_KEYWORDS),
                help="Edit or add search keywords for batch analysis",
                height=80,
            )
            search_keywords = [
                kw.strip() for kw in keywords_text.split(",") if kw.strip()
            ]

            if st.button(
                "Analyze All Locations", type="primary", use_container_width=True
            ):
                analyze_all_locations(
                    validation_summary.successful,
                    radius_miles,
                    search_keywords,
                    search_service,
                    analysis_service,
                )
        else:
            st.error(
                "No valid locations found. Please fix the issues above and try again."
            )


def analyze_all_locations(
    successful_locations: list[Any],
    radius_miles: int,
    search_keywords: list[str],
    search_service: CompetitorSearchService,
    analysis_service: CompetitorAnalysisService,
) -> dict[str, Any]:
    """Analyze competitors for all successful locations."""
    st.header("Multi-Location Analysis Results")

    total = len(successful_locations)
    location_results: dict[str, Any] = {}

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, loc_result in enumerate(successful_locations):
        loc = loc_result.location
        geocoded = loc_result.geocoded_location

        status_text.text(f"Analyzing {loc.display_name} ({i + 1}/{total})")
        progress_bar.progress((i + 1) / total)

        try:
            search_params = SearchParameters(
                location_name=loc.location_name,
                city=loc.city or "Unknown",
                state=loc.state or "Unknown",
                radius_miles=radius_miles,
                search_keywords=search_keywords,
            )

            enhanced_competitors = search_service.search_and_enhance_competitors(
                geocoded, radius_miles, search_terms=search_keywords
            )

            if enhanced_competitors:
                result = analysis_service.analyze_competitors(
                    enhanced_competitors, search_params, geocoded
                )
                location_results[loc.display_name] = result

        except Exception as e:
            st.error(f"Error analyzing {loc.display_name}: {e}")

    progress_bar.empty()
    status_text.empty()

    if location_results:
        display_multi_location_results(location_results)
    else:
        st.warning("No competitors found for any of the analyzed locations.")

    return location_results


def display_multi_location_results(location_results: dict[str, Any]) -> None:
    """Display results for multiple locations."""
    st.success(f"Analysis complete for {len(location_results)} locations!")

    total_competitors = sum(
        len(result.competitors) for result in location_results.values()
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Locations Analyzed", len(location_results))
    with col2:
        st.metric("Total Competitors Found", total_competitors)
    with col3:
        # Download all results
        all_data = []
        for loc_name, result in location_results.items():
            for comp in result.competitors:
                distance_csv = (
                    f"{comp.distance_miles:.1f}"
                    if comp.distance_miles is not None
                    else "N/A"
                )
                drive_time_csv = (
                    str(comp.drive_time_minutes)
                    if comp.drive_time_minutes is not None
                    else "N/A"
                )
                hours_csv = (
                    "; ".join(comp.operating_hours)
                    if comp.operating_hours
                    else "N/A"
                )

                all_data.append(
                    {
                        "Location": loc_name,
                        "Location Address": result.client_location.formatted_address,
                        "Competitor Name": comp.name,
                        "Competitor Address": comp.vicinity,
                        "Competitor ZIP Code": comp.zip_code or "N/A",
                        "Service Type": comp.effective_service_type.value,
                        "Rating": comp.rating,
                        "Reviews": comp.user_ratings_total,
                        "Distance (miles)": distance_csv,
                        "Drive Time (minutes)": drive_time_csv,
                        "Phone": comp.phone_number or "N/A",
                        "Website": comp.website or "N/A",
                        "Operating Hours": hours_csv,
                        "Google Maps URL": comp.google_maps_url or "N/A",
                    }
                )

        if all_data:
            df_all = pd.DataFrame(all_data)
            csv_all = df_all.to_csv(index=False)

            st.download_button(
                label="Download All Results",
                data=csv_all,
                file_name="all_aba_competitors.csv",
                mime="text/csv",
                key="download_all_results",
                type="primary",
            )

    # Individual location results
    st.subheader("Individual Location Results")

    for loc_name, result in location_results.items():
        with st.expander(f"{loc_name}", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Competitors", result.total_competitors)
            with col2:
                avg_rating = result.average_rating
                st.metric(
                    "Avg Rating",
                    f"{avg_rating:.1f} stars" if avg_rating else "N/A",
                )
            with col3:
                st.metric("Center-Based", result.center_based_count)

            tab1, tab2, tab3 = st.tabs(
                ["All Competitors", "Map View", "Summary"]
            )

            with tab1:
                comp_data = []
                for comp in result.competitors:
                    comp_data.append(
                        {
                            "Name": comp.name,
                            "Address": comp.vicinity,
                            "ZIP Code": comp.zip_code or "N/A",
                            "Service Type": comp.display_service_type,
                            "Rating": comp.rating,
                            "Reviews": comp.user_ratings_total,
                            "Distance": comp.display_distance,
                            "Drive Time": comp.display_drive_time,
                            "Phone": comp.display_phone_number,
                            "Website": comp.display_website,
                        }
                    )

                if comp_data:
                    df = pd.DataFrame(comp_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    csv = df.to_csv(index=False)
                    st.download_button(
                        label=f"Download {loc_name} Competitors",
                        data=csv,
                        file_name=f"{loc_name.replace(' ', '_')}_competitors.csv",
                        mime="text/csv",
                        key=f"download_{loc_name}",
                    )
                else:
                    st.info("No competitors found")

            with tab2:
                fig = go.Figure()

                fig.add_trace(
                    go.Scattermap(
                        lat=[result.client_location.lat],
                        lon=[result.client_location.lng],
                        mode="markers",
                        marker={"size": 20, "color": "red", "symbol": "star"},
                        text=[result.search_params.location_name],
                        name="Search Location",
                        showlegend=True,
                    )
                )

                if result.competitors:
                    lats = [c.location.lat for c in result.competitors]
                    lngs = [c.location.lng for c in result.competitors]
                    names = [
                        f"{c.name} ({c.effective_service_type.value})"
                        for c in result.competitors
                    ]

                    fig.add_trace(
                        go.Scattermap(
                            lat=lats,
                            lon=lngs,
                            mode="markers",
                            marker={
                                "size": 12,
                                "color": "#ED8B00",
                                "opacity": 0.8,
                            },
                            text=names,
                            name=f"Competitors ({len(result.competitors)})",
                            showlegend=True,
                        )
                    )

                fig.update_layout(
                    map_style="open-street-map",
                    map={
                        "center": {
                            "lat": result.client_location.lat,
                            "lon": result.client_location.lng,
                        },
                        "zoom": 12,
                    },
                    height=400,
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                )

                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                st.markdown(
                    f"""
                **Market Density:** {result.total_competitors} ABA providers within {result.search_params.radius_miles} miles

                **Service Breakdown:**
                - {result.center_based_count} center-based
                - {result.in_home_count} in-home
                - {result.total_competitors - result.center_based_count - result.in_home_count} unknown/both

                **Average Rating:** {f'{result.average_rating:.1f} stars' if result.average_rating else 'N/A'}
                """
                )


if __name__ == "__main__":
    main()
