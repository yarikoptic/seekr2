"""
test_runner_browndye2.py

test runner_browndye2.py script(s)
"""

import os
import glob
import pathlib # for 'touching' a nonexistent file
import shutil

import seekr2.tests.make_test_model as make_test_model
import seekr2.modules.common_sim_browndye2 as sim_browndye2
import seekr2.modules.runner_browndye2 as runner_browndye2

TEST_DIRECTORY = os.path.dirname(__file__)

def test_runner_browndye2_b_surface_default(tmp_path):
    model = make_test_model.make_test_model(tmp_path)
    b_surface_abs_path = os.path.join(tmp_path, "b_surface")
    receptor_pqr_filename = os.path.join(
        b_surface_abs_path, model.browndye_settings.receptor_pqr_filename)
    ligand_pqr_filename = os.path.join(
        b_surface_abs_path, model.browndye_settings.ligand_pqr_filename)
    bd_milestone = model.k_on_info.bd_milestones[0]
    
    ghost_index_rec = \
                sim_browndye2.add_ghost_atom_to_pqr_from_atoms_center_of_mass(
                    receptor_pqr_filename, bd_milestone.receptor_indices)
    ghost_index_lig = \
                sim_browndye2.add_ghost_atom_to_pqr_from_atoms_center_of_mass(
                    ligand_pqr_filename, bd_milestone.ligand_indices)
    assert ghost_index_rec == 148
    assert ghost_index_lig == 16
    
    receptor_xml_filename = sim_browndye2.make_pqrxml(receptor_pqr_filename)
    ligand_xml_filename = sim_browndye2.make_pqrxml(ligand_pqr_filename)
    
    debye_length, reaction_filename = \
        runner_browndye2.make_browndye_input_xml(
        model, tmp_path, receptor_xml_filename, ligand_xml_filename,
        model.k_on_info.b_surface_num_trajectories)
    model.browndye_settings.debye_length = debye_length
    assert os.path.exists(os.path.join(b_surface_abs_path, "apbs_input.xml"))
    assert os.path.exists(os.path.join(b_surface_abs_path, "input.xml"))
    abs_reaction_path = os.path.join(b_surface_abs_path, 
                                     reaction_filename)
    runner_browndye2.make_browndye_reaction_xml(model, abs_reaction_path)
    assert os.path.exists(abs_reaction_path)
    bd_directory = b_surface_abs_path
    runner_browndye2.run_bd_top(model.browndye_settings.browndye_bin_dir, 
               bd_directory)
    #runner_browndye2.modify_variables(bd_directory, 10000)
    runner_browndye2.run_nam_simulation(
        model.browndye_settings.browndye_bin_dir, bd_directory, 
        model.k_on_info.bd_output_glob)
    #assert os.path.exists(os.path.join(b_surface_abs_path, "results.xml"))
    assert len(glob.glob(os.path.join(b_surface_abs_path, "results*.xml"))) > 0
    
    bd_milestone_abs_path = os.path.join(tmp_path, bd_milestone.directory)
    assert os.path.exists(bd_milestone_abs_path)
    
    traj_xml_src_filename = os.path.join(TEST_DIRECTORY, "data/traj_test.xml")
    traj_xml_dest_filename = os.path.join(bd_directory, "traj1_0.xml")
    shutil.copyfile(traj_xml_src_filename, traj_xml_dest_filename)
    traj_index_src_filename = os.path.join(TEST_DIRECTORY, 
                                           "data/traj_test.index.xml")
    traj_index_dest_filename = os.path.join(bd_directory, 
                                            "traj1_0.index.xml")
    shutil.copyfile(traj_index_src_filename, traj_index_dest_filename)
    bd_milestone.outer_milestone.index = 13
    
    lig_pqr_filenames, rec_pqr_filenames = runner_browndye2.extract_bd_surface(
        model, bd_milestone, 2)
    bd_directory_list = runner_browndye2.make_fhpd_directories(
        model, bd_milestone, lig_pqr_filenames, rec_pqr_filenames)
    
    for bd_directory in bd_directory_list:
        runner_browndye2.run_bd_top(model.browndye_settings.browndye_bin_dir, 
                           bd_directory)
        runner_browndye2.modify_variables(bd_directory, 
                                          model.k_on_info.bd_output_glob, 
                                          n_trajectories=10)
        runner_browndye2.run_nam_simulation(
            model.browndye_settings.browndye_bin_dir, bd_directory, 
            model.k_on_info.bd_output_glob)
    
    runner_browndye2.combine_fhpd_results(
        model, bd_milestone, bd_directory_list)
    assert os.path.exists(os.path.join(bd_milestone_abs_path, "results.xml"))
    
    return

