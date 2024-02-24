import pygame as py
from racesim.src.car import decodeCommand
from racesim.src.constants import MIDDLE, NODE_RADIUS, INPUT, OUTPUT, NODE_FONT
from racesim.src.constants import BLACK, GREEN, CONNECTION_WIDTH, RED
import numpy as np


class Node:
    def __init__(self, id, x, y, type, color, label="", index=0):
        self.id = id
        self.x = x
        self.y = y
        self.type = type
        self.color = color
        self.label = label
        self.index = index

    def draw_node(self, game_screen_id, game_best_inputs, game_best_commands):

        colorScheme = self.getNodeColors(game_best_inputs, game_best_commands)

        py.draw.circle(game_screen_id, colorScheme[0], (self.x, self.y), NODE_RADIUS)
        py.draw.circle(game_screen_id, colorScheme[1], (self.x, self.y), NODE_RADIUS-2)

        # draw labels
        if self.type != MIDDLE:
            text = NODE_FONT.render(self.label, 1, BLACK)
            game_screen_id.blit(text, (self.x + (self.type-1) * (
                (text.get_width() if not self.type else 0) + NODE_RADIUS + 5
                ), self.y - text.get_height()/2))

    def getNodeColors(self, game_best_inputs, game_best_commands):

        if self.type == INPUT:
            ratio = game_best_inputs[self.index]
        elif self.type == OUTPUT:
            ratio = 1 if game_best_inputs[self.index] >= 0.5 else 0
        else:
            ratio = 0

        col = [[0, 0, 0], [0, 0, 0]]
        for i in np.arange(3):
            col[0][i] = int(ratio * (self.color[1][i]-self.color[3][i]
                                     ) + self.color[3][i])
            col[1][i] = int(ratio * (self.color[0][i]-self.color[2][i]
                                     ) + self.color[2][i])
        return col


class Connection:
    def __init__(self, input, output, wt):
        self.input = input
        self.output = output
        self.wt = wt

    def drawConnection(self, game_screen_id):
        color = GREEN if self.wt >= 0 else RED
        width = int(abs(self.wt * CONNECTION_WIDTH))
        py.draw.line(game_screen_id, color, (self.input.x + NODE_RADIUS, self.input.y),
                     (self.output.x - NODE_RADIUS, self.output.y), width)
