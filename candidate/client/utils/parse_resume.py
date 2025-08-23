


from datetime import datetime, date
import os
import pytz
import json,requests,logging
from django.core.files.base import ContentFile
from candidate.client.utils.resume_parser_helper import aggregate_titles, extract_titles, format_address, get_professional_summary, merge_soft_skills, merge_technical_skills, transform_education_data, transform_projects, transform_work_experience
from core.settings import AZURE_CONTAINER_CLIENT, AZURE_CONTAINER_NAME, AZURE_URL, RESUME_PARSER_ML_HOST
from core.settings import logger
from core.utils.utils import convert_to_pdf, create_path, format_name,media_path

logger = logging.LoggerAdapter(logger, {"app_name": "candidate.utils"})


def save_resumes(company_name, file, applicant_name):
    logger.info("save_resumes Envoked")
    logger.info(f"FILE NAME IS: {file.name}")
    resume_path = "Resumes"
    folder_path = resume_path
    create_path("Resumes", company_name)
    curr_date = str(datetime.now(pytz.utc).timestamp()).replace(".","")
    resume_file_name = (
        applicant_name.strip() + curr_date + "." + file.name.split(".")[-1]
    )
    local_directory = (
        os.path.join(os.path.abspath(os.curdir), media_path) + folder_path + "/"
    )
    file_name = local_directory + resume_file_name
    # s3 = boto3.resource(
    #     "s3", aws_access_key_id=AWSAccessKeyId, aws_secret_access_key=AWSSecretKey
    # )
    fout = open(file_name, "wb+")
    file_content = ContentFile(file.read())
    # Iterate through the chunks.
    for chunk in file_content.chunks():
        fout.write(chunk)
    fout.close()
    if file.name.endswith(".docx") or file.name.endswith(".doc"):
        file_name_end = os.path.splitext(file_name)[0] + ".pdf"
        file_name_end = file_name_end.split("/")[-1]
        time_now = datetime.datetime.now(pytz.utc)
        convert_to_pdf(file_name, local_directory)
        logger.info(
            f"TIME TAKEN FOR CONVERSION FROM DOCX TO PDF:{datetime.datetime.now(pytz.utc) - time_now}"
        )
        file_name = os.path.splitext(file_name)[0] + ".pdf"
        video_url = f"{AZURE_URL}/{AZURE_CONTAINER_NAME}/{folder_path}/{file_name_end}"
        # s3.Object(bucket_name, folder_path + "/" + file_name_end).upload_file(
        #     local_directory + file_name_end
        # )
        with open(local_directory + file_name_end, "rb") as data:
            AZURE_CONTAINER_CLIENT.upload_blob(folder_path + "/" + file_name_end, data)
    else:
        video_url = (
            f"{AZURE_URL}/{AZURE_CONTAINER_NAME}/{folder_path}/{resume_file_name}"
        )
        # s3.Object(bucket_name, folder_path + "/" + resume_file_name).upload_file(
        #     file_name
        # )
        with open(file_name, "rb") as data:
            AZURE_CONTAINER_CLIENT.upload_blob(
                folder_path + "/" + resume_file_name, data
            )
    os.remove(file_name)
    logger.info(video_url)
    return video_url, file_name

def resume_parser_ml(file_url):
    try:
        url = f"{RESUME_PARSER_ML_HOST}resume-parser/"
        payload = json.dumps({"file_url": file_url})
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()["data"]
    except Exception:
        return False
    
def format_date_of_birth(date_string):
    if not date_string or not isinstance(date_string, str) or not date_string.strip():
        return None
    try:
        parsed_date = datetime.strptime(date_string.strip(), "%Y-%m-%d").date()
        return parsed_date
    except ValueError:
        return None


