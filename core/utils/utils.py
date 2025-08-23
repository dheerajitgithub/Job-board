# """core.utils.utils"""

# import logging
import os,datetime,pytz
import string
import secrets
import re
from subprocess import Popen
from cryptography.fernet import Fernet
import requests
from core.settings import AZURE_CONTAINER_CLIENT, AZURE_CONTAINER_NAME, AZURE_URL, MEDIA_PATH, logger
from core.settings import CRYPT_KEY

# import pytz
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
# from reportlab.lib.units import inch
# import plotly.express as px
# import plotly.graph_objects as go
# from reportlab.lib.styles import ParagraphStyle


from django.core.files.base import ContentFile


# from django.utils import timezone
# from django.contrib.auth import get_user_model

# from asgiref.sync import async_to_sync

media_path = "media/"



# logger = logging.LoggerAdapter(logger, {"app_name": "core.utils.utils"})

# # def generate_random_password() -> str:
# #     """
# #         This function generate 8 digit random password
# #     """
# #     # ? Define character sets
# #     upper_case = string.ascii_uppercase
# #     lower_case = string.ascii_lowercase
# #     special_chars = string.punctuation
# #     digits = string.digits

# #     # ? Generate one character from each character set
# #     password = secrets.choice(upper_case)
# #     password += ''.join(secrets.choice(lower_case) for _ in range(3))
# #     password += secrets.choice(special_chars)
# #     password += ''.join(secrets.choice(digits) for _ in range(3))

# #     # ? Fill the rest of the password with random characters
# #     remaining_length = 8 - len(password)
# #     password += ''.join(secrets.choice(
# #         string.ascii_letters +
# #         digits +
# #         special_chars) for _ in range(remaining_length))

# #     # ? Shuffle the password to randomize the order
# #     password_list = list(password)
# #     secrets.SystemRandom().shuffle(password_list)
# #     password = ''.join(password_list)
# #     return password


def extract_serializer_error(serializer: object) -> str | dict:
    """
        This function takes serializer object and
        iterator the error & return's error string or 
        dict if error is too nested
    """
    print(serializer.errors)
    for key in serializer.errors.keys():
        error = serializer.errors[key]
        if isinstance(error, list):
            error = error[0]
        else:
            error = serializer.errors
    return error

def create_path(file_path, sub_path=None):
    """
    Create default media path and a sub-directory if it doesnt exists
    """
    try:
        if not os.path.exists(os.path.join(os.path.abspath(os.curdir), MEDIA_PATH)):
            os.mkdir(os.path.join(os.path.abspath(os.curdir), MEDIA_PATH))
        if not os.path.exists(
            os.path.join(os.path.abspath(os.curdir), MEDIA_PATH, file_path)
        ):
            os.mkdir(os.path.join(os.path.abspath(os.curdir), MEDIA_PATH, file_path))
        if sub_path and (not os.path.exists(
                os.path.join(
                    os.path.abspath(os.curdir), MEDIA_PATH, file_path, sub_path
                )
            )):
            os.mkdir(
                    os.path.join(
                        os.path.abspath(os.curdir), MEDIA_PATH, file_path, sub_path
                    )
                )
    except Exception as e:
        logger.error(f"Error while creating path: {e}")

import subprocess

def convert_w_mp4(in_file, out_file):
    command = [
        "/usr/bin/ffmpeg",
        "-i",
        in_file,
        "-c:v",
        "libx264",
        "-profile:v",
        "main",
        "-vf",
        "format=yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        out_file,
    ]
    subprocess.run(command)

def save_media(file, path_req=None) -> str:
    """
        Args:
            file(str) -> The file send by the user.
            path_req(None) 
        description:
            Custom function for storing the media files
        return:
            media_url 
    """
    if path_req:
        file_path = path_req
    else:
        file_path = "CompanyMedia/"
    create_path(file_path)
    curr_date = str(datetime.datetime.now(pytz.utc).timestamp()).replace(".","")
    file_path_name = file_path + curr_date + "." + file.name.split(".")[-1]
    file_name = os.path.join(os.path.abspath(os.curdir), MEDIA_PATH) + file_path_name
    fout = open(file_name, "wb+")
    file_content = ContentFile(file.read())
    for chunk in file_content.chunks():
        fout.write(chunk)
    fout.close()
    with open(file_name, "rb") as data:
        AZURE_CONTAINER_CLIENT.upload_blob(file_path_name, data)
    logger.info("File Saved")
    os.remove(file_name)
    media_url = f"{AZURE_URL}/{AZURE_CONTAINER_NAME}/{file_path_name}"
    return media_url

