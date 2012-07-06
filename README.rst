Serverinfo script
=================

**What it does**: extract information from your apache/nginx configuration
like sitename and port numbers. And from your buildout-generated
``bin/zopectl`` or ``bin/django`` to list the packages used.

Reinout van Rees made this script initially for The Health Agency. Quite
common-company-server-setup specific. Now it is still a bit company specific
as it is in use now at `Nelen & Schuurmans <http://www.nelen-schuurmans.nl>`_,
but it at least provides example code and ideas you can borrow.

On every server, a .json is generated and placed somewhere (preferrably a
network drive). One server grabs all the .json files and generates an overview
html page.


Setup: symlink the correct buildout configuration
-------------------------------------------------

Before you start, you have to symlink the correct buildout configuration::

    $ ln -s development.cfg buildout.cfg

This is if you want to develop on serverinfo itself. On the machines where you
want to grab information, use ``grabber.cfg``. On the central machine where
you want to generate and display the html overview pages from all the servers'
info, use ``displayer.cfg``.


TODO
----

- Extract info also from ngnix configurations.

- Italicize (or strikethrough) server lines in the output when there's no
  apache/nginx config linked to them (=they don't have a
  servername). Indicates they're not used.

- Perhaps also spit out a quick list of used (gunicorn) port numbers for easy
  consumption by other scripts.
