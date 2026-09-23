from __future__ import annotations
from enum import IntEnum
import numpy as np
import pygame

class Material(IntEnum):
    """Every cell in the grid holds one of these values.

    IntEnum means each name is also a normal integer, so a grid can be a plain NumPy array of numbers.
    EMPTY must stay 0 so that a fresh grid (which NumPy fills with zeros) starts out as empty space.
    """
    EMPTY = 0
    SAND = 1
    WATER = 2
    # BONUS: add more materials here, e.g.
    ROCK = 3 #(immovable — never update it)
    FIRE = 4 #(lives a few ticks, then becomes EMPTY)
    SMOKE = 5 #(rises instead of falling, then fades)
    SAWDUST = 6 #(like sand, but lighter and slower and burns more easily)

# The colour (R, G, B) drawn for each material.
PALETTE = {
    Material.EMPTY: (0, 0, 0),
    Material.SAND: (194, 178, 128),
    Material.WATER: (52, 120, 235),
    Material.ROCK: (100, 100, 100),
    Material.FIRE: (200, 50, 50),
    Material.SMOKE: (50, 50, 50),
    Material.SAWDUST: (150, 100, 50),
}

# Turned into a NumPy array so that looking up a cell's colour is a single
# fast indexing operation: COLORS[grid] gives the RGB value of every cell.
_COLORS = np.array([PALETTE[m] for m in Material], dtype=np.uint8)

# One shared random generator for the whole program. Everything that needs
# a coin-flip (diagonal direction, which side to move) pulls from this.
_rng = np.random.default_rng()

