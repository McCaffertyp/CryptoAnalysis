from enum import Enum
from bisect import bisect_left
from utils import adjust_hours_and_format_datetime, sort_dict, get_random_number, log

RELATIVE_MARGINS_RIGHT = {
    "LUNC": 0.000001,
    "FET": 0.01
}
WANTED_GROUP_COUNT = 100
USED_GROUP_COUNT = 100
WANTED_RECENT_COUNT = 200
USED_RECENT_COUNT = 200


def run_predictions(coin_abbreviation: str, coin_prices: list, predict_future_hours: int, most_recent_time):
    print("Working on creating predictions for the next {0} hour(s)".format(predict_future_hours))
    hour_prediction = predict_next_hour(coin_abbreviation, coin_prices)
    hour_prediction_pattern = predict_next_hour(coin_abbreviation, coin_prices, True)
    print("Datetime {0} prediction: {1:.8f}".format(adjust_hours_and_format_datetime(most_recent_time, 1), hour_prediction))
    print("Datetime {0} prediction: {1:.8f}".format(adjust_hours_and_format_datetime(most_recent_time, 1), hour_prediction_pattern))
    for i in range(1, predict_future_hours):
        coin_prices.append(hour_prediction)
        hour_prediction = predict_next_hour(coin_abbreviation, coin_prices)
        adjusted_hour = adjust_hours_and_format_datetime(most_recent_time, i + 1)
        print("Datetime {0} prediction: {1:.8f}".format(adjusted_hour, hour_prediction))


def predict_next_hour(
        coin_abbreviation: str,
        coin_prices: list,
        use_patterning: bool = False
) -> float:
    log("predict_next_hour_weights_method", "Working on creating prediction for new hour")
    cp_decimal_weights = {
        DecimalCategory.PL_FIVE: 0, DecimalCategory.PL_FOUR: 0, DecimalCategory.PL_THREE: 0,
        DecimalCategory.PL_TWO: 0, DecimalCategory.PL_ONE: 0, DecimalCategory.NL_FIVE: 0,
        DecimalCategory.NL_FOUR: 0, DecimalCategory.NL_THREE: 0, DecimalCategory.NL_TWO: 0,
        DecimalCategory.NL_ONE: 0, DecimalCategory.ZERO: 0, DecimalCategory.PR_ONE: 0,
        DecimalCategory.PR_TWO: 0, DecimalCategory.PR_THREE: 0, DecimalCategory.PR_FOUR: 0,
        DecimalCategory.PR_FIVE: 0, DecimalCategory.PR_SIX: 0, DecimalCategory.PR_SEVEN: 0,
        DecimalCategory.PR_EIGHT: 0, DecimalCategory.PR_NINE: 0, DecimalCategory.NR_ONE: 0,
        DecimalCategory.NR_TWO: 0, DecimalCategory.NR_THREE: 0, DecimalCategory.NR_FOUR: 0,
        DecimalCategory.NR_FIVE: 0, DecimalCategory.NR_SIX: 0, DecimalCategory.NR_SEVEN: 0,
        DecimalCategory.NR_EIGHT: 0, DecimalCategory.NR_NINE: 0
    }
    cp_fluctuation_weights = {
        CPFluctuation.INCREASE: 0, CPFluctuation.DECREASE: 0, CPFluctuation.SAME: 0, CPFluctuation.UNKNOWN: 0
    }

    coin_price_weights = dict()

    for i in range(len(coin_prices) - 1):
        cp_now = coin_prices[i]
        cp_next = coin_prices[i + 1]
        cp_diff = cp_now - cp_next
        cp_diff_category = get_cp_diff_category(cp_diff)
        cp_diff_category_value = cp_decimal_weights.get(cp_diff_category)
        cp_decimal_weights[cp_diff_category] = cp_diff_category_value + 1
        cp_fluctuation = get_diff_fluctuation(cp_diff_category)
        # cp_fluctuation_value = cp_fluctuation_weights.get(cp_fluctuation)
        # cp_fluctuation_weights[cp_fluctuation] = cp_fluctuation_value + 1
        cp_dict = {
            "CP Difference Category": cp_diff_category,
            "CP Difference": cp_diff,
            "CP Fluctuation": cp_fluctuation
        }
        coin_price_weights[cp_now] = cp_dict

    most_recent_price = coin_prices[-1]

    nearest_weights = get_nearest_weights(most_recent_price, coin_price_weights)
    recent_weights = get_recent_weights(coin_price_weights)

    nearest_and_recent_weights = nearest_weights + recent_weights
    if not use_patterning:
        for weight in nearest_and_recent_weights:
            # print("weight: {0}".format(weight))
            cp_fluctuation = weight["CP Fluctuation"]
            cp_fluctuation_value = cp_fluctuation_weights.get(cp_fluctuation)
            cp_fluctuation_weights[cp_fluctuation] = cp_fluctuation_value + 1

        highest_cp_fluctuation = get_highest_cp_fluctuation(cp_fluctuation_weights)

        nearest_weights_difference_values = get_nearest_weights_difference_values(
            nearest_weights,
            highest_cp_fluctuation
        )

        recent_weights_difference_values = get_recent_weights_difference_values(
            nearest_weights,
            highest_cp_fluctuation
        )

        price_prediction = get_price_prediction(
            most_recent_price,
            nearest_weights_difference_values,
            recent_weights_difference_values,
            len(nearest_weights_difference_values)
        )

        # print("{0:.8f}".format(most_recent_price))
        # print("{0:.8f}".format(price_prediction))

        return price_prediction

    else:
        # Use patterning
        most_likely_fluctuation = get_fluctuation_from_pattern(coin_prices)

        nearest_weights_difference_values = get_nearest_weights_difference_values(
            nearest_weights,
            most_likely_fluctuation
        )

        recent_weights_difference_values = get_recent_weights_difference_values(
            nearest_weights,
            most_likely_fluctuation
        )

        price_prediction = get_price_prediction(
            most_recent_price,
            nearest_weights_difference_values,
            recent_weights_difference_values,
            len(nearest_weights_difference_values)
        )

        # print("{0:.8f}".format(most_recent_price))
        # print("{0:.8f}".format(price_prediction))

        return price_prediction


