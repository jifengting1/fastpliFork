import setuptools

version = '@GIT_DESCRIBE_LOG@'
i = version.find('-')
if i > 0:
    version = version[:i] + '.dev' + version[i + 1:] + '-${CMAKE_BUILD_TYPE}'

setuptools.setup(
    name='fastpli',
    version=version,
    description='Fiber Architecture Simulation Toolbox for PLI',
    long_description='',
    author='Felix Matuschke',
    author_email='f.matuschke@fz-juelich.de',
    url='http://www.fz-juelich.de/inm/inm-1/EN/Forschung/\
        Fibre%20Architecture/Fibre%20Architecture_node.html',
    python_requires='>3.6.0',
    install_requires=['numpy', 'numba', 'scipy', 'h5py'],
    zip_safe=False,
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    package_data={'': ['*.so']},
)
