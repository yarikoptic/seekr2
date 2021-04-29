"""
mmvt/sim_openmm.py

Create the Sim_openmm object which contains the objects needed for an
openmm simulation based on the settings provided by a user. These
objects are specific to MMVT only.
"""

import os

import openmm
import openmm.app as openmm_app
from parmed import unit

from mmvtplugin import MmvtLangevinIntegrator, vectori, vectord
import mmvtplugin
import seekr2.modules.common_sim_openmm as common_sim_openmm

class MMVT_sim_openmm(common_sim_openmm.Common_sim_openmm):
    """
    traj_reporter : openmm.DCDReporter
        The OpenMM Reporter object to which the trajectory will be
        written.
        
    energy_reporter : openmm.StateDataReporter
        The OpenMM StateDataReporter to which the energies and other
        state data will be reported.
        
    """
    def __init__(self):
        super(MMVT_sim_openmm, self).__init__()
        self.system = None
        self.integrator = None
        self.simulation = None
        self.traj_reporter = openmm_app.DCDReporter
        self.energy_reporter = openmm_app.StateDataReporter
        return
        
class MMVT_sim_openmm_factory(common_sim_openmm.Common_sim_openmm_factory):
    """
    Create the sim_openmm objects which will be used to run MMVT
    calculations in OpenMM.
    """
    def __init__(self):
        self.sim_openmm = MMVT_sim_openmm()
        return
    
    def add_integrator(self, model, output_filename="", state_prefix=None):
        """
        
        """
        if model.openmm_settings.langevin_integrator is not None:
            target_temperature = \
                model.openmm_settings.langevin_integrator.target_temperature
            friction_coefficient = \
                model.openmm_settings.langevin_integrator.friction_coefficient
            random_seed = \
                model.openmm_settings.langevin_integrator.random_seed
            timestep = \
                model.openmm_settings.langevin_integrator.timestep
            rigid_constraint_tolerance = \
                model.openmm_settings.langevin_integrator\
                .rigid_tolerance
                
            self.sim_openmm.timestep = timestep
            
            self.sim_openmm.integrator = MmvtLangevinIntegrator(
                target_temperature*unit.kelvin, 
                friction_coefficient/unit.picoseconds, 
                timestep*unit.picoseconds, 
                self.sim_openmm.output_filename)
            
            if random_seed is not None:
                self.sim_openmm.integrator.setRandomNumberSeed(random_seed)
                
            if rigid_constraint_tolerance is not None:
                self.sim_openmm.integrator.setConstraintTolerance(
                    rigid_constraint_tolerance)
            
            if state_prefix is not None:
                self.sim_openmm.integrator.setSaveStateFileName(state_prefix)
                
            # For testing purposes:
            #self.sim_openmm.integrator.setSaveStatisticsFileName(
            #    os.path.join(os.path.dirname(output_filename), 
            #                 "test_stats.txt"))
            
        else:
            raise Exception("Settings not provided for available "\
                            "integrator type(s).")
        return
    
    def add_forces(self, model, anchor):
        """
        
        """
        for milestone in anchor.milestones:
            cv = milestone.get_CV(model)
            myforce = make_mmvt_boundary_definitions(
                cv, milestone)
            self.sim_openmm.integrator.addMilestoneGroup(milestone.alias_index)
            forcenum = self.sim_openmm.system.addForce(myforce)
        return
    
    def add_simulation(self, model, topology, positions, box_vectors):
        """
        
        """
        self.sim_openmm.simulation = openmm_app.Simulation(
            topology.topology, self.sim_openmm.system, 
            self.sim_openmm.integrator, self.sim_openmm.platform, 
            self.sim_openmm.properties)
        
        self.sim_openmm.simulation.context.setPositions(positions.positions)
        if box_vectors is not None:
            self.sim_openmm.simulation.context.setPeriodicBoxVectors(*box_vectors)
        if model.openmm_settings.run_minimization:
            print("Warning: running minimizations. It is recommended that "\
                  "structures are minimized and verified by the user before "\
                  "running SEEKR, since minimizations might cause the system "\
                  "to drift out of the MMVT cell.")
            self.sim_openmm.simulation.minimizeEnergy()
        
        self.sim_openmm.simulation.context.setVelocitiesToTemperature(
            model.openmm_settings.initial_temperature * unit.kelvin)
        assert self.sim_openmm.timestep is not None
        return
    
    def create_sim_openmm(self, model, anchor, output_filename, 
                          state_prefix=None):
        """
        Take all relevant model and anchor information and generate
        the necessary OpenMM objects to run the simulation.
        
        Parameters
        ----------
        model : Model()
            The Model which contains the anchor and all settings for
            the simulation that is about to be run.
            
        anchor : Anchor()
            The anchor object that this OpenMM simulation applies to.
            
        output_filename : str
            The name of the file that will be written by the plugin as
            the MMVT simulation proceeds, recording every 'bounce'.
            
        state_prefix : str or None
            The plugin can optionally save every state during a
            bounce. These can be used to seed simulations in other
            cells. This argument provides the file prefix for these
            saved states. If None, then no states will be written.
            
        Returns
        -------
        sim_openmm : Sim_openmm()
            The sim_openmm object, which contains everything needed
            to run an MMVT simulation within OpenMM.
            
        """
        super(MMVT_sim_openmm_factory, self).fill_generic_parameters(
            self.sim_openmm, model, anchor, output_filename)
        system, topology, positions, box_vectors = super(
            MMVT_sim_openmm_factory, self).create_openmm_system(
                self.sim_openmm, model, anchor)
        self.sim_openmm.system = system
        self.add_integrator(model, output_filename, state_prefix=state_prefix)
        super(MMVT_sim_openmm_factory, self).add_barostat(
            self.sim_openmm, model)
        super(MMVT_sim_openmm_factory, self).add_platform(
            self.sim_openmm, model)
        self.add_forces(model, anchor)
        self.add_simulation(model, topology, positions, box_vectors)
        return self.sim_openmm

def make_mmvt_boundary_definitions(cv, milestone):
    """
    Take a Collective_variable object and a particular milestone and
    return an OpenMM Force() object that the plugin can use to monitor
    crossings.
    
    Parameters
    ----------
    cv : Collective_variable()
        A Collective_variable object which contains all the information
        for the collective variable describine this variable. In fact,
        the boundaries are contours of the function described by cv.
        This variable contains information like the groups of atoms
        involved with the CV, and the expression which describes the
        function.
        
    milestone : Milestone()
        A Milestone object which describes the boundary between two
        Voronoi cells. This variable contains information like the 
        values of the variables which will be entered into the 
        Force() object.
        
    Returns
    -------
    myforce : openmm.Force()
        An OpenMM force object which does not affect atomic motion, but
        allows us to conveniently monitor a function of atomic 
        position.
    """
    myforce = cv.make_force_object()
    #mygroup_list = []
    #mygroup1 = myforce.addGroup(cv.group1)
    #mygroup_list.append(mygroup1)
    #mygroup2 = myforce.addGroup(cv.group2)
    #mygroup_list.append(mygroup2)
        
    myforce.setForceGroup(milestone.alias_index)
    
    variable_names_list = cv.add_parameters(myforce)
    cv.add_groups_and_variables(myforce, cv.get_variable_values_list(
                                    milestone))
    return myforce