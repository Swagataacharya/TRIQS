# ----------- Mesh  --------------------------
cdef class MeshImFreq: 
    cdef mesh_imfreq  _c

    def __init__(self, Beta, stat, int Nmax): 
        self._c =  make_mesh_imfreq(Beta,{'F' :Fermion, 'B' : Boson}[stat] ,Nmax) 
    
    def __len__ (self) : return self._c.size()
    
    property beta : 
        """Inverse temperature"""
        def __get__(self): return self._c.domain().beta
    
    property statistic : 
        def __get__(self): return 'F' if self._c.domain().statistic==Fermion else 'B'
    
    def __iter__(self) : # I use the C++ generator !
        cdef mesh_pt_generator[mesh_imfreq ] g = mesh_pt_generator[mesh_imfreq ](&self._c)
        while not g.at_end() : 
            yield g.to_point()
            g.increment()

    def __richcmp__(MeshImFreq self, MeshImFreq other,int op) : 
        if op ==2 : # ==
            return self._c == other._c

# C -> Python 
cdef inline make_MeshImFreq ( mesh_imfreq x) :
    return MeshImFreq( x.domain().beta, 'F', x.size() )
    #return MeshImFreq(C_Object = encapsulate (&x))

# ----------- GF --------------------------

cdef class GfImFreq(_ImplGfLocal) :
    cdef gf_imfreq _c
    def __init__(self, **d):
        """
        The constructor have two variants : you can either provide the mesh in
        Matsubara frequencies yourself, or give the parameters to build it.
        All parameters must be given with keyword arguments.

        GfImFreq(Indices, Beta, Statistic, NFreqMatsubara,  Data, Tail, Name)

               * ``Indices``:  a list of indices names of the block
               * ``Beta``:  Inverse Temperature 
               * ``Statistic``:  GF_Statistic.Fermion [default] or GF_Statistic.Boson
               * ``NFreqMatsubara``:  Number of Matsubara frequencies
               * ``Data``:   A numpy array of dimensions (len(Indices),len(Indices),NFreqMatsubara) representing the value of the Green function on the mesh. 
               * ``Tail``:  the tail 
               * ``Name``:  a name of the GF

        If you already have the mesh, you can use a simpler version :

        GfImFreq(Indices, Mesh, Data, Tail, Name)
            
               * ``Indices``:  a list of indices names of the block
               * ``Mesh``:  a MeshGF object, such that Mesh.TypeGF== GF_Type.Imaginary_Frequency 
               * ``Data``:   A numpy array of dimensions (len(Indices),len(Indices),NFreqMatsubara) representing the value of the Green function on the mesh. 
               * ``Tail``:  the tail 
               * ``Name``:  a name of the GF

        .. warning::
        The Green function take a **view** of the array Data, and a **reference** to the Tail.
        """
        c_obj = d.pop('encapsulated_c_object', None)
        if c_obj :
            assert d == {}, "Internal error : encapsulated_c_object must be the only argument"
            self._c = extractor [gf_imfreq] (c_obj) () 
            return 

        bss = d.pop('boost_serialization_string', None)
        if bss :
            assert d == {}, "Internal error : boost_serialization_string must be the only argument"
            boost_unserialize_into(<std_string>bss,self._c) 
            return 
        
        _ImplGfLocal.__init__(self, d)

        cdef MeshImFreq mesh = d.pop('Mesh',None)
        if mesh is None : # 'Mesh' not in d : 
            if 'Beta' not in d : raise ValueError, "Beta not provided"
            Beta = float(d.pop('Beta'))
            Nmax = d.pop('NFreqMatsubara',1025)
            stat = d.pop('Statistic','F') 
            sh = 1 if stat== 'F' else 0 
            #d['Mesh'] = MeshImFreq(Beta,'F',Nmax)
            mesh = MeshImFreq(Beta,'F',Nmax)

        self.dtype = numpy.complex_
        data_raw = d.pop('Data') if 'Data' in d else numpy.zeros((len(self._IndicesL),len(self._IndicesR),len(mesh)), self.dtype )
        
        cdef TailGf tail= d.pop('Tail') if 'Tail' in d else TailGf(OrderMin=-1, size=10, IndicesL=self._IndicesL, IndicesR=self._IndicesR)
    
        assert len(d) ==0, "Unknown parameters in GFBloc constructions %s"%d.keys() 
        
        self._c =  gf_imfreq ( mesh._c, array_view[dcomplex,THREE,COrder](data_raw), tail._c , nothing(), make_c_indices(self) ) 
       
        # object to keep that will never change
        #self.mesh = make_MeshImFreq (self._c.mesh())
        #self.N1, self.N2 = self._c.data_view().shape(0), self._c.data_view().shape(1)
        # end of construction ...
    
    # Access to elements of _c, only via C++
    property mesh : 
        """Mesh"""
        def __get__(self): return make_MeshImFreq (self._c.mesh())
    
    property tail : 
        def __get__(self): return make_TailGf (self._c.singularity_view()) 
        def __set__(self,TailGf t): 
            assert (self.N1, self.N2, self._c.singularity_view().size()) == (t.N1, t.N2, t.size)
            cdef tail t2 = self._c.singularity_view()
            t2 = t._c 

    property N1 : 
        def __get__(self): return self._c.data_view().shape(0)

    property N2 : 
        def __get__(self): return self._c.data_view().shape(1)

    property data : 
        """Access to the data array"""
        def __get__(self) : 
            return self._c.data_view().to_python()
        def __set__ (self, value) :
            cdef object a = self._c.data_view().to_python()
            a[:,:,:] = value
    
    #-------------- Reduction -------------------------------

    def __reduce__(self):
        return py_deserialize, (self.__class__,boost_serialize(self._c),)


    # -------------- HDF5 ----------------------------

    def write_hdf5__ (self, char * fout, char * path) :
        import h5py
        f = h5py.File('myfile.hdf5')
        g = f.create_group("SubGroup")
        print type(f), type(g)
        #h5_write (h5_group_or_file(f.id.id), path, self._c)
        h5_write (h5_group_or_file(g.id.id), path, self._c)
        f.close()
        #h5_write (h5_group_or_file(fout, 0), path, self._c)
        #h5_write (h5_group_or_file(fout, H5F_ACC_TRUNC), path, self._c)
    
    def __write_hdf5__ (self, gr , char * path) :
        h5_write (h5_group_or_file(gr.id.id), path, self._c)
    
    # -------------- Fourier ----------------------------

    def set_from_fourier_of(self,GfImTime gt) :
        """Fills self with the Fourier transform of gt"""
        self._c = lazy_fourier( gt._c )

    #-------------   COPY ----------------------------------------

    def copy (self) : 
        r = make_GfImFreq( clone_gf_imfreq(self._c))
        r.Name = self.Name
        return r
        
    def copy_from(self, GfImFreq G) :
        # Check that dimensions are ok ...
        self._c = G._c

    #--------------   PLOT   ---------------------------------------
   
    def _plot_(self, OptionsDict):
        """ Plot protocol. OptionsDict can contain : 
             * :param RIS: 'R', 'I', 'S', 'RI' [ default] 
             * :param x_window: (xmin,xmax) or None [default]
             * :param Name: a string [default ='']. If not '', it remplaces the name of the function just for this plot.
        """
        return self._plot_base( OptionsDict,  r'$\omega_n$', 
                lambda name : r'%s$(i\omega_n)$'%name, True, [x.imag for x in self.mesh] )
    
    #--------------------  Arithmetic operations  ---------------------------------

    def __iadd__(self, GfImFreq arg):
        self._c = self._c + arg._c
        return self

    def __add__(self, GfImFreq y):
        c = self.copy()
        c += y
        return c

    def __isub__(self, GfImFreq arg):
        self._c = self._c - arg._c
        return self

    def __sub__(self,GfImFreq y):
        c = self.copy()
        c -= y
        return c

    def __imul__(self,arg):
        """ If arg is a scalar, simple scalar multiplication
            If arg is a GF (any object with data and tail as in GF), they it is a matrix multiplication, slice by slice
        """
        n = type(arg).__name__
        if n == 'GfImFreq' :
            self._c = self._c * (<GfImFreq?>arg)._c
        elif n in ['float','int', 'complex'] : 
            self._c = as_dcomplex(arg) * self._c
        else : 
            raise RuntimeError, " argument type not recognized in imul for %s"%arg
        return self

    def __mul_impl__(self, arg, s) : 
        cdef GfImFreq res = self.copy()
        n = type(arg).__name__
        cdef matrix_view [dcomplex,COrder] a 
        if n == 'GfImFreq' :
            res._c =  self._c * (<GfImFreq?>arg)._c
        elif n in ['float','int', 'complex'] : 
            res._c = as_dcomplex(arg) * self._c
        else : 
            a= matrix_view[dcomplex,COrder](numpy.array(arg, self.dtype))
            #res._c =  a * self._c  if s else self._c *a
        return res

    def __mul__(self,arg):
        s = type(self).__name__ != 'GfImFreq' 
        return self.__mul_impl__(self, arg, s) if not s else self.__mul_impl__(arg,  self, s)

    def __idiv__(self,arg):
        self._c = self._c / as_dcomplex(arg)
        return self

    def __div_impl_(self, arg, s):
        if s : raise RuntimeError, "Can not divide by an GfImFreq"
        cdef GfImFreq res = self.copy()
        if type(arg).__name__  in ['float','int', 'complex'] : 
            res._c = self._c / as_dcomplex(arg)
        else : 
            raise RuntimeError, " argument type not recognized for %s"%arg
        return res

    def __div__(self,arg):
        s = type(self).__name__ != 'GfImFreq' 
        return self.__div_impl__(self, arg, s) if not s else self.__div_impl__(self, arg, s)

    #--------------   OTHER OPERATIONS -----------------------------------------------------

    def from_L_G_R (self, L,G,R):
        """ For all argument, replace the matrix by L *matrix * R"""
        warnings.warn("deprecated function : use simply G <<=  L * G * R !", DeprecationWarning)
        self <<= L * G * R
        #self._c = matrix_view[dcomplex,COrder](L) * self._c * matrix_view[dcomplex,COrder](R) 

    def invert(self) : 
        """Invert the matrix for all arguments"""
        pass
        #self._c = inverse_c (self._c)

    def replace_by_tail(self,start) : 
        d = self.data
        t = self.tail
        for n, om in enumerate(self.mesh) : 
            if n >= start : d[:,:,n] = t(om).array

#----------------  Convertions functions ---------------------------------------

# Python -> C
cdef gf_imfreq  as_gf_imfreq (g) except +: 
    return (<GfImFreq?>g)._c

# C -> Python 
cdef make_GfImFreq ( gf_imfreq x) except + :
        return GfImFreq(C_Object = encapsulate (&x))

# Python -> C for blocks
cdef gf_block_imfreq  as_gf_block_imfreq (G) except +:
        cdef vector[gf_imfreq] v_c
        for item in G:
            v_c.push_back(as_gf_imfreq(item))
        return make_gf_block_imfreq (v_c)

# C -> Python for block
cdef make_BlockGfImFreq (gf_block_imfreq G) except + :
    gl = []
    name_list = G.mesh().domain().names()
    cdef int i =0
    for n in name_list:
        gl.append( make_GfImFreq(G[i] ) )
    return GF( NameList = name_list, BlockList = gl)



from pytriqs.Base.Archive.HDF_Archive_Schemes import register_class
register_class (GfImFreq)

