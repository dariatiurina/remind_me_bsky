"""Module that  will create statistics"""
import os
from datetime import datetime
import sqlalchemy as db
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database/database.db')
    engine = db.create_engine("sqlite:///" + database_path)
    connection = engine.connect()
    metadata = db.MetaData()
    post_table = db.Table('POSTS', metadata, autoload_with=engine)
    df = pd.read_sql(sql=db.select(post_table.c.TIME_TO_REMIND, post_table.c.TIME_SEND_REQUEST), con=connection)
    if df.empty:
        raise ValueError("Your database does not contain any data!")
    df['DELTA'] = df.apply(lambda row: (
                datetime.strptime(row['TIME_TO_REMIND'], '%Y-%m-%d %H:%M') - datetime.strptime(row['TIME_SEND_REQUEST'],
                                                                                               '%Y-%m-%d %H:%M:%S')), axis=1)
    df['DELTA_SECONDS'] = df['DELTA'].dt.total_seconds() / 3600
    plt.hist(df['DELTA_SECONDS'], bins=int(np.sqrt(len(df)) + 1), edgecolor='black', rwidth=0.95)
    plt.title('Distribution of Time Differences Between Posts and Reminders')
    plt.xlabel('Time Difference (hours)')
    plt.ylabel('Frequency')
    plt.show()
