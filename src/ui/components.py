"""Reusable UI components for Streamlit app."""

from typing import Any, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import DEFAULT_SEARCH_KEYWORDS
from src.models import (
    AnalysisResult,
    BatchValidationSummary,
    ClientLocation,
    Competitor,
    SearchParameters,
    ServiceType,
)
from src.services.location_csv_parser import LocationCSVParser


def render_sidebar(states: List[str]) -> Optional[SearchParameters]:
    """Render sidebar with input controls and search keywords.

    Args:
    ----
        states: List of state codes

    Returns:
    -------
        SearchParameters if analyze button clicked, None otherwise

    """
    with st.sidebar:
        # Tuscany Strategy branding
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h2 style="color: #ED8B00; font-family: 'Inter', sans-serif; font-weight: 700;">
                    tuscany<span style="color: #1A1A1A;">strategy</span>
                </h2>
                <p style="color: #666666; font-size: 0.875rem; margin-top: -0.5rem;">
                    CONSULTING
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.header("Location Input")

        location_name = st.text_input(
            "Location Name",
            placeholder="e.g., Downtown Baltimore",
            help="Enter a location name or label for the search center",
        )

        city = st.text_input(
            "City",
            placeholder="e.g., Baltimore, Towson, etc.",
            help="City to search in",
        )

        state = st.selectbox("State", ["", *states], help="Select the state")

        st.header("Search Options")

        radius_miles = st.slider(
            "Search Radius (miles)",
            min_value=1,
            max_value=6,
            value=2,
            help="Radius to search for competitors",
        )

        # Editable search keywords
        st.header("Search Keywords")
        keywords_text = st.text_area(
            "Keywords (comma-separated)",
            value=", ".join(DEFAULT_SEARCH_KEYWORDS),
            help="Edit or add search keywords. Each keyword triggers a separate Google Maps search.",
            height=100,
        )

        # Parse keywords from text area
        search_keywords = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]

        analyze_button = st.button(
            "Analyze Competitors", type="primary", use_container_width=True
        )

        if analyze_button:
            if not all([location_name, city, state]):
                st.error("Please fill in all location fields")
                return None

            if not search_keywords:
                st.error("Please enter at least one search keyword")
                return None

            return SearchParameters(
                location_name=location_name,
                city=city,
                state=state,
                radius_miles=radius_miles,
                search_keywords=search_keywords,
            )

    return None


def render_csv_upload() -> Optional[List[ClientLocation]]:
    """Render CSV upload component for batch location analysis.

    Returns
    -------
        List of ClientLocation objects if upload successful, None otherwise

    """
    st.header("Batch Analysis")
    st.markdown("Upload a CSV file with multiple locations for batch analysis")

    upload_tab, template_tab = st.tabs(["Upload CSV", "Download Template"])

    with upload_tab:
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload a CSV file with locations",
            key="csv_upload",
        )

        if uploaded_file is not None:
            try:
                csv_content = uploaded_file.read().decode("utf-8")

                parser = LocationCSVParser()
                locations = parser.parse_csv(csv_content)

                st.success(f"Successfully parsed {len(locations)} locations from CSV")

                with st.expander("Parsed Locations", expanded=True):
                    location_data = []
                    for loc in locations:
                        location_data.append(
                            {
                                "Row": loc.row_number,
                                "Location Name": loc.location_name,
                                "Address": loc.address or "Not provided",
                                "City": loc.city or "Not provided",
                                "State": loc.state or "Not provided",
                                "Sufficient Info": (
                                    "Yes" if loc.has_sufficient_info else "No"
                                ),
                            }
                        )

                    df = pd.DataFrame(location_data)
                    st.dataframe(df, use_container_width=True)

                return locations

            except Exception as e:
                st.error(f"Error parsing CSV: {e!s}")

                with st.expander("CSV Format Help", expanded=True):
                    parser = LocationCSVParser()
                    st.markdown(parser.get_validation_instructions())

    with template_tab:
        st.markdown("**Download a template CSV file to get started:**")

        parser = LocationCSVParser()
        template_csv = parser.get_csv_template()

        st.download_button(
            label="Download CSV Template",
            data=template_csv,
            file_name="aba_locations_template.csv",
            mime="text/csv",
            help="Download a template CSV with example data",
        )

        st.markdown("**Template Preview:**")
        st.code(template_csv, language="csv")

        st.markdown(parser.get_validation_instructions())

    return None


