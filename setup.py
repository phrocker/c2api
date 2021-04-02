from setuptools import setup, find_packages

setup(
    name='c2api',
    version='0.1',
    description='C2 API endpoints for Apache NiFi MiNiFi agents',
    url='https://github.com/phrocker/c2api',
    author='Marc Parisi',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.8',
    ],

    keywords='rest restful api flask swagger openapi flask-restplus',

    packages=find_packages(),

    install_requires=['flask-restplus==0.13.0', 'Flask-SQLAlchemy==2.5.1'],
)