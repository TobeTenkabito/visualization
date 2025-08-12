# register_callbacks.py
from dash.dependencies import Input, Output, State
import dash.exceptions
import plotly.graph_objects as go
from data_loader import load_dataset
from plot_functions import create_combined_ar_figure
import base64
import json
import pandas as pd


def register_callbacks(app):
    # 添加一个新回调函数，专门用于在选择文件后立即显示文件名
    @app.callback(
        Output('output-filename', 'children', allow_duplicate=True),
        Input('upload-data', 'filename'),
        prevent_initial_call=True
    )
    def display_filename(filename):
        if filename is not None:
            return f"已选择文件: {filename}，正在处理中..."
        return ""

    @app.callback(
        [Output('variable-selector', 'options'),
         Output('variable-selector', 'value'),
         Output('time-slider', 'max'),
         Output('time-slider', 'marks'),
         Output('time-slider', 'value', allow_duplicate=True),
         Output('data-store', 'data'),
         Output('map-graph', 'figure'),
         Output('time-display', 'children')],
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
        prevent_initial_call=True
    )
    def update_output(contents, filename):
        # 增加更详细的调试信息
        if contents is None:
            print(f"警告：回调函数被触发，但文件内容为空。可能文件读取失败。")
            raise dash.exceptions.PreventUpdate

        print(f"用户已上传文件：{filename}，文件内容已成功接收。开始处理...")

        try:
            ds_dict, time_coords, lons, lats, options_new = load_dataset(contents, filename)

            if not ds_dict:
                initial_figure = go.Figure()
                initial_figure.update_layout(title="文件加载失败")
                return [], None, 0, None, 0, None, initial_figure, "文件加载失败"

            max_time = len(time_coords) - 1
            initial_variable = options_new[0]['value'] if options_new else None

            store_data = {
                'ds': ds_dict,
                'time_coords': time_coords,
                'lons': lons,
                'lats': lats,
            }

            initial_figure, initial_time_display = create_combined_ar_figure(0, go.Figure(), ds_dict, time_coords, lons,
                                                                             lats)

            return options_new, initial_variable, max_time, None, 0, store_data, initial_figure, initial_time_display

        except Exception as e:
            print(f"文件处理错误: {e}")
            initial_figure = go.Figure()
            initial_figure.update_layout(title=f"文件处理失败: {e}")
            return [], None, 0, None, 0, None, initial_figure, "文件处理失败"

    @app.callback(
        [Output('interval-component', 'disabled'),
         Output('time-slider', 'value', allow_duplicate=True)],
        [Input('play-button', 'n_clicks'),
         Input('pause-button', 'n_clicks'),
         Input('next-button', 'n_clicks'),
         Input('prev-button', 'n_clicks')],
        [State('interval-component', 'disabled'),
         State('time-slider', 'value'),
         State('data-store', 'data')],
        prevent_initial_call=True
    )
    def control_playback(play_n, pause_n, next_n, prev_n, is_disabled, current_index, stored_data):
        if stored_data is None:
            raise dash.exceptions.PreventUpdate

        time_coords = stored_data['time_coords']

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
        State('data-store', 'data'),
        prevent_initial_call=True
    )
    def update_slider_on_interval(n_intervals, current_index, stored_data):
        if stored_data is None:
            raise dash.exceptions.PreventUpdate

        time_coords = stored_data['time_coords']
        max_index = len(time_coords) - 1
        new_index = (current_index + 1) if current_index < max_index else 0
        return new_index

    @app.callback(
        [Output('map-graph', 'figure', allow_duplicate=True),
         Output('time-display', 'children', allow_duplicate=True)],
        [Input('time-slider', 'value'),
         Input('variable-selector', 'value')],
        [State('map-graph', 'figure'),
         State('data-store', 'data')],
        prevent_initial_call=True
    )
    def update_graph(selected_time_index, selected_variable, current_figure, stored_data):
        fig = go.Figure(current_figure)

        if stored_data is None or selected_variable is None:
            raise dash.exceptions.PreventUpdate

        ds_dict = stored_data['ds']
        time_coords = stored_data['time_coords']
        lons = stored_data['lons']
        lats = stored_data['lats']

        try:
            if selected_variable == 'Combined':
                fig, time_display = create_combined_ar_figure(selected_time_index, current_figure, ds_dict, time_coords,
                                                              lons, lats)
            else:
                fig = go.Figure(current_figure)
                fig.update_layout(title=f"动态变量 {selected_variable} 的可视化")
                time_display = f"正在显示变量: {selected_variable}"

            return [fig, time_display]

        except Exception as e:
            print(f"错误详情: {str(e)}")
            fig.update_layout(
                title="发生错误",
                annotations=[
                    {'text': f"可视化数据时出错：{str(e)}", 'x': 0.5, 'y': 0.5, 'xref': 'paper', 'yref': 'paper',
                     'showarrow': False, 'font': {'size': 16}}]
            )
            time_display = "发生错误"
            return [fig, time_display]
