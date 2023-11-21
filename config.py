import re
import string
from datetime import datetime, timedelta
from dotenv import load_dotenv
from os import getenv
outlook_channel_id = 1113843254966878318
spread_channel_id = 1116021973466746890

TOKEN = getenv("TOKEN")
password = getenv("password")
email = getenv("email")
zenrow_api_key = getenv("zenrow_api_key")
NEWS_API_KEY = getenv("NEWS_API_KEY")

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
filler_text = """  Symbol Summary
  SharpChart
  ACP Chart
  GalleryView
  Point & Figure
  Seasonality"""
calendar_url = "https://us.econoday.com/" \
               "byweek.asp?cust=us"
week_low_links = [
    "https://stockcharts.com/def/servlet/SC.scan?s=I.Y%7CTSAL[t.t_eq_s]![t.e_eq_y]![as0,20,tv_gt_40000]![tl0_lt_an1,253,tl]&report=predefalli",
    "https://stockcharts.com/def/servlet/SC.scan?s=I.Y%7CTSAL[t.t_eq_s]![T.E_EQ_N]![T.E_NE_O]![as0,20,tv_gt_40000]![tl0_lt_an1,253,tl]&report=predefalli"]
pre_scanned_links = [
    "https://stockcharts.com/def/servlet/SC.scan?s=I.Y%7CTSAL[t.t_eq_s]![t.e_eq_y]![as0,20,tv_gt_40000]![ba0_lt_0]![ba0_ge_bb0]![ba1_lt_bb1]![ba2_lt_bb2]![ba3_lt_bb3]&report=predefalli"]
news_count = 20
news_channel_id = 1118165179570589858
calendar_channel_id = 1123658368284905585
swing_channel_id = 1116789738616147968
pre_channel_id = 1116778103709118575
news_url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics=financial_markets&sort=LATEST&apikey={NEWS_API_KEY}"
investing_url = "https://www.investing.com/dividends-calendar/"
dividend_channel_id = 1117893441418952704


def find_longest_consecutive_chain(string, character):
    if not string:
        return 0

    max_count = current_count = 0

    for char in string:
        if char == character:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 0

    return max_count


def clean_chars(text):
    allowed_chars = string.ascii_letters + string.digits + string.punctuation + " " + "\n"
    cleaned_text = ''.join([char for char in text if char in allowed_chars])
    return cleaned_text


def has_alphabetical(string):
    pattern = re.compile(r'[a-zA-Z]')
    match = re.search(pattern, string)
    return match is not None


def fix_sentences(strings, spacing=" - "):
    bad = []
    for index in range(len(strings)):
        if ":" in strings[index] and index != 0:
            strings[index - 1] += spacing + strings[index]
            bad.append(index)
    for index in bad[::-1]:
        strings.pop(index)
    return strings


def change_font(text):
    conv = {'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷',
            'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁',
            'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇', 'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗',
            'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡',
            'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫',
            'Y': '𝗬', 'Z': '𝗭', '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳',
            '8': '𝟴', '9': '𝟵'}
    new_text = "".join([conv[i] if i in conv.keys() else i for i in text])
    return new_text


def get_current_week():
    data = dict()
    days_of_week = {
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
        "Sunday": 7
    }
    current_date = datetime.today().strftime("%Y/%m/%d")
    current_day = datetime.today().strftime("%A")
    current_pointer = days_of_week[current_day]

    for key in days_of_week.keys():
        if key == current_day:
            data[key] = current_date
        else:
            pointer = days_of_week[key]
            date = datetime.today() - timedelta(days=current_pointer - pointer)
            data[key] = date.strftime("%Y/%m/%d")
    return data
