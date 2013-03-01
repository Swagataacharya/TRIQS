# Import the Green's functions 
from pytriqs.base.gf.local import GfImFreq, iOmega_n, inverse

# Create the Matsubara-frequency Green's function and initialize it
g = GfImFreq(indices = [1], beta = 50, n_matsubara = 1000, name = "imp")
g <<= inverse( iOmega_n + 0.5 )

from pytriqs.base.plot.mpl_interface import oplot
oplot(g, '-o',  x_window  = (0,10))

