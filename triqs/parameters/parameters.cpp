#include "./parameters.hpp"
#include <triqs/utility/formatted_output.hpp>

namespace triqs { namespace utility {

 void h5_read ( h5::group F, std::string const & subgroup_name, parameters & p){
  auto gr = F.open_group(subgroup_name);
  std::vector<std::string> ds_name = F.get_all_dataset_names(subgroup_name), grp_name = F.get_all_subgroup_names(subgroup_name);
  for (auto & x : grp_name) {
   //std::cerr  << " loading group : "<< x <<std::endl;
   auto x_grp = gr.open_group(x);
   auto triqs_data_scheme = x_grp.read_triqs_hdf5_data_scheme(); 
   if (triqs_data_scheme != "") { 
    auto type_hash = _object::h5_scheme_to_code[triqs_data_scheme];
    auto it = _object::code_to_h5_read_fnts.find(type_hash);
    if (it == _object::code_to_h5_read_fnts.end()) TRIQS_RUNTIME_ERROR << "TRIQS_HDF5_data_scheme : ["<< triqs_data_scheme << "] is unknown. Did you register your object ?";
    p[x] = it->second(gr,x);
   }
   else { 
    parameters p2;
    h5_read (gr,x,p2);
    p[x] = p2;
   }
  }
  for (auto & x : ds_name) {
   //std::cerr  << " loading : "<< x <<std::endl;
   try {
    _object obj;
    h5_read(gr,x,obj);
    p[x] = obj;
   }
   catch(H5::Exception const & e) { TRIQS_RUNTIME_ERROR<< "Cannot load "<< x<<"\n H5 error is : \n   "<< e.getCDetailMsg();}
  }
 }

 //-----------------------------------------------------------------------

 void parameters::update (parameters const & pdef){ for (auto const & pvp : pdef) (*this)[pvp.first] = pvp.second; }

 void parameters::update (parameter_defaults const & pdef, ull_t flag ){

  if ( (flag & reject_key_without_default) ) { // check that no extra parameters are present
   for (auto const & pvp : *this) 
    if (!pdef.has_key( pvp.first)) 
     TRIQS_RUNTIME_ERROR << "update : parameter "<< pvp.first << " is absent from the defaults and no_parameter_without_default is ON. ";
  }

  std::vector<std::vector<std::string>> missing;
  std::vector<std::vector<std::string>> wrong_t;
#ifndef TRIQS_WORKAROUND_INTEL_COMPILER_BUGS
  std::vector<std::string> desc{"key:", "description:"};
  std::vector<std::string> tdesc{"key:", "expected type:", "actual type:"};
#else
  std::vector<std::string> desc; desc.push_back("key:"); desc.push_back("description:");
  std::vector<std::string> tdesc; tdesc.push_back("key:"); tdesc.push_back("expected type:"); tdesc.push_back("actual type:");
#endif

  for (auto const & pvp : pdef) {
   auto key = pvp.first;

   // check whether required parameters are present
   if (pdef.is_required(key) && (!this->has_key(key))){
    // delay exception until all parameters have been checked
    if (!missing.size()) missing.push_back(desc);
#ifndef TRIQS_WORKAROUND_INTEL_COMPILER_BUGS
    missing.push_back({key, pdef.doc(key)});    
#else
    { std::vector<std::string> v; v.push_back(key); v.push_back(pdef.doc(key)); missing.push_back(v);}
#endif
   }
   if (this->has_key(key)) { // check whether the type is correct 
    if (! have_same_type(pvp.second, (*this)[key])){
     // delay exception until all parameters have been checked
     if (!wrong_t.size()) wrong_t.push_back(tdesc);
#ifndef TRIQS_WORKAROUND_INTEL_COMPILER_BUGS
     wrong_t.push_back({key, pvp.second.type_name(), (*this)[key].type_name()});
#else
    { std::vector<std::string> v; v.push_back(key); v.push_back(pvp.second.type_name()); v.push_back((*this)[key].type_name()); 
     wrong_t.push_back(v);}
#endif

    }
   }
   else { 
    (*this)[key] = pvp.second; // insert the default
   }

  }
  // raise a runtime exception if errors occured
  if(missing.size()) TRIQS_RUNTIME_ERROR<< "update with defaults: the following keys are required but absent: \n"<< print_formatted(missing);
  if(wrong_t.size()) TRIQS_RUNTIME_ERROR << "update with defaults : the following parameters have incorrect type: \n"<< print_formatted(wrong_t);

 }

}}

