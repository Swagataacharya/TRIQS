
################################################################################
#
# TRIQS: a Toolbox for Research in Interacting Quantum Systems
#
# Copyright (C) 2011 by M. Aichhorn, L. Pourovskii, V. Vildosola
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


from pytriqs.solvers.operators import *
from pytriqs.solvers.ctqmc_hyb import Solver
from pytriqs.base.utility.my_utils import sum_list
import pytriqs.base.utility.mpi as mpi
from types import *
import numpy


#########################################
#
#  Solver for the Multi-Band problem
#
#########################################


class Solver_MultiBand (Solver):
    """ 
    This is a general solver for a multiband local Hamiltonian. 
    Calling arguments: 
    Beta = inverse temperature
    Norb = Number of local orbitals
    U_interact = Average Coulomb interaction
    J_Hund     = Hund coupling
    use_spinflip = true/false
    use_pairhop  = true/false
    useMatrix: Use the interaction matrix calculated from the Slater integrals
    is useMatrix, you need also:
        l: angular momentum of the orbital, l=2 is d
        T: Transformation matrix for U vertex. If not present, use standard complex harmonics
               
    """
    
    def __init__(self, Beta, Norb, U_interact=None, J_Hund=None, GFStruct=False, map=False, use_spinflip=False,
                 useMatrix = True, l=2, T=None, dimreps=None, irep=None, deg_orbs = [], Sl_Int = None):
    
        self.offset = 0
        self.use_spinflip = use_spinflip
        self.Norb = Norb
       
        self.U, self.Up, self.U4ind, self.offset = set_umatrix(U_interact,J_Hund,Norb,l,useMatrix,T,Sl_Int,use_spinflip,dimreps,irep) 

        if (GFStruct):
            assert map, "give also the mapping!"
            self.map = map
        else:
            # standard GFStruct and map
            GFStruct = [ ('%s'%(ud),[n for n in range(Norb)]) for ud in ['up','down'] ]
            self.map = {'up' : ['up' for v in range(self.Norb)], 'down' : ['down' for v in range(self.Norb)]}

        #print GFStruct,self.map
        
        if (use_spinflip==False):
            Hamiltonian = self.__setHamiltonian_density()
        else:
            if (useMatrix):
                #Hamiltonian = self.__setfullHamiltonian_Slater()
                Hamiltonian = self.__setspinflipHamiltonian_Slater()
            else:
                Hamiltonian = self.__setfullHamiltonian_Kanamori(J_Hund = J_Hund)

        Quantum_Numbers = self.__setQuantumNumbers(GFStruct)
    
        # Determine if there are only blocs of size 1:
        self.blocssizeone = True
        for ib in GFStruct:
            if (len(ib[1])>1): self.blocssizeone = False

       
        # now initialize the solver with the stuff given above:
        Solver.__init__(self,
                        Beta = Beta,
                        GFstruct = GFStruct,
                        H_Local = Hamiltonian,
                        Quantum_Numbers = Quantum_Numbers )

        #self.SetGlobalMoves(deg_orbs)

        self.N_Cycles  = 10000
        self.Nmax_Matrix = 100
        self.N_Time_Slices_Delta= 10000
        #if ((len(GFStruct)==2*Norb) and (use_spinflip==False)): 
        if ((self.blocssizeone) and (use_spinflip==False)):
            self.Use_Segment_Picture = True
        else:
            self.Use_Segment_Picture = False
        # check what all these parameters do!!!
   

    def SetGlobalMoves(self,deg_orbs,factor=0.05):
        # Sets some global moves given orbital degeneracies:
        
        strbl  = ''
        strind = ''
        inddone = []

        for orbs in deg_orbs:
            ln = len(orbs)
            orbsorted = sorted(orbs)
            for ii in range(ln):
                if (strbl!=''): strbl += ','
                bl1 = orbsorted[ii]
                bl2 = orbsorted[(ii+1)%ln]
                ind1 = [ll for ll in self.Sigma[bl1].Indices ]
                ind2 = [ll for ll in self.Sigma[bl2].Indices ]

                strbl += "'" + bl1 + "':'" + bl2 + "'"
                for kk, ind in enumerate(ind1):
                    if not (ind in inddone):
                        if (strind!=''): strind += ','
                        strind += '%s:%s'%(ind1[kk],ind2[kk])
                        inddone.append(ind)
                

        if len(deg_orbs)>0:
            str = 'self.Global_Moves = [ (%s, lambda (a,alpha,dag) : ({ '%factor + strbl + ' }[a], {' + strind + '}[alpha], dag) )]'
            exec str
    
        

    def __setHamiltonian_density(self):
        # density-density Hamiltonian:
        
        spinblocs = [v for v in self.map]
        #print spinblocs
        Hamiltonian = N(self.map[spinblocs[0]][0],0)       # initialize it

        for sp1 in spinblocs:
            for sp2 in spinblocs:
                for i in range(self.Norb):
                    for j in range(self.Norb):
                        if (sp1==sp2):
                            Hamiltonian += 0.5 * self.U[self.offset+i,self.offset+j] * N(self.map[sp1][i],i) * N(self.map[sp2][j],j) 
                        else:
                            Hamiltonian += 0.5 * self.Up[self.offset+i,self.offset+j] * N(self.map[sp1][i],i) * N(self.map[sp2][j],j) 

        Hamiltonian -= N(self.map[spinblocs[0]][0],0)      # substract the initializing value

        return Hamiltonian


    def __setfullHamiltonian_Slater(self):
      
        spinblocs = [v for v in self.map]
        Hamiltonian = N(self.map[spinblocs[0]][0],0)       # initialize it
        #print "Starting..."
        # use the full 4-index U-matrix:
        #for sp1 in spinblocs:
        #    for sp2 in spinblocs:
        for m1 in range(self.Norb):
            for m2 in range(self.Norb):
                for m3 in range(self.Norb):
                    for m4 in range(self.Norb):
                        if (abs(self.U4ind[self.offset+m1,self.offset+m2,self.offset+m3,self.offset+m4])>0.00001):
                            for sp1 in spinblocs:
                                for sp2 in spinblocs:
                                    #print sp1,sp2,m1,m2,m3,m4
                                    Hamiltonian += 0.5 * self.U4ind[self.offset+m1,self.offset+m2,self.offset+m3,self.offset+m4] * \
                                        Cdag(self.map[sp1][m1],m1) * Cdag(self.map[sp2][m2],m2) * C(self.map[sp2][m4],m4) * C(self.map[sp1][m3],m3)
        #print "end..."
        Hamiltonian -= N(self.map[spinblocs[0]][0],0)      # substract the initializing value
                        
        return Hamiltonian


    def __setspinflipHamiltonian_Slater(self):
        """Takes only spin-flip and pair-hopping terms"""
        
        spinblocs = [v for v in self.map]
        Hamiltonian = N(self.map[spinblocs[0]][0],0)       # initialize it
        #print "Starting..."
        # use the full 4-index U-matrix:
        #for sp1 in spinblocs:
        #    for sp2 in spinblocs:
        for m1 in range(self.Norb):
            for m2 in range(self.Norb):
                for m3 in range(self.Norb):
                    for m4 in range(self.Norb):
                        if ((abs(self.U4ind[self.offset+m1,self.offset+m2,self.offset+m3,self.offset+m4])>0.00001) and
                            ( ((m1==m2)and(m3==m4)) or ((m1==m3)and(m2==m4)) or ((m1==m4)and(m2==m3)) ) ):
                            for sp1 in spinblocs:
                                for sp2 in spinblocs:
                                    #print sp1,sp2,m1,m2,m3,m4
                                    Hamiltonian += 0.5 * self.U4ind[self.offset+m1,self.offset+m2,self.offset+m3,self.offset+m4] * \
                                        Cdag(self.map[sp1][m1],m1) * Cdag(self.map[sp2][m2],m2) * C(self.map[sp2][m4],m4) * C(self.map[sp1][m3],m3)
        #print "end..."
        Hamiltonian -= N(self.map[spinblocs[0]][0],0)      # substract the initializing value
                        
        return Hamiltonian


            
    def __setfullHamiltonian_Kanamori(self,J_Hund):

        spinblocs = [v for v in self.map]
        assert len(spinblocs)==2,"spinflips in Kanamori representation only implemented for up/down structure!"

        Hamiltonian = N(self.map[spinblocs[0]][0],0)       # initialize it

        # density terms:
        for sp1 in spinblocs:
            for sp2 in spinblocs:
                for i in range(self.Norb):
                    for j in range(self.Norb):
                        if (sp1==sp2):
                            Hamiltonian += 0.5 * self.U[self.offset+i,self.offset+j] * N(self.map[sp1][i],i) * N(self.map[sp2][j],j) 
                        else: 
                            Hamiltonian += 0.5 * self.Up[self.offset+i,self.offset+j] * N(self.map[sp1][i],i) * N(self.map[sp2][j],j) 

        # spinflip term:
        sp1 = spinblocs[0]
        sp2 = spinblocs[1]
        for i in range(self.Norb-1):
            for j in range(i+1,self.Norb):
                Hamiltonian -= J_Hund * ( Cdag(self.map[sp1][i],i) * C(self.map[sp2][i],i) * Cdag(self.map[sp2][j],j) * C(self.map[sp1][j],j) )     # first term
                Hamiltonian -= J_Hund * ( Cdag(self.map[sp2][i],i) * C(self.map[sp1][i],i) * Cdag(self.map[sp1][j],j) * C(self.map[sp2][j],j) )     # second term

        # pairhop terms:
        for i in range(self.Norb-1):
            for j in range(i+1,self.Norb):
                Hamiltonian -= J_Hund * ( Cdag(self.map[sp1][i],i) * Cdag(self.map[sp2][i],i) * C(self.map[sp1][j],j) * C(self.map[sp2][j],j) )     # first term
                Hamiltonian -= J_Hund * ( Cdag(self.map[sp2][j],j) * Cdag(self.map[sp1][j],j) * C(self.map[sp2][i],i) * C(self.map[sp1][i],i) )     # second term  

        Hamiltonian -= N(self.map[spinblocs[0]][0],0)       # substract the initializing value
                        
        return Hamiltonian
   

    def __setQuantumNumbers(self,GFStruct):
    
        QN = {}
        spinblocs = [v for v in self.map]

        # Define the quantum numbers:
        if (self.use_spinflip) :            
            Ntot = sum_list( [ N(self.map[s][i],i) for s in spinblocs for i in range(self.Norb) ] )
            QN['NtotQN'] = Ntot
            #QN['Ntot'] = sum_list( [ N(self.map[s][i],i) for s in spinblocs for i in range(self.Norb) ] )
            if (len(spinblocs)==2):
                # Assuming up/down structure:
                Sz = sum_list( [ N(self.map[spinblocs[0]][i],i)-N(self.map[spinblocs[1]][i],i) for i in range(self.Norb) ] )
                QN['SzQN'] = Sz
                # new quantum number: works only if there are only spin-flip and pair hopping, not any more complicated things
                for i in range(self.Norb):
                    QN['Sz2_%s'%i] = (N(self.map[spinblocs[0]][i],i)-N(self.map[spinblocs[1]][i],i)) * (N(self.map[spinblocs[0]][i],i)-N(self.map[spinblocs[1]][i],i))

        else :
            for ibl in range(len(GFStruct)):
                QN['N%s'%GFStruct[ibl][0]] = sum_list( [ N(GFStruct[ibl][0],GFStruct[ibl][1][i]) for i in range(len(GFStruct[ibl][1])) ] )

        return QN


    def fitTails(self): 
	"""Fits the tails using the constant value for the Re Sigma calculated from F=Sigma*G.
           Works only for blocks of size one."""
	
	#if (len(self.GFStruct)==2*self.Norb):
        if (self.blocssizeone):
            spinblocs = [v for v in self.map]
            mpi.report("Fitting tails manually")
	
            known_coeff = numpy.zeros([1,1,2],numpy.float_)
            msh = [x.imag for x in self.G[self.map[spinblocs[0]][0]].mesh ]
            fit_start = msh[self.fitting_Frequency_Start]
            fit_stop = msh[self.N_Frequencies_Accumulated]	
            
            # Fit the tail of G just to get the density
            for n,g in self.G:
                g.fitTail([[[0,0,1]]],7,fit_start,2*fit_stop) 
            densmat = self.G.density()

            for sig1 in spinblocs:
                for i in range(self.Norb):

                    coeff = 0.0

                    for sig2 in spinblocs:
                        for j in range(self.Norb):
                            if (sig1==sig2):
                                coeff += self.U[self.offset+i,self.offset+j] * densmat[self.map[sig1][j]][0,0].real
                            else:
                                coeff += self.Up[self.offset+i,self.offset+j] * densmat[self.map[sig2][j]][0,0].real

                    known_coeff[0,0,1] = coeff
                    self.Sigma[self.map[sig1][i]].fitTail(fixed_coef = known_coeff, order_max = 3, fit_start = fit_start, fit_stop = fit_stop)

        else:

            for n,sig in self.Sigma:

                known_coeff = numpy.zeros([sig.N1,sig.N2,1],numpy.float_)
                msh = [x.imag for x in sig.mesh]
                fit_start = msh[self.fitting_Frequency_Start]
                fit_stop  = msh[self.N_Frequencies_Accumulated]
            
                sig.fitTail(fixed_coef = known_coeff, order_max = 3, fit_start = fit_start, fit_stop = fit_stop)

		


	
