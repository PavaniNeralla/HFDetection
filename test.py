import streamlit as st
import pandas as pd

# Sample data with key-value structured EF values
data = {
    "Patient Name": ["John Doe", "Jane Smith", "Alice Brown"],
    "EF Values": [
        {"EF": "60%", "EF-A2C": "34%", "BMI": "23"},
        {"EF": "55%", "EF-A2C": "30%", "BMI": "22"},
        {"EF": "50%", "EF-A2C": "25%", "BMI": "24"},
    ],
    "Risk Nature": ["High Risk", "Low Risk", "Moderate Risk"],
}
df = pd.DataFrame(data)

# Function to create expandable HTML content for EF Values (key-value pairs)
def make_expandable_ef_html(values):
    ef_values_html = "".join(f"<li><b>{key}</b>: {value}</li>" for key, value in values.items())
    html = f"""
    <details>
      <summary>Click to Expand</summary>
      <ul>
        {ef_values_html}
      </ul>
    </details>
    """
    # Strip newlines and return clean HTML
    return html.replace("\n", "")

# Apply the function to the EF Values column
df["EF Values"] = df["EF Values"].apply(make_expandable_ef_html)

# Convert DataFrame to an HTML table
table_html = df.to_html(escape=False, index=False)

# Render the table in Streamlit
st.markdown("### Extracted EF and Additional Metrics")
st.markdown(table_html, unsafe_allow_html=True)
