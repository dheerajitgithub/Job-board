import json, logging
from core.settings import logger



with open("candidate/hardskills_sorted.json", "r") as file:
    hs_extracted_dict = json.load(file)
with open("candidate/softskills_sorted.json","r") as file:
    ss_extracted_dict=json.load(file)

logger = logging.LoggerAdapter(logger, {"app_name": "candidate.client.utils.cv_score"})



def calculate_hardskill_score(matched_skills, job_skills, is_experience=True):
    """
    Calculate score for matched hard skills.
    
    Args:
        matched_skills: List of matched skills
        job_skills: List of required job skills
        is_experience: Boolean indicating if these are experience-based skills
    
    Returns:
        Float score value
    """
    try:
        if not job_skills:
            return 0
            
        # Determine master score based on number of job skills
        if is_experience:
            if len(job_skills) <= 4:
                master_score = 45
            elif len(job_skills) <= 6:
                master_score = 55
            else:
                master_score = 60
        else:
            if len(job_skills) <= 4:
                master_score = 2
            elif len(job_skills) <= 6:
                master_score = 3
            else:
                master_score = 5
        
        # Calculate per-skill score
        per_skill_score = master_score / len(job_skills)
        
        # Calculate total score based on matches
        return per_skill_score * len(matched_skills)
    except Exception as e:
        logging.error(f"Error in calculate_hardskill_score: {str(e)}")
        return 0


def calculate_softskill_score(matched_skills, job_skills):
    """
    Calculate score for matched soft skills.
    
    Args:
        matched_skills: List of matched soft skills
        job_skills: List of required soft skills
    
    Returns:
        Float score value
    """
    try:
        if not job_skills:
            return 0
            
        # Determine master score based on number of soft skills
        if len(job_skills) <= 4:
            master_score = 3
        elif len(job_skills) <= 6:
            master_score = 4
        else:
            master_score = 5
        
        # Calculate per-skill score
        per_skill_score = master_score / len(job_skills)
        
        # Calculate total score based on matches
        return per_skill_score * len(matched_skills)
    except Exception as e:
        logging.error(f"Error in calculate_softskill_score: {str(e)}")
        return 0


def job_description_details(job_data):
    try:

        ml_key_hardskills = job_data.get("hardskills")
        ml_key_softskills = job_data.get("softskills")
        manual_skills=job_data.get('manual_keyskills', [])
        
        job_type = job_data.get('job_type', '')
        
        job_experience_min = job_data.get('experience_min', 0)
        job_experience_max = job_data.get('experience_max', 0)
        
        job_location = job_data.get('location', []) 
        
        job_education = job_data.get('education', '')
        
        job_title = job_data.get('jobtitle', '')

        return (ml_key_hardskills, ml_key_softskills, job_type, job_experience_min,
                job_experience_max, job_location, job_education, job_title,manual_skills)
    
    except Exception as e:
        print(f"An error occurred while extracting job details: {e}")
        # Return None or a tuple of None values, depending on your use case
        return ([], [], '', '', '', [], '', '')
    

def internship_or_not(resume_data):
  Internship_text = ''
  for i in range(len(resume_data.get('workExperience',{}))):
    text =  resume_data.get('workExperience')[i]['originalJobTitle']
    Internship_text = Internship_text + text + ' '
  i1 = Internship_text.lower()
  i1 = i1.replace(",",' ')
  resume_text_list = i1.split(' ')
  is_intern_or_internship_present = any(role.lower() in ['intern', 'internship'] for role in resume_text_list)
  return is_intern_or_internship_present


'''
    ngrams function is used to create the ngrams of the input sentence.
    For eg:-
        input = " i am a data scientist"
        and n is 2 then
        output = ["i am","am a","a data","data scientist"]
'''

def ngrams(input, n):
    input = input.split(' ')
    output = []
    for i in range(len(input)-n+1):
        output.append(input[i:i+n])
    return output