def render_validation_summary(summary: BatchValidationSummary) -> None:
    """Render batch validation summary with details."""
    st.subheader("Validation Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Locations", summary.total_locations)

    with col2:
        st.metric("Successful", summary.success_count)

    with col3:
        st.metric("Failed", summary.failed_count)

    with col4:
        st.metric("Flagged", summary.flagged_count)

    if summary.failed_count > 0 or summary.flagged_count > 0:
        tab1, tab2, tab3 = st.tabs(["Successful", "Failed", "Flagged"])

        with tab1:
            if summary.successful:
                st.success(f"{len(summary.successful)} locations ready for analysis")
                success_data = []
                for result in summary.successful:
                    success_data.append(
                        {
                            "Location": result.location.display_name,
                            "Row": result.location.row_number,
                            "Address": (
                                result.geocoded_location.formatted_address
                                if result.geocoded_location
                                else "N/A"
                            ),
                        }
                    )
                df = pd.DataFrame(success_data)
                st.dataframe(df, use_container_width=True)

        with tab2:
            if summary.failed:
                st.error(f"{len(summary.failed)} locations failed validation")
                for result in summary.failed:
                    with st.expander(
                        f"{result.location.display_name} "
                        f"(Row {result.location.row_number})"
                    ):
                        st.error(f"**Error:** {result.error_message}")
                        st.json(
                            {
                                "location_name": result.location.location_name,
                                "address": result.location.address,
                                "city": result.location.city,
                                "state": result.location.state,
                            }
                        )

        with tab3:
            if summary.flagged:
                st.warning(f"{len(summary.flagged)} locations require review")
                for result in summary.flagged:
                    with st.expander(
                        f"{result.location.display_name} "
                        f"(Row {result.location.row_number})"
                    ):
                        if result.warnings:
                            st.warning("**Warnings:**")
                            for warning in result.warnings:
                                st.write(f"- {warning}")
                        if result.similar_locations:
                            st.info(
                                f"**Similar locations:** "
                                f"{', '.join(result.similar_locations)}"
                            )
    else:
        st.success("All locations passed validation!")