def convert_blob_to_mp4(blob_url):
    file_name = str(datetime.datetime.now(pytz.utc).timestamp())
    blob_file_name = file_name + ".blob"
    mp4_file_name = file_name + ".mp4"
    folder = "BlobToMp4/"
    r = requests.get(blob_url)
    open(blob_file_name, "wb").write(r.content)
    convert_w_mp4(blob_file_name, mp4_file_name)
    os.remove(blob_file_name)
    with open(mp4_file_name, "rb") as data:
        AZURE_CONTAINER_CLIENT.upload_blob(folder + mp4_file_name, data)
    os.remove(mp4_file_name)
    video_url = f"{AZURE_URL}/{AZURE_CONTAINER_NAME}/{folder}{mp4_file_name}"
    return video_url

def check_password_custom(password : str)->bool:
    """
        Args:
            password(str) -> The password of the user.
        description:
            Custom function for checking password 
        return:
            True 
    """
    if len(password) < 8 or len(password) > 16:
        return False

    if not any(char in "!@#$%^&*()-_+=." for char in password):
        return False

    if not re.search("\d", password):
        return False

    return True


def is_filter_required(input_key : str, data : dict) -> bool:
    """checking if filter is required for the given key"""
    return data.get(input_key) not in [None, "", "undefined"]


# def generate_unique_azure_file_name(file_path_name, base_file_name):
#     counter = 1
#     new_file_path_name = file_path_name
#     while True:
#         blob_client = AZURE_CONTAINER_CLIENT.get_blob_client(new_file_path_name)
#         if not blob_client.exists():
#             break
#         new_file_path_name = file_path_name + base_file_name.split('.')[0] + f"({counter})." + base_file_name.split('.')[-1]
#         counter += 1
#     return new_file_path_name

# def get_file_data(file, path_req=None) -> tuple:
#     """
#     get file data such as size , type , name
#     """
#     if path_req:
#         file_path = path_req
#     else:
#         file_path = "attachment_files/"
#     create_path(file_path)
#     base_file_name = file.name
#     curr_date = str(datetime.datetime.now(pytz.utc).timestamp()).replace(".","")
#     file_type = file.name.split(".")[-1]
#     file_name = os.path.join(os.path.abspath(os.curdir), MEDIA_PATH) + file_path + curr_date + "." + file_type
#     fout = open(file_name, "wb+")
#     file_content = ContentFile(file.read())
#     for chunk in file_content.chunks():
#         fout.write(chunk)
#     fout.close()
#     file_path_name = generate_unique_azure_file_name(file_path, base_file_name)
#     with open(file_name, "rb") as data:
#         AZURE_CONTAINER_CLIENT.upload_blob(file_path_name, data)
#     logger.info("Image Saved")
#     os.remove(file_name)
#     media_url = f"{AZURE_URL}/{AZURE_CONTAINER_NAME}/{file_path_name}"
#     return media_url, file_type, file.name, file.size


# def broadcast_prev_next_tasks(user_id, task_id, filters):
#     conversation_name = f"task_filter_{str(user_id)}_{str(task_id)}"
#     channel_layer = get_channel_layer()
#     print("conversation_name_2", conversation_name)
#     task_instance = TaskManagementTaskModel.objects.get(id = task_id)
#     queryset = TaskManagementTaskModel.objects.all()
#     user_instance = get_user_model().objects.get(id = user_id)
#     if user_instance.role.role_name == "Client":
#         filters["client"] = user_id
#     filterset = TaskManagementTaskListModelFilterSet(filters, queryset)
#     tasks = filterset.qs
#     next_task = tasks.filter(created_at__lt=task_instance.created_at).first()
#     previous_task = tasks.filter(created_at__gt=task_instance.created_at).last()
#     next = None
#     previous = None
#     if next_task:
#         next = str(next_task.id)
#     if previous_task:
#         previous = str(previous_task.id)
#     print(100000)
#     broadcast_data = {
#         "type" : "task_filter",
#         "next" : next,
#         "previous" : previous
#     }
#     print(broadcast_data)
#     async_to_sync(channel_layer.group_send)(
#             conversation_name,
#             broadcast_data,
#     )


