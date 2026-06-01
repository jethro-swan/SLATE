## Some command line strings:

The following command line strings can be set as aliases.

#### To start SLATE:

    /home/slate/SLATE/venv/bin/gunicorn -w 4 --bind 0.0.0.0:8000 slate:app &

#### To find the master PID of the SLATE processes:

    ps ef | grep gunicorn | grep SLATE | grep 'Sl ' | awk '{print $1}'

#### To shut SLATE down cleanly:

    kill -TERM `ps ef | grep gunicorn | grep SLATE | grep ' Sl ' | awk '{print $1}'`
