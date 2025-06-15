import argparse
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from ioos_qc.qartod import (
    gross_range_test,
    spike_test,
    flat_line_test,
    rate_of_change_test,
)

def apply_qc_and_save(netcdf_file, output_file):
    """Applies IOOS QARTOD QC tests to selected variables in a NetCDF file."""
    ds = xr.open_dataset(netcdf_file)
    obs_dim = "obs"
    trajectory_dim = "trajectory"

    # Use dummy index time (change to real timestamps if needed)
    time_array = np.arange(ds.dims[obs_dim])

    # List the variables to QC
    target_vars = ['t090c', 'sal00', 'wetstar']
    print("🔍 QC target variables:", target_vars)

    for var in target_vars:
        print(f"🔬 Running QC for {var}")
        data = ds[var].isel(trajectory=0).values

        # Choose QC thresholds depending on variable
        if "t090c" in var:
            fail_span = [-5, 45]
            suspect_span = [-2, 35]
            spike_suspect = 0.5
            spike_fail = 1.0
        elif "sal" in var:
            fail_span = [0, 50]
            suspect_span = [0.1, 42]
            spike_suspect = 1.0
            spike_fail = 2.0
        else:
            fail_span = [0, 100]
            suspect_span = [0.01, 90]
            spike_suspect = 5.0
            spike_fail = 10.0

        # Run tests
        flags_gr = gross_range_test(data, suspect_span=suspect_span, fail_span=fail_span)
        flags_spike = spike_test(data, suspect_threshold=spike_suspect, fail_threshold=spike_fail)
        flags_flat = flat_line_test(data, time_array, suspect_threshold=5, fail_threshold=10, tolerance=0.001)
        flags_roc = rate_of_change_test(data, time_array, threshold=2.5)

        # Combine all tests using the most severe flag
        combined_flags = np.maximum.reduce([flags_gr, flags_spike, flags_flat, flags_roc])

        # Save as a new variable
        qc_var_name = f"{var}_qc"
        ds[qc_var_name] = ((trajectory_dim, obs_dim), combined_flags[np.newaxis, :].astype("int8"))
        ds[qc_var_name].attrs.update({
            "long_name": f"{var} quality control flags",
            "standard_name": "aggregate_quality_flag",
            "flag_values": [1, 2, 3, 4],
            "flag_meanings": "good_data probably_good_data potentially_bad_data bad_data"
        })

        # Save a plot
        plt.figure(figsize=(10, 3))
        plt.plot(combined_flags, marker='o', linestyle='-', label=f"{var} QC Flags")
        plt.title(f"IOOS QC Flags for {var}")
        plt.xlabel("Observation")
        plt.ylabel("QC Flag")
        plt.ylim(-1, 5)
        plt.grid(True)
        plt.savefig(f"{var}_qc_flags.png", dpi=150)
        plt.close()

        print(f"✅ QC flags for {var}: {np.unique(combined_flags, return_counts=True)}")

    # Save updated NetCDF
    ds.to_netcdf(output_file, format="NETCDF4", engine="netcdf4")
    print(f"\n🎉 QC-enhanced NetCDF saved as: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply IOOS QARTOD QC to NetCDF trajectory file.")
    parser.add_argument("--input", "-i", required=True, help="Input NetCDF file path")
    parser.add_argument("--output", "-o", required=True, help="Output NetCDF file path with QC flags")
    args = parser.parse_args()

    apply_qc_and_save(args.input, args.output)


# Example usage:
# python apply_ioos_qc.py --input 20210602_trajectory_cf.nc --output ctd_with_qc.nc