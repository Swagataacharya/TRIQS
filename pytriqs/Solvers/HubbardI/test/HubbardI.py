
################################################################################
#
# TRIQS: a Toolbox for Research in Interacting Quantum Systems
#
# Copyright (C) 2011 by M. Ferrero, O. Parcollet
#
# TRIQS is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# TRIQS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# TRIQS. If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from pytriqs.Base.Archive import *
from pytriqs.Solvers.HubbardI.Solver_HubbardI import Solver_HubbardI
import numpy

S = Solver_HubbardI(Beta = 200, Uint = 6.0, JHund=0.6, l=2, UseSpinOrbit=False)
eal={}
eal['up'] = -1*numpy.identity(5)
eal['down'] = -1*numpy.identity(5)
S.set_atomic_levels(eal=eal)

S.Solve()

ar=HDF_Archive('HubbardI.output.h5')
ar['G'] = S.G
ar['Sigma'] = S.Sigma
del ar