def get_fluctuation_from_pattern(coin_prices: list):
    cps_fluctuation = []
    for i in range(len(coin_prices) - 1):
        cp_now = coin_prices[i]
        cp_next = coin_prices[i + 1]
        cp_diff = cp_now - cp_next
        cp_diff_category = get_cp_diff_category(cp_diff)
        cps_fluctuation.append({"CP Difference": cp_diff, "CP Fluctuation": get_diff_fluctuation(cp_diff_category)})

    global USED_RECENT_COUNT
    if WANTED_RECENT_COUNT > len(cps_fluctuation):
        USED_RECENT_COUNT = len(cps_fluctuation)

    current_increase_run = 0
    longest_increase_run = 0
    current_decrease_run = 0
    longest_decrease_run = 0
    current_same_run = 0
    longest_same_run = 0
    fluctuation_runs = dict()

    for i in range(USED_RECENT_COUNT):
        cp_dict = cps_fluctuation[i]
        cp_fluctuation = cp_dict.get("CP Fluctuation")

        if cp_fluctuation is CPFluctuation.INCREASE:
            current_increase_run += 1
            if current_decrease_run > 0:
                decrease_run_value = fluctuation_runs.get("d{0}".format(current_decrease_run))
                if decrease_run_value is None:
                    fluctuation_runs["d{0}".format(current_decrease_run)] = 1
                else:
                    fluctuation_runs["d{0}".format(current_decrease_run)] = decrease_run_value + 1
                if current_decrease_run > longest_decrease_run:
                    longest_decrease_run = current_decrease_run
                current_decrease_run = 0
            if current_same_run > 0:
                same_run_value = fluctuation_runs.get("d{0}".format(current_same_run))
                if same_run_value is None:
                    fluctuation_runs["d{0}".format(current_same_run)] = 1
                else:
                    fluctuation_runs["d{0}".format(current_same_run)] = same_run_value + 1
                if current_same_run > longest_same_run:
                    longest_same_run = current_same_run
                current_same_run = 0

        elif cp_fluctuation is CPFluctuation.DECREASE:
            current_decrease_run += 1
            if current_increase_run > 0:
                increase_run_value = fluctuation_runs.get("i{0}".format(current_increase_run))
                if increase_run_value is None:
                    fluctuation_runs["i{0}".format(current_increase_run)] = 1
                else:
                    fluctuation_runs["i{0}".format(current_increase_run)] = increase_run_value + 1
                if current_increase_run > longest_increase_run:
                    longest_increase_run = current_increase_run
                current_increase_run = 0
            if current_same_run > 0:
                same_run_value = fluctuation_runs.get("d{0}".format(current_same_run))
                if same_run_value is None:
                    fluctuation_runs["d{0}".format(current_same_run)] = 1
                else:
                    fluctuation_runs["d{0}".format(current_same_run)] = same_run_value + 1
                if current_same_run > longest_same_run:
                    longest_same_run = current_same_run
                current_same_run = 0

        elif cp_fluctuation is CPFluctuation.SAME:
            current_same_run += 1
            if current_increase_run > 0:
                increase_run_value = fluctuation_runs.get("i{0}".format(current_increase_run))
                if increase_run_value is None:
                    fluctuation_runs["i{0}".format(current_increase_run)] = 1
                else:
                    fluctuation_runs["i{0}".format(current_increase_run)] = increase_run_value + 1
                if current_increase_run > longest_increase_run:
                    longest_increase_run = current_increase_run
                current_increase_run = 0
            if current_decrease_run > 0:
                decrease_run_value = fluctuation_runs.get("d{0}".format(current_decrease_run))
                if decrease_run_value is None:
                    fluctuation_runs["d{0}".format(current_decrease_run)] = 1
                else:
                    fluctuation_runs["d{0}".format(current_decrease_run)] = decrease_run_value + 1
                if current_decrease_run > longest_decrease_run:
                    longest_decrease_run = current_decrease_run
                current_decrease_run = 0

    fluctuation_runs = sort_dict(fluctuation_runs)

    increase_runs_total = 0
    decrease_runs_total = 0
    same_runs_total = 0
    for key in fluctuation_runs.keys():
        if key[0] == "i":
            increase_runs_total += fluctuation_runs.get(key)
        if key[0] == "d":
            decrease_runs_total += fluctuation_runs.get(key)
        if key[0] == "s":
            same_runs_total += fluctuation_runs.get(key)
    # runs_total = increase_runs_total + decrease_runs_total + same_runs_total

    random_fluctuation_value = get_random_number(0, 100)
    increase_fluctuation_chance = get_fluctuation_chance(
        fluctuation_runs,
        current_increase_run,
        increase_runs_total,
        current_decrease_run,
        decrease_runs_total,
        current_same_run,
        same_runs_total
    )
    decrease_fluctuation_chance = get_fluctuation_chance(
        fluctuation_runs,
        current_decrease_run,
        decrease_runs_total,
        current_increase_run,
        increase_runs_total,
        current_same_run,
        same_runs_total
    )
    same_fluctuation_chance = get_fluctuation_chance(
        fluctuation_runs,
        current_same_run,
        same_runs_total,
        current_increase_run,
        increase_runs_total,
        current_decrease_run,
        decrease_runs_total
    )

    increase_fluctuation_zone = increase_fluctuation_chance
    decrease_fluctuation_zone = increase_fluctuation_zone + decrease_fluctuation_chance
    same_fluctuation_zone = decrease_fluctuation_zone + same_fluctuation_chance

    if random_fluctuation_value <= increase_fluctuation_zone:
        return CPFluctuation.INCREASE
    elif random_fluctuation_value <= decrease_fluctuation_zone:
        return CPFluctuation.DECREASE
    elif random_fluctuation_value <= same_fluctuation_zone:
        return CPFluctuation.SAME
    else:
        return CPFluctuation.UNKNOWN


