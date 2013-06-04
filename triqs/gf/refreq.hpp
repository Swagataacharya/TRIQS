/*******************************************************************************
 *
 * TRIQS: a Toolbox for Research in Interacting Quantum Systems
 *
 * Copyright (C) 2012 by M. Ferrero, O. Parcollet
 *
 * TRIQS is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option) any later
 * version.
 *
 * TRIQS is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * TRIQS. If not, see <http://www.gnu.org/licenses/>.
 *
 ******************************************************************************/
#ifndef TRIQS_GF_FREQ_H
#define TRIQS_GF_FREQ_H
#include "./tools.hpp"
#include "./gf.hpp"
#include "./local/tail.hpp"
#include "./domains/R.hpp"
#include "./meshes/linear.hpp"

namespace triqs { namespace gf {

 struct refreq {};

 namespace gf_implementation { 

  template<typename Opt> struct mesh<refreq,Opt>                { 
   typedef linear_mesh<R_domain> type;
   typedef typename type::domain_t domain_t;
   static type make(double wmin, double wmax, size_t n_freq, mesh_kind mk) {
    return type(domain_t(), wmin, wmax, n_freq, mk);
   }
  };
  
  template<typename Opt> struct singularity<refreq,matrix,Opt>  { typedef local::tail type;};
  template<typename Opt> struct h5_name<refreq,matrix,Opt>      { static std::string invoke(){ return "GfReFreq";}};

  /// ---------------------------  evaluator ---------------------------------

  template<typename Opt>
   struct evaluator<refreq,matrix,Opt> {
    static constexpr int arity = 1;
    template<typename G>
     arrays::matrix_view<std::complex<double> >  operator() (G const * g,double w0)  const {
      auto & data = g->data();
      auto & mesh = g->mesh();
      size_t index; double w; bool in;
      std::tie(in, index, w) = windowing(mesh,w0);
      if (!in) TRIQS_RUNTIME_ERROR <<" Evaluation out of bounds";
      arrays::matrix<std::complex<double> > res = w*data(mesh.index_to_linear(index), arrays::ellipsis()) + (1-w)*data(mesh.index_to_linear(index+1), arrays::ellipsis());
      return res;
     }
    template<typename G>
     local::tail_view operator()(G const * g,freq_infty const &) const {return g->singularity();}
   };

  /// ---------------------------  data access  ---------------------------------

  template<typename Opt> struct data_proxy<refreq,matrix,Opt> : data_proxy_array<std::complex<double>,3> {};

  // -------------------------------   Factories  --------------------------------------------------

  template<typename Opt> struct factories<refreq, matrix,Opt> {
   typedef gf<refreq> gf_t;

   template<typename MeshType>
    static gf_t make_gf(MeshType && m, tqa::mini_vector<size_t,2> shape, local::tail_view const & t) {
     typename gf_t::data_non_view_t A(shape.front_append(m.size())); A() =0;
     return gf_t ( std::forward<MeshType>(m), std::move(A), t, nothing() ) ;
    }

   static gf_t make_gf(double wmin, double wmax, size_t n_freq, tqa::mini_vector<size_t,2> shape) {
    typename gf_t::data_non_view_t A(shape.front_append(n_freq)); A() =0;
    return gf_t(mesh<refreq,Opt>::make(wmin, wmax, n_freq, full_bins), std::move(A), local::tail(shape), nothing());
   }

   static gf_t make_gf(double wmin, double wmax, size_t n_freq, tqa::mini_vector<size_t,2> shape, mesh_kind mk) {
    typename gf_t::data_non_view_t A(shape.front_append(n_freq)); A() =0;
    return gf_t(mesh<refreq,Opt>::make(wmin, wmax, n_freq, mk), std::move(A), local::tail(shape), nothing());
   }

  };
 } // gf_implementation

}}
#endif

