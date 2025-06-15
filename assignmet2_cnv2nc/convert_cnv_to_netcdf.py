import re
import argparse
import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime, timedelta, UTC

def parse_cnv(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()

    variable_names = []
    units = []
    header_lines = []
    start_time = None

    for i, line in enumerate(lines):
        if line.strip() == "*END*":
            data_start = i + 1
            break
        header_lines.append(line)

        # Parse start_time
        if "start_time" in line.lower():
            match = re.search(r"# start_time\s*=\s*(.*)\s+\[", line)
            if match:
                start_time = match.group(1).strip()

        # Parse variable names and units
        match = re.match(r"# name \d+ = (.+?):", line)
        if match:
            variable = match.group(1).strip()
            variable_names.append(variable)
            unit_match = re.search(r"\[([^\]]+)\]", line)
            units.append(unit_match.group(1) if unit_match else "")

    df = pd.read_csv(filepath, skiprows=data_start, sep=r'\s+', engine='python', names=variable_names)
    df = df.apply(pd.to_numeric, errors='coerce')

    return df, variable_names, units, start_time


def create_cf_netcdf(df, variable_names, units, start_time_str, output_path):
    ds = xr.Dataset()
    obs_len = len(df)

    # Start time handling
    if start_time_str:
        start_time = datetime.strptime(start_time_str, "%b %d %Y %H:%M:%S").replace(tzinfo=UTC)
    else:
        start_time = datetime.now(UTC)

    # Time conversion
    if "timeJ" in df.columns:
        base = datetime(start_time.year, 1, 1, tzinfo=UTC)
        time_julian = df["timeJ"]
        time_datetimes = [base + timedelta(days=float(jd)) for jd in time_julian]
        seconds_since_epoch = [(dt - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds() for dt in time_datetimes]
        ds["time"] = ("obs", np.array(seconds_since_epoch))
        ds["time"].attrs.update({
            "standard_name": "time",
            "units": "seconds since 1970-01-01T00:00:00Z",
            "calendar": "gregorian",
            "axis": "T"
        })
    else:
        ds["time"] = ("obs", [np.datetime64(start_time)] * obs_len)

    # Coordinates
    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df.columns if "lon" in c.lower()), None)
    ds["lat"] = ("obs", df[lat_col].values if lat_col else [np.nan] * obs_len)
    ds["lon"] = ("obs", df[lon_col].values if lon_col else [np.nan] * obs_len)

    ds["lat"].attrs.update({"standard_name": "latitude", "units": "degrees_north", "axis": "Y"})
    ds["lon"].attrs.update({"standard_name": "longitude", "units": "degrees_east", "axis": "X"})

    # CF variable names
    standard_name_map = {
        "temperature": "sea_water_temperature",
        "salinity": "sea_water_practical_salinity",
        "pressure": "sea_water_pressure",
        "depth": "depth",
        "fluorescence": "volume_scattering_function"
    }

    for i, col in enumerate(df.columns):
        var_name = col.lower().replace(" ", "_")
        standard_name = next((v for k, v in standard_name_map.items() if k in var_name), None)

        ds[var_name] = ("obs", df[col].values)
        ds[var_name].attrs["long_name"] = variable_names[i]
        ds[var_name].attrs["units"] = units[i] if i < len(units) else ""
        if standard_name:
            ds[var_name].attrs["standard_name"] = standard_name

    ds = ds.expand_dims("trajectory")
    ds["trajectory"] = ("trajectory", ["trajectory_001"])
    ds["trajectory"].attrs["cf_role"] = "trajectory_id"

    # Global attributes
    time_coverage_start = ds["time"].values[0].astype("M8[s]").astype(str)
    time_coverage_end = ds["time"].values[-1].astype("M8[s]").astype(str)
    duration = str(ds["time"].values[-1] - ds["time"].values[0])

    ds.attrs.update({
        "title": "EAF-Nansen Programme CTD Data",
        "summary": "CTD profile data converted from CNV to CF-compliant NetCDF trajectory format.",
        "Conventions": "CF-1.12",
        "institution": "Institute of Marine Research (IMR)",
        "source": "Sea-Bird CTD",
        "history": f"Converted from CNV using start_time '{start_time_str}'",
        "featureType": "trajectory",
        "references": "http://metadata.nmdc.no",
        "time_coverage_start": time_coverage_start,
        "time_coverage_end": time_coverage_end,
        "time_coverage_duration": duration
    })

    ds.to_netcdf(output_path, format="NETCDF4", engine="netcdf4")
    print(f"✅ NetCDF written to: {output_path}")


if __name__ == "__main__":
    # 🔹 Argument parser for terminal usage
    parser = argparse.ArgumentParser(description="Convert a Sea-Bird .cnv file to CF-compliant NetCDF.")
    parser.add_argument("--input", "-i", required=True, help="Path to input CNV file")
    parser.add_argument("--output", "-o", required=True, help="Path to output NetCDF file")

    args = parser.parse_args()

    df, variable_names, units, start_time = parse_cnv(args.input)
    create_cf_netcdf(df, variable_names, units, start_time, args.output)