def get_fluctuation_chance(
        fluctuation_runs: dict,
        current_run: int,
        run_type_runs_total: int,
        alternate_one_current_run: int,
        alternate_one_runs_total: int,
        alternate_two_current_run: int,
        alternate_two_runs_total: int
) -> int:
    possible_run_alternate_one_paths = get_possible_run_paths(
        fluctuation_runs, alternate_one_current_run, alternate_one_runs_total
    )
    possible_run_alternate_two_paths = get_possible_run_paths(
        fluctuation_runs, alternate_two_current_run, alternate_two_runs_total
    )
    possible_other_run_paths = possible_run_alternate_one_paths + possible_run_alternate_two_paths
    possible_type_run_run_paths = get_possible_run_paths(fluctuation_runs, current_run, run_type_runs_total)
    possible_run_paths = possible_other_run_paths + possible_type_run_run_paths
    fluctuation_chance = round((possible_type_run_run_paths / possible_run_paths) * 100)
    return fluctuation_chance


def get_possible_run_paths(fluctuation_runs: dict, current_run: int, run_type_runs_total: int) -> int:
    current_run_total = 0
    for i in range(1, current_run + 1):
        current_run_total += fluctuation_runs.get("i{0}".format(i))
    return run_type_runs_total - current_run_total


# def predict_next_hour_pattern_method(coin_prices: list) -> float:
#     log("predict_next_hour_pattern_method", "Working on creating prediction for new hour")
#     cp_decimal_weights = {
#         DecimalCategory.PL_FIVE: 0, DecimalCategory.PL_FOUR: 0, DecimalCategory.PL_THREE: 0,
#         DecimalCategory.PL_TWO: 0, DecimalCategory.PL_ONE: 0, DecimalCategory.NL_FIVE: 0,
#         DecimalCategory.NL_FOUR: 0, DecimalCategory.NL_THREE: 0, DecimalCategory.NL_TWO: 0,
#         DecimalCategory.NL_ONE: 0, DecimalCategory.ZERO: 0, DecimalCategory.PR_ONE: 0,
#         DecimalCategory.PR_TWO: 0, DecimalCategory.PR_THREE: 0, DecimalCategory.PR_FOUR: 0,
#         DecimalCategory.PR_FIVE: 0, DecimalCategory.PR_SIX: 0, DecimalCategory.PR_SEVEN: 0,
#         DecimalCategory.PR_EIGHT: 0, DecimalCategory.PR_NINE: 0, DecimalCategory.NR_ONE: 0,
#         DecimalCategory.NR_TWO: 0, DecimalCategory.NR_THREE: 0, DecimalCategory.NR_FOUR: 0,
#         DecimalCategory.NR_FIVE: 0, DecimalCategory.NR_SIX: 0, DecimalCategory.NR_SEVEN: 0,
#         DecimalCategory.NR_EIGHT: 0, DecimalCategory.NR_NINE: 0
#     }
#     cps_fluctuation = []
#     for i in range(len(coin_prices) - 1):
#         cp_now = coin_prices[i]
#         cp_next = coin_prices[i + 1]
#         cp_diff = cp_now - cp_next
#         cp_diff_category = get_cp_diff_category(cp_diff)
#         cp_diff_category_value = cp_decimal_weights.get(cp_diff_category)
#         cp_decimal_weights[cp_diff_category] = cp_diff_category_value + 1
#         cps_fluctuation.append({"CP Difference": cp_diff, "CP Fluctuation": get_diff_fluctuation(cp_diff_category)})
#
#     print(cps_fluctuation)
#
#     global USED_RECENT_COUNT
#     if WANTED_RECENT_COUNT > len(cps_fluctuation):
#         USED_RECENT_COUNT = len(cps_fluctuation)
#
#     current_increase_run = 0
#     longest_increase_run = 0
#     current_decrease_run = 0
#     longest_decrease_run = 0
#     current_same_run = 0
#     longest_same_run = 0
#     fluctuation_runs = dict()
#
#     for i in range(USED_RECENT_COUNT):
#         cp_dict = cps_fluctuation[i]
#         cp_diff = cp_dict.get("CP Difference")
#         cp_fluctuation = cp_dict.get("CP Fluctuation")
#
#         if cp_fluctuation is CPFluctuation.INCREASE:
#             current_increase_run += 1
#             if current_decrease_run > 0:
#                 decrease_run_value = fluctuation_runs.get("d{0}".format(current_decrease_run))
#                 if decrease_run_value is None:
#                     fluctuation_runs["d{0}".format(current_decrease_run)] = 1
#                 else:
#                     fluctuation_runs["d{0}".format(current_decrease_run)] = decrease_run_value + 1
#                 if current_decrease_run > longest_decrease_run:
#                     longest_decrease_run = current_decrease_run
#                 current_decrease_run = 0
#             if current_same_run > 0:
#                 same_run_value = fluctuation_runs.get("d{0}".format(current_same_run))
#                 if same_run_value is None:
#                     fluctuation_runs["d{0}".format(current_same_run)] = 1
#                 else:
#                     fluctuation_runs["d{0}".format(current_same_run)] = same_run_value + 1
#                 if current_same_run > longest_same_run:
#                     longest_same_run = current_same_run
#                 current_same_run = 0
#
#         elif cp_fluctuation is CPFluctuation.DECREASE:
#             current_decrease_run += 1
#             if current_increase_run > 0:
#                 increase_run_value = fluctuation_runs.get("i{0}".format(current_increase_run))
#                 if increase_run_value is None:
#                     fluctuation_runs["i{0}".format(current_increase_run)] = 1
#                 else:
#                     fluctuation_runs["i{0}".format(current_increase_run)] = increase_run_value + 1
#                 if current_increase_run > longest_increase_run:
#                     longest_increase_run = current_increase_run
#                 current_increase_run = 0
#             if current_same_run > 0:
#                 same_run_value = fluctuation_runs.get("d{0}".format(current_same_run))
#                 if same_run_value is None:
#                     fluctuation_runs["d{0}".format(current_same_run)] = 1
#                 else:
#                     fluctuation_runs["d{0}".format(current_same_run)] = same_run_value + 1
#                 if current_same_run > longest_same_run:
#                     longest_same_run = current_same_run
#                 current_same_run = 0
#
#         elif cp_fluctuation is CPFluctuation.SAME:
#             current_same_run += 1
#             if current_increase_run > 0:
#                 increase_run_value = fluctuation_runs.get("i{0}".format(current_increase_run))
#                 if increase_run_value is None:
#                     fluctuation_runs["i{0}".format(current_increase_run)] = 1
#                 else:
#                     fluctuation_runs["i{0}".format(current_increase_run)] = increase_run_value + 1
#                 if current_increase_run > longest_increase_run:
#                     longest_increase_run = current_increase_run
#                 current_increase_run = 0
#             if current_decrease_run > 0:
#                 decrease_run_value = fluctuation_runs.get("d{0}".format(current_decrease_run))
#                 if decrease_run_value is None:
#                     fluctuation_runs["d{0}".format(current_decrease_run)] = 1
#                 else:
#                     fluctuation_runs["d{0}".format(current_decrease_run)] = decrease_run_value + 1
#                 if current_decrease_run > longest_decrease_run:
#                     longest_decrease_run = current_decrease_run
#                 current_decrease_run = 0
#
#     print(longest_increase_run)
#     print(longest_decrease_run)
#     print(longest_same_run)
#     print(fluctuation_runs)
#     fluctuation_runs = sort_dict(fluctuation_runs)
#     print(fluctuation_runs)
#     print(current_increase_run)
#     print(current_decrease_run)
#     print(current_same_run)
#
#     # TODO Create a dict tracking each run and how many times each run occurs
#     # TODO Based on current run, based on the groupings of the previous fluctuations, determine best run
#     # TODO Based on the best run selection, choose increase, decrease or same
#     # TODO Based on the fluctuation option, use the methodology applied in predict_next_hour_weight_method
#     # TODO Using the above methodology, get the nearest and recent groups to determine best value to apply for the fluctuation option
#
#     return 0.0


