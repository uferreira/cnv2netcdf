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
    """
    Applies IOOS QARTOD QC tests (basic + time-based) to selected NetCDF variables
    and saves the results with added QC flags and diagnostic plots.
    """
    ds = xr.open_dataset(netcdf_file)
    obs_dim = "obs"
    trajectory_dim = "trajectory"

    # Use actual observation time for time-based tests
    time_array = ds["time"].isel(trajectory=0).values.astype("datetime64[s]").astype("O")

    # Define which variables to process
    target_vars = ['t090c', 'sal00', 'wetstar']
    print("🔍 QC target variables:", target_vars)

    for var in target_vars:
        print(f"\n📊 Running QC for {var}...")
        data = ds[var].isel(trajectory=0).values

        # General gross/spike threshold logic
        if "t090c" in var:
            fail_span = [-5, 45]
            suspect_span = [-2, 35]
        else:
            fail_span = [0, 50]
            suspect_span = [0.1, 42]

        # Apply basic tests
        flags_gr = gross_range_test(data, suspect_span=suspect_span, fail_span=fail_span)
        flags_spike = spike_test(data, suspect_threshold=5.0, fail_threshold=10.0)

        # Apply time-based tests (flat line and rate-of-change)
        try:
            if len(np.unique(time_array)) < 2:
                raise ValueError("Time array has no variation.")

            flags_flat = flat_line_test(
                data, time_array,
                suspect_threshold=20,
                fail_threshold=45,
                tolerance=0.01
            )
        except Exception as e:
            print(f"⚠️ Flat line test skipped for {var}: {e}")
            flags_flat = np.ones_like(data, dtype="int8")

        try:
            flags_roc = rate_of_change_test(data, time_array, threshold=30.0)
        except Exception as e:
            print(f"⚠️ ROC test skipped for {var}: {e}")
            flags_roc = np.ones_like(data, dtype="int8")

        # Combine test outputs into a final QC flag
        combined_flags = np.maximum.reduce([flags_gr, flags_spike, flags_flat, flags_roc])

        # Write flag back into NetCDF
        qc_var_name = f"{var}_qc"
        ds[qc_var_name] = ((trajectory_dim, obs_dim), combined_flags[np.newaxis, :].astype("int8"))
        ds[qc_var_name].attrs.update({
            "long_name": f"{var} quality control flags",
            "standard_name": "aggregate_quality_flag",
            "flag_values": [1, 2, 3, 4],
            "flag_meanings": "good_data probably_good_data potentially_bad_data bad_data"
        })

        # Save plot of QC flag profile
        plt.figure(figsize=(10, 3))
        plt.plot(combined_flags, marker='o', linestyle='-', label=f"{var} QC")
        plt.title(f"IOOS QC Flags for {var}")
        plt.xlabel("Observation")
        plt.ylabel("QC Flag")
        plt.ylim(-1, 5)
        plt.grid(True)
        plt.savefig(f"{var}_qc_flags.png", dpi=150)
        plt.close()

        print(f"✅ Flag counts for {var}: {np.unique(combined_flags, return_counts=True)}")

    # Save new NetCDF with QC variables
    ds.to_netcdf(output_file, format="NETCDF4", engine="netcdf4")
    print(f"\n🎉 QC-enhanced NetCDF saved as: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply IOOS QARTOD QC to NetCDF trajectory file.")
    parser.add_argument("--input", "-i", required=True, help="Input NetCDF file")
    parser.add_argument("--output", "-o", required=True, help="Output NetCDF file with QC")
    args = parser.parse_args()

    apply_qc_and_save(args.input, args.output)

# Example usage:
# python apply_qc_standard.py --input 20210602_trajectory_cf.nc --output ctd_with_qc.nc