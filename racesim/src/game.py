import random
# from fiona import bounds
import pygame
from pygame.math import Vector2
import numpy as np
from math import degrees, atan2, radians, sin, cos
from shapely.geometry.linestring import LineString
from shapely.geometry.polygon import Point
import racesim.src.NNdraw
from racesim.src.track import Track
from racesim.src.constants import (BLACK, DARK_GRAY, GREEN, NODE_FONT, STAT_FONT)

import neat


class Game:
    def __init__(self):
        self.startPygame()
        # TODO : remove overrode & get values from const
        self.width = int(1280*0.7)
        self.height = 720 + 150
        #######
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.screen.fill(DARK_GRAY)
        self.score = 0
        self.bestGenome = None
        self.bestCarPos = Vector2(-self.width//2, -self.height//2)
        self.bestCarDistance = 0.0
        self.bestCommands = [0, 0, 0, 0]
        self.bestInputs = [0, 0, 0, 0, 0, 0]
        self.bestGenome = None
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
        self.laps = []
        self.max_laps = 0
        self.best_lap = 0
        self.racetime = 0
        self.cars_inrace = 0
        # AI
        self.generation = 0
        self.nets = []
        self.ge = []
        self.NNs = []

    def startGame(self):
        # Build Track
        # TODO : track selection (isolate track build in a method)
        self.track.build_track()

    def startPygame(self):
        pygame.init()  # Init game Clock
        pygame.display.set_caption("Formula Team Principal")

    def startRace(self, genomes, config):
        # Prepare AI & create cars
        p = 0
        self.cars_inrace = 0
        for id, g in genomes:
            # F1 2020 car dimensions 5.7 m length x 2 m width
            # (scale factor 10px per Meter)
            # CAR Setup
            self.cars.append(racesim.src.car.Car(-0, -0))
            self.cars_inrace += 1
            self.NNs.append(racesim.src.NNdraw.NN(config, g, (90, 210)))
            # TODO: add car to group.
            # TODO: add angle as init variable
            # I center the cars @ start line.
            self.cars[p].angle = -degrees(atan2(
                self.track.track_interp_cl[1][1] - self.track.track_interp_cl[0][1],
                self.track.track_interp_cl[1][0] - self.track.track_interp_cl[0][0])
                                 )
            # print(cars[_].angle)
            # Start car engine
            # self.cars[p].velocity.x = random.uniform(0, 1) * 10
            self.cars[p].velocity.rotate_ip(self.cars[p].angle)
            self.cars[p].velocity.x = max(1, random.uniform(0, 1) * 10 * cos(radians(self.cars[p].angle)))
            self.cars[p].velocity.y = max(1, random.uniform(0, 1) * 10 * sin(radians(self.cars[p].angle)))
            self.cars[p].acceleration = random.uniform(0, 1) * 10
            # self.cars[p].max_speed = random.uniform(1.5, 2.5) * 102.8
            self.cars[p].camera = (-self.width//2, -self.height//2)
            self.cars[p].car_no = p + 1
            self.startLap(p)
            # TODO if saved genomes load them and add it to cars
            p += 1

    def startLap(self, car_id):
        self.cars[car_id].lap_start_time = pygame.time.Clock()
        return self.cars[car_id].lap_start_time

    def endLap(self, car_id, lap_end_time):
        self.cars[car_id].laptimes.append(lap_end_time - self.cars[car_id].lap_start_time)
        self.cars[car_id].lap_number += 1
        self.lap_distance = 0.0
        # TODO Interpolate exact time car crossed start
        # time = (-speed +- sqrt(speed² + (4a/2*dsit)))/(2a/2*dist)
        # TODO Start new lap less interpolated time
        return self.cars[car_id].laptimes[-1]

    def endRace(self):
        # TODO summarize cars times, find winner
        # TODO make time board
        # TODO save genomes
        return self

    def endGame(self):
        return self

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
        self.bestNN.draw(self.screen, self.bestInputs, self.bestCommands)
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
                                    delta_big * (4) + delta_little * (r+4)))

    def distance_to_track(self, sensor,
                          intersection_points,
                          o_pt,
                          sensor_front_distance,
                          sensor_lateral_distance,
                          m):
        if intersection_points.geom_type == "MultiPoint":
            a = {o_pt.distance(pt): pt for pt in intersection_points.geoms}
            intersection_points = a[min(a.keys())]
        if intersection_points.is_empty is False:
            return sensor.project(intersection_points)
        else:
            return sensor_lateral_distance if m in [0, 1, 3, 4] else sensor_front_distance

    def getInputs(self, sensors, sensor_front_distance, sensor_lateral_distance, car_pos):
        inputs = []
        car_pos = Point(car_pos)
        for m, sensor in enumerate(sensors):

            left_intersection_points = self.track.left_line.intersection(sensor)
            right_intersection_points = self.track.right_line.intersection(sensor)
            dl = self.distance_to_track(sensor, left_intersection_points, car_pos,
                                        sensor_front_distance, sensor_lateral_distance, m)
            dr = self.distance_to_track(sensor, right_intersection_points, car_pos,
                                        sensor_front_distance, sensor_lateral_distance, m)
            inputs.append(min(dl, dr))
        inputs[0] = 1-(inputs[0] / sensor_lateral_distance)
        inputs[4] = 1-(inputs[4] / sensor_lateral_distance)
        inputs[1] = 1-(inputs[1] / sensor_lateral_distance)
        inputs[3] = 1-(inputs[3] / sensor_lateral_distance)
        inputs[2] = 1-(inputs[2] / sensor_front_distance)
        return inputs

    def detectCollision(self, car_mask, car_pos):
        # collition = False
        rect = car_mask.get_rect()
        mask_nb_bits_overlap = self.track.mask.overlap_mask(
            car_mask, (int(self.track.offset_x + car_pos.x - rect.center[0]),
                       int(self.track.offset_y + car_pos.y - rect.center[1])
                       )).count()

        return ((car_mask.count() - mask_nb_bits_overlap) > 50)

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
                    sensor_lateral_distance, camera):
        count = 180
        for i in np.arange(4, -1, -1):
            if i in [0, 4, 1, 3]:
                dist = (1-inputs[4-i]) * sensor_lateral_distance
            elif i == 2:
                # inputs[4-i] = 0 if inputs[4-i] == 1 else inputs[4-i]
                dist = (1-inputs[4-i]) * sensor_front_distance
            omega = -radians(angle + count - 180)
            count -= 60 if i in [4, 1] else 30
            dx = dist * sin(omega)
            dy = - dist * cos(omega)
            cx = center[0] - camera[0]
            cy = center[1] - camera[1]
            line = list(
                map(tuple, np.asarray(LineString([(cx, cy), (cx + dx, cy + dy)])))
                )
            pygame.draw.lines(self.screen,
                              GREEN,
                              False,
                              line,
                              2)
            text = NODE_FONT.render(str(4-i), 1, BLACK)
            self.screen.blit(text, (line[-1]))

    def create_brains(self, genomes, config):
        nets = []
        for id, g in genomes:
            # nets.append(neat.nn.RecurrentNetwork.create(g, config))
            g.fitness = 0
            nets.append(neat.nn.FeedForwardNetwork.create(g, config))
            # g.fitness = 0
        return nets
    def reset(self):
        
