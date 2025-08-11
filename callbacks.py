# callbacks.py

from dash.dependencies import Input, Output, State
import dash.exceptions
import plotly.graph_objects as go
import plotly.colors
import pandas as pd
import numpy as np
from data_loader import ds, time_coords, lons, lats


def register_callbacks(app):
    """
    注册所有 Dash 回调函数。
    """

    @app.callback(
        [Output('interval-component', 'disabled'),
         Output('time-slider', 'value')],
        [Input('play-button', 'n_clicks'),
         Input('pause-button', 'n_clicks'),
         Input('next-button', 'n_clicks'),
         Input('prev-button', 'n_clicks')],
        [State('interval-component', 'disabled'),
         State('time-slider', 'value')]
    )
    def control_playback(play_n, pause_n, next_n, prev_n, is_disabled, current_index):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        max_index = len(time_coords) - 1

        if button_id == 'play-button':
            return False, current_index
        elif button_id == 'pause-button':
            return True, current_index
        elif button_id == 'next-button':
            new_index = (current_index + 1) if current_index < max_index else max_index
            return True, new_index
        elif button_id == 'prev-button':
            new_index = (current_index - 1) if current_index > 0 else 0
            return True, new_index

        raise dash.exceptions.PreventUpdate

    @app.callback(
        Output('time-slider', 'value', allow_duplicate=True),
        Input('interval-component', 'n_intervals'),
        State('time-slider', 'value'),
        prevent_initial_call=True
    )
    def update_slider_on_interval(n_intervals, current_index):
        max_index = len(time_coords) - 1
        new_index = (current_index + 1) if current_index < max_index else 0
        return new_index

    @app.callback(
        [Output('map-graph', 'figure'),
         Output('time-display', 'children')],
        [Input('time-slider', 'value'),
         Input('variable-selector', 'value')],
        [State('map-graph', 'figure')]
    )
    def update_graph(selected_time_index, selected_variable, current_figure):
        fig = go.Figure(current_figure)
        fig.data = []

        current_time = pd.Timestamp(ds.time.isel(time=selected_time_index).values).tz_localize('UTC').tz_convert(
            'Asia/Tokyo').strftime('%Y-%m-%d %H:%M')
        time_display = f"当前时间 (JST): {current_time}"

        try:
            if selected_variable == 'Combined':
                # 加載AR屬性數據
                length_data = ds['length'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
                width_data = ds['width'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
                life_data = ds['klifetime'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
                axislon_data = ds['axislon'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()
                axislat_data = ds['axislat'].isel(time=selected_time_index, ens=0, lev=0).squeeze().compute()

                # 1. 繪製大气河流掩碼（背景）和AR軸線
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
                            # 獲取AR的長度和寬度，注意索引從1開始
                            ar_length = length_data.values[int(uid) - 1]
                            ar_width = width_data.values[int(uid) - 1]
                            ar_life = life_data.values[int(uid) - 1]

                            trace = go.Scattergeo(
                                lon=lon_points,
                                lat=lat_points,
                                mode='markers',
                                marker=dict(size=2, color=colors[idx % len(colors)], opacity=0.7),
                                name=f'AR {int(uid)}',
                                customdata=[[ar_length, ar_width, ar_life]] * len(lon_points),
                                hovertemplate='<b>經度: %{lon:.2f}<br>緯度: %{lat:.2f}</b><br>AR '
                                              '長度: %{customdata[0]:.2f} m<br>AR 寬度: %{customdata[1]:.2f} m<extra></extra>'
                                              '生命: %{customdata[2]:.2f} s<extra></extra>',
                                showlegend=True,
                            )
                            fig.add_trace(trace)

                        # 繪製AR軸線
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

                # 2. 繪製質心點和IVT向量
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

                # 3. 繪製頭部點
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

                # 4. 繪製尾部點
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

                # 5. 繪製登陸點
                lflon_data = ds['lflon'].isel(time=selected_time_index).squeeze().compute()
                lflat_data = ds['lflat'].isel(time=selected_time_index).squeeze().compute()
                lon_points_landfall = lflon_data.values[~np.isnan(lflon_data.values)]
                lat_points_landfall = lflat_data.values[~np.isnan(lflat_data.values)]

                if len(lon_points_landfall) > 0:
                    hover_text = [f"經度: {lon:.2f}<br>緯度: {lat:.2f}" for lon, lat in
                                  zip(lon_points_landfall, lat_points_landfall)]
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
            elif selected_variable == 'Other':
                return "待更新"
            return [fig, time_display]

        except Exception as e:
            print(f"错误详情: {str(e)}")
            fig.update_layout(
                title="发生错误",
                annotations=[
                    {'text': f"可视化数据时出错：{str(e)}", 'x': 0.5, 'y': 0.5, 'xref': 'paper', 'yref': 'paper',
                     'showarrow': False, 'font': {'size': 16}}]
            )
            return [fig, time_display]
