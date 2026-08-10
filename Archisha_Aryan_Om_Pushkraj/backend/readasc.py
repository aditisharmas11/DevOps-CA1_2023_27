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

        self.asc_name = os.path.splitext(os.path.basename(fname))[0].replace("_", " ")
        self.asc_name = " ".join([i.capitalize() for i in self.asc_name.split()])

        with open(fname, 'r', encoding='utf-8') as f:
            d = [line.rstrip('\r\n') for line in f]

        self.read_headers(d)

        for row in d[6:]:
            row_data = [float(i) for i in parse_line(row)]
            row_data = [0 if i == self.invalid_val else i for i in row_data]
            self.data.append(row_data)

    def read_headers(self, d):
        yll = 0
        for row in d[:6]:
            parsed = parse_line(row)
            if not parsed:
                continue
            key = parsed[0].lower()
            value = parsed[1]
            if key == 'ncols':
                self.ncols = int(value)
            elif key == 'nrows':
                self.nrows = int(value)
            elif key == 'xllcorner':
                self.xul = int(value) * 200 - 179_000_000 + 67
            elif key == 'yllcorner':
                yll = int(value) * 200 - 103_000_000 + 40.63
            elif key == 'nodata_value':
                self.invalid_val = int(value)
        self.yul = yll - (self.nrows * self.cellsize_y)

    def get_value_at_lat_long(self, lat, long):
        x_to_fetch, y_to_fetch = convert_lat_long_to_local_coordinates(lat, long)
        x_idx = int(round(x_to_fetch * self.ncols))
        y_idx = int(round(len(self.data) * y_to_fetch))
        x_idx = np.clip(x_idx, 0, self.ncols - 1)
        y_idx = np.clip(y_idx, 0, len(self.data) - 1)

        return self.data[y_idx][x_idx]

    def get_asc_name(self):
        return self.asc_name

location_xs = []
location_ys = []
outline_xs = []
outline_ys = []

def load_location_points():
    global location_xs, location_ys
    cache_path = os.path.join('datasets', 'geocode_cache.json')
    if not os.path.exists(cache_path):
        return
    with open(cache_path, 'r', encoding='utf-8') as f:
        locations = json.load(f)
    location_xs = [locations[k][0] for k in locations if locations[k][0] is not None]
    location_ys = [locations[k][1] for k in locations if locations[k][1] is not None]
    del locations


def load_india_outline():
    global outline_xs, outline_ys
    outline_xs.clear()
    outline_ys.clear()
    csv_path = 'ne_10m_admin_0_countries_ind.csv'
    if not os.path.exists(csv_path):
        return

    with open(csv_path, 'r', encoding='utf-8') as f:
        d = f.readlines()

    # these are (roughly) where india's coordinates are in the country data csv file.
    data_indices = [(0.05, 0.11)]

    for start_perc, end_perc in data_indices:
        for line in d[1 + int(len(d) * start_perc): int(len(d) * end_perc) - 1]:
            l = [float(k.strip()) for k in line.split(',') if k.strip()]
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