def set_umatrix(U_interact,J_Hund,Norb,l,useMatrix=True,T=None,Sl_Int=None,use_spinflip=False,dimreps=None,irep=None):
    """ Set up the interaction vertex""" 

    from pytriqs.dft.umatrix import *

    offset = 0
    U4ind = None
    U = None
    Up = None
    if (useMatrix):
        if not (Sl_Int is None):
            Umat = Umatrix(l=l)
            assert len(Sl_Int)==(l+1),"Sl_Int has the wrong length"
            if (type(Sl_Int)==ListType):
                Rcl = numpy.array(Sl_Int)
            else:
                Rcl = Sl_Int
            Umat(T=T,Rcl=Rcl)
        else:
            if ((U_interact==None)and(J_Hund==None)):
                mpi.report("Give U,J or Slater integrals!!!")
                assert 0
            Umat = Umatrix(U_interact=U_interact, J_Hund=J_Hund, l=l)
            Umat(T=T)
            
        Umat.ReduceMatrix()
        if (Umat.N==Umat.Nmat):
            # Transformation T is of size 2l+1
            U = Umat.U
            Up = Umat.Up
        else:
            # Transformation is of size 2(2l+1)
            U = Umat.U
         # now we have the reduced matrices U and Up, we need it for tail fitting anyways

        if (use_spinflip):
            #Take the 4index Umatrix
            # check for imaginary matrix elements:
            if (abs(Umat.Ufull.imag)>0.0001).any():
                mpi.report("WARNING: complex interaction matrix!! Ignoring imaginary part for the moment!")
                mpi.report("If you want to change this, look into Wien2k/Solver_MultiBand.py")
            U4ind = Umat.Ufull.real
    
        # this will be changed for arbitrary irep:
        # use only one subgroup of orbitals?
        if not (irep is None):
            #print irep, dimreps
            assert not (dimreps is None), "Dimensions of the representatives are missing!"
            assert Norb==dimreps[irep-1],"Dimensions of dimrep and Norb do not fit!"
            for ii in range(irep-1):
                offset += dimreps[ii]
    else:
        if ((U_interact==None)and(J_Hund==None)):
            mpi.report("For Kanamori representation, give U and J!!")
            assert 0
        U  = numpy.zeros([Norb,Norb],numpy.float_)
        Up = numpy.zeros([Norb,Norb],numpy.float_)
        for i in range(Norb):
            for j in range(Norb):
	        if (i==j):
	            Up[i,i] = U_interact + 2.0*J_Hund
	        else:
	       	    Up[i,j] = U_interact
		    U[i,j]  = U_interact - J_Hund

    return U, Up, U4ind, offset