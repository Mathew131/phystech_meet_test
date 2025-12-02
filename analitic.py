import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

conn = psycopg2.connect(
    dbname="phystech_meet",
    user="postgres",
    password="Elo327bbn",
    host="64.188.124.15",
    port=5432
)

print("✅ Подключение успешно")

DAYS_BACK = 30

def fetch_data(since: datetime):
    users = pd.read_sql(
        "SELECT telegram_id, created_at FROM users WHERE created_at >= %s;",
        conn,
        params=[since],
    ) # изначально в users время в utc

    users["created_at"] = pd.to_datetime(users["created_at"], utc=True).dt.tz_convert("Europe/Moscow")

    inter = pd.read_sql(
        """
        SELECT user_id, target_id, action, created_at
        FROM interactions
        WHERE created_at >= %s;
        """,
        conn,
        params=[since],
    ) # изначально в inter время в utc

    inter["created_at"] = pd.to_datetime(inter["created_at"], utc=True).dt.tz_convert("Europe/Moscow")

    if not users.empty:
        users["created_at"] = pd.to_datetime(users["created_at"])
        users["date"] = users["created_at"].dt.floor("D")

    if not inter.empty:
        inter["created_at"] = pd.to_datetime(inter["created_at"])
        inter["date"] = inter["created_at"].dt.floor("D") # округляем вниз по дням

    return users, inter


def daily_counts(dates: pd.Series, index: pd.DatetimeIndex):
    if dates.empty:
        return pd.Series(0, index=index)

    counts = dates.dt.floor("D").value_counts().sort_index()

    counts = counts.reindex(index, fill_value=0)

    return counts


def compute_mutual_likes(inter: pd.DataFrame):
    if inter.empty:
        return pd.Series(dtype="datetime64[ns]")

    likes = inter[inter["action"] == "like"][["user_id", "target_id", "created_at"]].copy()

    merged = likes.merge(
        likes,
        left_on=["user_id", "target_id"],
        right_on=["target_id", "user_id"],
        suffixes=("_a", "_b")
    )
    print(merged)

    if merged.empty:
        return pd.Series(dtype="datetime64[ns]")

    mutual_times = merged[["created_at_a", "created_at_b"]].max(axis=1)
    return pd.to_datetime(mutual_times).dt.floor("D")


def three_lines(series: pd.Series, mode: str = "sum"):
    out = pd.DataFrame(index=series.index)

    if mode == "mean":
        out["1d"] = series
        out["7d"] = series.rolling(window=7,  min_periods=1).mean()
        out["30d"] = series.rolling(window=30, min_periods=1).mean()
    else:
        out["1d"] = series.rolling(window=1,  min_periods=1).sum()
        out["7d"] = series.rolling(window=7,  min_periods=1).sum()
        out["30d"] = series.rolling(window=30, min_periods=1).sum()
    return out

def plot_all(new_users_daily, all_actions_daily, likes_daily, dislikes_daily, mutual_daily, mode="sum"):
    fig, axes = plt.subplots(5, 1, figsize=(12, 18), sharex=True, constrained_layout=True)

    locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
    formatter = mdates.ConciseDateFormatter(locator)

    def plot_one(ax, series, title):
        df = three_lines(series, mode=mode)

        ax.plot(df.index, df["1d"],  label="день",
                linewidth=1.6, marker="o", markersize=2.5, alpha=0.9, zorder=3, linestyle="-")
        ax.plot(df.index, df["7d"],  label="неделя",
                linewidth=2.0, alpha=0.95, zorder=2, linestyle="--")
        ax.plot(df.index, df["30d"], label="месяц",
                linewidth=2.2, alpha=0.95, zorder=1, linestyle=":")

        ax.set_title(title, pad=8, fontsize=12)
        ax.set_ylabel("Количество")
        ax.grid(True, alpha=0.3)
        ax.margins(x=0.01, y=0.08)

        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.legend(loc="upper left", ncol=3, frameon=True, framealpha=0.9, fontsize=9)

    plot_one(axes[0], new_users_daily, "Новые пользователи")
    plot_one(axes[1], all_actions_daily, "Все действия с анкетами")
    plot_one(axes[2], likes_daily, "Лайки")
    plot_one(axes[3], dislikes_daily, "Дизлайки")
    plot_one(axes[4], mutual_daily, "Взаимные лайки")

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))

    for ax in axes[:-1]:
        ax.label_outer()
    axes[-1].set_xlabel("Дата")
    for label in axes[-1].get_xticklabels():
        label.set_rotation(30)
        label.set_ha("right")

    plt.show()
    
# def three_lines(series: pd.Series) -> pd.DataFrame:
#     out = pd.DataFrame(index=series.index)
#     out["1d"] = series.rolling(window=1, min_periods=1).sum()
#     out["7d"] = series.rolling(window=7, min_periods=1).sum()
#     out["30d"] = series.rolling(window=30, min_periods=1).sum()
#     return out

# def plot_all(new_users_daily, all_actions_daily, likes_daily, dislikes_daily, mutual_daily):
#     fig, axes = plt.subplots(5, 1, figsize=(10, 15), sharex=True)

#     def plot_one(ax, df, title):
#         df = three_lines(df)

#         if (title == "Новые пользователи"):
#             ax.plot(df.index, df["1d"], label="день")
#             ax.plot(df.index, df["7d"], label="неделя")
#             ax.plot(df.index, df["30d"], label="месяц")
#         else:
#             ax.plot(df.index, df["1d"])
#             ax.plot(df.index, df["7d"])
#             ax.plot(df.index, df["30d"])

#         ax.set_title(title)
#         ax.set_ylabel("Количество")
#         ax.grid(True)
#         ax.legend()

#     plot_one(axes[0], new_users_daily, "Новые пользователи")
#     plot_one(axes[1], all_actions_daily, "Все действия с анкетами")
#     plot_one(axes[2], likes_daily, "Лайки")
#     plot_one(axes[3], dislikes_daily, "Дизлайки")
#     plot_one(axes[4], mutual_daily, "Взаимные лайки")

#     axes[-1].set_xlabel("Дата")
#     plt.tight_layout()
#     plt.show()

if __name__ == "__main__":
    end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=DAYS_BACK)

    users, inter = fetch_data(start - timedelta(days=DAYS_BACK))

    index = pd.date_range(start, end, freq="D", tz="Europe/Moscow")

    # 1) Новые пользователи
    new_users_daily = daily_counts(users["date"] if not users.empty else pd.Series(dtype="datetime64[ns]"), index)

    # 2) Лайки и дизлайки
    all_actions_daily = daily_counts(inter["date"] if not inter.empty else pd.Series(dtype="datetime64[ns]"), index)

    # 3) Лайки
    likes_daily = daily_counts(inter.loc[inter["action"] == "like", "date"] if not inter.empty else pd.Series(dtype="datetime64[ns]"), index)

    # 4) Дизлайки
    dislikes_daily = daily_counts(inter.loc[inter["action"] == "dislike", "date"] if not inter.empty else pd.Series(dtype="datetime64[ns]"), index)

    # 5) Взаимные лайки
    mutual_daily = daily_counts(compute_mutual_likes(inter), index)

    plot_all(new_users_daily, all_actions_daily, likes_daily, dislikes_daily, mutual_daily)
