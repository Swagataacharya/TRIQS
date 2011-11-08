.. index:: ipython

ipython and the ipython notebook  
--------------------------------

`ipython <http://ipython.scipy.org>`_ is a more user-friendly version of python with an enhanced interactive shell, which is specially useful
in conjunction with matplotlib. 

If :program:`ipython` is installed on your machine, it will be automatically detected by the TRIQS installation process.
A second script named `ipytriqs` will be generated along `pytriqs`, where the standard python shell is replaced by the ipython one.


IPython notebook
^^^^^^^^^^^^^^^^

TRIQS is compatible with the great new IPython notebook (ipython 0.12), which is a notebook-style web interface to IPython and can be started withe command ipython notebook.

If you wish to install the notebook:

* The simplest is to use an Enthought distribution.
* Download and install the *development* version of ipython.
  
  * Use the python of the Enthought distribution, it will *replace* the Enthought ipython.

  * Detailed instructions are on the 
    `ipython web site <http://ipython.org/ipython-doc/dev/install/install.html#dependencies-for-the-ipython-html-notebook>`_.

* Use the shell ipytriqs_notebook in the directory you want to work.

* NB : example of notebooks are provided in the notebook sudirectory.
