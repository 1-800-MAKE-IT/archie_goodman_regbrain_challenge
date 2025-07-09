import streamlit as st
import requests
from similarity import plot_similarity_over_time
import pandas as pd

#NOTE - script produced with help from chatgpt

# FastAPI base URL
API_BASE_URL = "http://127.0.0.1:8000"

# Streamlit app
st.title("Regulatory Similarity Analysis")

# Button to fetch available jurisdictions
if st.button("Get Available Jurisdictions"):
    try:
        response = requests.get(f"{API_BASE_URL}/jurisdictions/")
        response_data = response.json()

        if response.status_code == 200:
            jurisdictions = response_data.get("jurisdictions", [])
            if not jurisdictions:
                st.error("No jurisdictions found in the database.")
            else:
                st.write("Available Jurisdictions:")
                st.write(jurisdictions)
        else:
            st.error(response_data.get("detail", "An error occurred while fetching jurisdictions."))
    except Exception as e:
        st.error(f"Failed to connect to the API: {e}")

# User input for countries
country_a = st.text_input("Enter the first country:", placeholder="e.g., Canada")
country_b = st.text_input("Enter the second country:", placeholder="e.g., United States of America")

# Button to fetch and plot similarity
if st.button("Analyze Similarity"):
    if not country_a or not country_b:
        st.error("Please enter both country names.")
    else:
        # Call the FastAPI endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/similarity/", params={"country_a": country_a, "country_b": country_b})
            response_data = response.json()

            if response.status_code == 200:
                similarity_sequence = response_data.get("similarity_sequence", [])
                if not similarity_sequence:
                    st.error("No similarity data found for the given countries.")
                else:
                    # Convert the sequence to a DataFrame
                    similarity_df = pd.DataFrame(similarity_sequence)

                    # Plot the similarity graph
                    fig = plot_similarity_over_time(similarity_df, country_a, country_b)
                    st.pyplot(fig)
            else:
                st.error(response_data.get("detail", "An error occurred while fetching similarity data."))
        except Exception as e:
            st.error(f"Failed to connect to the API: {e}")