class SandSim:
    """Holds the grid and does the physics + rendering.

    The grid is ``self._types``, a 2D NumPy array of shape (HEIGHT, WIDTH) where grid[y, x] is the material at row ``y`` (0 = top) and column ``x`` (0 = left).
    """
    def __init__(self, width: int, height: int, cell_size: int = 4, fps: int = 60) -> None:
        self.cell_size = cell_size
        self.fps = 2*fps
        self.brush = Material.SAND
        self.brush_radius = 2
        self.resize_cells(width, height)

    # ------------------------------------------------------------------ #
    # # Grid lifecycle                                                   #
    # ------------------------------------------------------------------ #
    def resize_cells(self, width: int, height: int) -> None:
        """Replace the grid with a fresh empty one of the given size."""
        self.width = int(width)
        self.height = int(height)
        # NumPy fills with zeros = Material.EMPTY. Good.
        self._types = np.zeros((self.height, self.width), dtype=np.uint8)
        self._fire_lifespans = np.zeros((self.height, self.width), dtype=np.int8)
        self._smoke_lifespans = np.zeros((self.height, self.width), dtype=np.int8)

    def clear(self) -> None:
        """Reset every cell to empty space."""
        self._types[:] = 0
        self._fire_lifespans[:] = 0
        self._smoke_lifespans[:] = 0

    # ------------------------------------------------------------------ #
    # # Painting (mouse input)                                           #
    # ------------------------------------------------------------------ #
    def paint_at(self, x: int, y: int) -> None:
        """Place the current brush material in a disc of cells at (x, y).

        ``x``/``y`` are in *grid* coordinates (screen pixels / cell_size).
        """
        r = self.brush_radius
        x0, x1 = max(0, x - r), min(self.width, x + r + 1)
        y0, y1 = max(0, y - r), min(self.height, y + r + 1)
        if x1 <= x0 or y1 <= y0:
            return # mgrid gives two grids of y- and x-coordinates over the block;
        # the `disc` mask keeps only cells within a circle of radius r.
        yy, xx = np.mgrid[y0:y1, x0:x1]
        disc = ((xx - x) ** 2 + (yy - y) ** 2) <= r * r
        xs, ys = xx[disc], yy[disc]
        self._types[ys, xs] = int(self.brush)
        self._fire_lifespans[ys, xs] = _rng.integers(5, 13) if self.brush == Material.FIRE else 0
        self._smoke_lifespans[ys, xs] = _rng.integers(15, 31) if self.brush == Material.SMOKE else 0

    # ------------------------------------------------------------------ #
    # # Physics                                                          #
    # ------------------------------------------------------------------ #
    def update(self) -> None:
        """Advance the simulation by one tick. This is YOUR job.

        Rules to implement:
        * Process rows from the BOTTOM up (y = height-1 .. 0). If you go top down, a grain falls several cells per tick and flickers.
        * Process columns left-to-right but in a different random order each tick, so falling looks symmetrical instead of leaning one way.
        * SAND: 1. if the cell directly below is EMPTY -> move straight down
        2. else pick a random side; if the cell down-left or down-right is EMPTY -> move diagonally there
        3. else stay put (it rests)
        * WATER: the same as sand, PLUS:
        4. if it couldn't fall at all, move into a random EMPTY left/right neighbour — this is what makes water pool flat.
        Hint: if you write straight into the grid you'll re-process cells that already moved. Copy the grid before the loop, read from the copy, and write the result into the live grid (or vice versa).
        """
        if (self.width == 0 or self.height == 0):
            return # nothing to do
        
        # Take a snapshot copy of the current grid state to accurately track static frame data
        grid_copy = self._types.copy()

        for y in range(self.height - 1, -1, -1):
            for x in _rng.permutation(self.width):
                mat = grid_copy[y, x]
                if mat == Material.EMPTY:
                    continue
                
                # Check if the active particle was displaced or modified in this frame
                if self._types[y, x] != mat:
                    continue

                if mat == Material.SAND:
                    # 1. Look straight down
                    if y + 1 < self.height and self._types[y + 1, x] == Material.EMPTY:
                        self._types[y, x] = Material.EMPTY
                        self._types[y + 1, x] = Material.SAND
                    else:
                        # 2. Diagonal drop using a randomized direction choice
                        sides = [-1, 1]
                        _rng.shuffle(sides)
                        for dx in sides:
                            nx = x + dx
                            if 0 <= nx < self.width and y + 1 < self.height and self._types[y + 1, nx] == Material.EMPTY:
                                self._types[y, x] = Material.EMPTY
                                self._types[y + 1, nx] = Material.SAND
                                break

                elif mat == Material.WATER:
                    # 1. Look straight down
                    if y + 1 < self.height and self._types[y + 1, x] == Material.EMPTY:
                        self._types[y, x] = Material.EMPTY
                        self._types[y + 1, x] = Material.WATER
                    else:
                        # 2. Diagonal drop using a randomized direction choice
                        sides = [-1, 1]
                        _rng.shuffle(sides)
                        moved = False
                        for dx in sides:
                            nx = x + dx
                            if 0 <= nx < self.width and y + 1 < self.height and self._types[y + 1, nx] == Material.EMPTY:
                                self._types[y, x] = Material.EMPTY
                                self._types[y + 1, nx] = Material.WATER
                                moved = True
                                break
                        
                        # 4. Fallback: pool outward horizontally if vertical descent routes are blocked
                        if not moved:
                            for dx in sides:
                                nx = x + dx
                                if 0 <= nx < self.width and self._types[y, nx] == Material.EMPTY:
                                    self._types[y, x] = Material.EMPTY
                                    self._types[y, nx] = Material.WATER
                                    break

                elif mat == Material.ROCK:
                    continue

                elif mat == Material.FIRE:
                    # Fire logic: burn nearby sawdust, rise unpredictably, shoot sparks up in a cone, and leave minimal smoke
                    if self._fire_lifespans[y, x] <= 0:
                        self._fire_lifespans[y, x] = _rng.integers(5, 13)

                    # --- 1. BURN INTERACTIONS ---
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    _rng.shuffle(directions)
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            neighbor_mat = self._types[ny, nx]
                            if neighbor_mat == Material.SAWDUST:
                                # 80% chance to ignite adjacent sawdust.
                                if _rng.random() < 0.8:
                                    self._types[ny, nx] = Material.FIRE
                                    self._fire_lifespans[ny, nx] = _rng.integers(5, 13)
                            elif neighbor_mat == Material.WATER:
                                # 70% chance to extinguish fire when touching water.
                                if _rng.random() < 0.7:
                                    self._types[y, x] = Material.SMOKE
                                    self._smoke_lifespans[y, x] = _rng.integers(10, 20)
                                    break

                    remaining = self._fire_lifespans[y, x] - 1

                    # --- 2. NEW: UPWARD CONE SPARK SPAWNING ---
                    # 20% chance per frame to shoot a spark upward and outward.
                    if _rng.random() < 0.2:
                        # Randomize distance away (1 to 3 pixels up)
                        spark_dist_y = _rng.integers(1, 4)
                        # Upward cone: wider horizontal spread the higher up it goes
                        spark_dist_x = _rng.integers(-spark_dist_y, spark_dist_y + 1)
                        
                        spark_x = x + spark_dist_x
                        spark_y = y - spark_dist_y

                        # If the target location is inside bounds and empty, spawn a fresh fire unit
                        if 0 <= spark_x < self.width and 0 <= spark_y < self.height:
                            if self._types[spark_y, spark_x] == Material.EMPTY:
                                self._types[spark_y, spark_x] = Material.FIRE
                                self._fire_lifespans[spark_y, spark_x] = _rng.integers(3, 10) # Shorter life for sparks

                    # --- 3. MOVEMENT & REDUCED SMOKE ---
                    if y > 0 and self._types[y - 1, x] == Material.EMPTY and _rng.random() < 0.55:
                        # The rising-fire branch only leaves smoke 25% of the time, after the earlier empty-space check.
                        self._types[y, x] = Material.SMOKE if _rng.random() < 0.25 else Material.EMPTY
                        
                        if self._types[y, x] == Material.SMOKE:
                            self._smoke_lifespans[y, x] = _rng.integers(5, 15) # Shorter smoke lifespans
                        
                        self._types[y - 1, x] = Material.FIRE
                        self._fire_lifespans[y - 1, x] = max(1, remaining)
                        self._fire_lifespans[y, x] = 0

                    elif remaining <= 0:
                        # When fire dies naturally, it only becomes smoke 1% of the time.
                        # Otherwise, it vanishes cleanly.
                        if _rng.random() < 0.01:
                            self._types[y, x] = Material.SMOKE
                            self._smoke_lifespans[y, x] = _rng.integers(5, 15)
                        else:
                            self._types[y, x] = Material.EMPTY
                        self._fire_lifespans[y, x] = 0
                    else:
                        self._fire_lifespans[y, x] = remaining

                    
                elif mat == Material.SMOKE:
                    # Smoke logic: drift upward or sideways, then fade away

                    if y==0:
                        self._types[y, x] = Material.EMPTY
                        self._smoke_lifespans[y, x] = 0
                        continue

                    if self._smoke_lifespans[y, x] <= 0:
                        self._smoke_lifespans[y, x] = _rng.integers(5, 15)
                    directions = [(0, -1), (-1, -1), (1, -1), (-1, 0), (1, 0)]
                    _rng.shuffle(directions)
                    moved = False
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height and self._types[ny, nx] == Material.EMPTY:
                            self._types[y, x] = Material.EMPTY
                            self._types[ny, nx] = Material.SMOKE
                            self._smoke_lifespans[ny, nx] = self._smoke_lifespans[y, x] - 1
                            moved = True
                            break
                    if not moved:
                        self._smoke_lifespans[y, x] -= 1
                    if not moved and self._smoke_lifespans[y, x] <= 0:
                        self._types[y, x] = Material.EMPTY
                        self._smoke_lifespans[y, x] = 0

                if mat == Material.SAWDUST:
                    # 1. Look straight down
                    if y + 1 < self.height and self._types[y + 1, x] == Material.EMPTY:
                        self._types[y, x] = Material.EMPTY
                        self._types[y + 1, x] = Material.SAWDUST
                    else:
                        # 2. Diagonal drop using a randomized direction choice
                        sides = [-1, 1]
                        _rng.shuffle(sides)
                        for dx in sides:
                            nx = x + dx
                            if 0 <= nx < self.width and y + 1 < self.height and self._types[y + 1, nx] == Material.EMPTY:
                                self._types[y, x] = Material.EMPTY
                                self._types[y + 1, nx] = Material.SAWDUST
                                break

    # ------------------------------------------------------------------ #
    # # Rendering (boilerplate — nothing to do here)                     #
    # ------------------------------------------------------------------ #
    def surface(self) -> pygame.Surface:
        """Snapshot the grid as a pygame.Surface, scaled up by cell_size.

        _COLORS[grid] turns the cell-material grid into a grid of RGB pixels in one shot.
        pygame expects the axes as (WIDTH, HEIGHT), numpy stores them as (HEIGHT, WIDTH), so transpose swaps them back.
        """
        rgb = _COLORS[self._types]
        surf = pygame.surfarray.make_surface(
            np.ascontiguousarray(np.transpose(rgb, (1, 0, 2)))
        )
        if self.cell_size > 1:
            surf = pygame.transform.scale(
                surf, (self.width * self.cell_size, self.height * self.cell_size)
            )
        return surf

