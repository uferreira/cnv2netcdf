# IMR Assignment 2 – CNV to CF-Compliant NetCDF Converter

This repository was created for the **Institute of Marine Research (IMR)** and the **EAF-Nansen Program**.

This tool convert a CNV file from a SBE thermosalinograph into a **trajectory-style NetCDF** file compliant with the **Climate and Forecast (CF) Metadata Conventions**, including proper metadata population with CF-standard attributes and standard names.

## Repository Structure

```
├── assignment2_cnv2nc/
│   ├── 20210602.cnv                  # Original CNV file from Norwegian Data Center Catalog
│   ├── convert_cnv_to_netcdf.py     # Main conversion script (CNV → CF-compliant NetCDF)
│   └── 20210602_trajectory_cf.nc    # Resulting NetCDF file, fully CF-compliant
│
├── ioos_qc/                          # Bonus: Quality Control tests based on IOOS QC guidelines
│   ├── basic_test/                  # Basic IOOS QC flags
│   ├── dummy_time/                  # Handling of time dummy values with QC
│   ├── parameter_threshold/         # QC based on parameter-specific thresholds
│   ├── qc_standard/                 # Standard QC testing implementation
│   ├── IMR_Assignment2.ipynb        # Annotated Jupyter Notebook for QC workflows and visualization
│   ├── *.html, *.png                # Interactive plots and QC visualizations
│   └── readme_usage.txt             # Brief usage instructions for the QC pipeline
│
└── README.md                        # This file
```

---

## 1. 🧪 Assignment 2 – CNV to NetCDF

### 📄 Description
- Reads a `.cnv` file and parses metadata and variables based on the file header.
- Converts it to a **trajectory-style NetCDF** file using `xarray` and `netCDF4`.
- Applies **CF-1.8 conventions**, using appropriate `standard_name`, `units`, and `coordinates`.

### 🛠 Technologies & Setup

This project uses Python and the following key packages:
- `xarray`, `netCDF4`, `pandas`, `numpy`, `plotly`, `folium`, `ioos_qc`, etc.

📦 To install all required dependencies, run:

```bash
pip install -r requirements.txt
```

### 🚀 How to Run

```bash
python convert_cnv_to_netcdf.py --input [input cnv file name].cnv --output [output nc file name].nc
```

Ensure the CNV file is named `*.cnv` and is located in the same folder as the script.

---

## 2. Additional: IOOS Quality Control Extensions (Optional)

The `ioos_qc/` folder provides additional quality control workflows using **IOOS QC tests**. It includes:
- Temperature/salinity/wetstar QC flagging
- Trajectory mapping with **Plotly**, **Folium**, and static image outputs
- Multiple configurations for threshold-based and standard flagging
- Fully annotated **Jupyter Notebook** with usage examples

These tools can be used to complement and extend the validation of oceanographic datasets following FAIR principles.

---

## 📌 Notes

- The original CNV file used was downloaded from the [Norwegian Data Center Catalog](http://metadata.nmdc.no/metadata-api/landingpage/6eaf5271f09577e8743dc87d7fe7bf41).
- The CF conventions followed can be found at [cfconventions.org](https://cfconventions.org/Data/cf-conventions/cf-conventions-1.12/cf-conventions.html).
- IOOS QC methods refer to standards described in the [ioos_qc repository](https://github.com/ioos/ioos_qc).

---

## 🧑‍💼 Author

**Uggo Pinho**  
Oceanographer and Ocean Data Analyst.

---

## 🐳 License

This project is released for evaluation purposes and educational demonstration. Please contact the author for reuse.
