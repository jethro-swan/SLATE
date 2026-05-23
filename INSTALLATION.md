## Installation

SLATE is probably best run in its own virtual machine, although that is not
essential.

Choose a directory in which to install it, then clone the SLATE repository:

    git clone https://github.com/jethro-swan/SLATE
    cd SLATE

Create a Python3 virtual environment and activate it:

    python3 -m venv venv
    source venv/bin/activate

Create

    venv/lib/python3.x/site-packages/slate.pth

containing

    /home/slate/SLATE

To install the dependencies, run

    ./dependencies.sh

To create the data directory and the initial dataset tree, run

    ./setup.sh

To create the database files and to populate these with the seed entities, run

    ./initialize.py

which will also display the login credentials needed by the initial
administrator.

Create an alias (e.g. in ~/bashrc) to start Gunicorn:

    alias slate_run='/home/slate/SLATE/venv/bin/gunicorn -w 4 \
    --bind 0.0.0.0:8000 slate:app &'

---    

#### Testing the initial installation

##### Simple native installation

If you have installed SLATE natively, on a device with a desktop environment,
the simplest way to test it is to run

    flask run

and to view the user interface at

    http://localhost:5000

This is enough to test the core installation but is unsuitable for deployment.

In order to make it visible from from another machine on the same LAN, perhaps
using a different port (e.g. 5004), and if the IP address of the machine on
which it is hosted is 192.168.1.123 (for example), you can run it instead as

    flask run -h 0.0.0.0 -p 5000

making it accessible as

    http://192.168.1.123:5004

##### Simple testing of a VM installation

There are several options available for creating a virtual environment in which
to run SLATE. It would be impractical to attempt to cover all the options here,
but a convenient option is to use _VirtualBox_ with a bridged adapter and a
simple script (vboxm.sh) has been provided here to simplify this for you.

It is assumed here that you are installing SLATE on a headless server and
therefore do not have the option to use the _VirtualBox_ graphical interface.

You will need to choose an operating system (Debian and Ubuntu are both good
options), ports via which to access Flask (probably 5000 or above for testing
and 8000 or above for deployment using Gunicorn) and an RDP port. You may wish
to run several instances of SLATE alongside each other, each in its own virtual
machine.

###### Using Gunicorn

Assuming that SLATE is installed at

    /home/slate/SLATE/

then it can be started using

  /home/slate/SLATE/venv/bin/gunicorn -w 4 --bind 0.0.0.0:8000 slate:app

(for example).

Assuming you have installed this in a virtual machine (_VirtualBox_ is a
convenient option), you will need set up a reverse proxy in a web server on the
host machine.
