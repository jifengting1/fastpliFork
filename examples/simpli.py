import numpy as np
import numpy.ma as ma

import h5py
import os

import fastpli.simulation
import fastpli.analysis
import fastpli.io

import imageio


def data2image(data):
    return np.swapaxes(np.flip(data, 1), 0, 1)


FILE_NAME = os.path.abspath(__file__)
FILE_PATH = os.path.dirname(FILE_NAME)
FILE_BASE = os.path.basename(FILE_NAME)

np.random.seed(42)

with h5py.File(
        '/tmp/fastpli.example.' + FILE_BASE + '.' + fastpli.__git__hash__ +
        '.h5', 'w') as h5f:
    ### save script ###
    with open(os.path.abspath(__file__), 'r') as f:
        h5f['script'] = f.read()

    ### Setup Simpli for Tissue Generation
    simpli = fastpli.simulation.Simpli()
    simpli.omp_num_threads = 2
    simpli.voxel_size = 0.5  # in mu meter
    simpli.set_voi([-60, 60, -60, 60, -30, 30])  # in mu meter
    simpli.fiber_bundles = fastpli.io.fiber.load(
        os.path.join(FILE_PATH, 'cube.dat'))
    simpli.fiber_bundles_properties = [[(0.333, -0.004, 10, 'p'),
                                        (0.666, 0, 5, 'b'),
                                        (1.0, 0.004, 1, 'r')]]

    print('VOI:', simpli.get_voi())
    print('Memory:', str(round(simpli.memory_usage('MB'), 2)) + ' MB')

    ### Generate Tissue
    print("Run Generation:")
    label_field, vec_field, tissue_properties = simpli.generate_tissue()

    h5f['tissue'] = label_field.astype(np.uint16)
    h5f['vectorfield'] = vec_field
    h5f['tissue_properties'] = tissue_properties

    ### Simulate PLI Measurement ###
    simpli.filter_rotations = np.deg2rad([0, 30, 60, 90, 120, 150])
    simpli.light_intensity = 26000  # a.u.
    simpli.interpolate = True
    simpli.wavelength = 525  # in nm
    simpli.resolution = 20  # in mu meter
    TILTS = [(0, 0), (5.5, 0), (5.5, 90), (5.5, 180), (5.5, 270)]

    tilting_stack = [None] * len(TILTS)
    print("Run Simulation:")
    for t, (theta, phi) in enumerate(TILTS):
        print(theta, phi)
        images = simpli.run_simulation(label_field, vec_field,
                                       tissue_properties, np.deg2rad(theta),
                                       np.deg2rad(phi))

        # for resizing set nan values to image background
        images[np.isnan(images)] = simpli.light_intensity / 4

        h5f['data/' + str(t)] = images

        # apply optic to simulation
        print(images.shape)
        images = simpli.apply_optic(images, gain=3)
        h5f['optic/' + str(t)] = images

        # calculate modalities
        epa = simpli.apply_epa(images)
        h5f['epa/' + str(t) + '/transmittance'] = epa[0]
        h5f['epa/' + str(t) + '/direction'] = np.rad2deg(epa[1])
        h5f['epa/' + str(t) + '/retardation'] = epa[2]

        tilting_stack[t] = images

    # save mask for analysis
    mask = np.sum(label_field, 2) > 0
    mask = simpli.apply_resize(1.0 * mask) > 0.1
    h5f['optic/mask'] = np.uint8(mask)
    mask = None  # keep analysing all pixels

    print("Run ROFL analysis:")
    rofl_direction, rofl_incl, rofl_t_rel, _ = simpli.apply_rofl(
        tilting_stack, tilt_angle=np.deg2rad(5.5), gain=3, mask=mask)

    h5f['rofl/direction'] = np.rad2deg(rofl_direction)
    h5f['rofl/inclination'] = np.rad2deg(rofl_incl)
    h5f['rofl/trel'] = rofl_t_rel

    imageio.imwrite(
        '/tmp/fastpli.example' + FILE_BASE + '.png',
        data2image(
            fastpli.analysis.images.fom_hsv_black(rofl_direction, rofl_incl)))