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
    Apply variable-specific IOOS QC tests (gross range, spike, flat line, rate of change)
    to a NetCDF trajectory file and save updated dataset with QC flags and diagnostic plots.
    """
    ds = xr.open_dataset(netcdf_file)
    obs_dim = "obs"
    trajectory_dim = "trajectory"

    # Real timestamps for time-based tests
    time_array = ds["time"].isel(trajectory=0).values.astype("datetime64[s]").astype("O")

    # Define which variables to QC
    target_vars = ['t090c', 'sal00', 'wetstar']
    print("🔍 QC target variables:", target_vars)

    for var in target_vars:
        print(f"\n📊 Running QC for {var}...")
        data = ds[var].isel(trajectory=0).values

        # Variable-specific QC thresholds
        if var == "t090c":
            fail_span = [-2, 35]
            suspect_span = [-1.5, 32]
            spike_suspect, spike_fail = 0.5, 1.0
            flat_suspect, flat_fail, flat_tolerance = 15, 30, 0.005
            roc_threshold = 2.0

        elif var == "sal00":
            fail_span = [0, 42]
            suspect_span = [1, 40]
            spike_suspect, spike_fail = 1.0, 2.0
            flat_suspect, flat_fail, flat_tolerance = 30, 60, 0.01
            roc_threshold = 5.0

        else:  # wetstar or others
            fail_span = [0, 50]
            suspect_span = [0.1, 45]
            spike_suspect, spike_fail = 1.5, 3.0
            flat_suspect, flat_fail, flat_tolerance = 20, 45, 0.01
            roc_threshold = 10.0

        # Apply IOOS QARTOD tests
        flags_gr = gross_range_test(data, suspect_span=suspect_span, fail_span=fail_span)
        flags_spike = spike_test(data, suspect_threshold=spike_suspect, fail_threshold=spike_fail)

        try:
            if len(np.unique(time_array)) < 2:
                raise ValueError("time_array has no variation")
            flags_flat = flat_line_test(
                data, time_array,
                suspect_threshold=flat_suspect,
                fail_threshold=flat_fail,
                tolerance=flat_tolerance
            )
        except Exception as e:
            print(f"⚠️ Skipping flat_line_test for {var}: {e}")
            flags_flat = np.ones_like(data, dtype="int8")

        try:
            if len(np.unique(time_array)) < 2:
                raise ValueError("time_array has no variation")
            flags_roc = rate_of_change_test(data, time_array, threshold=roc_threshold)
        except Exception as e:
            print(f"⚠️ Skipping rate_of_change_test for {var}: {e}")
            flags_roc = np.ones_like(data, dtype="int8")

        # Combine all test results
        combined_flags = np.maximum.reduce([flags_gr, flags_spike, flags_flat, flags_roc])

        # Save QC result in dataset
        qc_var_name = f"{var}_qc"
        ds[qc_var_name] = ((trajectory_dim, obs_dim), combined_flags[np.newaxis, :].astype("int8"))
        ds[qc_var_name].attrs.update({
            "long_name": f"{var} quality control flags",
            "standard_name": "aggregate_quality_flag",
            "flag_values": [1, 2, 3, 4],
            "flag_meanings": "good_data probably_good_data potentially_bad_data bad_data"
        })

        # Create and save diagnostic plot
        plt.figure(figsize=(10, 3))
        plt.plot(combined_flags, marker='o', linestyle='-', label=f"{var} QC")
        plt.title(f"IOOS QC Flags for {var}")
        plt.xlabel("Observation")
        plt.ylabel("QC Flag")
        plt.ylim(-1, 5)
        plt.grid(True)
        plt.savefig(f"{var}_qc_flags_custom.png", dpi=150)
        plt.close()

        print(f"✅ Flag counts for {var}: {np.unique(combined_flags, return_counts=True)}")

    # Save updated NetCDF with QC flags
    ds.to_netcdf(output_file, format="NETCDF4", engine="netcdf4")
    print(f"\n🎉 QC-enhanced NetCDF saved as: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply IOOS QARTOD QC to NetCDF with custom thresholds.")
    parser.add_argument("--input", "-i", required=True, help="Input NetCDF file path")
    parser.add_argument("--output", "-o", required=True, help="Output NetCDF file path with QC flags")
    args = parser.parse_args()

    apply_qc_and_save(args.input, args.output)


# Example usage:
# python apply_custom_qc.py --input 20210602_trajectory_cf.nc --output ctd_with_qc_custom.nc