def main() -> None:
    """Setup + event loop. Boilerplate — nothing to do here."""
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("Falling Sand — 1 sand, 2 water, 3 rock, 4 fire, 5 smoke, 6 sawdust, 0 erase, [ ] brush, C clear")
    clock = pygame.time.Clock()
    sim = SandSim(800 // 4, 600 // 4)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_ESCAPE:
                    running = False
                elif k == pygame.K_1:
                    sim.brush = Material.SAND
                elif k == pygame.K_2:
                    sim.brush = Material.WATER
                elif k == pygame.K_3:
                    sim.brush = Material.ROCK
                elif k == pygame.K_4:
                    sim.brush = Material.FIRE
                elif k == pygame.K_5:
                    sim.brush = Material.SMOKE
                elif k == pygame.K_6:
                    sim.brush = Material.SAWDUST
                elif k in (pygame.K_0, pygame.K_e):
                    sim.brush = Material.EMPTY
                elif k == pygame.K_LEFTBRACKET:
                    sim.brush_radius = max(1, sim.brush_radius - 1)
                elif k == pygame.K_RIGHTBRACKET:
                    sim.brush_radius = min(40, sim.brush_radius + 1)
                elif k == pygame.K_c:
                    sim.clear()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                sim.resize_cells(event.size[0] // sim.cell_size, event.size[1] // sim.cell_size)

        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            sim.paint_at(mx // sim.cell_size, my // sim.cell_size)
        sim.update()
        screen.blit(sim.surface(), (0, 0))
        pygame.display.flip()
        clock.tick(sim.fps)
    pygame.quit()
if __name__ == "__main__":
    main()