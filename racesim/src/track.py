import os
from math import cos, pi, sin
import numpy as np
import pygame
import racesim.src.track_config
from racesim.src.constants import BLUE, DARK_GRAY, GRAY, RED
from shapely.geometry.polygon import LinearRing
from racesim.src.util.calc_splines import calc_splines
# import trajectory_planning_helpers as tph
from racesim.src.util.spline_approximation import \
    spline_approximation


class Track(pygame.sprite.Sprite):
    def __init__(self, angle=0, center_x=0, center_y=0):
        pygame.sprite.Sprite.__init__(self)
        # self.centerline_cl = 0
        # self.track_clv = []
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.params = racesim.src.track_config.trackConfig()
        # TODO to convert to constant or get it dynamically
        local_dir = os.path.dirname(__file__)
        self.track_path = os.path.join(local_dir, "tracks")
        self.img_from_file = False
        self.filename_prefix = self.params.track_pars['location']
        self.images_path = os.path.join(local_dir, "img")
        if os.path.exists(
            os.path.join(self.images_path, f'{self.filename_prefix}.png')
        ):
            self.img_from_file = False

        # TODO x & y var are to rework, they are'nt used as due
        self.x = int(center_x)
        self.y = int(center_y)
        self.friction = -1
        self.track_width_cl = self.params.track_pars["track_width"] * 10
        self.center_line = None
        # self.center = (self.x, self.y)

    def build_track(self):
        if os.path.exists(
            os.path.join(self.track_path, f'{self.filename_prefix}.png')
        ):
            self.track = np.loadtxt(
                os.path.join(
                    self.track_path, f"{self.filename_prefix}_generated_track.csv"
                ),
                comments='#',
                delimiter=',',
            )
        else:
            self.load_track_from_csv()
            self.center_line = LinearRing(self.track[:, :2])
            self.scale_track()
            self.vectorize_track()

        # Build track from vecots to img
        self.orig_image = pygame.Surface(
            (self.track_width,
             self.track_height),
            pygame.SRCALPHA)

        # === GET track form PNG if exist ===
        if self.img_from_file is True:
            self.load_track_from_png()
        else:
            self.prepare_track()

        self.offset_y = self.track_interp_cl[0][1]
        self.offset_x = self.track_interp_cl[0][0]
        self.rect = self.image.get_rect(center=(self.offset_x, self.offset_y))
        self.center = self.image.get_rect().center
        self.origrect = self.orig_image.get_rect(center=(self.offset_x, self.offset_y))
        self.mask = pygame.mask.from_surface(self.orig_image)
        # self.rect.center = self.center
        # self.image.set_colorkey(pygame.Color(0, 0, 0))
        # self.mask = self.mask.invert()
        # self.mask = pygame.mask.from_threshold(
        #     self.image, pygame.Color('black'), (1, 1, 1, 255))
        self.orig_image = None
        # self.rect.topleft = self.x, self.y
        self.left_line = LinearRing(np.array(self.bound_left_imp_cl))
        self.right_line = LinearRing(np.array(self.bound_right_imp_cl))
        self.center_line = LinearRing(np.array(self.track_interp_cl[:, :2]))
        self.bound_left_imp_cl = None
        self.bound_right_imp_cl = None

    def load_track_from_png(self):
        self.image = pygame.image.load(self.images_path + self.filename_prefix + 'b.png')
        # self.image = self.image.convet_alpha())
        # self.mask = pygame.mask.from_surface(self.image)
        self.image = pygame.image.load(
            os.path.join(self.images_path, f'{self.filename_prefix}.png')
        )
        self.img_file = True

    def prepare_track(self):
        self.img_from_file = False
        self.draw_track(self.orig_image)
        # Copy track path lines to new img
        self.image = self.orig_image
        # make mask
        # self.mask = pygame.mask.from_surface(self.image)
        # save base image
        pygame.image.save(self.image,
                          os.path.join(self.images_path,
                                       self.filename_prefix + 'b.png'))
        # create background
        self.imagetmp = pygame.Surface(
            (self.track_width,
             self.track_height),
            pygame.SRCALPHA)
        self.imagetmp.fill(DARK_GRAY)
        # merge fina image & saveit
        self.imagetmp.blit(self.image, (0, 0))
        self.image = self.imagetmp
        self.imagetmp = None
        pygame.image.save(self.image,
                          os.path.join(self.images_path,
                                       self.filename_prefix + '.png'))
        # self.track_interp_cl = None
        # TODO save image to à file
        # TODO create mask

    def load_track_from_csv(self):
        self.track = np.loadtxt(
            os.path.join(self.track_path, self.filename_prefix + '.csv'),
            comments='#',
            delimiter=',')

        # [x, y, w_tr_right, w_tr_left]
        if self.track.shape[1] != 4:
            print("WARNING: .csv track file must supply four columns")
            self.track = np.column_stack((self.track[:, :2],
                                          self.track[:, 2] / 2,
                                          self.track[:, 2] / 2))

    def save_track(self, data):
        with open(self.output_path, "wb") as fh:
            np.savetxt(fh,
                       data,
                       fmt="%.5f,%.5f,%.5f",
                       header="left_side,center,rigth_side")

    def scale_track(self, scale_factor=1.0):

        length_centerline = self.get_track_lenght()
        if self.params.track_pars["track_length"] is not None:
            scale_factor = self.params.track_pars[
                "track_length"] / length_centerline
        else:
            scale_factor = 1.0
        self.track[:, :2] *= scale_factor
        # TODO manage scaling proportions to handle px vs meters scale facto
        # self.track[:, :2] *= 10
        self.track *= 2
        # TODO Scale with also

        # check for too large deviation of lengths
        if np.abs(1.0 - scale_factor) > 0.02:
            print("WARNING: Large deviation (>2%%) between calculated (%.0fm) and stored\
                length (%.0fm) of the race track!"
                  % (length_centerline, self.params.track_pars["track_length"]))

    def get_track_lenght(self):
        return self.center_line.length

    def get_distance_from_start(self, actual_pos):
        return self.center_line.distance(actual_pos)

    def vectorize_track(self):

        # -------------------------------------------------
        # PREPARE TRACK -----------------------------------
        # -------------------------------------------------
        center_x = self.track[:, 0].max() - self.track[:, 0].min()
        # flip track 180° clockwise
        self.track[:, 0] = (self.track[:, 0] * cos(pi)) - (self.track[:, 0] * sin(pi))
        self.track[:, 1] = (self.track[:, 1] * sin(pi)) + (self.track[:, 1] * cos(pi))
        new_x = abs(center_x - self.track[:, 0])
        self.track[:, 0] = center_x + new_x
        # center track
        self.track[:, 0] -= (self.track[:, 0].min() - self.track_width_cl*0.4)
        self.track[:, 1] -= (self.track[:, 1].min() - self.track_width_cl*0.4)
        # use spline approximation to prepare centerline input
        self.track_interp = spline_approximation(track=self.track,
                                                 stepsize_prep=self.params.stepsize_opts[
                                                     "stepsize_prep"],
                                                 stepsize_reg=self.params.stepsize_opts[
                                                     "stepsize_reg"],
                                                 k_reg=self.params.reg_smooth_opts[
                                                     "k_reg"],
                                                 s_reg=self.params.reg_smooth_opts[
                                                     "s_reg"],
                                                 debug=True)
        self.track_interp *= 5
        # check if imported track should be flipped, i.e. reverse direction
        if self.params.imp_opts["flip_imp_track"]:
            self.track_interp = np.flipud(self.track_interp)

        # check if imported track should be reordered for a new starting point
        if self.params.imp_opts["set_new_start"]:
            ind_start = np.argmin(
                np.hypot(
                    self.track_interp[:, 0] - self.params.imp_opts["new_start"][0],
                    self.track_interp[:, 1] - self.params.imp_opts["new_start"][1]))
            self.track_interp = np.roll(self.track_interp,
                                        self.track_interp.shape[0] - ind_start,
                                        axis=0)
        # calculate splines
        self.track_interp_cl = np.vstack((self.track_interp,
                                          self.track_interp[0]))  # closed track
        el_lengths_imp_cl = np.sqrt(np.sum(np.power(
            np.diff(self.track_interp_cl[:, :2], axis=0), 2), axis=1))
        normvecs_normalized_imp = calc_splines(
            path=self.track_interp_cl[:, :2],
            el_lengths=el_lengths_imp_cl,
            use_dist_scaling=True)[3]
        normvecs_normalized_imp_cl = np.vstack((
            normvecs_normalized_imp, normvecs_normalized_imp[0]))

        # calculate boundaries
        self.bound_right_imp_cl = self.\
            track_interp_cl[:, :2] + normvecs_normalized_imp_cl * np.\
            expand_dims(self.track_interp_cl[:, 2], 1)
        self.bound_left_imp_cl = self.\
            track_interp_cl[:, :2] - normvecs_normalized_imp_cl * np.\
            expand_dims(self.track_interp_cl[:, 3], 1)
        self.track_width = abs(self.bound_left_imp_cl[:, 0].max()
                               ) + abs(self.bound_left_imp_cl[:, 0].min()
                                       ) + self.track_width_cl
        self.track_height = abs(self.bound_left_imp_cl[:, 1].max()
                                ) + abs(self.bound_left_imp_cl[:, 1].min()
                                        ) + self.track_width_cl

    def draw_track_segment(self, img_ptr,  car_pos_x, car_pos_y):
        # TODO : to update
        # TODO : draws aren't be in this class move to game classe
        return img_ptr

    def draw_track(self, image_ptr):

        if not (self.img_from_file):
            pygame.draw.lines(image_ptr, BLUE, True,
                              self.bound_left_imp_cl, 4)
        if not (self.img_from_file):
            pygame.draw.lines(image_ptr, RED, True,
                              self.bound_right_imp_cl, 4)
        # TODO this routine could simplified using numpy matrix dot & linspace
        # https://stackoverflow.com/questions/34738076/compute-matrix-of-pairwise-angles-between-two-arrays-of-points
        dx = np.diff(self.bound_left_imp_cl[:, 0])
        dy = np.diff(self.bound_left_imp_cl[:, 1])
        dist_l = np.sqrt(np.square(dx) + np.square(dy))
        angle_l = np.arctan2(dy, dx)
        dx = np.diff(self.bound_right_imp_cl[:, 0])
        dy = np.diff(self.bound_right_imp_cl[:, 1])
        dist_r = np.sqrt(np.square(dx) + np.square(dy))
        angle_r = np.arctan2(dy, dx)
        dx = None
        dy = None
        # #################################
        for i in np.arange(len(self.bound_left_imp_cl)-1):
            # print(dist_l, dist_r)
            dist = max(dist_r[i], dist_l[i])
            for j in np.arange(int(round(dist, 0))):
                start_x = self.bound_left_imp_cl[i][0] + j * cos(angle_l[i])
                start_y = self.bound_left_imp_cl[i][1] + j * sin(angle_l[i])
                end_x = self.bound_right_imp_cl[i][0] + j * cos(angle_r[i])
                end_y = self.bound_right_imp_cl[i][1] + j * sin(angle_r[i])
                pygame.draw.line(image_ptr,
                                 GRAY,
                                 (start_x, start_y),
                                 (end_x, end_y),
                                 2)

    def update(self, cam_x, cam_y, angle):
        # self.image = pygame.transform.rotate(self.image, angle)
        # self.rect = self.image.get_rect(center=self.rect.center)
        return True
        # self.rect.center = - cam_x,  - cam_y
        # self.center = self.image.get_rect().center
        # print('Track:update:', cam_x, cam_y, self.center, self.rect.center)
        # self.draw_track_segment(self.image, cam_x, cam_y)
        # pygame.transform.rotate(self.image, angle)

    def test(self):

        return True