# def broadcast_no_access_task_msg(conversation_name : str):
#     broadcast_data = {
#         "type" : "no_access_task"
#     }
#     channel_layer = get_channel_layer()
#     print(broadcast_data)
#     async_to_sync(channel_layer.group_send)(
#             conversation_name,
#             broadcast_data
#     )


# def delete_folder_and_subfolders(folder):
#     test_cases = folder.TestManagementTestCaseModel_folder.all()
#     for test_case in test_cases:
#         test_case.last_execution.all().delete()
#     folder.TestManagementTestCaseModel_folder.all().delete()
    
#     subfolders = folder.TestManagementTestFolderModel_parent_folder.all()
#     for subfolder in subfolders:
#         delete_folder_and_subfolders(subfolder)
    
#     folder.delete()


# def get_test_case_folder_count_recursive(folder, count=0, filters = {}):
    
#     # filters['last_execution__isnull'] = False
#     count += folder.TestManagementTestCaseModel_folder.filter(**filters).count()
#     subfolders = folder.TestManagementTestFolderModel_parent_folder.all()
#     for subfolder in subfolders:
#         count =  get_test_case_folder_count_recursive(
#             subfolder,
#             count=count, 
#             filters=filters
#         )
#     return count

# def get_test_execution_folder_count_recursive(folder, count=0, my_count=0, filters = {}):
#     filters['last_execution__isnull'] = False
#     my_count = folder.TestManagementTestCaseModel_folder.filter(**filters).distinct().count()
#     count += my_count
#     subfolders = folder.TestManagementTestFolderModel_parent_folder.all()
#     for subfolder in subfolders:
#         count =  get_test_execution_folder_count_recursive(
#             subfolder,
#             count=count, 
#             filters=filters,
#             my_count=my_count
#         )
#     return count

#     # return {
#     #     'count' : str(count),
#     #     'my_count' : str(my_count)
#     # }

# def get_test_reports_folder_count_recursive(folder, count=0, my_count=0, filters = {}):
#     filters['last_execution__isnull'] = False
    
#     my_count = folder.TestManagementTestCaseModel_folder.filter(**filters).distinct().count()
#     count += my_count
    
#     subfolders = folder.TestManagementTestFolderModel_parent_folder.all()
#     for subfolder in subfolders:
#         count =  get_test_reports_folder_count_recursive(
#             subfolder,
#             count=count, 
#             filters=filters,
#             my_count=my_count
#         )
        
#     return count

# def search_folders_recursive(search_val : str, project : CompanyProjectModel):
#     folder_ids = []
#     for folder in TestManagementTestFolderModel.objects.filter(project = project):
#         parent = folder
#         if search_val.lower() in folder.folder_title.lower():
#             folder_ids.append(parent.id)
#             while parent.parent_folder is not None:
#                 parent = parent.parent_folder
#                 folder_ids.append(parent.id)
#     folder_ids = list(set(folder_ids))
#     return folder_ids

# def search_outermost_parent_folders(folder, search_filter, parent_folder_ids=None):
#     if parent_folder_ids is None:
#         parent_folder_ids = set()

#     if folder.TestManagementTestCaseModel_folder.filter(**search_filter).exists():
#         outermost_folder = folder
#         # while outermost_folder.parent_folder is not None:
#         #     outermost_folder = outermost_folder.parent_folder
#         parent_folder_ids.add(outermost_folder.id)
#         return parent_folder_ids
    
#     # Recursively check each subfolder
#     subfolders = folder.TestManagementTestFolderModel_parent_folder.all()
#     for subfolder in subfolders:
#         search_outermost_parent_folders(subfolder, search_filter, parent_folder_ids)

#     return list(parent_folder_ids)


