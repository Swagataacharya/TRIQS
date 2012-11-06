
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
#ifndef TRIQS_GF_DISCRETE_DOMAIN_H
#define TRIQS_GF_DISCRETE_DOMAIN_H
#include "../tools.hpp"

namespace triqs { namespace gf { 

 /// The domain
 class discrete_domain {
  size_t Nmax;
  public:
  typedef long point_t;
  size_t size() const { return Nmax;};
  discrete_domain (size_t Nmax_=1) : Nmax(Nmax_) { }
  bool operator == (discrete_domain const & D) const { return (Nmax == D.Nmax);}

  /// Write into HDF5
  friend void h5_write (tqa::h5::group_or_file fg, std::string subgroup_name, discrete_domain const & d) {
   tqa::h5::group_or_file gr =  fg.create_group(subgroup_name);
   h5_write(gr,"Nmax",d.Nmax);
  }

  /// Read from HDF5
  friend void h5_read  (tqa::h5::group_or_file fg, std::string subgroup_name, discrete_domain & d){
   tqa::h5::group_or_file gr = fg.open_group(subgroup_name);
   long n; 
   h5_read(gr,"Nmax",n);
   d = discrete_domain(n);
  }
 };

}}
#endif
