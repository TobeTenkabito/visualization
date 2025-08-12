from dash.dependencies import Input, Output, State
import dash.exceptions
import plotly.graph_objects as go
from data_loader import time_coords
from plot_functions import create_combined_ar_figure, create_era5_figure


def register_callbacks(app):
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
        try:
            if selected_variable == 'Combined':
                fig, time_display = create_combined_ar_figure(selected_time_index, current_figure)
            elif selected_variable == 'Precipitation':
                fig, time_display = create_era5_figure(selected_time_index, current_figure)
            elif selected_variable == 'Other':
                fig = go.Figure(current_figure)
                time_display = "待更新"
            return [fig, time_display]

        except Exception as e:
            print(f"错误详情: {str(e)}")
            fig = go.Figure(current_figure)
            time_display = ""
            return [fig, time_display]
