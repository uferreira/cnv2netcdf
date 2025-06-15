cd ../basic_test
python apply_basic_qc.py --input 20210602_trajectory_cf.nc --output ctd_with_qc_basic.nc
python plot_qc_temperature_map.py --input ctd_with_qc_basic.nc --output trajectory_plotly_qc_inverted_colors.html

cd ../dummy_time
python apply_ioos_qc.py --input 20210602_trajectory_cf1.nc --output ctd_with_qc.nc
python plot_qc_temperature_map.py --input ctd_with_qc.nc --output trajectory_plotly_qc_inverted_colors.html

cd ../parameter_threshold
python apply_custom_qc.py --input 20210602_trajectory_cf.nc --output ctd_with_qc_custom.nc
python plot_qc_temperature_map.py --input ctd_with_qc_custom.nc --output trajectory_plotly_qc_inverted_colors.html

cd ../qc_standard
python apply_qc_standard.py --input 20210602_trajectory_cf.nc --output ctd_with_qc.nc
python plot_qc_temperature_map.py --input ctd_with_qc.nc --output trajectory_plotly_qc_inverted_colors.html
