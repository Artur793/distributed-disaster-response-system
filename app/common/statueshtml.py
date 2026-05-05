from app.common.state import SystemState

def render_status_html(status: dict) -> str:

    html = f"""
    <html>

    <head>

        <title>System Status</title>

        <style>

            body {{
                font-family: Arial;
                margin: 20px;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 30px;
            }}

            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background-color: #f0f0f0;
            }}

            .summary {{
                margin-bottom: 30px;
            }}

        </style>

    </head>

    <body>

        <h1>Leitstelle Status Dashboard</h1>

        <div class="summary">

            <h2>Overview</h2>

            <ul>
                <li>Map Loaded: {status["map_loaded"]}</li>
                <li>Vehicles: {status["vehicle_count"]}</li>
                <li>Sensors: {status["sensor_count"]}</li>
                <li>Incidents: {status["incident_count"]}</li>
            </ul>

        </div>
    """
    html += """
        <h2>Vehicles</h2>

        <table>

            <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Position</th>
                <th>Status</th>
            </tr>
    """

    for vehicle in status["vehicles"]:

        position = vehicle.get("position")

        position_text = "N/A"

        if position:
            position_text = f'({position["x"]}, {position["y"]})'

        html += f"""
            <tr>
                <td>{vehicle["id"]}</td>
                <td>{vehicle["vehicle_type"]}</td>
                <td>{position_text}</td>
                <td>{vehicle["status"]}</td>
            </tr>
        """

    html += "</table>"
    html += """
        <h2>Sensors</h2>

        <table>

            <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Position</th>
                <th>Status</th>
            </tr>
    """

    for sensor in status["sensors"]:

        position = sensor.get("position")

        position_text = "N/A"

        if position:
            position_text = f'({position["x"]}, {position["y"]})'

        html += f"""
            <tr>
                <td>{sensor["id"]}</td>
                <td>{sensor["sensor_type"]}</td>
                <td>{position_text}</td>
                <td>{sensor["status"]}</td>
            </tr>
        """

    html += "</table>"
    html += """
        <h2>Incidents</h2>

        <table>

            <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Source</th>
                <th>Message</th>
                <th>Priority</th>
                <th>Status</th>
            </tr>
    """

    for incident in status["incidents"]:

        html += f"""
            <tr>
                <td>{incident["id"]}</td>
                <td>{incident["incident_type"]}</td>
                <td>{incident["source_id"]}</td>
                <td>{incident["message"]}</td>
                <td>{incident["priority"]}</td>
                <td>{incident["status"]}</td>
            </tr>
        """

    html += """
        </table>

    </body>

    </html>
    """
    return html