def get_cp_diff_category(number: float):
    abs_num = abs(number)
    if abs_num >= 1.0:
        if abs_num > 10000.0:
            decimal_count = 5
        elif abs_num > 1000.0:
            decimal_count = 4
        elif abs_num > 100.0:
            decimal_count = 3
        elif abs_num > 10.0:
            decimal_count = 2
        elif abs_num > 1.0:
            decimal_count = 1
        else:
            decimal_count = -1

    else:
        decimal_count = count_zeros(str(abs_num))

    str_num = str(number)
    if str_num[0] == "-":
        if "e" in str_num:
            if str_num[-1] == "5":
                return DecimalCategory.NR_FIVE
            elif str_num[-1] == "6":
                return DecimalCategory.NR_SIX
            elif str_num[-1] == "7":
                return DecimalCategory.NR_SEVEN
            elif str_num[-1] == "8":
                return DecimalCategory.NR_EIGHT
            elif str_num[-1] == "9":
                return DecimalCategory.NR_NINE
            else:
                return DecimalCategory.UNKNOWN

        else:
            if number > 0.0:
                if decimal_count == 1:
                    return DecimalCategory.NL_ONE
                elif decimal_count == 2:
                    return DecimalCategory.NL_TWO
                elif decimal_count == 3:
                    return DecimalCategory.NL_THREE
                elif decimal_count == 4:
                    return DecimalCategory.NL_FOUR
                elif decimal_count == 5:
                    return DecimalCategory.NL_FIVE
                else:
                    return DecimalCategory.UNKNOWN

            else:
                if decimal_count == 1:
                    return DecimalCategory.NR_ONE
                elif decimal_count == 2:
                    return DecimalCategory.NR_TWO
                elif decimal_count == 3:
                    return DecimalCategory.NR_THREE
                elif decimal_count == 4:
                    return DecimalCategory.NR_FOUR

    else:
        if "e" in str_num:
            if str_num[-1] == "0":
                return DecimalCategory.ZERO
            if str_num[-1] == "5":
                return DecimalCategory.PR_FIVE
            elif str_num[-1] == "6":
                return DecimalCategory.PR_SIX
            elif str_num[-1] == "7":
                return DecimalCategory.PR_SEVEN
            elif str_num[-1] == "8":
                return DecimalCategory.PR_EIGHT
            elif str_num[-1] == "9":
                return DecimalCategory.PR_NINE
            else:
                return DecimalCategory.UNKNOWN

        else:
            if number > 0.0:
                if decimal_count == 1:
                    return DecimalCategory.PL_ONE
                elif decimal_count == 2:
                    return DecimalCategory.PL_TWO
                elif decimal_count == 3:
                    return DecimalCategory.PL_THREE
                elif decimal_count == 4:
                    return DecimalCategory.PL_FOUR
                elif decimal_count == 5:
                    return DecimalCategory.PL_FIVE
                else:
                    return DecimalCategory.UNKNOWN

            else:
                if decimal_count == 1:
                    return DecimalCategory.PR_ONE
                elif decimal_count == 2:
                    return DecimalCategory.PR_TWO
                elif decimal_count == 3:
                    return DecimalCategory.PR_THREE
                elif decimal_count == 4:
                    return DecimalCategory.PR_FOUR
                else:
                    return DecimalCategory.UNKNOWN


