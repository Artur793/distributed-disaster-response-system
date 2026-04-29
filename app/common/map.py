from dataclasses import dataclass, asdict
from enum import Enum


class TileType(str, Enum):
    LAND = "land"
    WATER = "water"


class InfrastructureType(str, Enum):
    BRIDGE = "bridge"
    HARBOR = "harbor"
    CHARGING_STATION = "charging_station"
    LANDING_FIELD = "landing_field"
    DEPOT = "depot"


@dataclass
class MapCell:
    x: int
    y: int
    tile_type: TileType
    infrastructure: InfrastructureType | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tile_type"] = self.tile_type.value
        data["infrastructure"] = self.infrastructure.value if self.infrastructure else None
        return data


@dataclass
class IslandMap:
    width: int
    height: int
    cells: list[list[MapCell]]  # Outer list -> y, Inner list -> x (so usage is cells[y][x])

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "cells": [
                [cell.to_dict() for cell in row]
                for row in self.cells
            ]
        }