def hardskill_matcher(text, hs_extracted_dict):
    text =  text.lower()
    hardskill_list = []
    text_ngrams = []
    n = 6
    ## here we are storing the ngrams data into the list - 1 gram to 6 gram data is stored.
    for i in range(1, n+1):
        ngram = [' '.join(x) for x in ngrams(text, i)]
        text_ngrams = text_ngrams+ngram
    

    for i in text_ngrams:
        try:
            skill_alpha_dict = hs_extracted_dict[i[0].lower()] # Get the first character
            for j in skill_alpha_dict.keys():
                if i in skill_alpha_dict[j]:
                    hardskill_list.append(j)
                # else:
                #     skill_misc = hs_extracted_dict['#misc'] # Look in miscellaneous dictionary
                #     for k in skill_misc.keys():
                #         if i in skill_misc[k]:
                #             hardskill_list.append(k)

        except Exception as e1:
            pass
    return list(set(hardskill_list))


## Function to get the list of softskills from the given text
# Here Input text : text, softskills dictionary : ss_extracted_dict
def softskill_matcher(text, ss_extracted_dict):
    text =  text.lower()
    softskill_list = []
    text_ngrams = []
    n = 6
    ## here we are storing the ngrams data into the list - 1 gram to 6 gram data is stored.
    for i in range(1, n+1):
        ngram = [' '.join(x) for x in ngrams(text, i)]
        text_ngrams = text_ngrams+ngram
    

    for i in text_ngrams:
        try:
            skill_alpha_dict = ss_extracted_dict[i[0].lower()] # Get the first character
            for j in skill_alpha_dict.keys():
                if i in skill_alpha_dict[j]:
                    softskill_list.append(j)
        except Exception as e1:
            # print('softskill_matcher', e1)
            pass
    return list(set(softskill_list))


def match_skills(source_skills, target_skills,resume_text):
    """
    Match skills between source and target lists, handling partial matches.
    
    Args:
        source_skills: List of skills to check against target
        target_skills: List of required skills to match against
    
    Returns:
        List of matched skills from target_skills
    """
    try:  
        matched_skills = []
        source_skills = [str(skill).lower() for skill in source_skills]
        target_skills = [str(skill).lower() for skill in target_skills]
        
        for target in target_skills:
            for source in source_skills:
                # Handle multi-word skills
                if len(source.split()) > 1 and len(target.split()) > 1:
                    if source.__contains__(target) or target.__contains__(source):
                        if target in resume_text.lower():
                            matched_skills.append(target)
                # Handle single-word skills
                elif len(source.split()) == 1 and len(target.split()) == 1:
                    if source.__contains__(target) or target.__contains__(source):
                        # Extra check for single-character matches
                        if len(source) == 1 and len(target) == 1:
                            matched_skills.append(target)
                        elif len(source) > 1 and len(target) > 1:
                            matched_skills.append(target)
                # Handle mixed cases (one single-word, one multi-word)
                elif len(source.split()) == 1 and target.__contains__(source):
                    if target in resume_text.lower():
                        matched_skills.append(target)
                elif len(target.split()) == 1 and source.__contains__(target):
                    if target in resume_text.lower():
                        matched_skills.append(target)
        
        return list(set(matched_skills))
    except Exception as e:
        logging.error(f"Error in match_skills: {str(e)}")
        return []
    

def calculate_degree_score(education_text, job_education):
    """Calculate score based on education level."""
    if not education_text:
        return 0
        
    if job_education:
        if 'master' in education_text and 'master' in job_education:
            return 5
        elif 'bachelor' in education_text and 'bachelor' in job_education:
            return 5
        elif 'master' in education_text:
            return 4
        elif 'bachelor' in education_text:
            return 3
        return 2
    else:
        if 'master' in education_text:
            return 4
        elif 'bachelor' in education_text:
            return 3
        return 2


def calculate_job_title_score(position, job_title):
    """Calculate score based on job title match."""
    if not position or not job_title:
        return 0
        
    if job_title.lower() == position.lower():
        return 5
    
    for word in position.split():
        if word.lower() in job_title.lower():
            return 2
    return 0


def calculate_experience_score(job_type, job_title_score, total_experience, 
                             job_experience_max, job_experience_min, internship):
    """Calculate score based on experience."""
    if job_type.lower() == 'internship':
        if (job_title_score == 5 and (internship or total_experience > 0)):
            return 10
        elif internship or total_experience > 0:
            return 6
        return 0
    
    if job_title_score == 5 and total_experience >= job_experience_max:
        return 10
    elif job_title_score == 5 and total_experience >= job_experience_min:
        return 10
    elif job_title_score == 2 and total_experience >= job_experience_max:
        return 5
    elif job_title_score == 2 and total_experience >= job_experience_min:
        return 5
    elif total_experience > 0:
        return 3
    elif internship:
        return 2
    return 0


