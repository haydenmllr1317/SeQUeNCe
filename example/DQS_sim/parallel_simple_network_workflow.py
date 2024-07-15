from datetime import datetime
import json
import os
import multiprocessing
from itertools import repeat

from simple_network_workflow import dqs_sim, dqs_sim_parser


if __name__ == "__main__":
    args = dqs_sim_parser()

    # logging params
    LOGGING = False
    LOG_OUTPUT = "results/test_log.log"
    MODULE_TO_LOG = ["timeline", "purification"]
    VERBOSE_OUTPUT = False

    # open config files
    with open(args.config, 'r') as config:
        simulation_config = json.load(config)
    with open(args.net_config, 'r') as config:
        network_config = json.load(config)

    # simulation params
    num_trials = simulation_config["num_trials"]
    num_other_nodes = len(simulation_config["applications"]["end_nodes"])

    # set up storing data (paths)
    now = datetime.now()
    output_subdir = f"dqs_sim_{now.strftime("%Y-%m-%d_%H%M%S")}"
    output_path = os.path.join(args.output, output_subdir)
    os.mkdir(output_path)
    main_results_file = os.path.join(output_path, "main.json")

    # data storage object
    data_dict = {
        "simulation config": simulation_config,
        "network config": network_config,
        "results": []
    }

    # main simulation loop
    print(f"Running {num_trials} trials for config '{args.config}' and topology '{args.net_config}'")
    with multiprocessing.Pool(processes=num_trials) as pool:
        results = pool.starmap(dqs_sim, zip(repeat(args.config),
                                            repeat(args.net_config),
                                            repeat(output_path),
                                            range(num_trials)))

    # calculate trial distributions
    results_distribution = {"generated pairs": [0] * (num_other_nodes + 1),
                            "purified pairs": [0] * (num_other_nodes + 1),
                            "GHZ generated": 0}
    for trial_result in results:
        num_gen_pairs = len([node for node in trial_result["initial entangled states"]
                             if len(trial_result["initial entangled states"][node]) > 0])
        num_purified_pairs = len([node for node in trial_result["purified states"]
                                  if len(trial_result["purified states"][node]) > 0])
        results_distribution["generated pairs"][num_gen_pairs] += 1
        results_distribution["purified pairs"][num_purified_pairs] += 1
        if trial_result["GHZ state"]:
            results_distribution["GHZ generated"] += 1

    print("Finished trials.")

    # save data for trials
    data_dict["results"] = results
    data_dict["results distribution"] = results_distribution

    # save output data
    with open(main_results_file, 'w') as fp:
        json.dump(data_dict, fp,
                  indent=4)
