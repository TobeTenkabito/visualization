# layout.py
from dash import dcc, html
import plotly.graph_objects as go

# 由于数据在启动时未加载，这里使用空列表和初始值
time_coords = []
visualization_options = []

initial_figure = go.Figure()
initial_figure.update_geos(
    visible=True,
    resolution=50,
    showcoastlines=True,
    showland=True,
    showocean=True,
    landcolor="#f5f5dc",
    oceancolor="#c8e2f8",
    countrycolor="#808080",
    coastlinecolor="#000",
    projection_type="natural earth",
    lonaxis_range=[0, 360],
    lataxis_range=[-90, 90],
)
initial_figure.update_layout(
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    title="请选择一个变量并拖动滑块",
    geo=dict(
        scope='world',
        showland=True,
        landcolor="#f5f5dc",
        showocean=True,
        oceancolor="#c8e2f8",
        showcoastlines=True,
        coastlinecolor="#000",
    ),
)

app_layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H1("全球netCDF数据可视化", style={'textAlign': 'center', 'color': '#003366'}),
    html.Hr(),

    # 文件上传组件
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            '拖拽或 ',
            html.A('选择文件')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='output-filename', style={'textAlign': 'center', 'marginBottom': '20px'}),

    # 隐藏的dcc.Store组件，用于在回调函数之间存储数据
    dcc.Store(id='data-store', data=None),

    html.Div([
        html.Label('选择可视化变量:', style={'marginRight': '10px'}),
        dcc.Dropdown(
            id='variable-selector',
            options=visualization_options,
            value=None,  # 初始值为None，等待数据加载
            clearable=False,
            style={'width': '250px'}
        ),
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),

    # 将dcc.Loading包裹在dcc.Graph周围，使其在图表更新时显示动画
    dcc.Loading(
        id="loading-map",
        type="default",
        children=dcc.Graph(id='map-graph', style={'height': '80vh', 'border': '1px solid #ddd'}, figure=initial_figure)
    ),

    html.Div([
        html.Button('播放', id='play-button', n_clicks=0, style={'marginRight': '10px'}),
        html.Button('暂停', id='pause-button', n_clicks=0, style={'marginRight': '20px'}),
        html.Button('上一帧', id='prev-button', n_clicks=0, style={'marginRight': '10px'}),
        html.Button('下一帧', id='next-button', n_clicks=0),

        dcc.Interval(
            id='interval-component',
            interval=2000,
            n_intervals=0,
            disabled=True
        ),
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginTop': '10px'}),

    html.Div([
        html.Label('选择时间步:', style={'marginBottom': '10px'}),
        dcc.Slider(
            id='time-slider',
            min=0,
            # 初始状态下max和value为0，因为没有数据
            max=0,
            value=0,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": True}
        ),
        html.Div(id='time-display', style={'marginTop': '10px'}),
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'marginTop': '20px'})
])