def format_ml_resume_data(resume_data):
    main_data = {
        "first_name": "",
        "last_name": "",
        "name": "",
        "title": "",
        "date_of_birth": "",
        "country_code": "",
        "phone_number": "",
        "email": "",
        "address": "",
        "professional_summary": "",
        "social_media_links": {},
        "github": "",
        "portfolio": "",
        "education": [],
        "work_experience": [],
        "soft_skills": [],
        "technical_skills": [],
        "spoken_languages": [],
        "projects": [],
        "awards": [],
        "certifications": [],
        "other_achievements": [],
    }

    try:
        logger.info("format_ml_resume_data")
        llm_response = resume_data.get("llm_response", {})
        logger.info("11")
        personal_information = llm_response.get("personalInformation", {})
        logger.info("22")
        address = personal_information.get("contactInformation", {}).get("address", "")
        logger.info("33")
        overall_summary = llm_response.get("overall_summary", "")
        logger.info("44")
        professional_summary = llm_response.get("professionalSummary", "")
        logger.info("55")
        social_media_links = personal_information.get("socialProfiles", {})
        logger.info("66")
        github = social_media_links.pop("github", "")
        logger.info("77")
        portfolio = social_media_links.pop("portfolio", "")
        logger.info("88")
        publications = llm_response.get("publications", [])
        logger.info("99")
        conferences_attended = llm_response.get("conferencesAttended", [])
        logger.info("100")
        professional_memberships = llm_response.get("professionalMemberships", [])
        logger.info("111")
        references = llm_response.get("references", [])
        logger.info("122")
        first_name = personal_information.get("name", {}).get("firstName", "")
        logger.info(f"122 {first_name}")
        last_name = personal_information.get("name", {}).get("lastName", "")
        logger.info(f"133 {last_name}")
        name = format_name(first_name, last_name)
        logger.info(f"134 {name}")
        title = personal_information.get("name", {}).get("jobTitle", "")
        logger.info(f"144 {title}")
        date_of_birth = personal_information.get("dateOfBirth", "")
        if date_of_birth:
            try:
                # Just validate the format, actual conversion happens in serializer
                datetime.strptime(date_of_birth, "%Y-%m-%d")
            except ValueError:
                date_of_birth = ""
        
        main_data["date_of_birth"] = date_of_birth
        # date_of_birth = personal_information.get("dateOfBirth", "")
        logger.info(f"155 {date_of_birth}")
        country_code = personal_information.get("contactInformation", {}).get("countryCode", "")
        logger.info(f"166 {country_code}")
        phone_number = personal_information.get("contactInformation", {}).get("phoneNumber", "")
        logger.info(f"177 {phone_number}")
        email = personal_information.get("contactInformation", {}).get("emailAddress", "")
        logger.info(f"188 {email}")
        formatted_address = format_address(address)
        logger.info(f"199 {formatted_address}")
        summary_format = get_professional_summary(professional_summary, overall_summary)
        logger.info(f"200 {summary_format}")
        education = transform_education_data(llm_response.get("education", []))
        logger.info(f"211 {education}")
        work_experience = transform_work_experience(llm_response.get("workExperience", []))
        logger.info(f"222 {work_experience}")
        soft_skills = merge_soft_skills(resume_data.get("generic_soft_skills", []), resume_data.get("work_experience_soft_skills", []))
        logger.info(f"233 {soft_skills}")
        technical_skills = merge_technical_skills(resume_data.get("generic_technical_skills", []), resume_data.get("work_experience_technical_skills", []))
        logger.info(f"244 {technical_skills}")
        spoken_languages = llm_response.get("skills", {}).get("spokenlanguages", [])
        logger.info(f"255 {spoken_languages}")
        projects = transform_projects(llm_response.get("projects", []))
        logger.info(f"266 {projects}")
        awards = extract_titles(llm_response.get("awardsAndHonors", []))
        logger.info(f"277 {awards}")
        certifications = llm_response.get("skills", {}).get("certifications", [])
        logger.info(f"288 {certifications}")
        other_achievements = aggregate_titles(publications, conferences_attended, professional_memberships, references)
        logger.info(f"299 {other_achievements}")

        # Update main_data with actual values
        main_data.update({
            "first_name": first_name,
            "last_name": last_name,
            "name": name,
            "title": title,
            "date_of_birth": date_of_birth,
            "country_code": country_code,
            "phone_number": phone_number,
            "email": email,
            "address": formatted_address,
            "professional_summary": summary_format,
            "social_media_links": social_media_links,
            "github": github,
            "portfolio": portfolio,
            "education": education,
            "work_experience": work_experience,
            "soft_skills": soft_skills,
            "technical_skills": technical_skills,
            "spoken_languages": spoken_languages,
            "projects": projects,
            "awards": awards,
            "certifications": certifications,
            "other_achievements": other_achievements,
        })
        return main_data
    except Exception as e:
        print(f"An error occurred while accessing the new resume parser: {str(e)}")
        return main_data
    