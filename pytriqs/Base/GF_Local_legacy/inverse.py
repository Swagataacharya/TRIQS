
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

import lazy_expressions, Descriptors

def inverse(x):
    if isinstance(x,(lazy_expressions.lazy_expr,lazy_expressions.lazy_expr_terminal)) : 
        return lazy_expressions.lazy_function("inverse", inverse) (x)
    assert hasattr(x,'invert') and hasattr(x,'copy')
    cop = x.copy() 
    cop.invert()
    return cop

