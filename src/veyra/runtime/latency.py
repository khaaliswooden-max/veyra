"""
Latency Simulation

Simulates interplanetary communication delays for testing and development.
"""

import asyncio
import math
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Planet(Enum):
    """Supported planetary bodies."""

    EARTH = "earth"
    MARS = "mars"
    MOON = "moon"
    JUPITER = "jupiter"


@dataclass
class OrbitalPosition:
    """Simplified orbital position."""

    planet: Planet
    timestamp: datetime
    # Simplified: use distance from sun in AU
    distance_au: float


# Average distances in AU (1 AU = Earth-Sun distance)
ORBITAL_DISTANCES = {
    Planet.EARTH: 1.0,
    Planet.MOON: 1.0,  # Same as Earth for simplicity
    Planet.MARS: 1.524,
    Planet.JUPITER: 5.203,
}

# Speed of light in AU per second
SPEED_OF_LIGHT_AU_PER_SEC = 0.002004  # ~299,792 km/s = 0.002004 AU/s


def calculate_light_delay(distance_au: float) -> float:
    """
    Calculate one-way light delay in seconds.

    Args:
        distance_au: Distance in astronomical units

    Returns:
        Delay in seconds
    """
    return distance_au / SPEED_OF_LIGHT_AU_PER_SEC


def calculate_mars_delay(
    earth_position: float = 1.0,
    mars_position: float = 1.524,
    conjunction: bool = False,
) -> float:
    """
    Calculate Earth-Mars communication delay.

    Simplified model assuming circular orbits.

    Args:
        earth_position: Earth orbital position (AU from sun)
        mars_position: Mars orbital position (AU from sun)
        conjunction: If True, planets on opposite sides of sun

    Returns:
        One-way delay in seconds
    """
    if conjunction:
        # Maximum distance: both on opposite sides
        distance = earth_position + mars_position
    else:
        # Simplified: use average distance
        # Real distance varies from 0.524 AU to 2.524 AU
        distance = abs(mars_position - earth_position) + 0.5  # Add some variation

    return calculate_light_delay(distance)


class LatencySimulator:
    """
    Simulates interplanetary communication latency.

    Provides realistic delay simulation for testing systems
    designed to operate across planetary distances.
    """

    # Mars delay ranges
    MARS_MIN_DELAY = 182.0  # ~3 minutes (closest approach)
    MARS_MAX_DELAY = 1342.0  # ~22 minutes (conjunction)
    MARS_AVG_DELAY = 750.0  # ~12.5 minutes (average)

    # Moon delay
    MOON_DELAY = 1.3  # ~1.3 seconds

    def __init__(
        self,
        target: Planet = Planet.MARS,
        use_realistic_variance: bool = True,
        time_acceleration: float = 1.0,
    ):
        """
        Initialize latency simulator.

        Args:
            target: Target planet for communication
            use_realistic_variance: Add realistic jitter
            time_acceleration: Speed up time for testing (1.0 = real time)
        """
        self.target = target
        self.use_realistic_variance = use_realistic_variance
        self.time_acceleration = time_acceleration

        # Track simulated orbital position
        self._orbital_phase = random.random() * 2 * math.pi

    def get_current_delay(self) -> float:
        """
        Get current one-way communication delay in seconds.

        Returns:
            Delay in seconds
        """
        if self.target == Planet.MOON:
            base_delay = self.MOON_DELAY
        elif self.target == Planet.MARS:
            # Simulate orbital variation
            # Mars distance varies sinusoidally over ~780 days
            orbital_factor = (1 + math.sin(self._orbital_phase)) / 2
            base_delay = self.MARS_MIN_DELAY + orbital_factor * (
                self.MARS_MAX_DELAY - self.MARS_MIN_DELAY
            )
        else:
            base_delay = self.MARS_AVG_DELAY

        # Add realistic jitter (±5%)
        if self.use_realistic_variance:
            jitter = random.uniform(-0.05, 0.05)
            base_delay *= 1 + jitter

        return base_delay / self.time_acceleration

    async def simulate_delay(self, round_trip: bool = True) -> float:
        """
        Simulate communication delay.

        Args:
            round_trip: If True, simulate round-trip delay

        Returns:
            Actual delay applied in seconds
        """
        delay = self.get_current_delay()
        if round_trip:
            delay *= 2

        await asyncio.sleep(delay)
        return delay

    def advance_orbital_phase(self, days: float) -> None:
        """
        Advance simulated orbital position.

        Args:
            days: Number of days to advance
        """
        # Mars orbital period ~687 days
        # Synodic period (Earth-Mars alignment) ~780 days
        phase_increment = (2 * math.pi * days) / 780
        self._orbital_phase = (self._orbital_phase + phase_increment) % (2 * math.pi)

    def get_delay_range(self) -> tuple[float, float]:
        """Get min/max delay range for current target."""
        if self.target == Planet.MOON:
            return (self.MOON_DELAY, self.MOON_DELAY * 1.1)
        elif self.target == Planet.MARS:
            return (self.MARS_MIN_DELAY, self.MARS_MAX_DELAY)
        else:
            return (self.MARS_AVG_DELAY, self.MARS_AVG_DELAY)
