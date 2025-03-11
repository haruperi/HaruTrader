from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read long description from README
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='harutrader',
    version='0.1.0',
    description='Algorithmic trading and management application for MetaTrader 5',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/HaruTrader',
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: Other/Proprietary License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.13',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    python_requires='>=3.13.2',
    entry_points={
        'console_scripts': [
            'harutrader=algotrader.live_trading.executor:main',
            'harutrader-dashboard=algotrader.dashboard.app:main',
            'harutrader-backtest=algotrader.backtest.engine:main',
        ],
    },
    # TODO: Add package data (templates, static files, etc.)
    # TODO: Add test suite configuration
    # TODO: Add additional package metadata
) 