# def generate_current_progress_chart(project : CompanyProjectModel):
#     print("inside cur daw")
#     last_sprint = BoardsAndBacklogsSprintModel.objects.filter(status = "IN_PROGRESS", project = project).first()
#     statuses = project.status_workflow.task_statuses.filter(is_primary = True).order_by("progress")
#     categories = [i.status_name for i in statuses]
#     values = []
#     print("cat categpre", categories)
#     for status in statuses:
#         if last_sprint:
#             values.append(last_sprint.tasks.filter(project = project, task_status = status).count())
#         else:
#             values.append(TaskManagementTaskModel.objects.filter(project = project, task_status = status).count())
#     print("valuesss", values)
#     colors = ['#DAD2E4' for i in range(len(categories))]
#     fig = go.Figure([go.Bar(x=categories, y=values, text=values, textposition='auto', marker_color=colors)])
#     fig.update_layout(title="", xaxis_title="", yaxis_title="", showlegend=False,
#                       plot_bgcolor='rgba(0,0,0,0)',  # Remove plot background
#         paper_bgcolor='rgba(0,0,0,0)',
#         #  margin=dict(l=100, r=100, t=100, b=100),  # Increased padding around the chart
#         # width=1200,                    # Width of the image
#         # height=800,
#         autosize = True,
#         font=dict(
#             family="Arial, sans-serif",  # Font family
#             size=22,                     # Font size (increase/decrease as needed)
#             color="#747474"                # Font color
#         ),
#         title_font = dict(
#             family="Arial, sans-serif",  # Font family for other text
#             size=35,                     # Font size for other text
#             color="black"                # Font color for other text
#         )
#     )  # Remove paper background)
#     fig.add_shape(
#         type="rect",
#         x0=0, y0=0, x1=1, y1=1,
#         xref="paper", yref="paper",
#         line=dict(color="#CBCBCB", width=1),  # Border color and thickness
#         fillcolor='white',                  # Inside color (same as paper background)
#         xanchor="left",                     # Ensure it's around the content
#         yanchor="top",
#         xsizemode="scaled",
#         ysizemode="scaled",
#         layer="below",                      # Puts it behind the chart
#         editable=False,
#         opacity=1,
#     )
#     cur_timestamp = str(datetime.datetime.now().timestamp())
#     # Save the chart as an image
#     file_path = f"{MEDIA_PATH}{cur_timestamp}.png"
#     print(6, file_path)
#     fig.write_image(file_path, scale = 3, width = 1200, height = 800)
#     print(7)
#     return file_path


# def generate_progress_trend_chart(project : CompanyProjectModel):
#     print("inside prog tre")
#     cur_date = timezone.now().date()
#     if project.project_template == "SCRUM":
#         print(19)
#         last_sprint = BoardsAndBacklogsSprintModel.objects.filter(project = project, status = "IN_PROGRESS").first()
#         print(22)
#         if not last_sprint or not (last_sprint.start_date and last_sprint.due_date):
#             return ""
#         unformatted_dates = generate_dates(last_sprint.start_date, last_sprint.due_date)
#         dates = [i.strftime('%d %b %y') for i in unformatted_dates]
#     else:
#         print(20)
#         start_date = cur_date - datetime.timedelta(days = 9)
#         unformatted_dates = generate_dates(start_date, cur_date)
#         dates = [i.strftime('%d %b %y') for i in unformatted_dates]
#     print(21)
#     to_do = []
#     in_progress = []
#     done = []
#     print(18)
#     for day in unformatted_dates:
#         if project.project_template == "SCRUM":
#             report_instance = get_sprint_report_instance(project = project, day = day, sprint=last_sprint)
#         else:
#             report_instance = get_sprint_report_instance(project = project, day = day)
#         to_do.append(report_instance.to_do_count)
#         in_progress.append(report_instance.in_progress_count)
#         done.append(report_instance.done_count)

#     to_do_colors = ["#C3C3C3" for i in range(len(to_do))]
#     in_progress_colors = ["#6F5885" for i in range(len(in_progress))]
#     done_colors = ["#DAD2E4" for i in range(len(done))]
#     print(16)
#     fig = go.Figure()
#     fig.add_trace(go.Bar(x=dates, y=to_do, name="To-Do", marker_color=to_do_colors, text=to_do))
#     fig.add_trace(go.Bar(x=dates, y=in_progress, name="In Progress", marker_color=in_progress_colors, text=in_progress))
#     fig.add_trace(go.Bar(x=dates, y=done, name="Done", marker_color=done_colors, text=done))
#     print(17)
#     fig.update_layout(barmode='group', title="", xaxis_title="", yaxis_title="", showlegend=False,
#                       plot_bgcolor='rgba(0,0,0,0)',
#         paper_bgcolor='rgba(0,0,0,0)',
#         #  margin=dict(l=100, r=100, t=100, b=100),  # Increased padding around the chart
#         # width=1500,                    # Width of the image
#         # height=1200,
#         autosize = True,
#         font=dict(
#             family="Arial, sans-serif",  # Font family
#             size=26,                     # Font size (increase/decrease as needed)
#             color="#747474",                # Font color
#         ),
#         title_font = dict(
#             family="Arial, sans-serif",  # Font family for other text
#             size=35,                     # Font size for other text
#             color="black"               # Font color for other text
#         ))
#     fig.add_shape(
#         type="rect",
#         x0=0, y0=0, x1=1, y1=1,
#         xref="paper", yref="paper",
#         line=dict(color="#CBCBCB", width=1),  # Border color and thickness
#         fillcolor='white',                  # Inside color (same as paper background)
#         xanchor="left",                     # Ensure it's around the content
#         yanchor="top",
#         xsizemode="scaled",
#         ysizemode="scaled",
#         layer="below",                      # Puts it behind the chart
#         editable=False,
#         opacity=1,
#     )
#     cur_timestamp = str(datetime.datetime.now().timestamp())
#     # Save the chart as an image
#     file_path = f"{MEDIA_PATH}{cur_timestamp}.png"
#     print("file_2", file_path)
#     fig.write_image(file_path, scale = 3, width = 1200, height = 800)
#     return file_path

