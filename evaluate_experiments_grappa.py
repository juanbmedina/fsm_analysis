import os
import stat
import subprocess
import json
import ast
import numpy as np
import xml.etree.ElementTree as ET


# =========================================================
# MODIFY ARGOS FILE
# =========================================================
def modify_argos_file(argos_file, fsm_config, random_seed):
    """Insert FSM configuration and random seed into the ARGoS XML file."""
    tree = ET.parse(argos_file)
    root = tree.getroot()

    # Update FSM in <params>
    for params in root.findall(".//params"):
        params.set("fsm-config", fsm_config)

    # Update seed
    for experiment in root.findall(".//experiment"):
        experiment.set("random_seed", str(random_seed))

    xml_declaration = "<?xml version='1.0' ?>\n"
    new_content = xml_declaration + ET.tostring(root, encoding='unicode')

    with open(argos_file, "w") as f:
        f.write(new_content)


# =========================================================
# RUN ARGOS SIMULATION
# =========================================================
def run_argos(argos_file):
    """Execute ARGoS simulation headlessly."""
    script_path = "./argos.sh"
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"argos3 -c {argos_file}\n")

    os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)

    subprocess.run(
        ["bash", script_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# =========================================================
# READ SCORE.TXT
# =========================================================
def read_score(file_path, n_expected=None):
    """
    Read scores from score_file that has one score per line.
    Returns a Python list of parsed numbers (ints or floats if possible).
    If n_expected is provided, returns only the last n_expected entries.
    """
    scores = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                # try to parse as int, then float, else keep string
                try:
                    v = int(s)
                except ValueError:
                    try:
                        v = float(s)
                    except ValueError:
                        # fall back to literal_eval if the line contains repr-like values
                        try:
                            v = ast.literal_eval(s)
                        except Exception:
                            v = s
                scores.append(v)
    except FileNotFoundError:
        return []

    if n_expected is not None:
        # return only the last n_expected results (if file has more lines)
        return scores[-n_expected:]
    return scores



# =========================================================
# CLEAN SCORE FILE
# =========================================================
def clean_previous_data(score_file):
    """Clear previous results in score.txt."""
    with open(score_file, "w"):
        pass


# =========================================================
# RUN 10 RUNS FOR A LIST OF FSMs
# =========================================================
def evaluate_fsm_list(argos_file, score_file, fsm_list, n_runs):
    """
    Runs each FSM configuration n_runs times and returns a list of lists:
    [
        [10 scores for FSM #1],
        [10 scores for FSM #2],
        ...
    ]
    """
    mission_results = []

    for idx, fsm_config in enumerate(fsm_list):
        print(f"  → FSM #{idx}")

        clean_previous_data(score_file)

        # Run 10 seeds
        for seed in range(n_runs):
            modify_argos_file(argos_file, fsm_config, random_seed=100+seed)
            run_argos(argos_file)

        # Read 10 results
        scores = read_score(score_file)
        mission_results.append(scores)

    return mission_results


# =========================================================
# MAIN PIPELINE
# =========================================================
def main():
    fsm_path = "/home/robotmaster/experiments-loop-functions/data/fsm/fsm.json"
    score_file = "/home/robotmaster/experiments-loop-functions/data/scores/score.txt"

    with open(fsm_path, "r") as f:
        fsm_data = json.load(f)

    n_runs = 10

    # fsm_data structure:
    # {
    #   "Aggregation-1 (1 groups)": {
    #       "Grappa-1": [[scoreStr, fsmStr, []], ...]
    #   },
    #   ...
    # }
    for mission_name, behaviours in fsm_data.items():
        print(f"\n=== Mission: {mission_name} ===")

        # Extract mission number: "Aggregation-1" → "1"
        mission_number = mission_name.split()[0].split("-")[1]

        # Path to correct ARGoS file
        argos_file = (
            f"/home/robotmaster/experiments-loop-functions/scenarios/"
            f"heterogeneity/aggregation{mission_number}.argos"
        )

        for behaviour_name, fsm_entries in behaviours.items():
            print(f"\n→ Behaviour: {behaviour_name}")

            # Extract only FSM strings
            fsm_strings = [entry[1] for entry in fsm_entries]

            # Evaluate them
            results = evaluate_fsm_list(argos_file, score_file, fsm_strings, n_runs)

            # Insert results back into JSON structure and save JSON immediately
            for entry, scores in zip(fsm_entries, results):
                entry[2] = scores

                # Save JSON after each FSM is completed
                with open(fsm_path, "w") as f:
                    json.dump(fsm_data, f, indent=4)

                print("    ✓ Saved results for one FSM")


    # Save updated JSON
    with open(fsm_path, "w") as f:
        json.dump(fsm_data, f, indent=4)

    print("\n✔ All experiments completed. Results saved to fsm.json")


# =========================================================
# RUN SCRIPT
# =========================================================
if __name__ == "__main__":
    main()
