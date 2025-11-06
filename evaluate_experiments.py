import os
import stat
import subprocess
import json
import ast
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def modify_argos_file(argos_file, fsm_config, random_seed):
    """Modify the .argos XML file to update the FSM configuration."""
    tree = ET.parse(argos_file)
    root = tree.getroot()
    
    for params in root.findall(".//params"):
        params.set("fsm-config", fsm_config)

    for experiment in root.findall(".//experiment"):
        experiment.set("random_seed", str(100+random_seed))

    xml_declaration = "<?xml version='1.0' ?>\n"
    modified_content = xml_declaration + ET.tostring(root, encoding='unicode')
    
    with open(argos_file, "w") as f:
        f.write(modified_content)

#################################3

def run_argos(argos_file):
    """Run ARGoS simulation with the given configuration."""
    script_path = "./argos.sh"
    with open(script_path, 'w+') as f:
        f.write("#!/bin/bash\n")
        f.write(f"argos3 -c {argos_file}\n")
    
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IEXEC)
    
    subprocess.run(["bash", script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def read_score(file_path):
    """Read the score from the score.txt file."""
    data_score = []
    try:
        with open(file_path, 'r') as f:
            for score in f.readlines(): 
                data_score.append(ast.literal_eval(score[:-1]))
            return np.array(data_score)
    except FileNotFoundError:
        return None
    
def clean_previous_data():
    with open("/home/robotmaster/experiments-loop-functions/data/score_cho-6s.txt", "w") as file:
        pass 


def plot_boxplots(data, plot_title, number_plots, plots_ticks = []):
    plt.boxplot(data, notch=True)
    plt.ticklabel_format(style='plain', axis='y', scilimits=(0,0))
    plt.title(plot_title, fontsize=20, family='sans-serif', pad=30)
    plt.xticks(np.arange(1, number_plots + 1),plots_ticks, fontsize=15)
    plt.yticks(fontsize=15)

def plot_boxplots2(data, plot_title, number_plots, plots_ticks, yticks, ylim):
    gray_color = 'gray'
    # Crear el boxplot con color interior gris
    box = plt.boxplot(data, notch=True, patch_artist=True)

    # Cambiar color del interior de los boxplots
    for patch in box['boxes']:
        patch.set(facecolor='lightgray') 
    plt.ticklabel_format(style='plain', axis='y', scilimits=(0,0))
    plt.title(plot_title, fontsize=20, family='sans-serif', pad=30)
    plt.xticks(np.arange(1, number_plots + 1),plots_ticks, fontsize=15, rotation=45)
    plt.yticks(yticks,fontsize=15)
    plt.ylim(ylim[0], ylim[1])
    plt.xlabel("Instances of control software", fontsize=18, labelpad=30)
    plt.ylabel("Scores (10 runs)", fontsize=18, labelpad=30)
    

def run_experiments(argos_file,score_file, mission_name, n_experiments):
    """Main function to automate the FSM testing process."""

    with open("/home/robotmaster/experiments-loop-functions/data/missions.json", "r") as f:
        fsm_configs = json.load(f)

    m = 0

    clean_previous_data()
 

    for fsm_config in fsm_configs["missions"][0][mission_name]:
        print(f"Running simulation for {mission_name}, fsm {m}...")
        n = 0
        # run experiments
        for i in range(n_experiments):
            modify_argos_file(argos_file, fsm_config, random_seed=int(n))
           

            run_argos(argos_file)

            n += 1
        # Save data
        m += 1
    return read_score(score_file)


if __name__ == "__main__":
    score_dict = {}
    argos_file = "/home/robotmaster/experiments-loop-functions/scenarios/heterogeneity/aggregation.argos"
    score_file = "/home/robotmaster/experiments-loop-functions/data/score_cho-6s.txt"
    mission_names = ["cho-6s", "cho-hom", "grappa-het"]
    n_experiments = 1

    # for mission_name in mission_names:
    #     score = run_experiments(argos_file, score_file, mission_name, n_experiments)
    #     score_dict[mission_name] = score.reshape(10,n_experiments)
    #     print(score_dict)
    mission_name = "cho-hom"
    score = run_experiments(argos_file, score_file, mission_name, n_experiments)

    
    # with open("/home/robotmaster/experiments-loop-functions/data/total_score.txt", "w") as f:
    #     f.write(str(score_dict))   # write as JSON