# def generate_scheduled_reports(context : dict, project : CompanyProjectModel, is_weekly= False):
#     print("inside schdule_reprt")
#     # Create the PDF document
#     if not os.path.exists(MEDIA_PATH):
#         os.mkdir(MEDIA_PATH)
#     cur_date = str(timezone.now().timestamp()).replace(".", "")
#     print(1)
#     pdf_file = f"{MEDIA_PATH}{context['project_name']}-{'EOD' if not is_weekly else 'Weekly'}-Report-{cur_date}.pdf"
#     print(2)

#     document = SimpleDocTemplate(pdf_file, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []

#     # Title and headers
#     elements.append(Paragraph(f"Hello {context['username']},", styles['Normal']))
#     elements.append(Spacer(1, 12))
#     print(3)
#     custom_title_style = ParagraphStyle(
#         name='CustomTitle',
#         fontName='Helvetica-Bold',
#         fontSize=16,
#         textColor="#252525",  # Change this to your desired color
#         spaceAfter=12,
#         alignment=1,  # Center alignment
#     )
#     custom_sub_title_style = ParagraphStyle(
#         name='CustomSubTitle',
#         fontName='Helvetica-Bold',
#         fontSize=12,
#         textColor="#252525",  # Change this to your desired color
#         spaceAfter=12,
#     )
#     elements.append(Paragraph(f"<b>{context['project_name']} - {'Daily EOD' if not is_weekly else 'Weekly'} Report</b>", custom_title_style))
#     elements.append(Spacer(1, 12))
#     print(4)
#     # Sprint details
#     if context['is_scrum']:
#         sprint_start_date = f"Sprint Start Date: {context['start_date']}"
#         sprint_end_date = f"Sprint End Date: {context['due_date']}"
#         days_left = f"Days Left: {context['days_left']}"

#         # Create a table with 3 columns to hold the sprint information
#         sprint_data = [[
#             Paragraph(sprint_start_date, ParagraphStyle('Normal', fontSize=9)),
#             Paragraph(sprint_end_date, ParagraphStyle('Normal', fontSize=9)),
#             Paragraph(days_left, ParagraphStyle('Normal', fontSize=9))
#         ]]
#         sprint_table = Table(sprint_data, colWidths=['*', '*', '*'], hAlign='CENTER')

#         # Add the table to elements
#         elements.append(sprint_table)
#     elements.append(Spacer(1, 12))
#     # Adding Key Highlights
#     elements.append(Paragraph("<b>Key Highlights of the day:</b>", styles['Normal']))
#     elements.append(Spacer(1, 12))
#     elements.append(Paragraph(f"1. No. of Tasks in To-Do: {context['to_do_count']}", styles['Normal']))
#     elements.append(Paragraph(f"2. No. of Tasks/Bugs in Progress: {context['in_progress_count']}", styles['Normal']))
#     elements.append(Paragraph(f"3. No. of Tasks/Bugs Done: {context['done_count']}", styles['Normal']))
#     elements.append(Paragraph(f"4. Percentage of Completion: {context['completion_percentage']}", styles['Normal']))
#     elements.append(Spacer(1, 24))

#     elements.append(Paragraph("<b>Current Progress</b>", custom_sub_title_style))
#     # Generate the first graph - Current Progress
#     print(11)
#     cur_progress_img_path = generate_current_progress_chart(project=project)
#     print(12)
#     # Adding the graph to the PDF
#     elements.append(Image(cur_progress_img_path, width=6*inch, height=3*inch))

