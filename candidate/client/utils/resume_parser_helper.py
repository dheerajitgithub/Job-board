def format_address(address):
    street_address = address.get("streetAddress", "").strip()
    city = address.get("city", "").strip()
    state = address.get("state", "").strip()
    country = address.get("country", "").strip()
    postal_code = address.get("postalCode", "").strip()
    address_parts = [street_address, city, state, country, postal_code]
    formatted_address = " ".join(part for part in address_parts if part)
    return formatted_address


def get_professional_summary(professional_summary, overall_summary):
    overall_summary = overall_summary.strip()
    objective = professional_summary.get("objective", "").strip()
    professional_info = professional_summary.get("professionalInfo", "").strip()
    
    if overall_summary:
        return overall_summary
    elif professional_info:
        return professional_info
    elif objective:
        return objective
    else:
        return ""


# def month_to_number(month):
#     month_mapping = {
#         "January": "01",
#         "February": "02",
#         "March": "03",
#         "April": "04",
#         "May": "05",
#         "June": "06",
#         "July": "07",
#         "August": "08",
#         "September": "09",
#         "October": "10",
#         "November": "11",
#         "December": "12"
#     }
#     return month_mapping.get(month, "01")


# def transform_education_data(education_data):
#     transformed_data = []
#     for entry in education_data:
#         start_month = month_to_number(entry.get("graduationStartMonth", ""))
#         start_year = entry.get("graduationStartYear", "01")
#         end_month = month_to_number(entry.get("graduationEndMonth", ""))
#         end_year = entry.get("graduationEndYear", "01")

#         start_date = f"01-{start_month}-{start_year}"
#         end_date = f"01-{end_month}-{end_year}"

#         transformed_entry = {
#             "degree": entry.get("degree"),
#             "major": entry.get("major"),
#             "achieved_marks": entry.get("achievedMarks"),
#             "location": entry.get("location"),
#             "institute": entry.get("institution"),
#             "start_date": start_date,
#             "end_date": end_date
#         }
#         transformed_data.append(transformed_entry)
#     return transformed_data


# def transform_work_experience(work_experience):
#     transformed_experience = []
#     for experience in work_experience:
#         company_name = experience.get("companyName", "").strip()
#         job_title = experience.get("originalJobTitle", "").strip()
        
#         start_month = month_to_number(experience["employmentPeriod"].get("startMonth", ""))
#         start_year = experience["employmentPeriod"].get("startYear", "01")
#         end_month = month_to_number(experience["employmentPeriod"].get("endMonth", ""))
#         end_year = experience["employmentPeriod"].get("endYear", "01")

#         start_date = f"01-{start_month}-{start_year}"
#         end_date = f"01-{end_month}-{end_year}"

#         city = experience["location"].get("city", "").strip()
#         skills = list(set(experience.get("skills", []) + experience.get("keywords", [])))
#         responsibilities = experience.get("responsibilities", [])

#         transformed_entry = {
#             "company_name": company_name,
#             "job_title": job_title,
#             "start_date": start_date,
#             "end_date": end_date,
#             "location": city,
#             "skills": skills,
#             "responsibilities": responsibilities
#         }
#         transformed_experience.append(transformed_entry)
#     return transformed_experience


def month_to_number(month):
    month_mapping = {
        "January": "01", "Jan": "01", "JAN": "01", "jan": "01", "JANUARY": "01", "january": "01",
        "Jan.": "01", "jan.": "01", "JAN.": "01", "Jany": "01", "jany": "01", "1": "01", "01": "01",
        
        "February": "02", "Feb": "02", "FEB": "02", "feb": "02", "FEBRUARY": "02", "february": "02",
        "Feb.": "02", "feb.": "02", "FEB.": "02", "Febr": "02", "febr": "02", "Febuary": "02", "febuary": "02", "2": "02", "02": "02",
        
        "March": "03", "Mar": "03", "MAR": "03", "mar": "03", "MARCH": "03", "march": "03",
        "Mar.": "03", "mar.": "03", "Mrach": "03", "mrach": "03", "3": "03", "03": "03",
        
        "April": "04", "Apr": "04", "APR": "04", "apr": "04", "APRIL": "04", "april": "04",
        "Apr.": "04", "apr.": "04", "Apirl": "04", "apirl": "04", "4": "04", "04": "04",
        
        "May": "05", "MAY": "05", "may": "05", "Maay": "05", "maay": "05", "5": "05", "05": "05",
        
        "June": "06", "Jun": "06", "JUN": "06", "jun": "06", "JUNE": "06", "june": "06",
        "Jun.": "06", "jun.": "06", "6": "06", "06": "06",
        
        "July": "07", "Jul": "07", "JUL": "07", "jul": "07", "JULY": "07", "july": "07",
        "Jul.": "07", "jul.": "07", "7": "07", "07": "07",
        
        "August": "08", "Aug": "08", "AUG": "08", "aug": "08", "AUGUST": "08", "august": "08",
        "Aug.": "08", "aug.": "08", "Augst": "08", "augst": "08", "8": "08", "08": "08",
        
        "September": "09", "Sep": "09", "SEP": "09", "sep": "09", "SEPTEMBER": "09", "september": "09",
        "Sept": "09", "sept": "09", "Sept.": "09", "sept.": "09", "Sep.": "09", "sep.": "09",
        "Setp": "09", "setp": "09", "Septembre": "09", "septembre": "09", "9": "09", "09": "09",
        
        "October": "10", "Oct": "10", "OCT": "10", "oct": "10", "OCTOBER": "10", "october": "10",
        "Oct.": "10", "oct.": "10", "Octorber": "10", "octorber": "10", "10": "10",
        
        "November": "11", "Nov": "11", "NOV": "11", "nov": "11", "NOVEMBER": "11", "november": "11",
        "Nov.": "11", "nov.": "11", "Novenber": "11", "novenber": "11", "11": "11",
        
        "December": "12", "Dec": "12", "DEC": "12", "dec": "12", "DECEMBER": "12", "december": "12",
        "Dec.": "12", "dec.": "12", "Dece": "12", "dece": "12", "Decembre": "12", "decembre": "12", "12": "12"
    }
    return month_mapping.get(month, "01")