def count_zeros(str_num: str):
    zero_count = 0
    for s in str_num:
        if s == "0":
            zero_count += 1
        elif s == ".":
            continue
        else:
            break
    return zero_count


def get_nearest_weights(number: float, coin_price_weights: dict) -> list:
    cp_key_values = [key for key in coin_price_weights.keys()]
    nearest_weights = []

    global USED_GROUP_COUNT
    if WANTED_GROUP_COUNT > len(cp_key_values):
        USED_GROUP_COUNT = len(cp_key_values)

    for i in range(USED_GROUP_COUNT):
        nearest_value = get_nearest_value(number, cp_key_values)
        cp_key_values.remove(nearest_value)
        nearest_weights.append(coin_price_weights[nearest_value])

    return nearest_weights


def get_nearest_value(number: float, values: list) -> float:
    pos = bisect_left(values, number)
    if pos == 0:
        return values[0]
    if pos == len(values):
        return values[-1]

    before = values[pos - 1]
    after = values[pos]
    if after - number < number - before:
        return after
    else:
        return before


def get_recent_weights(coin_price_weights: dict) -> list:
    cp_key_values = [key for key in coin_price_weights.keys()]
    recent_weights = []

    global USED_RECENT_COUNT
    if WANTED_RECENT_COUNT > len(cp_key_values):
        USED_RECENT_COUNT = len(cp_key_values)

    cp_key_values.reverse()
    for i in range(1, USED_RECENT_COUNT):
        recent_value = cp_key_values[i]
        cp_key_values.remove(recent_value)
        recent_weights.append(coin_price_weights[recent_value])

    return recent_weights


