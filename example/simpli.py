import time
import h5py
import numpy as np
import sys
import os

from fastpli.simulation import Simpli

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

# Read fiber data and prepair for PliGenerator
# TODO: write json -> parameter function

global_start = time.time()

simpli = Simpli()
# PliGeneration ###
simpli.pixel_size = 1
simpli.dim = [100, 100, 100]
simpli.ReadFiberFile('example/cube.h5')
# simpli.fiber_bundles = [[[[0,0,30,100],[640,640,30,100]]]]
simpli.fiber_bundles_properties = [[(0.333, 0.004, 10, 'p'),
                                    (0.666, -0.004, 5, 'b'), (1.0, 0.004, 1,
                                                              'r')]]

print(simpli.get_voi())
print(simpli.MemoryUseage())

# manipulation of fibers
simpli.RotateVolumeAroundPoint(
    np.deg2rad(20), np.deg2rad(-10), np.deg2rad(5), [10, -5, 7.5])
simpli.TranslateVolume([25, -15, 50])

with h5py.File('/tmp/fastpli.example.simpli.h5', 'w') as h5f:

    start = time.time()
    # label_field, _, tissue_properties =
    # simpli.GenerateTissue(only_label=True)
    label_field, vec_field, tissue_properties = simpli.GenerateTissue()

    h5f['tissue'] = np.array(label_field, np.uint16)
    h5f['vectorfield'] = vec_field
    end = time.time()

    print("TissueGeneration:", end - start)

    # PliSimulation ###
    simpli.filter_rotations = np.deg2rad([0, 30, 60, 90, 120, 150])
    simpli.light_intensity = 26000
    simpli.pixel_size = 1
    simpli.untilt_sensor = True
    simpli.wavelength = 525

    start = time.time()
    print("RunSimulation: 0")
    image = simpli.RunSimulation(label_field, vec_field, tissue_properties, 0,
                                 0)
    h5f['data/0'] = image

    print("RunSimulation: 1")
    image = simpli.RunSimulation(label_field, vec_field, tissue_properties,
                                 np.deg2rad(5.5), np.deg2rad(0))
    h5f['data/1'] = image

    print("RunSimulation: 2")
    image = simpli.RunSimulation(label_field, vec_field, tissue_properties,
                                 np.deg2rad(5.5), np.deg2rad(90))
    h5f['data/2'] = image

    print("RunSimulation: 3")
    image = simpli.RunSimulation(label_field, vec_field, tissue_properties,
                                 np.deg2rad(5.5), np.deg2rad(180))
    h5f['data/3'] = image

    print("RunSimulation: 4")
    image = simpli.RunSimulation(label_field, vec_field, tissue_properties,
                                 np.deg2rad(5.5), np.deg2rad(270))
    h5f['data/4'] = image

    end = time.time()
    print("RunSimulation:", end - start)

global_end = time.time()
print("GlobalRuntime:", global_end - global_start)
