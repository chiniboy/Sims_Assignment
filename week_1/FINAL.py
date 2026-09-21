import pygame
import numpy as np
import random

# Configuration

#Normalization: 1 metre = 300 pixels. The arena is a circle of radius 1 metre... sadly.
ARENA_R_PIXELS = 300
ARENA_RADIUS_METERS = 1.0
PIXELS_PER_METER = ARENA_R_PIXELS / ARENA_RADIUS_METERS
METERS_PER_PIXEL = 1.0 / PIXELS_PER_METER

WIDTH = 800
HEIGHT = 800

ARENA_CENTER_PIXELS = np.array([WIDTH / 2, HEIGHT / 2], dtype=float)
ARENA_CENTER = ARENA_CENTER_PIXELS * METERS_PER_PIXEL
ARENA_R = ARENA_RADIUS_METERS

# Start with 1 ball, then 2. Many at once is the bonus.
NUM_PARTICLES = 150
PARTICLE_RADIUS_PIXELS = 5
PARTICLE_RADIUS = PARTICLE_RADIUS_PIXELS * METERS_PER_PIXEL

# Metres per second squared.
GRAVITY = 9.8
GRAVITY_VECTOR = np.array([0.0, GRAVITY])

# How much normal speed survives a bounce. 1.0 is perfectly elastic.
E_WALL = 1
RESTITUTION = 1

FPS = 60
SIMULATION_SUBSTEPS = 8

positions = []
velocities = []

# Randomly place the balls inside the bowl, and give them a random velocity.
for i in range(NUM_PARTICLES):
    PARTICLE_SPEED = random.uniform(0.0, 0.5)  # Metres per second
    # A random spot inside the bowl, with the whole ball fitting.
    angle = random.uniform(0, 2 * np.pi)
    distance = random.uniform(0, ARENA_R - PARTICLE_RADIUS)

    positions.append(ARENA_CENTER + distance * np.array([
        np.cos(angle),
        np.sin(angle)
    ]))

    # A random direction, at roughly PARTICLE_SPEED.
    # Swap for np.array([0.0, 0.0]) to drop the ball from rest.
    angle = random.uniform(0, 2 * np.pi)

    velocities.append(PARTICLE_SPEED * np.array([
        np.cos(angle),
        np.sin(angle)
    ]))

# Total energy calculations
def total_mechanical_energy():
    position_array = np.array(positions)
    velocity_array = np.array(velocities)
    kinetic_energy = 0.5 * np.sum(velocity_array ** 2)
    potential_energy = -GRAVITY * np.sum(position_array[:, 1] - ARENA_CENTER[1])
    return kinetic_energy + potential_energy

INITIAL_TOTAL_ENERGY = total_mechanical_energy()

#Keepin initial enegy same throughout
def restore_total_energy():
    position_array = np.array(positions)
    velocity_array = np.array(velocities)
    potential_energy = -GRAVITY * np.sum(position_array[:, 1] - ARENA_CENTER[1])
    kinetic_energy = 0.5 * np.sum(velocity_array ** 2)
    target_kinetic_energy = INITIAL_TOTAL_ENERGY - potential_energy

    if kinetic_energy > 1e-7 and target_kinetic_energy >= 0.0:
        velocities[:] = velocity_array * np.sqrt(target_kinetic_energy / kinetic_energy)

# Pygame setup

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Particle Simulation")

clock = pygame.time.Clock()

running = True

while running:
    for event in pygame.event.get():
        print("total mechanical energy:", total_mechanical_energy())
        if event.type == pygame.QUIT:
            running = False

    dt = clock.tick(FPS) / 1000.0
    substep_dt = dt / SIMULATION_SUBSTEPS

    for _ in range(SIMULATION_SUBSTEPS):
        for i in range(NUM_PARTICLES):
            velocities[i] += GRAVITY_VECTOR * substep_dt
            positions[i] += velocities[i] * substep_dt

            offset = positions[i] - ARENA_CENTER
            distance = np.linalg.norm(offset)
            wall_distance = ARENA_R - PARTICLE_RADIUS
            if distance > wall_distance:
                normal = offset / distance
                positions[i] = ARENA_CENTER + wall_distance * normal
                velocity_toward_wall = np.dot(velocities[i], normal)
                if velocity_toward_wall > 0.0:
                    velocities[i] -= (1.0 + E_WALL) * velocity_toward_wall * normal

        for i in range(NUM_PARTICLES):
            for j in range(i + 1, NUM_PARTICLES):
                delta_pos = positions[j] - positions[i]
                distance = np.linalg.norm(delta_pos)
                minimum_distance = 2.0 * PARTICLE_RADIUS

                if distance < minimum_distance:
                    if distance > 1e-7:
                        normal = delta_pos / distance
                    else:
                        normal = np.array([1.0, 0.0])

                    overlap = minimum_distance - distance
                    positions[i] -= 0.5 * overlap * normal
                    positions[j] += 0.5 * overlap * normal

                    relative_velocity = velocities[j] - velocities[i]
                    velocity_along_normal = np.dot(relative_velocity, normal)
                    if velocity_along_normal < 0.0:
                        impulse = -(1.0 + RESTITUTION) * velocity_along_normal / 2.0
                        velocities[i] -= impulse * normal
                        velocities[j] += impulse * normal

    restore_total_energy()

    # Render

    screen.fill((20, 20, 25))

    pygame.draw.circle(
        screen,
        (180, 180, 180),
        ARENA_CENTER_PIXELS.astype(int),
        ARENA_R_PIXELS,
        width=3
    )

    for position in positions:
        pygame.draw.circle(
            screen,
            (220, 220, 220),
            (position * PIXELS_PER_METER).astype(int),
            PARTICLE_RADIUS_PIXELS
        )

    pygame.display.flip()

pygame.quit()
