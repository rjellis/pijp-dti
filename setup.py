from setuptools import setup

setup(
    name='pijp-dti',
    version='0.2.0',
    author='Ryan Ellis',
    author_email='ellis2012ryan@gmail.com',
    packages=['pijp_dti',],
    include_package_data = True,
    install_requires=[
        "numpy",
        "scipy",
        "matplotlib",
        "dipy",
        "nibabel",
    ],
    entry_points="""
        [console_scripts]
        dti.py=pijp_dti.dti:run
    """
)
