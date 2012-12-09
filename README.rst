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
    pip install flask

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




Tim Sutton
