class trackConfig:
    def __init__(self):
        self.track_pars = {"location": "lemanscik",
                           "track_length": 1385.0,
                           "track_width": 14.0}
        # self.track_pars = {"location": "Monza",
        #                    "track_length": 5793.0,
        #                    "track_width": 14.0}
    # set import options ---------------------------------------------------
    # mode:          "track" or "centerline" -> track is supplied as .csv
    #                and contains [x, y, w_tr_right, w_tr_left],
    #                centerline is supplied as .geojson
    # flip_imp_track:flip imported track to reverse direction
    # set_new_start: set new starting point (changes order, not coordinates)
    # new_start:     [x_m, y_m] coordinates of new starting point
    # plot_track:    plot imported as well as smoothed track

        self.imp_opts = {"mode": "centerline",
                         "flip_imp_track": False,
                         "set_new_start": False,
                         "new_start": [0.0, 0.0],
                         "plot_track": False}

    # spline regression smoothing options ----------------------------------
    # k_reg:    [-] order of BSplines -> standard: 3
    # s_reg:    [-] smoothing factor -> range [1.0, 100.0] (play a little bit)

        self.reg_smooth_opts = {"k_reg": 3,
                                "s_reg": 10.0}

    # set stepsizes used during optimization -------------------------------
    # stepsize_prep:             [m] used for linear interpolation before
    #                                spline approximation
    # stepsize_reg:              [m] used for spline interpolation after
    #                                spline approximation (stepsize during opt.)
    # stepsize_interp_after_opt: [m] used for spline interpolation after
    #                                optimization

        self.stepsize_opts = {"stepsize_prep": 1.0,
                              "stepsize_reg": 5.0,
                              "stepsize_interp_after_opt": 5.0}

    # optimization problem options -----------------------------------------
    # width_opt:             [m] vehicle width for optimization incl.
    #                            safety distance
    # curvlim:               [rad/m] curvature limit for optimization
    # iqp_iters_min:         [-] minimum number of iterations for the IQP
    # iqp_curverror_allowed: [rad/m] maximum allowed curvature error for the IQP

        self.optim_opts_mincurv = {"width_opt": 2.0,
                                   "curvlim": 0.12,
                                   "iqp_iters_min": 5,
                                   "iqp_curverror_allowed": 0.001}
        # TODO: set car profile and use it on car init class
        # self car_pars_ = {"max_vel" : 1028}
        # TODO: set driver profile and use it on driver init class
