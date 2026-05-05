from app.common.map import IslandMap
from app.common.map import MapCell
from app.common.map import InfrastructureType
from app.common.map import TileType

def generate_default_map() -> IslandMap:

    cells : list[list[MapCell]] = []

    width : int = 20
    height : int = 20

    for y in range(height):   # first start with the rows (zeilen) , outside list 
        row : list[MapCell] = []

        for x in range(width): # add cells (spalten) , inside list
            
            if x == 0 or y == 0 or x == width - 1 or y == height - 1:   # water on the border , land in the middle
                tile_type = TileType.WATER
            else:
                tile_type = TileType.LAND

            
            infrastructure = None  # only on land , by default none 

            if (x, y) == (1, 1):   # harbor at top left corner , near water 
                infrastructure = InfrastructureType.HARBOR

            elif (x, y) == (10, 10): # depot in the center
                infrastructure = InfrastructureType.DEPOT

            elif (x, y) == (15, 15):  # chargin station , bottom right corner
                infrastructure = InfrastructureType.CHARGING_STATION

            elif (x, y) == (5, 14):   # landing field 
                infrastructure = InfrastructureType.LANDING_FIELD

            elif (x, y) == (0, 10):  # on water edge , but also can be put on two cells if you have water in between , we just have land in the middle
                infrastructure = InfrastructureType.BRIDGE

            # more infrastructure could be added 

            cell = MapCell(    # create a cell with the respective attributes 
                x=x,
                y=y,
                tile_type=tile_type,
                infrastructure=infrastructure
            )

            row.append(cell)   # add the cell in the row 

        cells.append(row)   # add the row in the grid 

    return IslandMap(     # return the map with respective attributes 
        width=width,
        height=height,
        cells=cells
    )