def render_metrics(result: AnalysisResult) -> None:
    """Render summary metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Competitors", result.total_competitors)

    with col2:
        avg_rating = result.average_rating
        st.metric(
            "Avg Rating", f"{avg_rating:.1f} stars" if avg_rating else "N/A"
        )

    with col3:
        closest = result.closest_competitor
        if closest and closest.distance_miles is not None:
            st.metric("Closest", f"{closest.distance_miles:.1f} mi")
        else:
            st.metric("Closest", "N/A")

    with col4:
        st.metric("Center-Based", result.center_based_count)


def render_all_competitors_tab(
    competitors: List[Competitor], search_params: SearchParameters
) -> None:
    """Render all competitors tab with service type column."""
    st.subheader("All Competitors")

    df_data = []
    for c in competitors:
        df_data.append(
            {
                "Name": c.name,
                "Address": c.vicinity,
                "Service Type": c.display_service_type,
                "Rating": c.rating,
                "Reviews": c.user_ratings_total,
                "Distance": c.display_distance,
                "Drive Time": c.display_drive_time,
                "Phone": c.display_phone_number,
                "Website": c.display_website,
                "Hours": c.display_operating_hours,
                "Google Maps": c.display_google_maps_url,
            }
        )

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # CSV export
    csv_data = []
    for c in competitors:
        distance_csv = (
            f"{c.distance_miles:.1f}" if c.distance_miles is not None else "N/A"
        )
        drive_time_csv = (
            str(c.drive_time_minutes) if c.drive_time_minutes is not None else "N/A"
        )
        hours_csv = "; ".join(c.operating_hours) if c.operating_hours else "N/A"

        csv_data.append(
            {
                "Name": c.name,
                "Address": c.vicinity,
                "Service Type": c.effective_service_type.value,
                "Rating": c.rating,
                "Reviews": c.user_ratings_total,
                "Distance (miles)": distance_csv,
                "Drive Time (minutes)": drive_time_csv,
                "Phone": c.phone_number or "N/A",
                "Website": c.website or "N/A",
                "Operating Hours": hours_csv,
                "Google Maps URL": c.google_maps_url or "N/A",
            }
        )
    csv_df = pd.DataFrame(csv_data)
    csv = csv_df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name=(
            f"aba_competitors_{search_params.location_name}_"
            f"{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        ),
        mime="text/csv",
    )


def render_map_view(result: AnalysisResult) -> None:
    """Render interactive map of competitors."""
    st.subheader("Competitor Map")

    fig = go.Figure()

    # Add client location
    center_loc = result.client_location
    fig.add_trace(
        go.Scattermap(
            lat=[center_loc.lat],
            lon=[center_loc.lng],
            mode="markers",
            marker={"size": 20, "color": "red", "symbol": "star"},
            text=[f"{result.search_params.location_name}"],
            name="Search Location",
            showlegend=True,
        )
    )

    # Add all competitors in Tuscany orange
    if result.competitors:
        lats = [c.location.lat for c in result.competitors]
        lngs = [c.location.lng for c in result.competitors]
        names = [
            f"{c.name} ({c.effective_service_type.value})" for c in result.competitors
        ]

        fig.add_trace(
            go.Scattermap(
                lat=lats,
                lon=lngs,
                mode="markers",
                marker={"size": 12, "color": "#ED8B00", "opacity": 0.8},
                text=names,
                name=f"Competitors ({len(result.competitors)})",
                showlegend=True,
            )
        )

    fig.update_layout(
        map_style="open-street-map",
        map={
            "center": {"lat": center_loc.lat, "lon": center_loc.lng},
            "zoom": 12,
        },
        height=500,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend={
            "yanchor": "top",
            "y": 0.99,
            "xanchor": "left",
            "x": 0.01,
            "bgcolor": "rgba(255,255,255,0.8)",
            "bordercolor": "rgba(0,0,0,0.2)",
            "borderwidth": 1,
        },
    )

    st.plotly_chart(fig, use_container_width=True)


def render_analysis_tab(result: AnalysisResult) -> None:
    """Render analysis tab with service type breakdown and rating distribution."""
    st.subheader("Market Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Service type distribution pie chart
        type_counts = {}
        for st_type in ServiceType:
            count = len(
                [
                    c
                    for c in result.competitors
                    if c.effective_service_type == st_type
                ]
            )
            if count > 0:
                type_counts[st_type.value] = count

        if type_counts:
            fig_pie = px.pie(
                values=list(type_counts.values()),
                names=list(type_counts.keys()),
                title="Competitors by Service Type",
                color_discrete_sequence=["#ED8B00", "#F5A623", "#A4514D", "#999999"],
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Rating distribution histogram
        ratings = [c.rating for c in result.competitors if c.rating is not None]
        if ratings:
            fig_hist = px.histogram(
                x=ratings,
                nbins=10,
                title="Competitor Rating Distribution",
                labels={"x": "Rating", "y": "Count"},
                color_discrete_sequence=["#ED8B00"],
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # Market summary
    st.markdown("### Market Summary")

    total = result.total_competitors
    avg_rating = result.average_rating
    center_count = result.center_based_count
    in_home_count = result.in_home_count

    st.markdown(
        f"""
    **Market Density:** {total} ABA providers within {result.search_params.radius_miles} miles

    **Service Breakdown:**
    - {center_count} center-based providers
    - {in_home_count} in-home providers
    - {total - center_count - in_home_count} unknown/both

    **Average Rating:** {f'{avg_rating:.1f} stars' if avg_rating else 'N/A'}
    """
    )


def render_progress(current: int, total: int, message: str) -> Tuple[Any, Any]:
    """Render progress bar and status message."""
    progress = current / total
    progress_bar = st.progress(progress)
    status_text = st.empty()
    status_text.text(message)
    return progress_bar, status_text
