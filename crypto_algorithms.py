from enum import Enum
from bisect import bisect_left

RELATIVE_MARGINS_RIGHT = {
    "LUNC": 0.000001
}
VALUE_GROUP_COUNT = 100


def predict_next_hour(coin_abbreviation: str, coin_prices: list):
    print("Working on creating prediction for next hour")
    relative_margin_right = RELATIVE_MARGINS_RIGHT.get(coin_abbreviation)
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

    coin_price_weights = dict()

    for i in range(len(coin_prices) - 1):
        cp_now = coin_prices[i]
        cp_next = coin_prices[i + 1]
        cp_diff = cp_now - cp_next
        cp_diff_category = get_cp_diff_category(cp_diff)
        cp_diff_category_value = cp_decimal_weights.get(cp_diff_category)
        cp_decimal_weights[cp_diff_category] = cp_diff_category_value + 1
        coin_price_weights[cp_now] = {"CP Difference Category": cp_diff_category, "CP Difference": cp_diff}

    print(cp_decimal_weights)
    print(coin_price_weights)

    most_recent_price = coin_prices[-1]
    most_recent_price_weight_prediction = {"CP Difference Category": DecimalCategory.UNKNOWN, "CP Difference": 0.0}
    # print(most_recent_price)

    cp_fluctuation_weights = {
        CPFluctuation.INCREASE: 0, CPFluctuation.DECREASE: 0, CPFluctuation.SAME: 0, CPFluctuation.UNKNOWN: 0
    }

    nearest_weights = get_nearest_weights(most_recent_price, coin_price_weights)
    print(nearest_weights)

    for weight in nearest_weights:
        # weight_fluctuation(coin_weight: dict) can return "increase," "decrease," "same" or "unknown."
        coin_fluctuation = weight_fluctuation(weight)
        cp_fluctuation_value = cp_fluctuation_weights.get(coin_fluctuation)
        cp_fluctuation_weights[coin_fluctuation] = cp_fluctuation_value + 1

    print(cp_fluctuation_weights)


def get_cp_diff_category(number: float):
    str_num = str(number)
    if number > 0.0:
        if number > 10000.0:
            decimal_count = 5
        elif number > 1000.0:
            decimal_count = 4
        elif number > 100.0:
            decimal_count = 3
        elif number > 10.0:
            decimal_count = 2
        elif number > 1.0:
            decimal_count = 1
        else:
            decimal_count = -1

    else:
        decimal_count = count_zeros(str_num)

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


def count_zeros(str_num: str):
    zero_count = 0
    for s in str_num:
        if s == "0":
            zero_count += 1
        else:
            break
    return zero_count


def get_nearest_weights(number: float, coin_price_weights: dict) -> list:
    cp_key_values = [key for key in coin_price_weights.keys()]
    nearest_weights = []

    for i in range(VALUE_GROUP_COUNT):
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


def weight_fluctuation(coin_weight: dict):
    cp_category: DecimalCategory = coin_weight.get("CP Difference Category")
    cp_category_identifier = cp_category.value[0]
    if cp_category_identifier == "p":
        return CPFluctuation.INCREASE
    elif cp_category_identifier == "n":
        return CPFluctuation.DECREASE
    elif cp_category_identifier == "z":
        return CPFluctuation.SAME
    else:
        return CPFluctuation.UNKNOWN


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
