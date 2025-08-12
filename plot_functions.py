import plotly.graph_objects as go
import plotly.colors
import pandas as pd
import numpy as np
from data_loader import ds, lons, lats


def create_combined_ar_figure(selected_time_index, current_figure):
    """
    根据给定的时间索引和当前图形数据，生成一个包含大气河流综合可视化数据的 Plotly Figure。

    参数:
    - selected_time_index (int): 选定的时间步索引。
    - current_figure (dict): 当前地图图形的 JSON 格式字典，用于更新。

    返回:
    - tuple: (go.Figure, str) 包含更新后的图形对象和时间显示字符串。
    """
    # 初始化图形对象
    fig = go.Figure(current_figure)
    fig.data = []

    # 获取当前时间并格式化
    current_time = pd.Timestamp(ds.time.isel(time=selected_time_index).values).tz_localize('UTC').tz_convert(
        'Asia/Tokyo').strftime('%Y-%m-%d %H:%M')
    time_display = f"当前时间 (JST): {current_time}"

    # 加载AR属性数据
    length_data = ds['length'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    width_data = ds['width'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    life_data = ds['klifetime'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    distance_data = ds['kdist'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    id_data = ds['kid'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    axislon_data = ds['axislon'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    axislat_data = ds['axislat'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    kspeed_data = ds['kspeed'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    kstatus_data = ds['kstatus'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()

    # --- 1. 绘制大气河流掩码（背景）和AR轴线 ---
    shapemap = ds['shapemap'].isel(time=selected_time_index, ens=0, lev=0).compute()
    ar_values = shapemap.values[::-1, :]
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    unique_ids = np.unique(ar_values[~np.isnan(ar_values)])
    colors = plotly.colors.qualitative.Plotly

    if len(unique_ids) > 0:
        for idx, uid in enumerate(unique_ids):
            mask = ar_values == uid
            lon_points = lon_grid[mask]
            lat_points = lat_grid[mask]
            if len(lon_points) > 0:
                ar_length = length_data.values[int(uid) - 1]
                ar_width = width_data.values[int(uid) - 1]
                ar_life = life_data.values[int(uid) - 1]
                ar_distance = distance_data.values[int(uid) - 1]
                ar_id = id_data.values[int(uid) - 1]
                ar_speed = kspeed_data.values[int(uid) - 1]
                ar_status = kstatus_data.values[int(uid) - 1]

                trace = go.Scattergeo(
                    lon=lon_points,
                    lat=lat_points,
                    mode='markers',
                    marker=dict(size=2, color=colors[idx % len(colors)], opacity=0.7),
                    name=f'AR {int(uid)}',
                    customdata=[[ar_length, ar_width, ar_life, ar_distance, ar_id, ar_speed, ar_status]] * len(
                        lon_points),
                    hovertemplate='<b>經度: %{lon:.2f} 緯度: %{lat:.2f}</b><br>'
                                  'AR 長度: %{customdata[0]:.2f} m<br>'
                                  'AR 寬度: %{customdata[1]:.2f} m<br>'
                                  'AR 生命: %{customdata[2]:.2f} s<br>'
                                  'AR 距離: %{customdata[3]:.2f} m<br>'
                                  'AR 速度: %{customdata[5]:.2f} m/s<br>'
                                  'AR 狀態: %{customdata[6]:.0f}<br>'
                                  'AR 标识: %{customdata[4]:.2f} <extra></extra>',
                    showlegend=True,
                )
                fig.add_trace(trace)

            axis_lon_points = axislon_data.isel(lat=int(uid) - 1).values[
                ~np.isnan(axislon_data.isel(lat=int(uid) - 1).values)]
            axis_lat_points = axislat_data.isel(lat=int(uid) - 1).values[
                ~np.isnan(axislat_data.isel(lat=int(uid) - 1).values)]

            if len(axis_lon_points) > 0:
                axis_trace = go.Scattergeo(
                    lon=axis_lon_points,
                    lat=axis_lat_points,
                    mode='lines',
                    line=dict(color='purple', width=1),
                    name=f'AR {int(uid)} 軸',
                    showlegend=False,
                    hoverinfo='none',
                )
                fig.add_trace(axis_trace)

    # --- 2. 繪製質心點和IVT向量 ---
    clon_data = ds['clon'].isel(time=selected_time_index).squeeze().compute()
    clat_data = ds['clat'].isel(time=selected_time_index).squeeze().compute()
    ivt_x_data = ds['ivtx'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    ivt_y_data = ds['ivty'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()

    ar_indices = np.where(~np.isnan(clon_data.values))[0]
    lon_points_centroid = clon_data.values[ar_indices]
    lat_points_centroid = clat_data.values[ar_indices]
    ivt_x_points = ivt_x_data.values[ar_indices]
    ivt_y_points = ivt_y_data.values[ar_indices]

    if len(lon_points_centroid) > 0:
        ivt_magnitude = np.sqrt(ivt_x_points ** 2 + ivt_y_points ** 2)
        ivt_direction_rad = np.arctan2(ivt_y_points, ivt_x_points)
        ivt_direction_deg = np.rad2deg(ivt_direction_rad)

        scatter_trace_centroid = go.Scattergeo(
            lon=lon_points_centroid,
            lat=lat_points_centroid,
            mode='markers',
            marker=dict(color='red', size=5, opacity=0.8),
            name='質心',
            showlegend=True,
        )
        fig.add_trace(scatter_trace_centroid)

        ivt_vectors = go.Scattergeo(
            lon=lon_points_centroid,
            lat=lat_points_centroid,
            mode='markers',
            marker=dict(
                symbol='arrow',
                size=(ivt_magnitude / np.nanmax(ivt_magnitude)) * 10 + 2,
                color=ivt_magnitude,
                colorscale='Viridis',
                cmin=0,
                cmax=np.nanmax(ivt_magnitude),
                showscale=True,
                colorbar=dict(
                    title='IVT強度',
                    orientation='h',
                    x=0.5,
                    xanchor='center',
                    y=-0.1,
                    yanchor='top'
                ),
                opacity=0.7,
                angle=ivt_direction_deg + 180,
            ),
            text=[f"IVT強度: {mag:.2f}<br>方向: {dir:.0f}°" for mag, dir in
                  zip(ivt_magnitude, ivt_direction_deg)],
            hovertemplate='<b>經度: %{lon:.2f}<br>緯度: %{lat:.2f}</b><br>%{text}<extra></extra>',
            name='IVT向量',
            showlegend=False,
        )
        fig.add_trace(ivt_vectors)

    # --- 3. 繪製頭部點 ---
    hlon_data = ds['hlon'].isel(time=selected_time_index).squeeze().compute()
    hlat_data = ds['hlat'].isel(time=selected_time_index).squeeze().compute()
    head_lon_points = hlon_data.values[~np.isnan(hlon_data.values)]
    head_lat_points = hlat_data.values[~np.isnan(hlat_data.values)]

    if len(head_lon_points) > 0:
        head_trace = go.Scattergeo(
            lon=head_lon_points,
            lat=head_lat_points,
            mode='markers',
            marker=dict(color='green', size=8, symbol='triangle-up',
                        line=dict(width=1, color='DarkSlateGrey')),
            name='頭部',
            text=[f"經度: {lon:.2f}<br>緯度: {lat:.2f}" for lon, lat in
                  zip(head_lon_points, head_lat_points)],
            hovertemplate='<b>%{text}</b><extra></extra>',
            showlegend=True,
        )
        fig.add_trace(head_trace)

    # --- 4. 繪製尾部點 ---
    tlon_data = ds['tlon'].isel(time=selected_time_index).squeeze().compute()
    tlat_data = ds['tlat'].isel(time=selected_time_index).squeeze().compute()
    tail_lon_points = tlon_data.values[~np.isnan(tlon_data.values)]
    tail_lat_points = tlat_data.values[~np.isnan(tlat_data.values)]

    if len(tail_lon_points) > 0:
        tail_trace = go.Scattergeo(
            lon=tail_lon_points,
            lat=tail_lat_points,
            mode='markers',
            marker=dict(color='blue', size=8, symbol='square', line=dict(width=1, color='DarkSlateGrey')),
            name='尾部',
            text=[f"經度: {lon:.2f}<br>緯度: {lat:.2f}" for lon, lat in
                  zip(tail_lon_points, tail_lat_points)],
            hovertemplate='<b>%{text}</b><extra></extra>',
            showlegend=True,
        )
        fig.add_trace(tail_trace)

    # --- 5. 繪製登陸點 ---
    lflon_data = ds['lflon'].isel(time=selected_time_index).squeeze().compute()
    lflat_data = ds['lflat'].isel(time=selected_time_index).squeeze().compute()
    lfivtdir_data = ds['lfivtdir'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    lfivtx_data = ds['lfivtx'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
    lfivty_data = ds['lfivty'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()

    valid_indices = ~np.isnan(lflon_data.values)
    lon_points_landfall = lflon_data.values[valid_indices]
    lat_points_landfall = lflat_data.values[valid_indices]
    ivtdir_points = lfivtdir_data.values[valid_indices]
    ivtx_points = lfivtx_data.values[valid_indices]
    ivty_points = lfivty_data.values[valid_indices]

    if len(lon_points_landfall) > 0:
        hover_text = [
            f"經度: {lon:.2f}<br>緯度: {lat:.2f}<br>"
            f"IVT 方向: {ivtdir:.2f}°<br>"
            f"IVT 經向分量: {ivtx:.2f} kg m^-1 s^-1<br>"
            f"IVT 緯向分量: {ivty:.2f} kg m^-1 s^-1"
            for lon, lat, ivtdir, ivtx, ivty in zip(
                lon_points_landfall,
                lat_points_landfall,
                ivtdir_points,
                ivtx_points,
                ivty_points
            )
        ]
        landfall_trace = go.Scattergeo(
            lon=lon_points_landfall,
            lat=lat_points_landfall,
            mode='markers',
            marker=dict(color='#ff7f0e', size=7, opacity=1, symbol='star',
                        line=dict(width=1, color='DarkSlateGrey')),
            name='登陸點',
            text=hover_text,
            hovertemplate='<b>%{text}</b><extra></extra>',
            showlegend=True,
        )
        fig.add_trace(landfall_trace)

    fig.update_layout(title=f"全球大气河流綜合可視化 - 時間: {current_time}", showlegend=True)

    covered_points = np.sum(~np.isnan(ar_values))
    total_points = lons.size * lats.size
    time_display += f" | 覆蓋格點: {covered_points}/{total_points} ({covered_points / total_points * 100:.2f}%)"

    return fig, time_display


def create_era5_figure(selected_time_index, selected_variable, current_figure):
    fig = go.Figure(current_figure)
    fig.data = []

    current_time = pd.Timestamp(ds.time.isel(time=selected_time_index).values).tz_localize('UTC').tz_convert(
        'Asia/Tokyo').strftime('%Y-%m-%d %H:%M')
    time_display = f"当前时间 (JST): {current_time}"

    # 定义变量映射和显示名称
    variable_map = {
        'ERA5-temp': {'data_var': 't2m', 'title': '2米温度 (K)', 'colorscale': 'Viridis'},
        'ERA5-precip': {'data_var': 'tp', 'title': '总降水 (m)', 'colorscale': 'Blues'}
    }

    if selected_variable in variable_map:
        var_info = variable_map[selected_variable]
        data_var = var_info['data_var']
        title = var_info['title']
        colorscale = var_info['colorscale']

        # 加载ERA5数据
        era5_data = ds[data_var].isel(time=selected_time_index).squeeze().compute()
        # 将数据翻转以匹配地图坐标
        z_data = era5_data.values[::-1, :]

        # 创建热力图
        heatmap_trace = go.Heatmap(
            z=z_data,
            x=lons,
            y=lats,
            colorscale=colorscale,
            name=title,
            colorbar=dict(title=title)
        )
        fig.add_trace(heatmap_trace)

        fig.update_layout(title=f"ERA5 {title} 可視化 - 時間: {current_time}", showlegend=False)
        return fig, time_display
    else:
        # 如果变量不存在，返回一个空图
        return fig, "变量未找到"
