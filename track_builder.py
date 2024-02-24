from racesim.src.track import Track
import racesim.src.track_config
import pygame
import os


# Build Track
track = Track(0, 0, 0)
track.set_parameters(racesim.src.track_config.trackConfig())
track.build_track()