def get_diff_fluctuation(cp_diff_category):
    cp_category_identifier = cp_diff_category.value[0]
    if cp_category_identifier == "p":
        return CPFluctuation.INCREASE
    elif cp_category_identifier == "n":
        return CPFluctuation.DECREASE
    elif cp_category_identifier == "z":
        return CPFluctuation.SAME
    else:
        return CPFluctuation.UNKNOWN


def get_highest_cp_fluctuation(cp_fluctuation_weights: dict):
    cp_fluctuation_inc = cp_fluctuation_weights[CPFluctuation.INCREASE]
    cp_fluctuation_dec = cp_fluctuation_weights[CPFluctuation.DECREASE]
    cp_fluctuation_same = cp_fluctuation_weights[CPFluctuation.SAME]
    cp_fluctuation_unknown = cp_fluctuation_weights[CPFluctuation.UNKNOWN]
    highest_cp_fluctuation = CPFluctuation.UNKNOWN

    if cp_fluctuation_inc > cp_fluctuation_dec:
        if cp_fluctuation_inc > cp_fluctuation_same:
            if cp_fluctuation_inc > cp_fluctuation_unknown:
                highest_cp_fluctuation = CPFluctuation.INCREASE
        else:
            if cp_fluctuation_same > cp_fluctuation_unknown:
                highest_cp_fluctuation = CPFluctuation.SAME
    else:
        if cp_fluctuation_dec > cp_fluctuation_same:
            if cp_fluctuation_dec > cp_fluctuation_unknown:
                highest_cp_fluctuation = CPFluctuation.DECREASE
        else:
            if cp_fluctuation_same > cp_fluctuation_unknown:
                highest_cp_fluctuation = CPFluctuation.SAME

    return highest_cp_fluctuation