def calculate_skills_scores(parsing_data, job_hardskills, job_softskills, resume_text):
    """Calculate scores for different types of skills."""
    try:
        # Extract skills from parsing data
        exp_skills = list(set(parsing_data.get('work_experience_technical_skills', [])))
        tech_skills = list(set(parsing_data.get('generic_technical_skills', [])))
        soft_skills = list(set(parsing_data.get('work_experience_soft_skills', [])))
        
        # Match skills
        matched_exp_hs = match_skills(exp_skills, job_hardskills, resume_text)
        remaining_hs = list(set(job_hardskills) - set(matched_exp_hs))
        matched_tech_hs = match_skills(tech_skills, remaining_hs, resume_text)
        
        matched_softskills = match_skills(soft_skills, job_softskills, resume_text)
        
        # Calculate scores
        exp_hs_score = calculate_hardskill_score(matched_exp_hs, job_hardskills, is_experience=True)
        tech_hs_score = calculate_hardskill_score(matched_tech_hs, remaining_hs, is_experience=False)
        soft_score = calculate_softskill_score(matched_softskills, job_softskills)
        
        return {
            'scores': {
                'experience_hardskill_score': exp_hs_score,
                'generic_hardskill_score': tech_hs_score,
                'experience_softskills_score': soft_score
            },
            'total': exp_hs_score + tech_hs_score + soft_score,
            'matched_exp_hs': matched_exp_hs,
            'matched_tech_hs': matched_tech_hs,
            'matched_softskills': matched_softskills,
            'missed_hardskills': list(set(job_hardskills) - set(matched_exp_hs + matched_tech_hs)),
            'missed_softskills': list(set(job_softskills) - set(matched_softskills)),
            'additional_skills': list(set(exp_skills + tech_skills) - set(matched_exp_hs + matched_tech_hs))
        }
    except Exception as e:
        logging.error(f"Error in calculate_skills_scores: {str(e)}")
        return {
            'scores': {'experience_hardskill_score': 0, 'generic_hardskill_score': 0, 'experience_softskills_score': 0},
            'total': 0,
            'matched_exp_hs': [],
            'matched_tech_hs': [],
            'matched_softskills': [],
            'missed_hardskills': job_hardskills,
            'missed_softskills': job_softskills,
            'additional_skills': []
        }

def calculate_location_score(resume_data, job_location, job_title_score, exp_hardskill_score):
    """Calculate score based on location match."""
    try:
        parsed_location = (resume_data.get('personalInformation', {})
                         .get('contactInformation', {})
                         .get('address', {})
                         .get('city', '').lower())
        
        if not parsed_location or not job_location:
            return 0

        # Normalize job location
        if isinstance(job_location, list):
            job_location = [loc.lower().split('-')[0] for loc in job_location]
        else:
            job_location = job_location.lower().split('-')[0]

        # Check location match
        location_found = any(loc in parsed_location for loc in (job_location if isinstance(job_location, list) else [job_location]))

        # Calculate score based on other factors
        if job_title_score >= 5 and exp_hardskill_score >= 55 and location_found:
            return 5
        elif job_title_score >= 5 and exp_hardskill_score >= 55:
            return 3
        elif (job_title_score >= 5 or exp_hardskill_score >= 55) and location_found:
            return 3
        elif job_title_score >= 5 or exp_hardskill_score >= 55:
            return 2
        elif location_found:
            return 2
        return 0
    except Exception as e:
        logging.error(f"Error calculating location score: {str(e)}")
        return 0

def get_default_response(job_hardskills, job_softskills, parsing_data):
    """Return default response structure when critical errors occur."""
    return {
        'project_resume_hardskills': [],
        'generic_resume_hardskills': [],
        'resume_additional_hardskills': [],
        'resume_softskills': [],
        'job_hardskills': job_hardskills,
        'job_softskills': job_softskills,
        'missed_hardskills': job_hardskills,
        'missed_softskills': job_softskills,
        'total_score': 0,
        'scores_dict': {
            'degree_score': 0,
            'job_title_score': 0,
            'experience_score': 0,
            'experience_hardskill_score': 0,
            'experience_softskills_score': 0,
            'generic_hardskill_score': 0,
            'location_score': 0
        },
        'resume_parser': parsing_data,
        'skill_count': 0,
        'year_skill_data': parsing_data.get('year_skill_data', {}) if parsing_data else {}
    }


