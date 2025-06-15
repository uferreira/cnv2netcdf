import argparse
import xarray as xr
import pandas as pd
import plotly.express as px

def plot_temperature_qc_map(netcdf_file, output_html):
    """
    Plots a temperature trajectory map using QC flags from a NetCDF file.
    Saves the output as an interactive HTML.
    """
    # Load NetCDF and extract variables to DataFrame
    ds = xr.open_dataset(netcdf_file)
    df = ds[["latitude", "longitude", "t090c", "t090c_qc"]].to_dataframe().reset_index().dropna()

    # Rename for clarity
    df = df.rename(columns={
        "latitude": "Latitude",
        "longitude": "Longitude",
        "t090c": "Temperature",
        "t090c_qc": "Temperature_QC_Flag"
    })

    # Label QC flag values for hover display
    qc_labels = {
        1: "1 - Good",
        2: "2 - Probably Good",
        3: "3 - Potentially Bad",
        4: "4 - Bad"
    }
    df["QC_Label"] = df["Temperature_QC_Flag"].map(qc_labels)

    # Inverted color scheme (Green = Good, Red = Bad)
    qc_colors = {
        "1 - Good": "green",
        "2 - Probably Good": "lightblue",
        "3 - Potentially Bad": "orange",
        "4 - Bad": "red"
    }

    # Plot the map using Plotly
    fig = px.scatter_map(
        df,
        lat="Latitude",
        lon="Longitude",
        hover_name="QC_Label",
        hover_data={
            "Latitude": True,
            "Longitude": True,
            "Temperature": True,
            "Temperature_QC_Flag": True
        },
        color="QC_Label",
        color_discrete_map=qc_colors,
        zoom=6,
        height=600
    )

    # Add map styling and QC legend annotation
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False
    )

    fig.add_annotation(
        text="QC Flags (IOOS):<br>"
             "<span style='color:green;'>1 = Good</span><br>"
             "<span style='color:lightblue;'>2 = Probably Good</span><br>"
             "<span style='color:orange;'>3 = Potentially Bad</span><br>"
             "<span style='color:red;'>4 = Bad</span>",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        align="left",
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )

    # Save but don't show interactively
    fig.write_html(output_html)
    print(f"✅ Map saved to: {output_html}")

    # Save and display
    # fig.write_html(output_html)
    # fig.show()
    # print(f"✅ Map saved to: {output_html}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot QC’d temperature map from NetCDF.")
    parser.add_argument("--input", "-i", required=True, help="Input NetCDF file (with t090c_qc)")
    parser.add_argument("--output", "-o", required=True, help="Output HTML file")
    args = parser.parse_args()

    plot_temperature_qc_map(args.input, args.output)