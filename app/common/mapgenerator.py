from app.common.map import IslandMap
from app.common.map import MapCell
from app.common.map import InfrastructureType
from app.common.map import TileType

def generate_default_map() -> IslandMap:

    cells : list[list[MapCell]] = []

    width : int = 20
    height : int = 20

    water = {
        # y=0
        (0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,0),(15,0),(16,0),(17,0),(18,0),(19,0),
        # y=1
        (0,1),(1,1),(2,1),(4,1),(16,1),(18,1),(19,1),
        # y=2
        (0,2),(1,2),(2,2),(15,2),(16,2),(18,2),(19,2),
        # y=3
        (0,3),(1,3),(2,3),(3,3),(16,3),(18,3),(19,3),
        # y=4
        (0,4),(18,4),(19,4),
        # y=5
        (0,5),(18,5),(19,5),
        # y=6
        (0,6),(18,6),(19,6),
        # y=7
        (0,7),(17,7),(18,7),(19,7),
        # y=8
        (0,8),(1,8),(16,8),(17,8),(18,8),
        # y=9
        (0,9),(1,9),(2,9),(16,9),(17,9),(19,9),
        # y=10
        (0,10),(1,10),(13,10),(15,10),(16,10),(19,10),
        # y=11
        (0,11),(1,11),(2,11),(12,11),(13,11),(14,11),(15,11),(18,11),(19,11),
        # y=12
        (0,12),(1,12),(11,12),(12,12),(13,12),(14,12),
        # y=13
        (0,13),(9,13),(10,13),(11,13),(13,13),(14,13),(15,13),
        # y=14
        (0,14),(1,14),(7,14),(8,14),(9,14),(10,14),(14,14),(18,14),(19,14),
        # y=15
        (0,15),(1,15),(8,15),(19,15),
        # y=16
        (0,16),(6,16),(7,16),(8,16),
        # y=17
        (0,17),(1,17),(6,17),(7,17),(19,17),
        # y=18
        (0,18),(1,18),(3,18),(4,18),(5,18),(6,18),(9,18),(10,18),(16,18),(17,18),
        # y=19
        (0,19),(1,19),(2,19),(3,19),(4,19),(5,19),(6,19),(7,19),(8,19),(9,19),(10,19),(11,19),(12,19),(13,19),(14,19),(15,19),(16,19),(17,19),(18,19),
    }

    for y in range(height):   # first start with the rows (zeilen) , outside list 
        row : list[MapCell] = []

        for x in range(width): # add cells (spalten) , inside list
            
            #if x == 0 or y == 0 or x == width - 1 or y == height - 1 :  # water on the border , land in the middle
            if (x,y) in water :
                tile_type = TileType.WATER
            else:
                tile_type = TileType.LAND
 
            #if (x,y) == (1 , 2) or (2 , 2) or (2 , 4) or (1 ,4):
               # tile_type = TileType.WATER
            
            infrastructure = None  # only on land , by default none 

            if (x, y) in [(3 , 3) , (10 , 18)]:   # harbor at top left corner , near water
                infrastructure = InfrastructureType.HARBOR

            elif (x, y) == (10, 10): # depot in the center
                infrastructure = InfrastructureType.DEPOT

            elif (x, y) in [(15, 15) , (9 , 6)]:  # chargin station , bottom right corner
                infrastructure = InfrastructureType.CHARGING_STATION

            elif (x, y) == (5, 14):   # landing field 
                infrastructure = InfrastructureType.LANDING_FIELD

            elif (x, y) in [(17, 7), (18, 9), (18, 8), (17, 8), (10, 12), (11, 13), (11, 12), (11, 14), (5 , 17), (6, 17), (6, 18),  (7 , 18)]:  # on water edge , but also can be put on two cells if you have water in between , we just have land in the middle
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