#     elements.append(Paragraph("<b>Progress Trend</b>", custom_sub_title_style))
#     # Generate the second graph - Progress Trend

#     print(13)
#     progress_trend_img_path = generate_progress_trend_chart(project=project)
#     print(14, progress_trend_img_path)
#     # Adding the second graph to the PDF
#     print(progress_trend_img_path)
#     elements.append(Image(progress_trend_img_path, width=6*inch, height=3*inch))

#     # Footer

#     # Build the PDF
#     document.build(elements)
#     os.remove(cur_progress_img_path)
#     os.remove(progress_trend_img_path)
#     # with open(pdf_file, "rb") as data:
#     #     AZURE_CONTAINER_CLIENT.upload_blob(f"PM_Tool/{pdf_file}", data)
#     # os.remove(pdf_file)
#     # media_url = f"{AZURE_URL}/{AZURE_CONTAINER_NAME}/PM_Tool/{pdf_file}"
#     print("pdf_file", pdf_file)
#     return pdf_file


# def crypt_password(password):
#     fernet = Fernet(CRYPT_KEY)
#     enc_pass = fernet.encrypt(password.encode())
#     enc_pass = enc_pass.decode("utf-8")
#     return enc_pass


# def decrypt_password(password):
#     fernet = Fernet(CRYPT_KEY)
#     password = str.encode(password)
#     dec_pass = fernet.decrypt(password).decode()
#     return dec_pass

def generate_alphanumeric_code(length):
    """
    This method is used to generate the referral code based on the length specified.
    The generated code is combination on alphanumeric character along with special characters.
    :param length: Integer value
    :return: generated code
    """
    characters = string.ascii_letters + string.digits
    result_str = "".join(secrets.choice(characters) for _ in range(length))
    return result_str

def crypt_password(password):
    fernet = Fernet(CRYPT_KEY)
    enc_pass = fernet.encrypt(password.encode())
    enc_pass = enc_pass.decode("utf-8")
    return enc_pass

def format_name(first_name=None, last_name=None, name = None):
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif name:
        return name
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    else:
        return "NA"
    
def create_path(file_path, sub_path=None):
    """
    Create default media path and a sub-directory if it doesnt exists
    """
    try:
        if not os.path.exists(os.path.join(os.path.abspath(os.curdir), media_path)):
            os.mkdir(os.path.join(os.path.abspath(os.curdir), media_path))
        if not os.path.exists(
            os.path.join(os.path.abspath(os.curdir), media_path, file_path)
        ):
            os.mkdir(os.path.join(os.path.abspath(
                os.curdir), media_path, file_path))
        if sub_path and (not os.path.exists(
            os.path.join(
                os.path.abspath(
                    os.curdir), media_path, file_path, sub_path
            )
        )):
            os.mkdir(
                os.path.join(
                    os.path.abspath(os.curdir), media_path, file_path, sub_path
                )
            )
    except Exception as e:
        logger.info(f"Error while creating path: {e}")


def convert_to_pdf(input_docx, out_folder):
    logger.info("convert_to_pdf Envoked")
    nums = [i for i in range(0, 999999)]
    LIBRE_OFFICE = "/usr/bin/soffice"
    rand_num = secrets.choice(nums)
    p = Popen(
        [
            LIBRE_OFFICE,
            "--headless",
            f"-env:UserInstallation=file:///tmp/{rand_num}",
            "--convert-to",
            "pdf",
            "--outdir",
            out_folder,
            input_docx,
        ]
    )
    logger.info([LIBRE_OFFICE, "--convert-to", "pdf", input_docx])
    p.communicate()

from user_agents import parse

def get_details_from_request(request):
    # ? check ip address
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    # ? get user agency details to know about browser and device formation
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    parsed_user_agent = parse(user_agent)


    # Do something with the extracted information
    request_data = {
        'browser': parsed_user_agent.browser.family,
        'browser_version': parsed_user_agent.browser.version_string,
        'os': parsed_user_agent.os.family,
        'os_version_string': parsed_user_agent.os.version_string,
        'device': parsed_user_agent.device.family,
        'device_brand': parsed_user_agent.device.brand,
        'device_model': parsed_user_agent.device.model,
        "ip_address" : ip 
    }
    return request_data
