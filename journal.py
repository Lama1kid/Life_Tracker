import calendar
import datetime
import sqlite3
from re import match


def main():
    global db, cur, options
    db = sqlite3.connect("/home/celeste/life_tracker/journal.db")
    cur = db.cursor()

    # features implemented here
    options_dict = {
        "journal": journal,
        "start a new month": start_a_new_month,
        "record study duration": record_study_duration,
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


main()
