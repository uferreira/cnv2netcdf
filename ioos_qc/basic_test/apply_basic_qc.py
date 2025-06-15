import argparse
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from ioos_qc.qartod import gross_range_test, spike_test

def apply_qc_and_save(netcdf_file, output_file):
    """
    Apply simplified IOOS QC (gross range + spike test) to selected variables in a NetCDF file.
    Saves updated file with QC flags and diagnostic plots.
    """
    ds = xr.open_dataset(netcdf_file)
    obs_dim = "obs"
    trajectory_dim = "trajectory"

    # Define which variables will be quality controlled
    target_vars = ['t090c', 'sal00', 'wetstar']
    print("🔍 QC target variables:", target_vars)

    for var in target_vars:
        print(f"\n📊 Running simplified QC for {var}...")
        data = ds[var].isel(trajectory=0).values

        # Conservative thresholds
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

        # Run basic tests
        flags_gr = gross_range_test(data, suspect_span=suspect_span, fail_span=fail_span)
        flags_spike = spike_test(data, suspect_threshold=spike_suspect, fail_threshold=spike_fail)

        # Combine flags (max value per observation)
        combined_flags = np.maximum(flags_gr, flags_spike)

        # Save QC result as a new variable in the dataset
        qc_var_name = f"{var}_qc"
        ds[qc_var_name] = ((trajectory_dim, obs_dim), combined_flags[np.newaxis, :].astype("int8"))
        ds[qc_var_name].attrs.update({
            "long_name": f"{var} quality control flags",
            "standard_name": "aggregate_quality_flag",
            "flag_values": [1, 2, 3, 4],
            "flag_meanings": "good_data probably_good_data potentially_bad_data bad_data"
        })

        # Generate diagnostic plot
        plt.figure(figsize=(10, 3))
        plt.plot(combined_flags, marker='o', linestyle='-', label=f"{var} QC")
        plt.title(f"IOOS QC Flags for {var} (Basic Only)")
        plt.xlabel("Observation")
        plt.ylabel("QC Flag")
        plt.ylim(-1, 5)
        plt.grid(True)
        plt.savefig(f"{var}_qc_flags_basic.png", dpi=150)
        plt.close()

        print(f"✅ Flag counts for {var}: {np.unique(combined_flags, return_counts=True)}")

    # Save updated NetCDF with QC flags
    ds.to_netcdf(output_file, format="NETCDF4", engine="netcdf4")
    print(f"\n🎉 Simplified QC NetCDF saved as: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply basic IOOS QC (gross range + spike) to NetCDF file.")
    parser.add_argument("--input", "-i", required=True, help="Input NetCDF file path")
    parser.add_argument("--output", "-o", required=True, help="Output NetCDF file path with QC flags")
    args = parser.parse_args()

    apply_qc_and_save(args.input, args.output)


# Example usage:
# python apply_basic_qc.py --input 20210602_trajectory_cf.nc --output ctd_with_qc_basic.nc