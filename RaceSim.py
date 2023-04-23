import os
import neat
import racesim.util.visualize as visualize
import pygame
import pygame.freetype
from pygame.math import Vector2
from racesim.src.constants import (BAD_GENOME_THRESHOLD, DEBUG,)
from racesim.src.game import Game

# ============ Game constants ======================

# TODO: create driver class


def game_init():
    # Start the Game (build track)
    # Build Track
    # TODO : track selection (isolate track build in a method)
    game.track.build_track()
    # game.startGame()
    game_reset()


def game_reset():
    game.__init__()
    game.generation += 1
    game.clock = pygame.time.Clock()
    game.ticks = 60
    # init lap numbrers
    game.set_laps(30)
    # game.cars = []
    # game.laps = []
    # game.max_laps = 0
    # game.best_lap = 0
    # game.racetime = 0

    # # AI
    # # game.generation = 0
    # game.nets = []
    # # game.ge = []
    # game.NNs = []
    # # game.updateScore(0)
    # game.bestCarPos = Vector2(-game.width // 2, -game.height // 2)
    # # game.bestCarDistance = 0.0
    # # game.bestCommands = None
    # # game.bestInputs = None
    # # game.bestGenome = None
    # # game.bestNN = None


def game_stats(config, stats):
    stats.save()
    unique_genomes = stats.best_unique_genomes(5)
    assert 1 <= len(unique_genomes) <= 5, "Unique genomes: {!r}".format(unique_genomes)
    genomes = stats.best_genomes(5)
    assert 1 <= len(genomes) <= 5, "Genomes: {!r}".format(genomes)
    stats.best_genome()
    # visualize.draw_net(config, genomes[0], True)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)


def neat_init(restore: bool, checkpoint_iterval: int, checkpoint_file: str = ""):
    if restore:
        # p = neat.Checkpointer.restore_checkpoint(
            # 'best_neat-291-7 sensor_cnnff')
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
    return p


def keystrokes_manager(pressed, game, config, stats):
    if pressed[pygame.K_q]:
        game.endRace
        game_stats(config, stats)
        pygame.quit()
    if pressed[pygame.K_r]:
        game_stats(config, stats)
    if pressed[pygame.K_f]:
        game.screen.blit(game.track.mask.to_surface(), game.track.center)
        pygame.display.flip()
    if pressed[pygame.K_s]:
        pygame.image.save(game.track.image, 'track.png')
    if pressed[pygame.K_v]:
        for z, _ in enumerate(game.cars):
            game.cars[z].max_speed = game.cars[z].max_speed * 1.05
    if pressed[pygame.K_b]:
        for z, _ in enumerate(game.cars):
            game.cars[z].max_speed = game.cars[z].max_speed * 0.95
    if pressed[pygame.K_d]:
        game.show_sensor = not game.show_sensor
    if pressed[pygame.K_p]:
        Mouse_x, Mouse_y = pygame.mouse.get_pos()
        print(Mouse_x, Mouse_y)


