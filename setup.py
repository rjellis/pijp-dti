from distutils.core import setup

setup(
    name='pijp-dti',
    version='0.1.0',
    author='Ryan Ellis',
    packages='pijp_dti',
    install_requires=[
        "numpy",
        "dipy",
        "nibabel",
    ],
)
