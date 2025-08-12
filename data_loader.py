import xarray as xr
file_path = 'G:/Ar_dataverse/globalARcatalog_ERA5_1940-2024_v4.0.nc'

try:
    ds = xr.open_dataset(file_path, chunks={'time': 1000})
    print("数据集加载成功。")

    time_coords = ds.time.values
    lons = ds.lon.values
    lats = ds.lat.values[::-1]

    # 添加新的综合可视化选项
    visualization_options = [
        {'label': '大气河流可视化', 'value': 'Combined'},
        {'label': '降水可视化', 'value': 'Precipitation'},
        {'label': '待拓展', 'value': 'Other'}
    ]

except FileNotFoundError:
    print(f"错误：文件 '{file_path}' 未找到。请检查文件路径是否正确。")
    ds = None
    time_coords = []
    lons = []
    lats = []
    visualization_options = []
except Exception as e:
    print(f"错误：加载数据集时出错 - {str(e)}")
    ds = None
    time_coords = []
    lons = []
    lats = []
    visualization_options = []