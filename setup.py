from setuptools import setup, find_packages

setup(
    name='django-properties-cache',
    version='0.1.1',
    description='Advanced database data caching tools of methods and properties of your Django models',
    long_description=open('README.markdown').read(),
    # Get more strings from http://www.python.org/pypi?:action=list_classifiers
    author='Max Klymyshyn',
    author_email='klymyshyn@gmail.com',
    url='https://github.com/joymax/django-properties-cache',
    download_url='https://github.com/joymax/django-properties-cache/downloads',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    tests_require=[
        'django',
        'django-picklefield',
        'django-model-utils',
    ],
    install_requires=[
        'django-picklefield',
        'django-model-utils',
    ],
    test_suite='properties_cache.runtests.runtests',
    include_package_data=True,
    zip_safe=False, # because we're including media that Django needs
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
