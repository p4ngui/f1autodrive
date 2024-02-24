from import_geojson_gps_centerline import import_geojson_gps_centerline
from pathlib import Path
import numpy as np


def main():
    track_path = Path("./racesim/src/tracks").resolve()
    trackfilepath = track_path / 'Monza.geojson'
    track_csv_filepath = trackfilepath.with_suffix(".csv")
    if trackfilepath.exists():
        # load centerline
        refline_imp = import_geojson_gps_centerline(trackfilepath=trackfilepath)
        # set artificial track widths in case of centerline
        track_imp = np.column_stack((refline_imp,
                                     np.ones((refline_imp.shape[0], 2))
                                     * 14.0 / 2))
        np.savetxt(track_csv_filepath, track_imp, delimiter=",")


if __name__ == '__main__':
    main()
