"""
jump_pad.py

Reusable physics module providing JumpPad and Player classes, trajectory simulation,
and basic restitution (bounce) on landing. Designed to be imported by a game script
or used in unit tests.
"""
import math
from typing import List, Tuple

GRAVITY_M_S2 = 9.81


class JumpPad:
    def __init__(self, spring_constant: float, max_compression: float = None, efficiency: float = 1.0):
        """
        spring_constant: k (N/m)
        max_compression: meters (optional)
        efficiency: fraction of spring energy converted to player kinetic energy (0..1)
        """
        if spring_constant <= 0:
            raise ValueError("spring_constant must be > 0")
        if efficiency <= 0 or efficiency > 1.0:
            raise ValueError("efficiency must be in (0, 1]")
        self.k = float(spring_constant)
        self.max_compression = float(max_compression) if max_compression is not None else None
        self.efficiency = float(efficiency)
        self.compression = 0.0

    def get_launch_velocity(self, compression_m: float, mass_kg: float) -> float:
        """
        Energy-based formula:
            1/2 m v^2 = efficiency * 1/2 k x^2
        so v = x * sqrt(k * efficiency / m)
        Returns upward velocity in m/s.
        """
        if mass_kg <= 0:
            raise ValueError("mass must be > 0")
        x = float(compression_m)
        if self.max_compression is not None:
            x = min(x, self.max_compression)
        v = x * math.sqrt(self.k * self.efficiency / mass_kg)
        return v

    def apply_to_player(self, player: "Player", compression_m: float) -> float:
        """Compute launch velocity and set player's vertical velocity (m/s)."""
        v = self.get_launch_velocity(compression_m, player.mass)
        player.velocity_y = v
        return v


class Player:
    def __init__(self, mass_kg: float, position_y: float = 0.0, restitution: float = 0.0):
        """
        mass_kg: player's mass in kg
        position_y: vertical position in meters (0 = ground)
        restitution: coefficient of restitution on landing (0..1). 0 = no bounce, 1 = perfect bounce.
        """
        if mass_kg <= 0:
            raise ValueError("mass must be > 0")
        if restitution < 0 or restitution > 1:
            raise ValueError("restitution must be in [0,1]")
        self.mass = float(mass_kg)
        self.position_y = float(position_y)
        self.velocity_y = 0.0
        self.restitution = float(restitution)

    def update(self, dt: float, gravity: float = GRAVITY_M_S2):
        """Euler integration step (vertical only) in SI units (meters, seconds)."""
        # integrate velocity and position
        self.velocity_y -= gravity * dt
        self.position_y += self.velocity_y * dt

        # ground collision handling with restitution
        if self.position_y <= 0.0:
            # if moving downwards, apply restitution bounce
            if self.velocity_y < 0:
                bounced_v = -self.velocity_y * self.restitution
                # if bounce is very small, stop completely
                if bounced_v < 1e-3:
                    self.velocity_y = 0.0
                    self.position_y = 0.0
                else:
                    self.velocity_y = bounced_v
                    self.position_y = 0.0
            else:
                # landed gently or already stationary
                self.velocity_y = 0.0
                self.position_y = 0.0


def simulate_trajectory(player: Player, duration: float = 5.0, dt: float = 0.01) -> List[Tuple[float, float, float]]:
    """
    Simulate vertical motion and return list of (t, position_y, velocity_y).
    Stops early if player lands and stops moving.
    """
    t = 0.0
    history: List[Tuple[float, float, float]] = [(t, player.position_y, player.velocity_y)]
    steps = int(max(1, duration / dt))
    for i in range(steps):
        player.update(dt)
        t += dt
        history.append((t, player.position_y, player.velocity_y))
        if player.position_y == 0.0 and player.velocity_y == 0.0 and t > 0:
            break
    return history
