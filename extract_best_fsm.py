import glob
import re
import json

missions_dict = {}

for n in range(1,7):
    # === 1. Filter stdout files by mission code ===
    file_filter = re.compile(fr'.*({n}g1s).*\.stdout$')   # captures mission code

    target_dir = "/home/juanbmedina/argos3-heterogeneity/experiments-loop-functions/data/AutoMoDe-Grappa-Unbalanced/Grappa/"
    mission_name = "Grappa-Unb"

    stdout_files = [f for f in glob.glob(f"{target_dir}*.stdout") if file_filter.match(f)]
    print("Filtered files:", len(stdout_files))

    # Pattern to extract FSM line
    pattern = re.compile(r'^\s*\d+\s+(--ngroups.*)')



    # === 2. Extract ONLY the next line after the header ===
    for fname in stdout_files:
        raw_code = file_filter.match(fname).group(1)   # e.g. "1g1s"
        mission_code = f"{mission_name}-{raw_code}"  

        if mission_code not in missions_dict:
            missions_dict[mission_code] = []

        with open(fname, 'r') as f:
            lines = f.readlines()

            for i, line in enumerate(lines):
                if line.startswith("# Best configurations as commandlines"):
                    # take EXACTLY the next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        match = pattern.match(next_line)
                        if match:
                            missions_dict[mission_code].append(match.group(1))
                    break  # do NOT search more blocks in this file

# === 3. Build final JSON ===
output_json = {
    "missions": [
        { mission: missions_dict[mission] }
        for mission in missions_dict
    ]
}

# === 4. Write JSON file ===
with open(f"fsm/{mission_name}_fsm.json", "w") as f:
    json.dump(output_json, f, indent=4)

print("JSON written to missions_fsm.json")
