//================================================================================================
// Project: SCAN - Searching Chemical Actions and Networks
//          Hokkaido University (2021)
//          Last Update: Q2 2023
//________________________________________________________________________________________________
// Authors: Mikael Nicander Kuwahara (Lead Developer) [2022-]
//          Jun Fujima (Former Lead Developer) [2021]
//________________________________________________________________________________________________
// Description: This is a hard coded list of available sort options when listing maps.
//------------------------------------------------------------------------------------------------
// Notes: 
//------------------------------------------------------------------------------------------------
// References: none
//================================================================================================

//------------------------------------------------------------------------------------------------
// Map Sort Options
//------------------------------------------------------------------------------------------------
const options = [
  'id',  
  'atom_name',
  'initxyz',
  'fname_top_abs',
  'fname_top_rel',
  'natoms',
  'lowest_energy',
  'highest_energy',
  'neq',
  'nts',
  'npt',
  'jobtime',
  'universal_gamma',
  'infile',
  'scpathpara',
  'jobtype',
  'pathtype',
  'nobondrearrange',
  'siml_tempearture_kelvin',
  'siml_pressure_atm',
  'energyshiftvalue_au',
  'level',
  'spinmulti',
  'totalcharge',
  'jobstatus',
  'ngradient',
  'nhessian',
  'elapsedtime_sec',
  'created_at',
  'updated_at',
];
//------------------------------------------------------------------------------------------------

export default options;
