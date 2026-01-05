ENDPOINTS: dict[str, str] = {
    "S_227_85": "outside_temperature",
    "S_259_85": "l1_supply_water_temperature",
    "S_272_85": "l1_valve_position",
    "S_89_85": "l1_supply_water_temperature_setback",
    "S_90_85": "l1_supply_water_greater_temperature_setback",
    "S_54_85": "l1_supply_water_minimum_temperature_setpoint",
    "S_55_85": "l1_supply_water_maximum_temperature_setpoint",
    "S_61_85": "l1_temperature_curve_-20_c_setpoint",
    "S_63_85": "l1_temperature_curve_0_c_setpoint",
    "S_65_85": "l1_temperature_curve_20_c_setpoint",
    "S_59_85": "operation_mode",
    "S_92_85": "valve_manual_setpoint",
    "S_135_85": "home_away_mode",
    "S_26_85": "trend_sampling_interval",
    "S_275_85": "l1_supply_water_temperature_setpoint",
    "S_134_85": "l1_room_temperature_fine_tuning",
    "S_0_0": "l1_heating_shutdown_status",
    "S_1000_0": "l1_temperature_level_status",
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
}
