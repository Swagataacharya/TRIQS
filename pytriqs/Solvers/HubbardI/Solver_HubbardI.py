
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

from types import *
from pytriqs.Solvers.HubbardI import Solver_HubbardI_base
from pytriqs.Base.GF_Local.GFBloc_ImFreq import *
from pytriqs.Base.GF_Local.GF import GF
from pytriqs.Wien2k.Umatrix import Umatrix
import copy,numpy

class Solver_HubbardI(Solver_HubbardI_base):
    """
       Hubbard I Solver
    """
   
   
    # initialisation:
    def __init__(self,Beta,Uint,JHund,l,Nmsb=1025,T=None, UseSpinOrbit=False, Verbosity=0):
        #If T is specified, it is used to transform the Basis set

        Nlm=2*l+1
        if (UseSpinOrbit):
            # no blocks!
            GFstruct = [ ('ud', range(2*Nlm)) ]
        else:
            # up/down blocks:
            GFstruct = [ ('up', range(Nlm)), ('down', range(Nlm)) ]
        
        # U matrix:
        #l = (Nlm-1)/2
        Umat = Umatrix(U_interact=Uint, J_Hund=JHund, l=l)  
        Umat(T=T)
        Umat.ReduceMatrix()
        assert (Umat.N==Umat.Nmat),"Transformation that mixes spins is not implemented in HubbardI Solver!!"
        # now we have the reduced matrices U and Up

        Solver_HubbardI_base.__init__(self, Beta=Beta, GFstruct=GFstruct, Nlm=Nlm, Nmsb = Nmsb, UseSpinOrbit = UseSpinOrbit, Verbosity=Verbosity)
        
        self.ur = Umat.Ufull
        self.umn  = Umat.Up             # reduced matrix, opposite spins
        self.ujmn = Umat.U              # reduced matrix, same spins


        # Define Atomic Levels Dictionary according to the GF Bloc Structure
        self.Eff_Atomic_Levels = {}
        for a,al in GFstruct:
            if (self.UseSpinOrbit):
                self.Eff_Atomic_Levels[a] = numpy.zeros([self.Nlm*2,self.Nlm*2],numpy.complex_)
            else:
                self.Eff_Atomic_Levels[a] = numpy.zeros([self.Nlm,self.Nlm],numpy.complex_)
            

    def set_atomic_levels(self,eal):
        """ Helps to set correctly the variables for the atomic levels from a dictionary."""

        assert (type(eal)==DictType), "Give a dictionary to set_atomic_levels!"

        cnt = 0
        self.ealmat[:,:] *= 0.0

        for ind in eal:
            self.Eff_Atomic_Levels[ind] = copy.deepcopy(eal[ind])
        
            if self.UseSpinOrbit:
                for ii in range(self.Nlm*2):
                    for jj in range(self.Nlm*2):
                        self.ealmat[ii,jj] = self.Eff_Atomic_Levels[ind][ii,jj]
            else:
                for ii in range(self.Nlm):
                    for jj in range(self.Nlm):
                        self.ealmat[cnt*self.Nlm + ii,cnt*self.Nlm + jj] = self.Eff_Atomic_Levels[ind][ii,jj] 
            
            cnt += 1

            
