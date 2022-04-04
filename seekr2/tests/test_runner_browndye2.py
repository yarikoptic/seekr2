"""
test_runner_browndye2.py

test runner_browndye2.py script(s)
"""

import os
import glob
import pathlib # for 'touching' a nonexistent file

import seekr2.modules.runner_browndye2 as runner_browndye2

TEST_DIRECTORY = os.path.dirname(__file__)

def test_runner_browndye2_b_surface_mmvt(host_guest_mmvt_model):
    model = host_guest_mmvt_model
    bd_directory = os.path.join(host_guest_mmvt_model.anchor_rootdir, "b_surface")
    runner_browndye2.run_bd_top(model.browndye_settings.browndye_bin_dir, 
               bd_directory)
    runner_browndye2.run_nam_simulation(
        model.browndye_settings.browndye_bin_dir, bd_directory, 
        model.k_on_info.bd_output_glob)
    assert len(glob.glob(os.path.join(bd_directory, "results*.xml"))) > 0
    return

def test_runner_browndye2_b_surface_elber(host_guest_elber_model):
    model = host_guest_elber_model
    bd_directory = os.path.join(host_guest_elber_model.anchor_rootdir, "b_surface")
    runner_browndye2.run_bd_top(model.browndye_settings.browndye_bin_dir, 
               bd_directory)
    runner_browndye2.run_nam_simulation(
        model.browndye_settings.browndye_bin_dir, bd_directory, 
        model.k_on_info.bd_output_glob)
    assert len(glob.glob(os.path.join(bd_directory, "results*.xml"))) > 0
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

def test_modify_variables(host_guest_mmvt_model):
    """
    Test the function that modifies variables within the BD input xml.
    """
    bd_directory = os.path.join(
        host_guest_mmvt_model.anchor_rootdir,
        host_guest_mmvt_model.k_on_info.b_surface_directory)
    print("host_guest_mmvt_model.anchor_rootdir:", host_guest_mmvt_model.anchor_rootdir)
    assert os.path.exists(host_guest_mmvt_model.anchor_rootdir)
    print("bd_directory:", bd_directory)
    assert os.path.exists(bd_directory)
    runner_browndye2.run_bd_top(
        host_guest_mmvt_model.browndye_settings.browndye_bin_dir, 
        bd_directory, force_overwrite=True)
    runner_browndye2.modify_variables(
        bd_directory, host_guest_mmvt_model.k_on_info.bd_output_glob, 
        100, 4, 3456, "my_out.xml", restart=False,
        n_trajectories_per_output=25)
    # TODO: more checks here?
    return