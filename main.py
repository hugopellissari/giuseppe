from datetime import date, datetime, timedelta, timezone

import numpy as np
import requests
from PIL import Image, ImageColor


SQUARE_SIZE = 10  # area in pixels


# convert integers to 3x8 bit tuples
def integer_to_rgb_tuple(value):
    if value < 0 or value > 16777215:
        raise Exception("Invalid input")

    blue = value & 255
    green = (value >> 8) & 255
    red = (value >> 16) & 255

    return red, green, blue


def validate_input_size(input_list, square_size=SQUARE_SIZE):
    if len(input_list) != square_size * square_size:
        raise Exception("Invalid integer list size")


def build_array_from_integer_list(integer_list, square_size=SQUARE_SIZE):
    """Maps the value, from left to right, top to down, with the data in the input (list)"""
    array = np.zeros((SQUARE_SIZE, SQUARE_SIZE, 3), dtype=np.uint8)
    validate_input_size(integer_list)

    counter = 0
    for i in range(square_size):
        for j in range(square_size):
            array[i][j] = integer_to_rgb_tuple(integer_list[counter])
            counter += 1

    return array


def build_integer_list(timeseries, signature, square_size=SQUARE_SIZE):
    """
    Function that transforms a timeseries and signature transforms into list, where the position
    of the signature is a 2x2 square in the bottom right of the image
    """
    signature_length = len(signature)
    timeseries_length = len(timeseries)
    output_expected_length = square_size * square_size

    if signature_length != 4:
        raise Exception("Signature must be a list of 4 values")

    if signature_length + timeseries_length != output_expected_length:
        raise Exception("Timeseries + singature length must be equal to SQUARE_SIZE^2")

    # signature must be rendered in positions 88,89,98,99
    output = []
    for i in range(output_expected_length):
        signature_position = [88, 89, 98, 99]  # signature must be rendered in positions 88,89,98,99
        if i in signature_position:
            value = signature.pop(0)
        else:
            value = timeseries.pop(0)

        output.append(value)

    return output


def get_currency_data(timestamp):
    url = f"https://min-api.cryptocompare.com/data/v2/histominute?fsym=BTC&aggregate=15&toTs={timestamp}&tsym=USD&limit=95"
    response = requests.get(url)
    try:
        response_data = response.json()["Data"]["Data"]
    except KeyError:
        print(response.json())
        raise

    first_date = datetime.utcfromtimestamp(response_data[0]["time"])
    end_date = datetime.utcfromtimestamp(response_data[95]["time"])

    assert first_date.hour == 0 and first_date.minute == 15
    assert end_date.hour == 0 and end_date.minute == 0
    assert end_date.day == first_date.day + 1

    return response_data


def get_timeseries_data(timestamp):
    # we need to get the Epoch timestamp in order to fetch the 96 datapoints before that
    timeseries_data = get_currency_data(timestamp)

    output = []
    for item in timeseries_data:
        price = int(item["close"] * 100)
        output.append(price)

    return output


def get_signature_data(year, month, day):
    date_string = f"{month}{day}{year}"
    color_code = int(date_string)
    return [color_code, color_code, color_code, color_code]


def generate_art_from_datetime(datetime_seed):
    epoch_timestamp = datetime(
        datetime_seed.year, datetime_seed.month, datetime_seed.day, 0, 0, tzinfo=timezone.utc).timestamp()

    # fetch data
    timeseries = get_timeseries_data(epoch_timestamp)
    signature = get_signature_data(datetime_seed.year, datetime_seed.month, datetime_seed.day)

    # process data to build array
    dataset = build_integer_list(timeseries, signature)
    array = build_array_from_integer_list(dataset)

    # # Generate image from array
    image = Image.fromarray(array, mode="RGB")
    image.save(f"{datetime_seed.year}-{datetime_seed.month}-{datetime_seed.day}.png")


def generate_yesterday_art():
    yesterday = datetime.today() - timedelta(days=1)
    generate_art_from_datetime(yesterday)


def generate_art_last_seven_days():
    today = datetime.today()
    art_datetime = today - timedelta(days=6)
    while True:
        art_datetime = art_datetime + timedelta(days=1)

        if art_datetime == today:
            break

        generate_art_from_datetime(art_datetime)


generate_art_last_seven_days()