def model_scoring(job, parsing_data):
    try:
        job_keyword_ss, job_keyword_hs = [], []
        resume_text=parsing_data.get('resume_text','')
        # Initialize default response structure
        filtered_skill_count = {}
        final_model_dict = {
            'project_resume_hardskills': [],
            'generic_resume_hardskills': [],
            'resume_additional_hardskills': [],
            'resume_softskills': [],
            'job_hardskills': [],
            'job_softskills': [],
            'missed_hardskills': [],
            'missed_softskills': [],
            'total_score': 0,
            'scores_dict': {
                'degree_score': 0,
                'job_title_score': 0,
                'experience_score': 0,
                'experience_hardskill_score': 0,
                'experience_softskills_score': 0,
                'generic_hardskill_score': 0,
                'location_score': 0
            },
            'resume_parser': {},
            'skill_count': {},
            'year_skill_data': {}
        }
        # Extract base data with error handling
        parsed_score_dict = {}
        resume_data = parsing_data.get('llm_response', {})
        total_score = 0
        # Calculate total experience
        try:
            year_skill_data = parsing_data.get('year_skill_data', {})
            if year_skill_data:
                first_year = min(year_skill_data.keys())
                last_year = max(year_skill_data.keys())
                total_experience = int(last_year) - int(first_year)
            else:
                total_experience = 0
        except Exception as e:
            logging.error(f"Error calculating experience: {str(e)}")
            total_experience = 0

        # Get job description details
        try:

            # logger.info(f"Getting job description details...{job}")
            (job_keyword_hs, job_keyword_ss, job_type, 
             job_experience_max, job_experience_min, 
             job_location, job_education, job_title,manual_skills) = job_description_details(job)
            try:

                manual_skills_lower = list(set(str(skill).lower() for skill in manual_skills))
                job_keyword_hs_lower = list(set(str(skill).lower() for skill in job_keyword_hs))
                job_keyword_ss_lower = list(set(str(skill).lower() for skill in job_keyword_ss))
                existing_keywords = set(job_keyword_hs_lower + job_keyword_ss_lower)
                unique_manual_skills = [skill for skill in manual_skills_lower if skill not in existing_keywords]
                skills_paragraph_1 = ' '.join(unique_manual_skills)

                #skill matcher for hard skill or soft skills

                manual_hardskills=hardskill_matcher(skills_paragraph_1, hs_extracted_dict)
                manual_softskills=softskill_matcher(skills_paragraph_1, ss_extracted_dict)
                
                job_keyword_hs.extend(manual_hardskills)
                job_keyword_ss.extend(manual_softskills)
                logger.info(f"job_keyword_hs_lower: {job_keyword_hs_lower}")
                logger.info(f"job_keyword_ss_lower: {job_keyword_ss_lower}")
                logger.info(f"existing_keywords: {existing_keywords}")
                logger.info(f"skills_paragraph_1: {skills_paragraph_1}")
                logger.info(f"manual_hardskills: {manual_hardskills}")
                logger.info(f"manual_softskills: {manual_softskills}")
                logger.info(f"unique_manual_skills: {unique_manual_skills}")
            except Exception as err:
                logging.info(f"Exception occurred in skill matcher {str(err)}")

            job_hardskills_lower = [skill.lower() for skill in job_keyword_hs]
            final_model_dict['job_hardskills'] = job_keyword_hs
            final_model_dict['job_softskills'] = job_keyword_ss

            # try:
            #     for skill, count in parsing_data.get('skill_count', {}).items():
            #         if any(job_skill in skill.lower() or skill.lower() in job_skill for job_skill in job_hardskills_lower):
            #             filtered_skill_count[skill] = count
            # except Exception as err:
            #     logging.info(f"Exception occurred in skill filter {str(err)}")
            skill_count_skills=list(parsing_data.get('skill_count', {}).keys())
            skill_count_skills=[skill.lower() for skill in skill_count_skills]
            matched_skill_count_skills=match_skills(skill_count_skills,job_hardskills_lower,resume_text)
            logging.info(f"matched_skill_count_skills {matched_skill_count_skills}")
            for skill, count in parsing_data.get('skill_count', {}).items():
                if skill.lower() in matched_skill_count_skills:
                    filtered_skill_count[skill] = count
            
        except Exception as e:
            logging.error(f"Error processing job description: {str(e)}")
            job_keyword_hs, job_keyword_ss = [], []
            job_type, job_title = "", ""
            job_experience_max, job_experience_min = 0, 0
            job_location, job_education = "", ""

        # Calculate degree score
        try:
            education_text = str(resume_data.get('education', '')).lower()
            degree_score = calculate_degree_score(education_text, job_education)
            parsed_score_dict['degree_score'] = degree_score
            total_score += degree_score
        except Exception as e:
            logging.error(f"Error calculating degree score: {str(e)}")
            parsed_score_dict['degree_score'] = 0

        # Calculate job title score
        try:
            position = resume_data.get('personalInformation', {}).get('name', {}).get('jobTitle', "")
            job_title_score = calculate_job_title_score(position, job_title)
            parsed_score_dict['job_title_score'] = job_title_score
            print("job_title_score", job_title_score)
            total_score += job_title_score
        except Exception as e:
            logging.error(f"Error calculating job title score: {str(e)}")
            parsed_score_dict['job_title_score'] = 0

        # Calculate experience score
        try:
            internship = internship_or_not(resume_data)
            experience_score = calculate_experience_score(
                job_type, job_title_score, total_experience,
                job_experience_max, job_experience_min, internship
            )
            parsed_score_dict['experience_score'] = experience_score
            print('experience_score', experience_score)
            total_score += experience_score
        except Exception as e:
            logging.error(f"Error calculating experience score: {str(e)}")
            parsed_score_dict['experience_score'] = 0

        # Calculate skills scores.
        try:
            skills_scores = calculate_skills_scores(
                parsing_data, job_keyword_hs, job_keyword_ss, resume_text
            )
            parsed_score_dict.update(skills_scores['scores'])
            print("skills_scores", skills_scores)
            total_score += skills_scores['total']
            final_model_dict.update({
                'project_resume_hardskills': skills_scores['matched_exp_hs'],
                'generic_resume_hardskills': skills_scores['matched_tech_hs'],
                'resume_additional_hardskills': skills_scores['additional_skills'],
                'resume_softskills': skills_scores['matched_softskills'],
                'missed_hardskills': skills_scores['missed_hardskills'],
                'missed_softskills': skills_scores['missed_softskills']
            })
        except Exception as e:
            logging.error(f"Error calculating skills scores: {str(e)}")
            parsed_score_dict.update({
                'experience_hardskill_score': 0,
                'experience_softskills_score': 0,
                'generic_hardskill_score': 0
            })

        # Calculate location score
        try:
            location_score = calculate_location_score(
                resume_data, job_location, job_title_score,
                parsed_score_dict.get('experience_hardskill_score', 0)
            )
            parsed_score_dict['location_score'] = location_score
            print("location_score", location_score)
            total_score += location_score
        except Exception as e:
            logging.error(f"Error calculating location score: {str(e)}")
            parsed_score_dict['location_score'] = 0
        print("Done", total_score)
        # Update final results
        final_model_dict.update({
            'total_score': int(round(total_score, 0)),
            'scores_dict': parsed_score_dict,
            'resume_parser': resume_data,
            'skill_count': filtered_skill_count,
            'year_skill_data': parsing_data.get('year_skill_data', {})
        })

        return final_model_dict

    except Exception as e:
        logging.error(f"Critical error in model_scoring: {str(e)}", exc_info=True)
        return get_default_response(job_keyword_hs, job_keyword_ss, parsing_data)
    

def get_manual_skills(hard_skills, soft_skills, key_skills):
    try:
        hard_skills_set = set(hard_skills)
        soft_skills_set = set(soft_skills)
        manual_keyskills = [skill for skill in key_skills if skill not in hard_skills_set and skill not in soft_skills_set]
        return manual_keyskills
    except Exception as e:
        return []