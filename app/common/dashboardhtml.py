from app.common.maphtml import render_map_html
from app.common.statueshtml import render_status_html

def render_dashboard_html(state):

    map_html = render_map_html(state.get_map())

    status_html = render_status_html(state.get_status())

    html = f"""
    <html>

    <head>

        <title>Leitstelle Dashboard</title>

        <style>

            body {{
                margin: 0;
                font-family: Arial;
            }}

            .container {{
                display: flex;
                height: 100vh;
            }}

            .left {{
                flex: 1;
                padding: 20px;
                overflow: auto;
                border-right: 2px solid black;
            }}

            .right {{
                flex: 2;
                padding: 20px;
                overflow: auto;
                background-color: #f5f5f5;
            }}

        </style>

    </head>

    <body>

        <div class="container">

            <div class="left">
                {map_html}
            </div>

            <div class="right">
                {status_html}
            </div>

        </div>

    </body>

    </html>
    """

    return html