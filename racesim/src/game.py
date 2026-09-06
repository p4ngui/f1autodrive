import random
# from fiona import bounds
import pygame
from pygame.math import Vector2
import numpy as np
from math import degrees, atan2, radians, sin, cos
# from shapely.geometry.linestring import LineString
import racesim.src.NNdraw
from racesim.src.track import Track
from racesim.src.constants import (BLACK, DARK_GRAY, GREEN, NODE_FONT, STAT_FONT)
from racesim.src.constants import BAD_GENOME_THRESHOLD
import racesim.src.util.visualize as visualize
from shapely.geometry.polygon import Point
import neat


class Game:
    def __init__(self):
        self.startPygame()
        # TODO : remove override & get values from const
        self.width = int(1280*0.7)
        self.height = 720 + 150
        #######
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.screen.fill(DARK_GRAY)
        self.score = 0
        self.bestGenome = None
        self.bestCarPos = Vector2(-self.width//2, -self.height//2)
        self.bestCarDistance = 0.0
        self.bestActions = [0, 0, 0, 0]
        self.bestInputs = [0, 0, 0, 0, 0, 0]
        self.bestNN = None
        self.best_lap_Distance = None
        self.best_lap_speed = 0
        self.best_lap_steer = 0
        self.best_lap_acceleration = 0
        self.exit = False
        self.score = 0.0
        self.best_local = None
        self.best_local_pos = None
        self.best_local_cam = None
        self.best_local_mean_speed = 0.0
        self.show_sensor = False
        self.best_local_inputs = None
        self.sum_l = 0.0
        self.sum_d = 0.0

        self.cars = []
        self.laps = 0
        self.laps_left = 0
        self.max_laps = 0
        self.best_lap = 0
        self.racetime = 0
        self.cars_inrace = 0
        # AI
        self.generation = 0
        self.nets = []
        self.ge = []
        self.NNs = []
        self.track = None
        self.clock = None

    def set_clock(self, ticks: int = 60):
        self.clock = pygame.time.Clock()
        self.ticks = ticks
        self.clock.tick(self.ticks)

    def set_laps(self, laps):
        self.laps = laps
        self.laps_left = self.laps_left

    def buildTrack(self, track_config):
        # Build Track
        self.track = Track(0, self.width//2, self.height//2)
        self.track.set_parameters(track_config)
        # TODO : track selection
        self.track.build_track()

    def startPygame(self):
        pygame.init()  # Init game Clock
        pygame.display.set_caption("Formula Team Principal")

    def startRace(self, genomes, config):
        # Prepare AI & create cars
        p = 0
        self.cars_inrace = 0
        for p, (id, g) in enumerate(genomes):
            # F1 2023 car dimensions 5.5 m length x 2 m width
            # (scale factor 10px per Meter)
            # CAR Setup
            self.cars.append(racesim.src.car.Car(-0, -0))
            self.cars[p].set_track_offset(self.track.offset_x,
                                          self.track.offset_y)
            # global neats
            g.fitness = 0
            self.cars[p].set_ia(neat.nn.FeedForwardNetwork.create(g, config))
            self.cars[p].set_genome(g)
            self.cars_inrace = len(self.cars)
            self.NNs.append(racesim.src.NNdraw.NN(config, g, (90, 210)))
            # TODO: add car to group.
            # TODO: add angle as init variable
            # center the cars @ start line pointing track direction
            self.cars[p].yaw = -degrees(atan2(
                self.track.track_interp_cl[1][1] - self.track.track_interp_cl[0][1],
                self.track.track_interp_cl[1][0] - self.track.track_interp_cl[0][0])
                                 )
            # print(cars[_].angle)
            # Start car engine @ random speed btw 0 - 10 px/s
            self.cars[p].velocity.x = random.uniform(0, 1) * 10
            # self.cars[p].velocity.rotate_ip(self.cars[p].angle)
            # self.cars[p].velocity.x = max(1, random.uniform(0,
            # 1) * 10 * cos(radians(self.cars[p].angle)))
            # self.cars[p].velocity.y = max(1,
            # random.uniform(0, 1) * 10 * sin(radians(self.cars[p].angle)))
            self.cars[p].acceleration = random.uniform(0, 1) * 5
            # self.cars[p].max_speed = random.uniform(1.5, 2.5) * 102.8
            self.cars[p].camera = (-self.width//2, -self.height//2)
            self.cars[p].car_no = p + 1
            self.startLap(p)
            # TODO if saved genomes load them and add it to cars

    def startLap(self, car_id):
        self.cars[car_id].lap_start_time = pygame.time.Clock()
        return self.cars[car_id].lap_start_time

    def endLap(self, car_id, lap_end_time):
        self.cars[car_id].laptimes.append(lap_end_time - self.cars[car_id].lap_start_time)
        self.cars[car_id].lap_number += 1
        self.lap_distance = 0.0
        # TODO Interpolate exact time car crossed start
        # time = (-speed +- sqrt(speed² + (4a/2*dist)))/(2a/2*dist)
        # TODO Start new lap less interpolated time
        return self.cars[car_id].laptimes[-1]

    def endRace(self):
        # TODO summarize cars times, find winner
        # TODO make time board
        # TODO save genomes
        return self

    def endGame(self):
        pass

    def draw_win(self, GEN):
        delta_big = 25
        delta_little = 15
        text = STAT_FONT.render(
            f"Best Car Score: {str(round(self.getScore(), 1))}", 1, BLACK
        )
        self.screen.blit(text, (self.width-text.get_width() - 10, 5))
        text = STAT_FONT.render(f"Gen: {str(GEN)}", 1, BLACK)
        self.screen.blit(text, (self.width-text.get_width() - 10, delta_big))
        text = STAT_FONT.render(f"Cars: {str(self.cars_inrace)}", 1, BLACK)
        self.screen.blit(text, (self.width-text.get_width() - 10, delta_big*2))
        text = NODE_FONT.render(
            f"Lap Score: {str(round(self.best_lap_Distance, 1))}", 1, BLACK
        )
        self.screen.blit(text, (self.width-text.get_width() - 10, delta_big*3))
        text = NODE_FONT.render(
            f"Speed : {str(round(self.best_lap_speed, 1))}", 1, BLACK
        )
        self.screen.blit(text, (self.width-text.get_width() - 10,
                                delta_big * 3 + delta_little))
        text = NODE_FONT.render(
            f"Accel. : {str(round(self.best_lap_acceleration, 1))}", 1, BLACK
        )
        self.screen.blit(text, (self.width-text.get_width() - 10,
                                delta_big * 3 + delta_little * 2))
        text = NODE_FONT.render(
            f"Steer : {str(round(self.best_lap_steer, 1))}", 1, BLACK
        )
        self.screen.blit(text, (self.width-text.get_width() - 10,
                                delta_big * 3 + delta_little * 3))
        mx = ', '.join((str(round(w, 3)) for w in self.best_local_inputs))
        text = NODE_FONT.render(f"Inputs : {mx}", 1, BLACK)
        self.screen.blit(text, (self.width-text.get_width() - 10,
                                delta_big * 3 + delta_little * 4))
        mx = ', '.join((str(round(w, 3)) for w in self.bestActions))
        text = NODE_FONT.render(f"Outputs : {mx}", 1, BLACK)
        self.screen.blit(text, (self.width-text.get_width() - 10,
                                delta_big * 4 + delta_little * 5))
        self.bestNN.draw(self.screen, self.bestInputs, self.bestActions)
        r = 1
        dist = []
        for car in self.cars:
            if not car.is_out:
                dist.append([car.car_no, car.lap_distance])
                r += 1
        dist = sorted(dist, key=lambda l: l[1])
        for r in np.arange(1, len(dist)+1):
            text = NODE_FONT.render(
                f"Pos {str(r)} : {str(dist[r - 1][0])} : {str(round(dist[0][1] - dist[r - 1][1], 3))}",
                1,
                BLACK,
            )
            self.screen.blit(text, (self.width-text.get_width() - 10,
                                    delta_big * (5) + delta_little * (r+5)))

    # TODO rename method to update sensor
    # TODO create a sensor class

    def updateCars(self, dt, t):
        k = 0
        # track_length = self.track.get_track_length()
        for k, car in enumerate(self.cars):
            # genomes[k][1].fitness = 0 if genomes[k][1].fitness is None else None
            car_current_lap_time = self.cars[k].lap_start_time.tick()/1000
            collision = False
            # Apply car actions for AI Inputs
            self.cars[k].gen_ia_actions(self.track.left_line, self.track.right_line)
            car_lap_distance_old = self.cars[k].lap_distance
            # Update car vel, accel, lap_distance, .... after AI actions
            # Update current car vector over the track
            (x, y) = self.cars[k].update(dt)
            # Detect Collision
            delta_distance = self.cars[k].lap_distance - car_lap_distance_old
            delta_best_distance = self.best_lap_Distance - self.cars[k].lap_distance
            car_mean_speed = self.cars[k].lap_distance / car_current_lap_time
            collision = self.cars[k].detect_collision(self.track.mask,
                                                      self.track.offset_x,
                                                      self.track.offset_y) if t > 9 else False

            # self.cars[k].update_fitness((delta_distance * 0.01) + car_mean_speed * 0.001)
            # pos = self.cars[k].get_car_pos()
            # pos = Point(pos.x,pos.y)
            #dst_rwd =self.cars[k].lap_distance/self.track.get_track_length()
            # print(delta_distance,delta_distance/dt)
            fitness = delta_distance/dt # + 100 * dst_rwd
            self.cars[k].update_fitness(fitness,collision)
            # TODO :  change method of detection to remove bad genomes
            if ((collision) or (delta_best_distance > BAD_GENOME_THRESHOLD) or (
                self.cars[k].lap_distance < car_lap_distance_old
                    ) or self.cars[k].velocity.x < 0.1):
                # self.cars[k].update_fitness((-delta_distance * 5))
                # if self.cars_inrace == 1:
                #     self.cars[k].genome.fitness *= 1.1
                self.cars[k].is_out = True
            else:
                if self.best_lap_Distance < self.cars[k].lap_distance:
                    self.update_best(k, self.cars[k].inputs)
                    # self.drawsensors(sensors)
                if self.best_local < self.cars[k].lap_distance:
                    self.update_best_local(self.cars[k])
                if car_mean_speed > self.best_local_mean_speed:
                    self.best_local_mean_speed = car_mean_speed
                if (self.cars[k].genome.fitness > self.getScore()):
                    # print(self.ge[k].fitness,)
                    self.updateScore(self.cars[k].genome.fitness)
                    self.bestNN = self.NNs[k]
                    self.bestCarDistance = self.cars[k].lap_distance
                    self.bestCarPos = self.cars[k].camera
            if self.cars[k].is_out:
                self.cars_inrace = len(self.cars)
        for car in self.cars:
            if car.is_out:
                self.cars.remove(car)
                self.cars_inrace = len(self.cars)

    def update_best(self, k, inputs):
        self.best_lap_Distance = self.cars[k].lap_distance
        self.best_lap_speed = self.cars[k].velocity.x
        self.best_lap_steer = self.cars[k].steering
        self.best_lap_acceleration = self.cars[k].acceleration
        self.bestCarPos = self.cars[k].camera
        self.bestInputs = inputs
        self.bestActions = self.cars[k].actions

    def update_best_local(self, car):
        self.best_local = car.lap_distance
        self.best_local_pos = car.position
        self.best_local_cam = car.camera
        self.best_local_inputs = car.inputs

    def updateBestCarPos(self, pos):
        self.bestCarPos = pos

    def getScreenCoords(self, x, y):
        return (int(x + self.initialPos[0] - self.bestCarPos[0]), int(
            y + self.initialPos[1] - self.bestCarPos[1]))

    def getBestCarPos(self):
        return self.bestCarPos

    def updateScore(self, new_score):
        self.score = new_score

    def getScore(self):
        return self.score

    def drawsensors(self, center, angle, inputs, sensor_front_distance,
                    sensor_lateral_distance,sensor_diag_distance, camera):
        count = 180
        for i in np.arange(4, -1, -1):
            if i == 2 :
                dist = (1-inputs[4-i]) * sensor_front_distance
            elif i in [0, 4]:
                dist = (1-inputs[4-i]) * sensor_lateral_distance
            else:
                dist = (1-inputs[4-i]) * sensor_diag_distance                
            omega = -radians(angle + count - 180)
            count -= 60 if i in [4, 1] else 30
            dx = dist * sin(omega)
            dy = - dist * cos(omega)
            cx = center[0] - camera[0]
            cy = center[1] - camera[1]
            # line = list(
            #     map(tuple, np.asarray(LineString([(cx, cy), (cx + dx, cy + dy)])))
            #     )
            line = np.asarray([(cx, cy), (cx + dx, cy + dy)])
            pygame.draw.lines(self.screen,
                              GREEN,
                              False,
                              line,
                              2)
            text = NODE_FONT.render(str(4-i), 1, BLACK)
            self.screen.blit(text, (line[-1]))

    def soft_reset(self):
        self.set_clock()
        # init lap numbers
        self.set_laps(30)
        self.cars = []
        self.laps = []
        self.max_laps = 0
        self.best_lap = 0
        self.racetime = 0

        # AI
        self.generation += 1
        # self.nets = []
        # self.ge = []
        self.NNs = []
        # self.updateScore(0)
        self.bestCarPos = Vector2(-self.width // 2, -self.height // 2)
        # self.bestCarDistance = 0.0
        # self.bestActions = None
        # self.bestInputs = None
        # self.bestGenome = None
        # self.bestNN = None

    def main_keystrokes_manager(self, pressed, stats, config):
        if pressed[pygame.K_q]:
            self.endRace
            self.game_stats(stats)
            pygame.quit()

            quit(0)
        if pressed[pygame.K_r]:
            self.game_stats(stats, 2)
        if pressed[pygame.K_t]:
            self.game_stats(stats, 1, config)
        if pressed[pygame.K_y]:
            self.game_stats(stats, 3)
        if pressed[pygame.K_f]:
            self.screen.blit(self.track.mask.to_surface(), self.track.center)
            pygame.display.flip()
        if pressed[pygame.K_s]:
            pygame.image.save(self.track.image, 'track.png')
        if pressed[pygame.K_v]:
            for z, _ in enumerate(self.cars):
                self.cars[z].max_speed = self.cars[z].max_speed * 1.05
        if pressed[pygame.K_b]:
            for z, _ in enumerate(self.cars):
                self.cars[z].max_speed = self.cars[z].max_speed * 0.95
        if pressed[pygame.K_d]:
            self.show_sensor = not self.show_sensor
        if pressed[pygame.K_p]:
            Mouse_x, Mouse_y = pygame

    def game_stats(self, stats, choice, config=None):
        stats.save()
        unique_genomes = stats.best_unique_genomes(5)
        assert 1 <= len(unique_genomes) <= 5, "Unique genomes: {!r}".format(unique_genomes)
        genomes = stats.best_genomes(5)
        assert 1 <= len(genomes) <= 5, "Genomes: {!r}".format(genomes)
        stats.best_genome()
        if choice == 1 and config:
            visualize.draw_net(config, genomes[0], True)
        elif choice == 2:
            visualize.plot_stats(stats, ylog=False, view=True)
        elif choice == 3:
            visualize.plot_species(stats, view=True)
