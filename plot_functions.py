import plotly.graph_objects as go
import plotly.colors
import pandas as pd
import numpy as np


def create_combined_ar_figure(selected_time_index, current_figure, ds_dict, time_coords, lons, lats):
    """
    根据给定的时间索引和当前图形数据，生成一个包含大气河流综合可视化数据的 Plotly Figure。

    参数:
    - selected_time_index (int): 选定的时间步索引。
    - current_figure (dict): 当前地图图形的 JSON 格式字典，用于更新。
    - ds_dict (dict): 从dcc.Store中传递过来的数据集字典。
    - time_coords (list): 时间坐标列表。
    - lons (list): 经度坐标列表。
    - lats (list): 纬度坐标列表。

    返回:
    - tuple: (go.Figure, str) 包含更新后的图形对象和时间显示字符串。
    """
    fig = go.Figure(current_figure)
    fig.data = []

    current_time = pd.Timestamp(time_coords[selected_time_index]).tz_localize('UTC').tz_convert(
        'Asia/Tokyo').strftime('%Y-%m-%d %H:%M')
    time_display = f"当前时间 (JST): {current_time}"

    # 从字典中提取数据
    shapemap = np.array(ds_dict['variables']['shapemap'][selected_time_index])
    ar_values = shapemap[::-1, :]

    # 假设'length'等变量的数据结构与'shapemap'相同
    length_data = np.array(ds_dict['variables']['length'][selected_time_index])
    width_data = np.array(ds_dict['variables']['width'][selected_time_index])
    life_data = np.array(ds_dict['variables']['klifetime'][selected_time_index])
    distance_data = np.array(ds_dict['variables']['kdist'][selected_time_index])
    id_data = np.array(ds_dict['variables']['kid'][selected_time_index])
    axislon_data = np.array(ds_dict['variables']['axislon'][selected_time_index])
    axislat_data = np.array(ds_dict['variables']['axislat'][selected_time_index])
    kspeed_data = np.array(ds_dict['variables']['kspeed'][selected_time_index])
    kstatus_data = np.array(ds_dict['variables']['kstatus'][selected_time_index])
    clon_data = np.array(ds_dict['variables']['clon'][selected_time_index])
    clat_data = np.array(ds_dict['variables']['clat'][selected_time_index])
    ivt_x_data = np.array(ds_dict['variables']['ivtx'][selected_time_index])
    ivt_y_data = np.array(ds_dict['variables']['ivty'][selected_time_index])
    hlon_data = np.array(ds_dict['variables']['hlon'][selected_time_index])
    hlat_data = np.array(ds_dict['variables']['hlat'][selected_time_index])
    tlon_data = np.array(ds_dict['variables']['tlon'][selected_time_index])
    tlat_data = np.array(ds_dict['variables']['tlat'][selected_time_index])
    lflon_data = np.array(ds_dict['variables']['lflon'][selected_time_index])
    lflat_data = np.array(ds_dict['variables']['lflat'][selected_time_index])
    lfivtdir_data = np.array(ds_dict['variables']['lfivtdir'][selected_time_index])
    lfivtx_data = np.array(ds_dict['variables']['lfivtx'][selected_time_index])
    lfivty_data = np.array(ds_dict['variables']['lfivty'][selected_time_index])

    lon_grid, lat_grid = np.meshgrid(lons, lats)
    unique_ids = np.unique(ar_values[~np.isnan(ar_values)])
    colors = plotly.colors.qualitative.Plotly

    if len(unique_ids) > 0:
        for idx, uid in enumerate(unique_ids):
            mask = ar_values == uid
            lon_points = lon_grid[mask]
            lat_points = lat_grid[mask]
            if len(lon_points) > 0:
                # 确保索引在数据范围内
                ar_idx = int(uid) - 1
                if ar_idx < len(length_data):
                    ar_length = length_data[ar_idx]
                    ar_width = width_data[ar_idx]
                    ar_life = life_data[ar_idx]
                    ar_distance = distance_data[ar_idx]
                    ar_id = id_data[ar_idx]
                    ar_speed = kspeed_data[ar_idx]
                    ar_status = kstatus_data[ar_idx]

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

            axis_lon_points = np.array(axislon_data[int(uid) - 1])
            axis_lat_points = np.array(axislat_data[int(uid) - 1])

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

    ar_indices = np.where(~np.isnan(clon_data))[0]
    lon_points_centroid = clon_data[ar_indices]
    lat_points_centroid = clat_data[ar_indices]
    ivt_x_points = ivt_x_data[ar_indices]
    ivt_y_points = ivt_y_data[ar_indices]

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

    head_lon_points = hlon_data[~np.isnan(hlon_data)]
    head_lat_points = hlat_data[~np.isnan(hlat_data)]

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

    tail_lon_points = tlon_data[~np.isnan(tlon_data)]
    tail_lat_points = tlat_data[~np.isnan(tlat_data)]

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

    lon_points_landfall = lflon_data[~np.isnan(lflon_data)]
    lat_points_landfall = lflat_data[~np.isnan(lflat_data)]
    ivtdir_points = lfivtdir_data[~np.isnan(lflon_data)]
    ivtx_points = lfivtx_data[~np.isnan(lflon_data)]
    ivty_points = lfivty_data[~np.isnan(lflon_data)]

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
    total_points = len(lons) * len(lats)
    time_display += f" | 覆蓋格點: {covered_points}/{total_points} ({covered_points / total_points * 100:.2f}%)"

    return fig, time_display
