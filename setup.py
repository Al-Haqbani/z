from setuptools import setup, find_packages

setup(
    name='emploleaksguardian',
    version='0.1.0',
    packages=find_packages(),
    py_modules=['emploleaks'],
    install_requires=[],
    entry_points={'console_scripts': ['emploleaks=emploleaks:main']},
)