def grun(genomes, config):
    # Setup Race
    # TODO : creat grid (qualif)
    nets = game.create_brains(genomes, config)
    pos = Vector2(0, 0)
    game.clock.tick(0)
    t = 0
    # init Track
    game.track = Track(0, game.width//2, game.height//2)
    # setup cars
    game_reset()
    # start car engins
    # Start Race
    game.startRace(genomes, config)
    game.bestCarPos = Vector2(-640, -360)
    game.best_lap_Distance = 0
    are_we_alone = False
    game.updateScore(0.0)
    track_length = game.track.get_track_lenght()
    # Loop
    while not are_we_alone:
        t += 1
        # ======== init crono ===========
        dt = game.clock.tick(game.ticks) / 1000
        # ======== Event queue ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.exit = True
                are_we_alone = True
        # ======== User input ===========
        pressed = pygame.key.get_pressed()
        keystrokes_manager(pressed, game, config, stats)
        k = 0
        game.best_local = 0.0
        while (k < len(game.cars)):
            # genomes[k][1].fitness = 0 if genomes[k][1].fitness is None else None
            collision = False
            if not game.cars[k].is_out:
                car_pos = Vector2(game.cars[k].position.x + game.track.offset_x,
                                  game.cars[k].position.y + game.track.offset_y)

                # Beam detection (IDAR)
                sensors = game.cars[k].getSensors(car_pos)
                inputs = []

                inputs = game.getInputs(sensors,
                                        game.cars[k].sensor_front_distance,
                                        game.cars[k].sensor_lateral_distance, car_pos)
                if game.cars[k].velocity.length() > 0:
                    game.cars[k].velocity.scale_to_length(max(10e-1,
                                                              min(game.cars[k].max_speed,
                                                                  game.cars[k].velocity.length())))
                else:
                    game.cars[k].velocity = Vector2(10e-1, 10e-1)
                inputs.append(game.cars[k].velocity.length()/game.cars[k].max_speed)
                # inputs.append(game.cars[k].angle/180)

                print(inputs) if DEBUG else None
                # Get AI inputs
                print_inp = False
                if print_inp:
                    print(inputs)
                    print_inp = False
                car_lap_distance_old = game.cars[k].lap_distance
                print("Old position : ",
                      car_pos.length(),
                      game.cars[k].velocity.length()) if DEBUG else None
                # Apply car actions for AI Inputs
                game.cars[k].commands = nets[k].activate(tuple(inputs))
                game.cars[k].move(dt)
                # Update car vel, accel, lap_distance, .... after AI actions
                (x, y) = game.cars[k].update(dt)
                # Update curret car vector over the track
                car_pos = Vector2(x + game.track.offset_x,
                                  y + game.track.offset_y)
                # Detect Collision
                if t > 9:
                    collision = game.detectCollision(game.cars[k].mask,
                                                     game.cars[k].position)
                delta_distance = game.best_lap_Distance - game.cars[k].lap_distance

                print("New position : ", car_pos.length(),
                      game.cars[k].velocity.length(),
                      game.cars[k].lap_distance, delta_distance) if DEBUG else None
                # TODO :  change method of detection to remove bad genomes
                if (t > 9) and ((collision) or (delta_distance > BAD_GENOME_THRESHOLD) or (
                    game.cars[k].lap_distance < car_lap_distance_old
                     ) or game.cars[k].velocity.length() < 0.1):
                    if game.cars_inrace > 1:
                        genomes[k][1].fitness = genomes[k][1].fitness*0.9
                    else:
                        genomes[k][1].fitness = genomes[k][1].fitness*1.1
                    game.cars[k].is_out = True
                    game.cars_inrace -= 1
                    if game.cars_inrace == 0:
                        k = 0
                        break
                else:
                    if game.best_lap_Distance < game.cars[k].lap_distance:
                        update_best(game, k, inputs)
                        # game.drawsensors(sensors)
                    if game.best_local < game.cars[k].lap_distance:
                        game.best_local = game.cars[k].lap_distance
                        game.best_local_pos = game.cars[k].position
                        game.best_local_cam = game.cars[k].camera
                        game.best_local_inputs = inputs
                    car_current_lap_time = game.cars[k].lap_start_time.tick()/1000
                    car_mean_speed = game.cars[k].lap_distance / car_current_lap_time

                    if car_mean_speed > game.best_local_mean_speed:
                        game.best_local_mean_speed = car_mean_speed
                    # genomes[k][1].fitness = (game.cars[k].lap_distance / track_length) * 10000 + car_current_lap_time/6
                    genomes[k][1].fitness = (game.cars[k].lap_distance / track_length) * 100 * car_mean_speed 

                    if (genomes[k][1].fitness > game.getScore()):
                        # print(game.ge[k].fitness,)
                        game.updateScore(genomes[k][1].fitness)
                        game.bestNN = game.NNs[k]
                        game.bestCarDistance = game.cars[k].lap_distance
                        game.bestCarPos = game.cars[k].camera
            k += 1

            if game.cars_inrace == 0:
                break
                # print(car.position, car.camera,
                #       car.rect.topleft, car.rect.center) if car.is_out else None
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


def update_best(game, k, inputs):
    game.best_lap_Distance = game.cars[k].lap_distance
    game.best_lap_speed = game.cars[k].velocity.length()
    game.best_lap_steer = game.cars[k].steering
    game.best_lap_acceleration = game.cars[k].acceleration
    game.bestCarPos = game.cars[k].camera
    game.bestInputs = inputs
    game.bestCommands = game.cars[k].commands


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "racesim", "config", "neat_config.ini")
    GEN = 0
    pygame.font.init()
    # Create the game environment
    game = Game()
    game_init()

    # init AI
    RESTORE = False
    CHECKPOINT_INTERVAL = 5
    p = neat_init(RESTORE, CHECKPOINT_INTERVAL, '')

    # Run the game
    p.run(grun, 10000)

    # End Race
    # End Game
    pygame.quit()

    # TODO create a separeted windows for genome,
        #  another one for score & positions

