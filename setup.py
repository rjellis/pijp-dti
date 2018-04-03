from setuptools import setup
import pijp_dti

setup(
    name='pijp-dti',
    version=pijp_dti.__version__,
    author='Ryan Ellis',
    author_email='ellis2012ryan@gmail.com',
    packages=['pijp_dti', ],
    include_package_data=True,
    install_requires=[
        "numpy",
        "scipy",
        "matplotlib",
        "dipy",
        "nibabel",
        "pymssql",
        "pyqt5",
        "pijp",
        "pijp_nnicv",
    ],
    entry_points="""
        [console_scripts]
        dti.py=pijp_dti.dti:run
    """
)
