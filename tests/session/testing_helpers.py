BLANK_PERSISTENCE = """
{
    "persistence": {
        "machine": {
            "model": "Mass Portal XD20",
            "buildarea_maxdim1": 200,
            "buildarea_maxdim2": 200,
            "form": "elliptic",
            "temperature_controllers": {
                "extruder": {
                    "tool": "T0",
                    "temperature_max": 350,
                    "part_cooling": true,
                    "nozzle": {
                        "size_id": 0.8
                    }
                },
                "chamber": {
                    "tool": "",
                    "gcode_command": "M141 S$temp",
                    "temperature_max": 80,
                    "chamber_heatable": false
                },
                "printbed": {
                    "printbed_heatable": true
                }
            }
        },
        "material": {
            "size_od": 1.75,
            "name": "FormFutura Premium M"
        },
        "session": {
            "uid": 95,
            "target": "mechanical_strength",
            "test_number": "10",
            "min_max_parameter_one": [],
            "min_max_parameter_two": [
                10.0,
                30.0
            ],
            "min_max_parameter_three": [
                60.0,
                120.0
            ],
            "test_type": "A",
            "user_id": "user name",
            "offset": [
                0,
                0
            ],
            "slicer": "Prusa",
            "previous_tests": [
                {
                    "comments": 0,
                    "datetime_info": "2019-11-13 14:13:04",
                    "executed": true,
                    "extruded_filament_mm": 1183.18,
                    "parameter_one_name": "first-layer track height",
                    "parameter_one_precision": "{:.2f}",
                    "parameter_one_units": "mm",
                    "parameter_three_name": null,
                    "parameter_two_name": "first-layer printing speed",
                    "parameter_two_precision": "{:.0f}",
                    "parameter_two_units": "mm/s",
                    "selected_parameter_one_value": 0.33,
                    "selected_parameter_two_value": 17.0,
                    "selected_volumetric_flow-rate_value": 0,
                    "test_name": "first-layer track height vs first-layer printing speed",
                    "test_number": "01",
                    "tested_parameter_one_values": [
                        0.22,
                        0.26,
                        0.29,
                        0.33,
                        0.37,
                        0.4,
                        0.44
                    ],
                    "tested_parameter_two_values": [
                        10.0,
                        17.0,
                        23.0,
                        30.0
                    ],
                    "tested_parameters": [
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                0.08000000000000002,
                                0.8
                            ],
                            "name": "first-layer track height",
                            "precision": "{:.2f}",
                            "programmatic_name": "track_height_raft",
                            "units": "mm",
                            "values": [
                                0.22,
                                0.25666666666666665,
                                0.29333333333333333,
                                0.33,
                                0.3666666666666667,
                                0.4033333333333333,
                                0.44
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": "Typically, the values in the range of 5-15 mm/s are adequate for printing flexible materials; for harder materials, you can go up to 10-30 mm/s.",
                            "min_max": [
                                1,
                                140
                            ],
                            "name": "first-layer printing speed",
                            "precision": "{:.0f}",
                            "programmatic_name": "speed_printing_raft",
                            "units": "mm/s",
                            "values": [
                                10.0,
                                16.666666666666668,
                                23.333333333333336,
                                30.0
                            ]
                        }
                    ],
                    "tested_volumetric_flow-rate_values": [
                        [
                            1.656,
                            1.912,
                            2.162,
                            2.406,
                            2.645,
                            2.878,
                            3.105
                        ],
                        [
                            2.76,
                            3.187,
                            3.603,
                            4.01,
                            4.408,
                            4.796,
                            5.174
                        ],
                        [
                            3.864,
                            4.461,
                            5.045,
                            5.615,
                            6.171,
                            6.714,
                            7.244
                        ],
                        [
                            4.968,
                            5.736,
                            6.486,
                            7.219,
                            7.934,
                            8.633,
                            9.314
                        ]
                    ],
                    "validated": true
                },
                {
                    "comments": 0,
                    "datetime_info": "2019-11-15 09:59:11",
                    "executed": true,
                    "extruded_filament_mm": 3943.753,
                    "parameter_one_name": "extrusion temperature",
                    "parameter_one_precision": "{:.0f}",
                    "parameter_one_units": "degC",
                    "parameter_three_name": null,
                    "parameter_two_name": "printing speed",
                    "parameter_two_precision": "{:.0f}",
                    "parameter_two_units": "mm/s",
                    "selected_parameter_one_value": 272.0,
                    "selected_parameter_two_value": 23.0,
                    "selected_volumetric_flow-rate_value": 0,
                    "test_name": "extrusion temperature vs printing speed",
                    "test_number": "03",
                    "tested_parameter_one_values": [
                        260.0,
                        266.0,
                        272.0,
                        278.0,
                        285.0,
                        291.0,
                        297.0
                    ],
                    "tested_parameter_two_values": [
                        10.0,
                        17.0,
                        23.0,
                        30.0
                    ],
                    "tested_parameters": [
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                30,
                                350
                            ],
                            "name": "extrusion temperature",
                            "precision": "{:.0f}",
                            "programmatic_name": "temperature_extruder",
                            "units": "degC",
                            "values": [
                                260.0,
                                266.0,
                                272.0,
                                278.0,
                                285.0,
                                291.0,
                                297.0
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                1,
                                140
                            ],
                            "name": "printing speed",
                            "precision": "{:.0f}",
                            "programmatic_name": "speed_printing",
                            "units": "mm/s",
                            "values": [
                                10.0,
                                16.666666666666668,
                                23.333333333333336,
                                30.0
                            ]
                        }
                    ],
                    "tested_volumetric_flow-rate_values": [
                        [
                            1.514,
                            1.514,
                            1.514,
                            1.514,
                            1.514,
                            1.514,
                            1.514
                        ],
                        [
                            2.524,
                            2.524,
                            2.524,
                            2.524,
                            2.524,
                            2.524,
                            2.524
                        ],
                        [
                            3.533,
                            3.533,
                            3.533,
                            3.533,
                            3.533,
                            3.533,
                            3.533
                        ],
                        [
                            4.542,
                            4.542,
                            4.542,
                            4.542,
                            4.542,
                            4.542,
                            4.542
                        ]
                    ],
                    "validated": true
                },
                {
                    "comments": 0,
                    "datetime_info": "2019-11-15 09:59:23",
                    "executed": true,
                    "extruded_filament_mm": 3153.209,
                    "parameter_one_name": "extrusion temperature",
                    "parameter_one_precision": "{:.0f}",
                    "parameter_one_units": "degC",
                    "parameter_three_name": "retraction speed",
                    "parameter_three_precision": "{:.0f}",
                    "parameter_three_units": "mm/s",
                    "parameter_two_name": "retraction distance",
                    "parameter_two_precision": "{:.3f}",
                    "parameter_two_units": "mm",
                    "selected_parameter_one_value": 0,
                    "selected_parameter_three_value": 0,
                    "selected_parameter_two_value": 0,
                    "selected_volumetric_flow-rate_value": 3.483,
                    "test_name": "extrusion temperature vs retraction distance",
                    "test_number": "08",
                    "tested_parameter_one_values": [
                        267.0,
                        269.0,
                        270.0,
                        272.0,
                        274.0,
                        275.0,
                        277.0
                    ],
                    "tested_parameter_three_values": [
                        60.0,
                        120.0
                    ],
                    "tested_parameter_two_values": [
                        0.0,
                        1.333,
                        2.667,
                        4.0
                    ],
                    "tested_parameters": [
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                30,
                                350
                            ],
                            "name": "extrusion temperature",
                            "precision": "{:.0f}",
                            "programmatic_name": "temperature_extruder",
                            "units": "degC",
                            "values": [
                                267.0,
                                268.6666666666667,
                                270.3333333333333,
                                272.0,
                                273.6666666666667,
                                275.3333333333333,
                                277.0
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                0,
                                20
                            ],
                            "name": "retraction distance",
                            "precision": "{:.3f}",
                            "programmatic_name": "retraction_distance",
                            "units": "mm",
                            "values": [
                                0.0,
                                1.3333333333333333,
                                2.6666666666666665,
                                4.0
                            ]
                        },
                        {
                            "active": true,
                            "hint_active": null,
                            "min_max": [
                                1,
                                140
                            ],
                            "name": "retraction speed",
                            "precision": "{:.0f}",
                            "programmatic_name": "retraction_speed",
                            "units": "mm/s",
                            "values": [
                                60.0,
                                120.0
                            ]
                        }
                    ],
                    "tested_volumetric_flow-rate_values": [
                        3.483
                    ],
                    "validated": false
                }
            ]
        },
        "settings": {
            "speed_travel": 140,
            "raft_density": 100,
            "speed_printing_raft": 17,
            "track_height": 0.2,
            "track_height_raft": 0.33,
            "track_width": 0.8,
            "track_width_raft": 0.8,
            "extrusion_multiplier": 1.0,
            "temperature_extruder": 272,
            "temperature_extruder_raft": 260,
            "retraction_restart_distance": 0.0,
            "retraction_speed": 100,
            "retraction_distance": 0.0,
            "bridging_extrusion_multiplier": 1.0,
            "bridging_part_cooling": 0,
            "bridging_speed_printing": 0,
            "speed_printing": 23,
            "coasting_distance": 0.0,
            "critical_overhang_angle": 27,
            "temperature_printbed_setpoint": 90,
            "temperature_chamber_setpoint": 0,
            "part_cooling_setpoint": 0
        }
    }
}
"""


