Cookbook
========

Create a real time Green function
---------------------------------

.. compileblock:: 

    #include <triqs/gf/retime.hpp>
    #include <triqs/arrays.hpp>
    
    using triqs::gf::make_gf;
    using triqs::gf::retime;
    
    int main() {
      double tmin=0;
      double tmax=10;
      //we will have 5 points
      size_t n_times=5;
      //we want a Green function whose values are complex numbers
      auto shape = triqs::arrays::make_shape(1,1);
      // the type of GF is triqs::gf::gf<triqs::gf::retime>
      auto GF=make_gf<retime>(tmin, tmax, n_times, shape);  
    };

Create a real frequency Green function 
--------------------------------------
.. compileblock:: 

    #include <triqs/arrays.hpp>
    #include <triqs/gf/refreq.hpp>
    
    using triqs::gf::make_gf;
    using triqs::gf::refreq;

    int main() {
      double wmin=0;
      double wmax=10;
      size_t n_freq=5;
      //we want a Green function whose values are 2*2 matrices of complex numbers
      auto shape = triqs::arrays::make_shape(2,2);
      auto GF=make_gf<refreq>(wmin, wmax, n_freq, shape);
    };


Create a Matsubara frequency Green function
-------------------------------------------

The particularity here is that the statistics influences the position of the Matsubara frequencies. 

.. compileblock:: 

    #include <triqs/gf/imfreq.hpp>
    #include <triqs/arrays.hpp>
    
    using triqs::gf::make_gf;
    using triqs::gf::imfreq;

    int main() {
      double beta=1; //inverse temperature
      triqs::gf::statistic_enum stat=triqs::gf::Fermion;
      //we will have 5 points including iw=0 and iw=beta
      size_t n_freq=5;
      auto shape = triqs::arrays::make_shape(1,1);
      auto GF=make_gf<imfreq>(beta, stat, shape, n_freq);  
    };


Create a Matsubara time Green function
--------------------------------------
.. compileblock:: 

    #include <triqs/gf/imtime.hpp>
    #include <triqs/arrays.hpp>
    using triqs::gf::make_gf;
    using triqs::gf::imtime;

    int main() {
      double beta=1; //inverse temperature
      triqs::gf::statistic_enum stat=triqs::gf::Fermion;
      size_t n_times=5;
      auto shape = triqs::arrays::make_shape(1,1);
      auto GF=make_gf<imtime>(beta, stat, shape, n_times);  
    };