def get_nearest_weights_difference_values(
        nearest_weights: list,
        cp_fluctuation
) -> list:
    nearest_weight_difference_values = []

    for weight in nearest_weights:
        if weight["CP Fluctuation"] == cp_fluctuation:
            nearest_weight_difference_values.append(weight["CP Difference"])

    return nearest_weight_difference_values


def get_recent_weights_difference_values(
        recent_weights: list,
        cp_fluctuation
) -> list:
    recent_weights_difference_values = []

    for weight in recent_weights:
        if weight["CP Fluctuation"] == cp_fluctuation:
            recent_weights_difference_values.append(weight["CP Difference"])

    return recent_weights_difference_values


def get_price_prediction(
        most_recent_price: float,
        nearest_weights_differences: list,
        recent_weights_differences: list,
        highest_cp_fluctuation_value: int
) -> float:
    cp_fluctuation_influence = highest_cp_fluctuation_value / USED_GROUP_COUNT
    combined_weight_class_differences = nearest_weights_differences + recent_weights_differences
    combined_weight_class_differences.sort()
    combined_weight_class_differences_use_index = round(len(combined_weight_class_differences) * cp_fluctuation_influence)
    cp_price_change_prediction = combined_weight_class_differences[combined_weight_class_differences_use_index]
    return most_recent_price + cp_price_change_prediction


class DecimalCategory(Enum):
    PL_FIVE = "pl5"
    PL_FOUR = "pl4"
    PL_THREE = "pl3"
    PL_TWO = "pl2"
    PL_ONE = "pl1"
    NL_FIVE = "nl5"
    NL_FOUR = "nl4"
    NL_THREE = "nl3"
    NL_TWO = "nl2"
    NL_ONE = "nl1"
    ZERO = "z0"
    PR_ONE = "pr1"
    PR_TWO = "pr2"
    PR_THREE = "pr3"
    PR_FOUR = "pr4"
    PR_FIVE = "pr5"
    PR_SIX = "pr6"
    PR_SEVEN = "pr7"
    PR_EIGHT = "pr8"
    PR_NINE = "pr9"
    NR_ONE = "nr1"
    NR_TWO = "nr2"
    NR_THREE = "nr3"
    NR_FOUR = "nr4"
    NR_FIVE = "nr5"
    NR_SIX = "nr6"
    NR_SEVEN = "nr7"
    NR_EIGHT = "nr8"
    NR_NINE = "nr9"
    UNKNOWN = "unknown"


class CPFluctuation(Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    SAME = "same"
    UNKNOWN = "unknown"