def transform_education_data(education_data):
    transformed_data = []
    for entry in education_data:
        # Check for start and end years and only format the date if both are present
        start_month = month_to_number(entry.get("graduationStartMonth", ""))
        start_year = entry.get("graduationStartYear")
        end_month = month_to_number(entry.get("graduationEndMonth", ""))
        end_year = entry.get("graduationEndYear")
        
        start_date = f"{start_year}-{start_month}-01" if start_year else ""
        end_date = f"{end_year}-{end_month}-01" if end_year else ""

        transformed_entry = {
            "degree": entry.get("degree"),
            "major": entry.get("major"),
            "achieved_marks": entry.get("achievedMarks"),
            "location": entry.get("location"),
            "institute": entry.get("institution"),
            "start_date": start_date,
            "end_date": end_date
        }
        transformed_data.append(transformed_entry)
    return transformed_data


def transform_work_experience(work_experience):
    transformed_experience = []
    for experience in work_experience:
        company_name = experience.get("companyName", "").strip()
        job_title = experience.get("originalJobTitle", "").strip()
        
        # Check for start and end years and only format the date if both are present
        start_month = month_to_number(experience["employmentPeriod"].get("startMonth", ""))
        start_year = experience["employmentPeriod"].get("startYear")
        end_month = month_to_number(experience["employmentPeriod"].get("endMonth", ""))
        end_year = experience["employmentPeriod"].get("endYear")
        
        start_date = f"01-{start_month}-{start_year}" if start_year else ""
        end_date = f"01-{end_month}-{end_year}" if end_year else ""

        city = experience["location"].get("city", "").strip()
        skills = list(set(experience.get("skills", []) + experience.get("keywords", [])))
        responsibilities = experience.get("responsibilities", [])

        transformed_entry = {
            "company_name": company_name,
            "job_title": job_title,
            "start_date": start_date,
            "end_date": end_date,
            "location": city,
            "skills": skills,
            "responsibilities": responsibilities
        }
        transformed_experience.append(transformed_entry)
    return transformed_experience


def merge_soft_skills(generic_soft_skills, work_experience_soft_skills):
    combined_skills = generic_soft_skills + work_experience_soft_skills
    unique_skills = list(set(combined_skills))
    return unique_skills


def merge_technical_skills(generic_technical_skills, work_experience_technical_skills):
    combined_skills = generic_technical_skills + work_experience_technical_skills
    unique_skills = list(set(combined_skills))
    return unique_skills


def transform_projects(projects):
    transformed_projects = []
    for project in projects:
        transformed_entry = {
            "title": project.get("title", "").strip(),
            "description": project.get("description", "").strip(),
            "project_skills": project.get("projectSkills", []),
            "link": project.get("link", "").strip()
        }
        transformed_projects.append(transformed_entry)
    return transformed_projects


def extract_titles(data):
    titles = []
    for each in data:
        title = each.get("title", "").strip()
        if title:
            titles.append(title)
    return titles


def aggregate_titles(publications, conferences_attended, professional_memberships, references):
    all_titles = []
    all_titles.extend(extract_titles(publications))
    all_titles.extend(extract_titles(conferences_attended))
    all_titles.extend(extract_titles(professional_memberships))
    all_titles.extend(extract_titles(references))
    return all_titles
