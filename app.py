import dash
from layout import app_layout
from callbacks import register_callbacks

app = dash.Dash(__name__)
app.layout = app_layout
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
