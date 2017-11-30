from setuptools import setup

setup(
    name='pijp-dti',
    version='0.1.0',
    author='Ryan Ellis',
    author_email='ellis2012ryan@gmail.com',
    packages=['pijp_dti',],
    include_package_data=True,
    install_requires=[
        "numpy",
        "dipy",
        "nibabel",
        "matplotlib",
        "click",
        "scipy"
    ],
    entry_points="""
        [console_scripts]
        dti=pijp_dti.cli:cli
    """
)
