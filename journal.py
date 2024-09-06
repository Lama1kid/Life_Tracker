import calendar
import datetime
import sqlite3
from re import match
from random import randrange


def main():
    global db, cur, options
    db = sqlite3.connect("/home/celeste/life_tracker/journal.db")
    cur = db.cursor()

    # features implemented here
    options_dict = {
        "journal": journal,
        "start a new month": start_a_new_month,
        "record study duration": record_study_duration,
        "daily prompt": daily_prompt,
    }  # map to functions

    # query loop
    while True:
        # display each option marked by serial number
        serial_num = 0
        options_by_order = {}
        for option in options_dict.keys():
            # populate the dict options_by_order
            options_by_order[serial_num] = option
            print(f"({serial_num}) {option}")
            serial_num += 1

        # request input
        operation_num = input(
            "What you want to do?(select a nubmer; press q to exit) ")
        if operation_num == "q":
            break
        operation = options_by_order[int(operation_num)]
        if operation not in options_dict.keys():
            print("not a option")
            continue
        options_dict[operation]()


def journal():
    """
    request metrics_value to insert into db
    before that aquire column names first in order to display them one by each requests
    """
    # request input date
    while True:
        date = input("date(enter nothing to journal today): ")
        if date == '':
            date = 'now'  # default date value
            # acquire month name from date used for specifying table name later
            month_name = datetime.datetime.now().strftime("%B")
            break
        # verify the date format
        if match("\d\d\d\d-\d\d-\d\d", date):
            month_name = calendar.month_name[int(date[5:7])]
            break
        else:
            print("date format must be YYYY-MM-DD")
            continue

    # aquire column names
    table_description = cur.execute(f"""
    SELECT get_up_early,
    immerse,
    learn_sth_new,
    "info_overloaded(N)",
    "overthink(N)",
    "obsessed(N)",
    "improper_stimulus(N)",
    read_bef_bed FROM {month_name};
    """).description
    names = [description[0] for description in table_description]

    # request metric value for each column
    while True:
        total = 0
        metrics_value = {}
        metrics_value["date"] = date  # used for named style substitution later
        for name in names:
            metric = input(f"metric value for column {name}: ")
            if metric != '0' and metric != '1':
                print("enter 0 or 1")
                continue
            metrics_value[name] = int(metric)
            total += int(metric)  # used for compute condition metrics
        break
    # compute condition metrics (percentage)
    col_num = len(names)
    metrics_value["condition(%)"] = float(f"{total / col_num * 100:.2f}")
    print(f"condition: {metrics_value['condition(%)']}%")

    # execute insertion
    cur.execute(
        f"""
    UPDATE {month_name}
    SET (get_up_early,
        immerse,
        learn_sth_new,
        "info_overloaded(N)",
        "overthink(N)",
        "obsessed(N)",
        "improper_stimulus(N)",
        read_bef_bed,
        "condition(%)") =
        (:get_up_early,
        :immerse,
        :learn_sth_new,
        :info_overloaded(N),
        :overthink(N),
        :obsessed(N),
        :improper_stimulus(N),
        :read_bef_bed,
        :condition(%))
    WHERE date = strftime('%m-%d', :date);""", metrics_value)
    db.commit()
    print("------------------------------------------")


def start_a_new_month():
    """
    require month name from today's date to start a new month journal
    """
    month_name = datetime.datetime.now().strftime("%B")

    cur.execute(f"""
            CREATE TABLE IF NOT EXISTS
                {month_name}(
                "date" date,
                get_up_early,
                immerse,
                learn_sth_new,
                "info_overloaded(N)",
                "overthink(N)",
                "obsessed(N)",
                "improper_stimulus(N)",
                read_bef_bed,
                study_duration FLOAT,
                "condition(%)" FLOAT
                );
                """)
    # autofill
    cur.execute(f"""
            with recursive DataGenerated(date) as ( 
                select date('now', 'start of month') as date union
                select date(date, '+1 day') from DataGenerated where date < date('now', 'start of month', '+1 month', '-1 days')
            )

            insert into {month_name} (date)
                select strftime('%m-%d', date) from DataGenerated;
            """)
    db.commit()
    print("start to journal in a new month!")
    print("------------------------------------------")


def record_study_duration():
    """
    request enter r to start record and e to end record, take the data into the database
    store data duration with minute as units
    """
    # record
    start_time, end_time = 0, 0
    while True:
        flag = input("enter r to start record and e to end record: ")
        if flag == 'r':
            start_time = datetime.datetime.now()
            print("...")
        elif flag == 'e':
            if start_time:
                end_time = datetime.datetime.now()
                break
            else:
                print("you didn't start recording")
        else:
            break

    if start_time and end_time:
        month_name = datetime.datetime.now().strftime("%B")
        duration = db.execute(f"""
                        SELECT study_duration FROM {month_name}
                        WHERE date = strftime('%m-%d', 'now');""").fetchall(
        )[0][0]
        # convert duration's data type
        if isinstance(duration, type(None)):
            duration = 0.0
        # compute duration and store it
        time_delta = float(f"{(end_time - start_time).seconds / 60:.2f}")
        duration += time_delta
        print(f"study duration today: {duration}m(+ {time_delta}m)")
        db.execute(
            f"""
                    UPDATE {month_name}
                    SET study_duration = ?
                    WHERE date = strftime('%m-%d', 'now');""", (duration, ))
        db.commit()
        print("------------------------------------------")
    else:
        print("you didn't start to record or end the recording.")

def daily_prompt():
    # initalize prompts
    # prompt0, 1, 5 have subprompts
    prompts = [
        ["What would you do if money were no object?", 
         "Imagine a world where you have all the time and money, what would you use your talent and skills to server other people?"
         ],
        ["What you would like people to say in your funeral?"
         "What sort of spouse/parent/child you want to be?"
         "to what extent I am actually living in alignment with that?"
         ],
        "If I repeat this week's action for next 10 years, where I would end up? and is that where I want to be?",
        "What activities I have done in last 2 weeks has energised me and drain me?",
        "How is your wheel of life?",
        ["What is your odyssey plan?",
         "What you life would look life 5 years from now if you continued down current path?",
         "What you life would look life 5 years from now if you took a completely different path?",
         "What your life would look life if money and social obligation and what people would think were completely irrelevent?",
         ],
        "Which goal will have the greatest positive impact on your life?",
        "Do you work for your business or does business work for you?",
        "If you knew you'd die in two years, how would you spend your time?"
    ]
    prompts_serial_num = randrange(len(prompts))
    if isinstance(prompts[prompts_serial_num], list):
        print(prompts[prompts_serial_num][0])
        for i in range(len(prompts[prompts_serial_num])):
            print(f"    ({i}) {prompts[prompts_serial_num][i]}")
    print("------------------------------------------")

main()
