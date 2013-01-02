from pytriqs.dft.sumk_lda import *
from pytriqs.dft.converters.wien2k_converter import *
from pytriqs.solvers.hubbard_I.solver import Solver

LDAFilename = 'Ce-gamma'
Beta = 40
Uint = 6.00
JHund = 0.70
Loops =  3                       # Number of DMFT sc-loops
Mix = 0.7                        # Mixing factor in QMC
DC_type = 0                      # 0...FLL, 1...Held, 2... AMF, 3...Lichtenstein
DC_Mix = 1.0                     # 1.0 ... all from imp; 0.0 ... all from Gloc   
useBlocs = False                 # use bloc structure from LDA input
useMatrix = True                 # use the U matrix calculated from Slater coefficients instead of (U+2J, U, U-J)

HDFfilename = LDAFilename+'.h5'

# Convert DMFT input:
# Can be commented after the first run
Converter = SumK_LDA_Wien2k_input(Filename=LDAFilename,repacking=True)
Converter.convert_DMFT_input()

#check if there are previous runs:
previous_runs = 0
previous_present = False

if mpi.is_master_node():
    ar = HDF_Archive(HDFfilename,'a')
    if 'iterations' in ar:
        previous_present = True
        previous_runs = ar['iterations']
    else: 
        previous_runs = 0
        previous_present = False
    del ar

mpi.barrier()
previous_runs    = mpi.bcast(previous_runs)
previous_present = mpi.bcast(previous_present)

# Init the SumK class
SK=SumK_LDA(HDFfile=LDAFilename+'.h5',UseLDABlocs=False)

Norb = SK.corr_shells[0][3]
l    = SK.corr_shells[0][2]

# Init the Solver:
S = Solver(Beta = Beta, Uint = Uint, JHund = JHund, l = l, Verbosity=2)
S.Nmoments=10

if (previous_present):
    # load previous data:
    mpi.report("Using stored data for initialisation")
    if (mpi.is_master_node()):
        ar = HDF_Archive(HDFfilename,'a')
        S.Sigma <<= ar['SigmaF']
        del ar
    S.Sigma = mpi.bcast(S.Sigma)
    SK.load()

# DMFT loop:
for Iteration_Number in range(1,Loops+1):
    
        itn = Iteration_Number + previous_runs
       
        # put Sigma into the SumK class:
        SK.put_Sigma(Sigmaimp = [ S.Sigma ])

        # Compute the SumK, possibly fixing mu by dichotomy
        if SK.Density_Required and (Iteration_Number > 0):
            Chemical_potential = SK.find_mu( precision = 0.000001 )
        else:
            mpi.report("No adjustment of chemical potential\nTotal density  = %.3f"%SK.total_density(mu=Chemical_potential))

        # Density:
        S.G <<= SK.extract_Gloc()[0]
        mpi.report("Total charge of Gloc : %.6f"%S.G.total_density())
        dm = S.G.density()

        if ((Iteration_Number==1)and(previous_present==False)):
	    SK.SetDoubleCounting( dm, U_interact = Uint, J_Hund = JHund, orb = 0, useDCformula = DC_type)

        # set atomic levels:
        eal = SK.eff_atomic_levels()[0]
        S.set_atomic_levels( eal = eal )

        # update hdf5
        if (mpi.is_master_node()):
            ar = HDF_Archive(HDFfilename,'a')
            ar['Chemical_Potential%s'%itn] = Chemical_potential
            del ar

        # solve it:
        S.Solve()

        if (mpi.is_master_node()):
            ar = HDF_Archive(HDFfilename)
            ar['iterations'] = itn
 
        # Now mix Sigma and G:
        if ((itn>1)or(previous_present)):
            if (mpi.is_master_node()):
                mpi.report("Mixing Sigma and G with factor %s"%Mix)
                if ('SigmaF' in ar):
                    S.Sigma <<= Mix * S.Sigma + (1.0-Mix) * ar['SigmaF']
                if ('GF' in ar):
                    S.G <<= Mix * S.G + (1.0-Mix) * ar['GF']

            S.G = mpi.bcast(S.G)
            S.Sigma = mpi.bcast(S.Sigma)


        
        if (mpi.is_master_node()):
            ar['SigmaF'] = S.Sigma
            ar['GF'] = S.G
        
        # after the Solver has finished, set new double counting: 
        dm = S.G.density()
        SK.SetDoubleCounting( dm, U_interact = Uint, J_Hund = JHund, orb = 0, useDCformula = DC_type )
        # correlation energy calculations:
        correnerg = 0.5 * (S.G * S.Sigma).total_density()
        mpi.report("Corr. energy = %s"%correnerg)
        if (mpi.is_master_node()):
            ar['correnerg%s'%itn] = correnerg
            ar['DCenerg%s'%itn] = SK.DCenerg
            del ar


        #Save stuff:
        SK.save()
        if (mpi.is_master_node()):
            print 'DC after solver: ',SK.dc_imp[SK.invshellmap[0]]


        # do some analysis:
        mpi.report("Orbital densities of impurity Green function:")
        dm1 = S.G.density()
        for s in dm1:
            mpi.report("Block %s: "%s)
            for ii in range(len(dm1[s])):
                str = ''
                for jj in range(len(dm1[s])):
                    if (dm1[s][ii,jj].real>0):
                        str += "   %.4f"%(dm1[s][ii,jj].real)
                    else:
                        str += "  %.4f"%(dm1[s][ii,jj].real)
                mpi.report(str)
        mpi.report("Total charge of impurity problem : %.6f"%S.G.total_density())


# find exact chemical potential
if (SK.Density_Required):
    SK.Chemical_potential = SK.find_mu( precision = 0.000001 )
dN,d = SK.calc_DensityCorrection(Filename = LDAFilename+'.qdmft')

mpi.report("Trace of Density Matrix: %s"%d)

#correlation energy:
if (mpi.is_master_node()):
    ar = HDF_Archive(HDFfilename)
    itn = ar['iterations'] 
    correnerg = ar['correnerg%s'%itn] 
    DCenerg = ar['DCenerg%s'%itn]
    del ar
    correnerg -= DCenerg[0]
    f=open(LDAFilename+'.qdmft','a')
    f.write("%.16f\n"%correnerg)
    f.close()


