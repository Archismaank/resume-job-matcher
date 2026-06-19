from app.parsers.naukri_scraper import search_naukri_jobs


def main():
    print("\n========================================")
    print("TESTING NAUKRI SCRAPER")
    print("========================================\n")

    try:
        jobs = search_naukri_jobs(
            query="python developer",
            location="bangalore",
            experience="0",
            remote_only=False,
            employment_type="FULLTIME",
        )

        print("\n========================================")
        print("SCRAPER FINISHED")
        print("========================================")

        print(f"\nTotal jobs returned: {len(jobs)}")

        if not jobs:
            print("\n❌ No jobs returned.")
            print(
                "This means either:\n"
                "1. Cards were not parsed\n"
                "2. JobListing validation failed\n"
                "3. All jobs were filtered out\n"
            )
            return

        print("\n========================================")
        print("JOBS")
        print("========================================")

        for i, job in enumerate(jobs, start=1):
            print(f"\n----- JOB {i} -----")

            try:
                print("Title:", job.title)
            except Exception:
                pass

            try:
                print("Company:", job.company)
            except Exception:
                pass

            try:
                print("Location:", job.location)
            except Exception:
                pass

            try:
                print("Experience:", job.experience_required)
            except Exception:
                pass

            try:
                print("URL:", job.url)
            except Exception:
                pass

            try:
                print("Skills:", job.required_skills)
            except Exception:
                pass

            print()

    except Exception as e:
        print("\n========================================")
        print("TOP LEVEL ERROR")
        print("========================================")
        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    main()