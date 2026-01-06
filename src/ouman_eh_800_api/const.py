ENDPOINTS: dict[str, str] = {
    "S_227_85": "outside_temperature",
    "S_135_85": "home_away_mode",
    # Value S_222_85 is updated at the same time as S_135_85 with the same value for some reason
    "S_222_85": "home_away_update_sync",
    "S_26_85": "trend_sampling_interval",

    "S_0_0": "l1_heating_shutdown_status",
    "S_1000_0": "l1_temperature_level_status_text",
    "S_54_85": "l1_supply_water_minimum_temperature_setpoint",
    "S_55_85": "l1_supply_water_maximum_temperature_setpoint",
    "S_59_85": "l1_operation_mode",
    "S_61_85": "l1_temperature_curve_-20_c_setpoint",
    "S_63_85": "l1_temperature_curve_0_c_setpoint",
    "S_65_85": "l1_temperature_curve_20_c_setpoint",
    "S_89_85": "l1_supply_water_temperature_setback",
    "S_90_85": "l1_supply_water_greater_temperature_setback",
    "S_92_85": "l1_valve_manual_setpoint",
    "S_102_85": "l1_room_temperature_fine_tuning_with_sensor",
    "S_131_85": "l1_circuit_name",
    "S_134_85": "l1_room_temperature_fine_tuning",
    "S_259_85": "l1_supply_water_temperature",
    "S_261_85": "l1_room_temperature",
    "S_272_85": "l1_valve_position",
    "S_275_85": "l1_supply_water_temperature_setpoint",
    "S_278_85": "l1_room_temperature_setpoint",

    ## not verified start ##
    "S_274_85": "l1_room_sensor_potentiometer",
    "S_307_85": "l2_room_sensor_potentiometer",

    # L2 (Secondary Loop)
    "S_1001_0": "l2_temperature_level_status_text",
    "S_141_85": "l2_supply_water_minimum_temperature_setpoint",
    "S_142_85": "l2_supply_water_maximum_temperature_setpoint",
    "S_146_85": "l2_operation_mode",
    "S_148_85": "l2_temperature_curve_-20_c_setpoint",
    "S_150_85": "l2_temperature_curve_0_c_setpoint",
    "S_152_85": "l2_temperature_curve_20_c_setpoint",
    "S_176_85": "l2_supply_water_temperature_setback",
    "S_177_85": "l2_supply_water_greater_temperature_setback",
    "S_179_85": "l2_valve_manual_setpoint",
    "S_189_85": "l2_room_temperature_fine_tuning_with_sensor",
    "S_218_85": "l2_circuit_name",
    "S_221_85": "l2_room_temperature_fine_tuning",
    "S_293_85": "l2_supply_water_temperature",
    "S_295_85": "l2_room_temperature",
    "S_310_85": "l2_supply_water_temperature_setpoint",
    "S_313_85": "l2_room_temperature_setpoint",

    # System / Configuration
    "S_140_85": "l2_installed_status",
    "S_261_111": "l1_room_sensor_installed",
    "S_295_111": "l2_room_sensor_installed",
    "S_1002_85": "relay_configuration_type",
    "S_1004_0": "relay_status_text_2",
    "S_1004_85": "relay_status_text",
    ## not verified end ##
}

ENDPOINT_VALUE_MAPPING: dict[str, dict[str, str]] = {
    "S_59_85": {
        "0": "automatic",
        "1": "temperature_setback",
        "2": "greater_temperature_setback",
        "3": "normal_temperature",
        "5": "shutdown",
        "6": "manual_valve_control",
    },
    "S_135_85": {
        "0": "home",
        "1": "away",
        "2": "home_away_off",
    },

    ## not verified start ##
    # L2 uses the same mapping as L1 (S_59_85)
    "S_146_85": {
        "0": "automatic",
        "1": "temperature_setback",
        "2": "greater_temperature_setback",
        "3": "normal_temperature",
        "5": "shutdown",
        "6": "manual_valve_control",
    },
    ## not verified end ##
}
