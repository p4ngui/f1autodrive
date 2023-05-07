import os

import neat
import pygame
import pygame.freetype
from pygame.math import Vector2

import racesim.src.track_config
from racesim.src.game import Game

# ============ Game constants ======================

# TODO: create driver class


def neat_init(checkpoint_iterval: int = 5,
              restore: bool = False,
              checkpoint_file: str = "",
              config_path=""):
    if restore:
        # p = neat.Checkpointer.restore_checkpoint(
        # 'best_neat-291-7 sensor_cnnff')
        if not checkpoint_file:
            print("Restore is set to True, but no checkpoint file was set,\
                  consider to set a checkpoint file")
            pygame.quit()
            exit(1)
        else:
            p = neat.Checkpointer.restore_checkpoint(checkpoint_file)
            config = p.config
            game.generation = p.generation
    else:
        config = neat.config.Config(neat.DefaultGenome,
                                    neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet,
                                    neat.DefaultStagnation,
                                    config_path)
        p = neat.Population(config)
        p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    # save checkpoint each n genome iteration
    p.add_reporter(neat.Checkpointer(checkpoint_iterval))
    p.add_reporter(stats)
    return p, stats


def genome_evaluation(genomes, config):
    pass

# TODO eval genome => car net
#       car fitness todo
# TODO Build track inly on restart or star game ot iteration


def generation_iteration(genomes, config):
    # Setup Race
    pos = Vector2(0, 0)
    # TODO : create grid (qualif)
    # init Track
    # Build Track
    # TODO : track selection
    game.soft_reset()
    # setup cars
    # start car engins
    # Start Race
    game.startRace(genomes, config)
    game.bestCarPos = Vector2(-640, -360)
    game.best_lap_Distance = 0
    are_we_alone = False
    game.updateScore(0.0)
    # TODO method to change game frequency
    t = 0
    game.set_clock(60)
    # Loop
    # TODO add terminator when race laps are reached
    while not are_we_alone:
        t += 1
        # ==x====== Event queue ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.exit = True
                are_we_alone = True
            # else:
            #     print(f"Events : {event}")
        # ======== User input ===========
        game.main_keystrokes_manager(pygame.key.get_pressed(), stats)
        # ======== init chrono ===========
        game.best_local = 0.0
        dt = game.clock.tick(game.ticks) / 1000
        game.updateCars(dt, t)
        pos.x = game.best_local_cam.x + game.track.offset_x
        pos.y = game.best_local_cam.y + game.track.offset_y
        game.screen.blit(game.track.image, -pos)
        game.draw_win(game.generation) if game.bestNN is not None else None
        if game.cars_inrace > 0:
            for car in game.cars:
                if car.lap_distance < game.best_local:
                    dx = game.best_local_pos.x - car.position.x
                    dy = game.best_local_pos.y - car.position.y
                    car_p = Vector2(car.rect.topleft[0] - car.camera[0] - dx,
                                    car.rect.topleft[1] - car.camera[1] - dy)
                else:
                    car_p = Vector2(car.rect.topleft[0] - car.camera[0],
                                    car.rect.topleft[1] - car.camera[1])
                    game.drawsensors(car.rect.center,
                                     car.angle,
                                     game.best_local_inputs,
                                     car.sensor_front_distance,
                                     car.sensor_lateral_distance,
                                     car.camera
                                     ) if game.show_sensor else None
                game.screen.blit(car.image, car_p)
            pygame.display.update()
            # TODO end
            # TODO stop lap chrono
            # TODO add lap chrono to race time

        # TODO  Start new Lap
        # TODO init lap chrono
        else:
            pygame.display.flip()
            are_we_alone = True
            break
            # End lap
            # End Race
            # End GEN
    return game.best_lap_Distance


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    GEN = 0
    pygame.font.init()
    # Create the game environment
    game = Game()
    game.buildTrack(racesim.src.track_config.trackConfig())
    # init AI
    RESTORE = False
    CHECKPOINT_INTERVAL = 5
    stats = None
    config_path = os.path.join(local_dir, "racesim", "config", "neat_config.ini")
    p, stats = neat_init(CHECKPOINT_INTERVAL, RESTORE, '', config_path)

    # Run AI main routine for each generation cycle util generation_iteration or dead of all species
    GENERATION_CYCLES = 100000
    p.run(generation_iteration, GENERATION_CYCLES)

    # End Race
    # End Game
    pygame.quit()

    # TODO create a separated windows for genome,
    #  another one for score & positions
