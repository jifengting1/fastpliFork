#!/usr/bin/python3

from fastpli.simulation import generation, simulation
from fastpli.objects import Fiber, Cell
from fastpli.tools import rotation
import numpy as np
import h5py
from mpi4py import MPI

# Read fiber data and prepair for PliGenerator
# TODO: write json -> parameter function


class Simpli:

    def __init__(self):
        self._fiber_bundles = None
        self._fiber_bundles_properties = None
        self._cells_populations = None
        self._cells_populations_properties = None


        self._gen = generation.Generator()
        self._sim = simulation.Simulator()

        self._dim = None
        self._dim_origin = np.array([0, 0, 0], dtype=int)

        self.pixel_size = 0
        self.setup = simulation.Setup()

    @property
    def dim(self):
        return self._dim
    
    @dim.setter
    def dim(self, dim):
        self._dim = np.array(dim)

    @property
    def dim_origin(self):
        return self._dim_origin
    
    @dim_origin.setter
    def dim_origin(self, dim_origin):
        self._dim_origin = np.array(dim_origin)

    @property
    def fiber_bundles(self):
        return self._fiber_bundles

    @fiber_bundles.setter
    def fiber_bundles(self, fbs):
        if not isinstance(fbs, (list, tuple)):
            raise TypeError("fbs is not a list")

        for fb_i, fb in enumerate(fbs):
            if not isinstance(fb, (list, tuple)):
                raise TypeError("fb is not a list")

            for f_i, f in enumerate(fb):
                if isinstance(f, Fiber):
                    continue
                elif isinstance(f, (list, tuple)):
                    f = np.array(f)        
        
                if isinstance(f, np.ndarray):
                    if len(f.shape) is not 2 or f.shape[1] is not 4:
                        raise TypeError("fiber elements has to be of dim nx4")
                    fbs[fb_i][f_i] = Fiber(f[:, 0:-1], f[:, -1]) 
                else:
                    raise TypeError("fiber hast to be a objects.Fiber, 4d-list or 4d-array")

        self._fiber_bundles = fbs

    @property
    def fiber_bundles_properties(self):
        return self._fiber_bundles_properties

    @fiber_bundles_properties.setter
    def fiber_bundles_properties(self, bundle_layer_properties):
        if not isinstance(bundle_layer_properties, (list, tuple)):
            raise TypeError("properties must be a list(list(tuples))")

        if len(self._fiber_bundles) != len(bundle_layer_properties):
            raise TypeError(
                "properties must have the same size as fiber_bundles")

        self._fiber_bundles_properties = []
        for prop in bundle_layer_properties:
            if not isinstance(prop, (list, tuple)):
                raise TypeError(
                    "properties must be a list(list(tuples))")

            self._fiber_bundles_properties.append([])
            for ly in prop:
                if len(ly) != 4:
                    raise TypeError(
                        "properties must have len 4 (float, float, float, char)")
                self._fiber_bundles_properties[
                    -1].append(generation.LayerProperty(ly[0], ly[1], ly[2], ly[3]))

    @property
    def cells_populations(self):
        return self._cells_populations

    @cells_populations.setter
    def cells_populations(self, cps):
        if not isinstance(cps, (list, tuple)):
            raise TypeError("cells_populations is not a list")

        for cp_i, cp in enumerate(cps):
            if not isinstance(cp, (list, tuple)):
                raise TypeError("cells_population is not a list")

            for c_i, c in enumerate(cp):
                if isinstance(c, Cell):
                    continue
                elif isinstance(c, (list, tuple)):
                    c = np.array(c)        
        
                if isinstance(c, np.ndarray):
                    if len(c.shape) is not 2 or c.shape[1] is not 4:
                        raise TypeError("cell elements has to be of dim nx4")
                    cps[cp_i][c_i] = Cell(c[:, 0:-1], c[:, -1]) 
                else:
                    raise TypeError("cell hast to be a objects.Cell, 4d-list or 4d-array")

        self._cells_populations = cps

    @property
    def cells_populations_properties(self):
        return self._cells_populations_properties

    @cells_populations_properties.setter
    def cells_populations_properties(self, cells_populations_properties):

        if not isinstance(cells_populations_properties, (list, tuple)):
            raise TypeError("properties must be a list")

        self._cells_populations_properties = []
        for prop in cells_populations_properties:

            if not isinstance(prop, (list, tuple)):
                raise TypeError("properties must be a list of 2 arguments")

            if len(prop) != 2:
                raise TypeError("properties must be a list of 2 arguments")

            self._cells_populations_properties.append(generation.CellProperty(prop[0], prop[1]))


    def ReadFiberFile(self, filename):
        self._fiber_bundles = []
        with h5py.File(filename, 'r') as h5f:

            fbs = h5f['fiber_bundles']
            for fb in fbs:
                self._fiber_bundles.append([])
                fb = fbs[fb]
                for f in fb:
                    f = fb[f]
                    self._fiber_bundles[-1].append(
                        Fiber(f['points'][:].flatten(), f['radii'][:]))

    def ReadFiberCellFile(self, filename):
        self._fiber_bundles = []
        with h5py.File(filename, 'r') as h5f:

            fb = h5f['fiber_bundles']
            self._fiber_bundles = []
            self._fiber_bundles.append([])
            for f in fb:
                f = fb[f]
                self._fiber_bundles[-1].append(
                    Fiber(f['points'][:].flatten(), f['radii'][:]))

            self._cells_populations = []
            
            cells = h5f['cells/astrocytes']
            self._cells_populations.append([])
            for c in cells:
                c = cells[c]
                self._cells_populations[-1].append(
                    Cell(c['points'][:].flatten(), c['radii'][:]))

            cells = h5f['cells/oligodendrocytes']
            self._cells_populations.append([])
            for c in cells:
                c = cells[c]
                self._cells_populations[-1].append(
                    Cell(c['points'][:].flatten(), c['radii'][:]))

    def TranslateVolume(self, offset):
        if not isinstance(offset, (list, tuple)):
            raise TypeError("offset must be a list")

        for fb in self._fiber_bundles:
            for f in fb:
                f.translate(offset)

    def RotateVolume(self, phi, theta, psi):
        rot_mat = rotation.zyz(phi, theta, psi)
        for fb in self._fiber_bundles:
            for f in fb:
                f.rotate(list(rot_mat))

    def RotateVolumeAroundPoint(self, phi, theta, psi, offset):
        offset = np.array(offset)
        if offset.shape != (3,):
            raise TypeError("offset must a point")
        rot_mat = rotation.zyz(phi, theta, psi)
        for fb in self._fiber_bundles:
            for f in fb:
                f.rotate_around_point((rot_mat), offset)

    def __CheckDataLength(self):
        if(self._fiber_bundles):
            if len(self._fiber_bundles) != len(self._fiber_bundles_properties):
                raise TypeError(
                    "properties must have the same size as fiber_bundles")

        if(self._cells_populations):
            if len(self._cells_populations) != len(self._cells_populations_properties):
                raise TypeError(
                    "properties must have the same size as cell_populations")

    def GenerateTissue(self, only_label=False, progress_bar = False):
        self._gen.set_volume(self._dim, self.dim_origin, self.pixel_size)
        self.__CheckDataLength()
        if self._fiber_bundles:
            self._gen.set_fiber_bundles(
                self._fiber_bundles, self._fiber_bundles_properties)
        if self._cells_populations:
            self._gen.set_cell_populations(self._cells_populations, self._cells_populations_properties)
        label_field, vec_field, tissue_properties = self._gen.run_generation(only_label, progress_bar)

        return label_field, vec_field, tissue_properties

    def InitSimulation(self, label_field, vec_field, tissue_properties):
        self._sim.set_pli_setup(self.setup)
        self._sim.set_tissue(
            label_field, vec_field, tissue_properties, self.pixel_size)

    def RunSimulation(self, label_field, vec_field,
                      tissue_properties, theta, phi, do_untilt=True):

        self.setup.pixel_size = self.pixel_size
        self._sim.set_pli_setup(self.setup)
        self._sim.set_tissue_properties(tissue_properties)

        image = self._sim.run_simulation(self._dim, label_field, vec_field, theta, phi, do_untilt)
        return image

    def DimData(self):
        dim_local = self._gen.dim_local()
        dim_offset = self._gen.dim_offset()
        return dim_local, dim_offset

    def SaveAsH5(self, h5f, data, data_name):

        dim_local, dim_offset = self.DimData()
        if data_name is 'tissue':
            dim = self._dim
            dset = h5f.create_dataset(data_name, dim, dtype=np.uint16)

            for i in range(data.shape[0]):
                dset[i+dim_offset[0], dim_offset[1]:dim_offset[1]
                 + dim_local[1], dim_offset[2]:dim_offset[2] + dim_local[2]] = data[i,:,:]

        elif data_name is 'vectorfield':
            dim = [self._dim[0], self._dim[1], self._dim[2], 3]
            dset = h5f.create_dataset(data_name, dim, dtype=np.float32)
            for i in range(data.shape[0]):
                dset[i+dim_offset[0], dim_offset[1]:dim_offset[1]
                 + dim_local[1], dim_offset[2]:dim_offset[2] + dim_local[2]] = data[i,:,:]
        elif 'data/' in data_name:
            dim = [self._dim[0], self._dim[1], len(self.setup.filter_rotations)]
            dset = h5f.create_dataset(data_name, dim, dtype=np.float32)

            if tuple(dim) == data.shape:
                dset[:] = data[:]
            else:
                mask = (np.count_nonzero(data, axis=2) != 0)

                for i in range(data.shape[0]):

                    first = 0
                    for idx, elm in enumerate(mask[i,:]):
                        if elm:
                            first = idx
                            break
                    

                    last = -1
                    for idx, elm in reversed(list(enumerate(mask[i,:]))):
                        if elm:
                            last = idx+1
                            break
                    
                    if first <= last:
                        dset[i+dim_offset[0], first+dim_offset[1]:last+dim_offset[1],:] = data[i, first:last,:]
                

        else:
            raise TypeError("no compatible SaveAsH5: " + data_name)