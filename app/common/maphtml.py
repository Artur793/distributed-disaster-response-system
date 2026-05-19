from app.common.map import TileType, InfrastructureType


def render_map_html(island_map) -> str:
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .grid { 
                display: grid;
                grid-template-columns: repeat(20, 20px); 
                grid-template-rows: repeat(20, 20px);
            }

            .cell {
                width: 20px;
                height: 20px;
                border: 1px solid #333;
                box-sizing: border-box;
            }

            .land {
                background-color: #7CFC00;
            }

            .water {
                background-color: #1E90FF;
            }

            .harbor { background-color: orange; }
            .depot { background-color: gray; }
            .charging_station { background-color: yellow; }
            .landing_field { background-color: pink; }
            .bridge { background-color: brown; }
        </style>
    </head>
    <body>
        <h2>Island Map</h2>
        <div class="grid">
    """

    for row in island_map.cells:
        for cell in row:

            tile_class = "land" if cell.tile_type == TileType.LAND else "water"  # assighning html class for land and water for the  cells 

            infra_class = ""

            if cell.infrastructure:
                infra_class = cell.infrastructure.value  # assighning the cell to html class if there is any infrastructure 

            html += f'<div class="cell {tile_class} {infra_class}"></div>'

    html += """
        </div>

        <h3>Legend</h3>

        <div style="display: flex; gap: 15px; margin-top: 15px; flex-wrap: wrap;">

            <div style="display: flex; align-items: center; gap: 5px;">
                <div class="cell land"></div>
                <span>Land</span>
            </div>

            <div style="display: flex; align-items: center; gap: 5px;">
                <div class="cell water"></div>
                <span>Water</span>
            </div>

            <div style="display: flex; align-items: center; gap: 5px;">
                <div class="cell harbor"></div>
                <span>Harbor</span>
            </div>

            <div style="display: flex; align-items: center; gap: 5px;">
                <div class="cell depot"></div>
                <span>Depot</span>
            </div>

            <div style="display: flex; align-items: center; gap: 5px;">
                <div class="cell charging_station"></div>
                <span>Charging Station</span>
            </div>

            <div style="display: flex; align-items: center; gap: 5px;">
                <div class="cell landing_field"></div>
                <span>Landing Field</span>
            </div>

            <div style="display: flex; align-items: center; gap: 5px;">
                <div class="cell bridge"></div>
                <span>Bridge</span>
            </div>

        </div>

    </body>
    </html>
"""

    return html