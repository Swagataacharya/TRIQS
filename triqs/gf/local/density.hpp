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
#ifndef TRIQS_GF_LOCAL_DENSITY_H
#define TRIQS_GF_LOCAL_DENSITY_H 
#include "../gf.hpp"
#include "../matsubara_freq.hpp"

namespace triqs { 
 namespace gf { 

  //-------------------------------------------------------
  // For Imaginary Matsubara Frequency functions
  // ------------------------------------------------------

  tqa::matrix<double> density( gf_view<matsubara_freq> const & G);

  // For anything that has the ImmutableGfMatsubaraFreq concept, create such a function and compute
  // Here I choose to create G and call the function to avoid creating one code for each expression...
  template<typename GfType>
   TYPE_ENABLE_IF (tqa::matrix<double>, ImmutableGfMatsubaraFreq<GfType>) 
   density( GfType const & G) { return density( gf<matsubara_freq>(G));} 

 }

 namespace clef {
  TRIQS_CLEF_MAKE_FNT_LAZY (1, density);
 }
}

#endif

