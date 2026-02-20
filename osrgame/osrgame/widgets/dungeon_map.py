"""ASCII dungeon map widget that renders explored locations."""

from collections import deque

from textual.widgets import Static

from osrlib.dungeon import Direction, Dungeon


# Direction offsets: (col_delta, row_delta)
_DIR_OFFSETS = {
    Direction.NORTH: (0, -1),
    Direction.SOUTH: (0, 1),
    Direction.EAST: (1, 0),
    Direction.WEST: (-1, 0),
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
}


class DungeonMapWidget(Static):
    """Renders an ASCII dungeon map from explored locations."""

    DEFAULT_CSS = """
    DungeonMapWidget {
        height: 100%;
        padding: 1;
    }
    """

    def refresh_map(self, dungeon: Dungeon) -> None:
        """Rebuild and display the map from current dungeon state."""
        positions = self._build_grid(dungeon)
        ascii_map = self._render_grid(positions, dungeon)
        self.update(ascii_map)

    def _build_grid(self, dungeon: Dungeon) -> dict[int, tuple[int, int]]:
        """BFS from start location to assign (col, row) grid coordinates.

        Returns:
            Mapping of location_id -> (col, row).
        """
        start = dungeon.start_location
        if start is None:
            return {}

        positions: dict[int, tuple[int, int]] = {start.id: (0, 0)}
        queue: deque[int] = deque([start.id])

        while queue:
            loc_id = queue.popleft()
            loc = dungeon.get_location_by_id(loc_id)
            if loc is None:
                continue
            col, row = positions[loc_id]

            for exit_obj in loc.exits:
                dest_id = exit_obj.destination
                if dest_id in positions:
                    continue
                dc, dr = _DIR_OFFSETS[exit_obj.direction]
                target = (col + dc, row + dr)

                # Avoid placing two different locations at the same cell
                occupied = set(positions.values())
                if target in occupied:
                    for alt_dc, alt_dr in [
                        (dc + 1, dr),
                        (dc - 1, dr),
                        (dc, dr + 1),
                        (dc, dr - 1),
                    ]:
                        alt = (col + alt_dc, row + alt_dr)
                        if alt not in occupied:
                            target = alt
                            break

                positions[dest_id] = target
                queue.append(dest_id)

        return positions

    def _render_grid(
        self, positions: dict[int, tuple[int, int]], dungeon: Dungeon
    ) -> str:
        """Render the grid positions into an ASCII map string."""
        if not positions:
            return "No map data"

        current_loc = dungeon.current_party_location
        current_id = current_loc.id if current_loc else -1

        # Determine grid bounds
        cols = [c for c, _ in positions.values()]
        rows = [r for _, r in positions.values()]
        min_col, max_col = min(cols), max(cols)
        min_row, max_row = min(rows), max(rows)

        # Build reverse lookup: (col, row) -> list of location_ids
        grid: dict[tuple[int, int], list[int]] = {}
        for loc_id, (c, r) in positions.items():
            grid.setdefault((c, r), []).append(loc_id)

        # Collect connection info for drawing
        connections: set[tuple[int, int, str]] = set()  # (col, row, direction_char)
        for loc_id, (c, r) in positions.items():
            loc = dungeon.get_location_by_id(loc_id)
            if loc is None:
                continue
            for exit_obj in loc.exits:
                dest_id = exit_obj.destination
                if dest_id not in positions:
                    continue
                if exit_obj.direction == Direction.EAST:
                    connections.add((c, r, "E"))
                elif exit_obj.direction == Direction.SOUTH:
                    connections.add((c, r, "S"))
                elif exit_obj.direction == Direction.UP:
                    connections.add((c, r, "U"))
                elif exit_obj.direction == Direction.DOWN:
                    connections.add((c, r, "D"))

        lines: list[str] = []
        for row in range(min_row, max_row + 1):
            room_line = ""
            conn_line = ""
            for col in range(min_col, max_col + 1):
                loc_ids = grid.get((col, row), [])
                if loc_ids:
                    # Render the primary location at this cell
                    primary_id = loc_ids[0]
                    loc = dungeon.get_location_by_id(primary_id)
                    if primary_id == current_id:
                        cell = "[@]"
                    elif loc and loc.is_visited:
                        cell = f"[{primary_id}]"
                    else:
                        cell = "[?]"

                    # Add UP/DOWN labels if applicable
                    up_down = ""
                    if (col, row, "U") in connections:
                        up_down += "U"
                    if (col, row, "D") in connections:
                        up_down += "D"
                    if up_down:
                        cell = cell + up_down
                    else:
                        cell = cell + " "
                else:
                    cell = "    "

                # Horizontal connection to the east
                if (col, row, "E") in connections:
                    cell += "---"
                else:
                    cell += "   "

                room_line += cell

                # Vertical connection to the south
                if (col, row, "S") in connections:
                    conn_line += " |      "
                else:
                    conn_line += "        "

            lines.append(room_line.rstrip())
            if row < max_row:
                lines.append(conn_line.rstrip())

        return "\n".join(lines)
