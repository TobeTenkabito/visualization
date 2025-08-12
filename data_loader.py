import xarray as xr
import io
import base64


def load_dataset(file_content, file_name):
    """
    根据文件内容和名称加载数据集，并将其转换为可JSON序列化的字典。
    支持 .nc (NetCDF) 和 .grib 格式。

    参数:
    - file_content (str): Base64 编码的文件内容。
    - file_name (str): 上传的文件名。

    返回:
    - tuple: (JSON字典, 时间坐标, 经度, 纬度, 可视化选项)
    """
    ds_dict = {}
    time_coords = []
    lons = []
    lats = []
    visualization_options = []

    try:
        content_type, content_string = file_content.split(',')
        decoded = base64.b64decode(content_string)

        file_buffer = io.BytesIO(decoded)

        if file_name.endswith('.nc'):
            # 使用 dask 自动分块，优化大文件处理
            ds = xr.open_dataset(file_buffer, chunks={'time': 1000})

            ds_dict = {
                'variables': {},
                'coords': {
                    # 将时间坐标转换为字符串，因为dcc.Store无法直接存储numpy日期时间对象
                    'time': ds.time.values.astype(str).tolist(),
                    'lon': ds.lon.values.tolist(),
                    'lat': ds.lat.values.tolist()
                }
            }

            # 提取所有变量的数据并转换为列表，使用dask.array.array将其转换为dask数组
            for var in ds.data_vars:
                if 'time' in ds[var].dims and 'lon' in ds[var].dims:
                    # 仅加载可视化所需的数据，而不是整个数据集
                    data = ds[var].values
                    # 为了在dcc.Store中存储，需要将数据转换为列表
                    ds_dict['variables'][var] = data.tolist()

            time_coords = ds.time.values
            lons = ds.lon.values
            lats = ds.lat.values[::-1]

            dynamic_options = [{'label': var, 'value': var} for var in ds.data_vars if
                               'time' in ds[var].dims and 'lon' in ds[var].dims]
            visualization_options = [
                                        {'label': '大气河流可视化', 'value': 'Combined'},
                                        {'label': '待拓展', 'value': 'Other'}
                                    ] + dynamic_options

            return ds_dict, time_coords, lons, lats, visualization_options

        elif file_name.endswith('.grib'):
            print("注意：目前尚不支持GRIB文件格式，请上传NetCDF文件。")
            return {}, [], [], [], []
        else:
            print("不支持的文件格式。")
            return {}, [], [], [], []

    except Exception as e:
        print(f"错误：加载文件时出错 - {str(e)}")
        return {}, [], [], [], []
