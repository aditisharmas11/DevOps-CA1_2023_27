import matplotlib.pyplot as plt
import numpy as np
import json
import os
from matplotlib import animation

def coordinate_dist(lat1, long1, lat2, long2):
    return ((lat2 - lat1) ** 2 + (long2 - long1) ** 2) ** 0.5

def parse_line(line):
    return [i for i in line.split(" ") if i != ""]


def convert_local_coordinates_to_lat_long(x_in, y_in):
    out_long = x_in * 32.125 + 67
    out_lat = -(x_in * 1.15) ** 2.5 - y_in * 31.0 + 38.2

    return out_long, out_lat


def convert_lat_long_to_local_coordinates(lat, long):
    x_local = (long - 67) / 32.125
    if x_local < 0:
        raise RuntimeError(f"oh no lat/long: {lat} {long}")

    y_local = -(lat - 38.2 + ((x_local * 1.15) ** 2.5)) / 31.0
    return x_local, y_local


class Asc:
    def __init__(self, fname):
        self.yul = None
        self.xul = None
        self.nrows = None
        self.ncols = None
        self.invalid_val = None
        self.data = []
        self.cellsize_x = 0.0498
        self.cellsize_y = 0.047

        self.asc_name = fname.replace("_", " ")[:-4]
        self.asc_name = " ".join([i.capitalize() for i in self.asc_name.split(" ")])

        with open(fname, "r") as f:
            d = [i.replace("\r", "").replace("\n", "") for i in f.readlines()]

        self.read_headers(d)

        for row in d[6:]:
            row_data = [float(i) for i in parse_line(row)]
            row_data = [0 if i == self.invalid_val else i for i in row_data]
            self.data.append(row_data)

    def read_headers(self, d):
        yll = 0
        for row in d[:6]:
            parsed = parse_line(row)
            if parsed[0] == "ncols":
                self.ncols = int(parsed[1])
            if parsed[0] == "nrows":
                self.nrows = int(parsed[1])
            if parsed[0] == "xllcorner":
                self.xul = int(parsed[1]) * 200 - 179_000_000 + 67
            if parsed[0] == "yllcorner":
                yll = int(parsed[1]) * 200 - 103_000_000 + 40.63
            if parsed[0] == "NODATA_value":
                self.invalid_val = int(parsed[1])
        self.yul = (yll - (self.nrows * self.cellsize_y))

    def get_value_at_lat_long(self, lat, long):
        x_to_fetch, y_to_fetch = convert_lat_long_to_local_coordinates(lat, long)
        x_idx = max(0, round(x_to_fetch * self.ncols))
        y_idx = max(0, round(len(self.data) * y_to_fetch))
        x_idx = min(self.ncols - 1, x_idx)
        y_idx = min(len(self.data) - 1, y_idx)

        return self.data[y_idx][x_idx]

    def get_asc_name(self):
        return self.asc_name

location_xs = []
location_ys = []
outline_xs = []
outline_ys = []

def load_location_points():
    global location_xs, location_ys
    with open("geocode_cache.json", "r") as f:
        locations = json.loads(f.read())
    location_xs = [locations[i][0] for i in locations]
    location_ys = [locations[i][1] for i in locations]
    del locations


def load_india_outline():
    global outline_xs, outline_ys
    with open("ne_10m_admin_0_countries_ind.csv", "r") as f:
        d = f.readlines()

    # these are (roughly) where india's coordinates are in the country data csv file.
    dataIndices = [
        (0.05, 0.11)
    ]

    for dat in dataIndices:
        startPerc = dat[0]
        endPerc = dat[1]
        for i in d[1 + int(len(d) * startPerc): int(len(d) * endPerc) - 1]:
            l = [float(k.strip()) for k in i.split(",")]
            if l[0] < 65:  # longitude
                continue
            outline_xs.append(l[0])
            outline_ys.append(l[1])

    # outline_xs = []
    # outline_ys = []
    # for i in d[1:len(d) // 8]:
    #     l = [float(k.strip()) for k in i.split(",")]
    #     #if l[0] < 65:  # longitude
    #     #    continue
    #     outline_xs.append(l[0])
    #     outline_ys.append(l[1])

    del d

ani = None
def load_asc_file(file_to_plot):
    global ani
    ret_asc = Asc(file_to_plot)
    res = 1
    for y in range(0, res):
        cur_y = 7 + (y * 31) / res
        arr = [0] * res
        for x in range(0, res):
            cur_x = 67 + (x * 31) / res
            arr[x] = ret_asc.get_value_at_lat_long(cur_y, cur_x)
        plt.scatter(
            np.linspace(67, 97, num=res), [cur_y] * res,
            c=arr,
            cmap='viridis'
        )

    # plt.scatter(location_ys, location_xs, c="magenta", s=2)
    last_i = 0
    for i in range(0, len(outline_xs)):
        if coordinate_dist(outline_ys[last_i], outline_xs[last_i], outline_ys[i], outline_xs[i]) > 4:
            plt.scatter(outline_xs[last_i:i], outline_ys[last_i:i], c="pink", s=1)
            last_i = i
    plot_title = file_to_plot.replace("_", " ")[:-4]
    plot_title = " ".join([i.capitalize() for i in plot_title.split(" ")])
    plt.title(plot_title)
    if file_to_plot != files[-1]:
        plt.figure()

    return ret_asc


if __name__ == "__main__":
    load_location_points()
    load_india_outline()

    files = [i for i in os.listdir() if i.endswith(".asc")]
    for file in files:
        load_asc_file(file)
    plt.xlim(65, 100)
    plt.ylim(5, 40)
    plt.show()
