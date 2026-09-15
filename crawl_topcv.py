from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import pandas as pd
import sqlite3
from clean import deal_salary, group_job_title
from discord_notify import send_job_to_discord

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

DB_NAME = "crawled_jobs.db"


def crawl_jobs(url="https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257"):
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    print("Đang đợi trang tải...")
    time.sleep(5)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.find_all("div", class_="job-item-search-result")
    print(f"Crawl được {len(job_cards)} job")

    jobs = []
    for card in job_cards:
        try:
            job_id = card.get("data-job-id")
            title_tag = card.find("h3", class_="title").find("a")
            job_title = title_tag.find("span").get_text(strip=True)
            link = title_tag.get("href")
            company = card.find("span", class_="company-name").get_text(strip=True)
            salary = card.find("label", class_="title-salary").get_text(strip=True)
            city = card.find("span", class_="city-text").get_text(strip=True)
            exp = card.find("label", class_="exp").get_text(strip=True)

            jobs.append({
                "job_id": job_id, "job_title": job_title, "company": company,
                "salary": salary, "city": city, "exp": exp, "link": link
            })
        except AttributeError:
            continue

    return pd.DataFrame(jobs)


def process_jobs(df):
    df[['min_salary', 'max_salary', 'salary_unit']] = df['salary'].apply(
        lambda x: pd.Series(deal_salary(x))
    )
    df['job_group'] = df['job_title'].apply(group_job_title)
    return df


def get_existing_job_ids():
    try:
        conn = sqlite3.connect(DB_NAME)
        existing = pd.read_sql("SELECT job_id FROM jobs", conn)
        conn.close()
        return set(existing['job_id'].astype(str))
    except Exception:
        return set()


def save_to_db(df, table_name="jobs"):
    conn = sqlite3.connect(DB_NAME)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"Đã lưu {len(df)} job vào {DB_NAME}")


def run():
    old_ids = get_existing_job_ids()
    print(f"Đã có {len(old_ids)} job trong database từ trước")

    df = crawl_jobs()
    df = process_jobs(df)

    df['job_id'] = df['job_id'].astype(str)
    new_jobs = df[~df['job_id'].isin(old_ids)]
    print(f"Phát hiện {len(new_jobs)} job MỚI")

    de_new_jobs = new_jobs[new_jobs['job_group'] == 'Data Engineer/Scientist']
    print(f"Trong đó có {len(de_new_jobs)} job Data Engineer mới")

    for _, job in de_new_jobs.iterrows():
        success = send_job_to_discord(job)
        if success:
            print(f"Đã gửi: {job['job_title']}")
        else:
            print(f"Gửi thất bại: {job['job_title']}")

    save_to_db(df)


if __name__ == "__main__":
    run()