def test_make_empty_pqrxml(tmp_path):
    """
    Test the function that makes an empty pqrxml file in order to
    write encounter complexes of one molecule at a time.
    """
    runner_browndye2.make_empty_pqrxml(tmp_path, filename="empty.pqrxml")
    file_path = os.path.join(tmp_path, "empty.pqrxml")
    assert os.path.exists(file_path)
    return

def test_cleanse_bd_outputs(tmp_path):
    """
    Test the utility that 'cleanses' BD directories, that is, it
    removes files generated by old simulations.
    """
    directory = os.path.join(tmp_path, "cleanse_bd")
    if not os.path.exists(directory):
        os.mkdir(directory)
    files_exist1 = runner_browndye2.cleanse_bd_outputs(directory)
    assert not files_exist1
    results_filename = os.path.join(directory, "results1.xml")
    pathlib.Path(results_filename).touch()
    simulation_filename = os.path.join(directory, "rec_lig_simulation.xml")
    pathlib.Path(simulation_filename).touch()
    traj_filename = os.path.join(directory, "traj0_0.xml")
    pathlib.Path(traj_filename).touch()
    assert len(os.listdir(directory)) > 0
    files_exist2 = runner_browndye2.cleanse_bd_outputs(directory, 
                                                       check_mode=False)
    assert files_exist2
    assert len(os.listdir(directory)) == 0
    return

def test_modify_variables(tryp_ben_mmvt_model):
    """
    Test the function that modifies variables within the BD input xml.
    """
    bd_directory = os.path.join(
        tryp_ben_mmvt_model.anchor_rootdir,
        tryp_ben_mmvt_model.k_on_info.b_surface_directory)
    runner_browndye2.run_bd_top(
        tryp_ben_mmvt_model.browndye_settings.browndye_bin_dir, 
        bd_directory)
    runner_browndye2.modify_variables(
        bd_directory, tryp_ben_mmvt_model.k_on_info.bd_output_glob, 
        100, 4, 3456, "my_out.xml", restart=False,
        n_trajectories_per_output=25)
    return

def test_make_proc_file_last_frame(tmp_path):
    """
    Test the function that extracts the last frame of the BD simulation
    trajectory.
    """
    input_filename = os.path.join(TEST_DIRECTORY, "data/proc_traj_test.xml")
    output_filename = os.path.join(tmp_path, "proc_last.xml")
    runner_browndye2.make_proc_file_last_frame(
        input_filename, output_filename, "dummy1", "dummy2")
    assert os.path.exists(output_filename)
    return

def test_make_big_fhpd_trajectory(tmp_path):
    """
    Test the function that combines all FHPD structures into a single
    trajectory PDB.
    """
    lig_pqr_filename = os.path.join(TEST_DIRECTORY, 
                                    "data/tryp_ben_encounter_lig.pqr")
    lig_pqr_filenames = [lig_pqr_filename, lig_pqr_filename]
    rec_pqr_filename = os.path.join(TEST_DIRECTORY, 
                                    "data/tryp_ben_encounter_rec.pqr")
    rec_pqr_filenames = [rec_pqr_filename, rec_pqr_filename]
    
    runner_browndye2.make_big_fhpd_trajectory(
        tmp_path, lig_pqr_filenames, rec_pqr_filenames)
    return