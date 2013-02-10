A simple tool for getting stats for an openstreetmap area.

See http://linfiniti.com/2012/12/holiday-openstreetmap-project-for-swellendam/


Install
=======

First clone::

    cd /home/web
    git clone git://github.com/timlinux/osm-reporter.git

Then setup a venv::

    cd osm-reporter
    virtualenv python
    source python/bin/activate
    pip install -r REQUIREMENTS.txt

Then deploy under apache mod_wsgi::

   cd apache
   cp osm-reporter.apache.conf.templ osm-reporter.apache.conf

Modify the contents of osm-reporter.apache.conf to suite your installation. Then do ::

   sudo apt-get install libapache2-mod-wsgi
   cd /etc/apache/sites-available
   sudo ln -s /home/web/osm-reporter/apache/osm-reporter.apache.conf .
   sudo a2ensite osm-reporter.apache.conf

If deploying locally you can leave the apache conf file mostly unchanged and add this to your /etc/hosts file::

    127.0.0.1       osm-reporter.localhost

Next restart apache::

    sudo service apache2 restart

Now test - open chrome and visit: http://osm-reporter.localhost


Config
======

You can optionally define a 'config' python module to override the default
behaviour of *OSM-Reporter*.

You can create the python wherever you want, and then you will need to add
the environnement var `REPORTER_CONFIG_MODULE` to make `reporter` aware of
it. For example::

    export REPORTER_CONFIG_MODULE="path.to.the.module"

Then you can override the config properties to fit your need. Note that you
can override only the properties you need to, the other will fallback to
default values. For inspiration, you can have a look at
:file:`reporter/config/default.py`

*Available config*

CREW :

    (list) valid OSM users names of people actively working on your data gathering project

BBOX :

    (str) default bbox to use for the map and the stats;
    format is: "{SW_lng},{SW_lat},{NE_lng},{NE_lat}

DISPLAY_UPDATE_CONTROL :

    (bool) either to display or not the "update stats" button on the map

CACHE_DIR :

    (str) path to a dir where to cache the OSM files used by the backend

TAG_NAMES :

    (list) tag names available for stats (default: ['building', 'highway'])


Tests and QA
------------

There is a test suite available, you can run it using nose e.g.::

    PYTHONPATH=`pwd`/reporter:`pwd`:$(PYTHONPATH) nosetests -v --with-id \
    --with-xcoverage --with-xunit --verbose --cover-package=reporter reporter


Jenkins
-------

We have Continuous Integration support via our Jenkins server at

http://jenkins.linfiniti.com

At the above site you can see the test results for each commit that is made
to the repository. The following jenkins shell commands were used in the
configuration options::

    export OSM_REPORTER_LOGFILE='/tmp/osm-reporter-jenkins.log'
    rm -rf venv
    virtualenv venv
    python/bin/pip install -r requirements.txt
    export PYTHONPATH=`pwd`/reporter:`pwd`:$(PYTHONPATH):`pwd`/python/lib/python2.7/site-packages/
    nosetests -v --with-id --with-xcoverage --with-xunit --verbose --cover-package=reporter reporter
    rm -f pylint.log
    pylint --output-format=parseable --reports=y --rcfile=pylintrc_jenkins -i y reporter > pylint.log
    pep8 --repeat --ignore=E203 --exclude none.py . > pep8.log


Sentry
------

Sentry is a service that collects exceptions and displays aggregate reports
for them. You can view the sentry project we have running for osm-reporter
here: http://sentry.linfiniti.com/osm-reporter/

Tim Sutton & Yohan Boniface
