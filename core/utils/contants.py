"""Constants to use throughout the application"""

EXCEPTION_MESSAGE = "Something went wrong"
DEFAULT_API_SUCCESS_MESSAGES = {
    "POST": "Created successfully",
    "PUT": "Updated successfully",
    "DELETE": "Deleted successfully",
    "GET" : "Success"
}
SUCCESS_MSG = "Success"

SIGNATURE_EXPIRED_MSG = "Signature has expired."
USER_DOESNT_EXIST_MSG = "User does not exist"
INCORRECT_EMAIL = "Incorrect email"
USER_NOT_ACTIVE = "Uh-oh! It appears that the account is not yet active"
USER_NOT_VERIFIED = "Uh-oh! It appears that the account is not yet verified"

INCORRECT_PASSWORD = "Uh-oh! It appears that the password entered is incorrect."

DEAFULT_INCORRECT_ID_ERROR_MESSAGE = "Id does not exist"

PASSWORD_CHANGE_SUCESSFULLY_MESSAGE = {
    "POST": "Link for updating your password has been successfully sent to your email ID",
    "PUT" : "Password Changed Successfully"
}


LOGOUT_SUCESSFULLY_MESSAGE = {
    "POST": "Logged out successfully",
}

PASSWORD_STRING_VALIDATION_MSG = {
   "PUT": "Password must have atleast one special character,one integer and should be between 8 to 16 characters"
}

PASSWORD_STRING_VALIDATION = "Password must have atleast one special character,one integer and should be between 8 to 16 characters"

CONFIRM_PASSWORD_VALIDATION = "Wrong new password, Please give same password as new password"

NEW_PASSWORD_SAME_AS_OLD_PASSWORD = "New password cannot be the same as current one"

INCORRECT_CURRENT_PASSWORD = "Current password is incorrect"
USER_PROFILE_SUCCESS_MESSAGE = {
    "PUT": "Details Updated Sucessfully",
    "GET" : "Success",
    "DELETE" : "Client Deleted Successfully"
}

PROFILE_PICTURE_SUCCESS_MESSAGE = {
    "POST" : "Uploaded Successfully",
}

COMPANY_DELETE_TASK_ATTACHMENT_MESSAGE = {
    "DELETE" : "File attachment removed"
}

FILE_ATTACHMMENT_ID_DOES_NOT_EXISTS = "File attachment with this id does not exist"

MANAGE_TASK_STATUS_MESSAGE = {
    "PUT"  : "Permissions updated Successfully",
    "GET"  : "Success",
}

PROJECT_ID_DOES_NOT_EXISTS = "Project with this ID does not exist"

USER_EMAIL_ALREADY_EXISTS_MESSAGE = "User with this email already exists"

USER_USERNAME_ALREADY_EXISTS_MESSAGE = "User with this username already exists"

USER_ID_DOES_NOT_EXIST = "User with this ID does not exist"

USERS_SUCCESS_MESSAGE = {
    "POST": "User created successfully",
    "PUT": "User updated successfully",
    "GET" : "Success",
    "DELETE" : "User deleted successfully"
}

DELETE_TASK_ATTACHMENT_MESSAGE = {
    "DELETE" : "Attachment deleted Successfully"
}

DOCUMENT_MESSAGE = {
    "POST" : "Document Created Successfully",
    "PUT"  : "Document Updated Successfully",
    "GET"  : "Success",
    "DELETE" : "Document Deleted Successfully"
}

DOCUMENT_ID_DOES_NOT_EXISTS = "Document with this ID does not exist"

TASK_MOVED_TO_SPRINTS_SUCCESS_MESSAGE = {
        "POST" : "Tasks moved successfully",
    }

GANTT_CHART_MESSAGE = {
    "PUT": "Data updated successfully",
    "GET" : "Success",
}

ACTIVE_SPRINT_TASK_MOVED_SUCCESS_MESSAGE = {
        "POST" : "Tasks moved successfully",
    }
BOARDS_ACTIVE_SPRINT_MESSAGE = {
    "GET"  : "Success",
}

TASK_ALREADY_IN_STATUS_ERROR_MESSAGE = "Task id already exists in this status"

TASK_STATUS_ID_DOES_NOT_EXISTS = "Task Status with this ID does not exist"

GENERATE_BULK_TEMPLATE_SUCCESS_MESSAGE = {
    "POST": "Excel file downloaded successfully",
}

SPRIONT_CLOSED_SUCCESS_MESSAGE = {
        "POST" : "Sprint closed successfully",
    }

FILE_UPLOAD_IN_TASK_CREATE_FORM_SUCCESS_MESSAGE = {
        "POST" : "File added successfully",
    }

TEST_CASES_FOLDERS_MESSAGE = {
    "POST" : "Folder Created Successfully",
    "PUT"  : "Folder Updated Successfully",
    "GET"  : "Success",
    "DELETE" : "Folder Deleted Successfully"
}

FOLDER_ID_DOES_NOT_EXISTS = "Folder with this ID does not exist"

FOLDER_ALREADY_ERROR_MESSAGE = "Folder with this id already exists"

FOLDER_INCORRECT_DELETE_ID_MESSAGE = "Incorrect Folder id"

FOLDER_NAME_ALREADY_ERROR_MESSAGE = "Folder name already exists in this project"

PARENT_FOLDER_ID_DOES_NOT_EXISTS = "Parent Folder with this ID does not exist"

EMAIL_ALREADY_EXISTS = "Email already Exists"

COMPANY_WEBSITE_ALREADY_EXISTS = "Company Website already Exists"

PHONE_NUMBER_ALREADY_EXISTS = "Phone Number already Exists"

COMPANY_VALIDATION_MESSAGE = "Company with this name already Exists"

COMPANY_EXISTS_MESSAGE = "Company with id does not exist's"

JOB_EXISTS_MESSAGE = "Job with this id does not exist's"

COMPANY_EXISTS_MESSAGE = "Company with this id does not exist's"

JOB_SUCCESS_MESSAGE = {
    # "POST": " created",
    "PUT": "Job Updated Successfully",
    "GET" : "Success",
    "DELETE" : "Job deleted Successfully"
}

JOB_INSTANCE_MESSAGE = {
    "GET" : "Success",
    "DELETE" : "Deleted Successfully"
}

CV_UPLOAD_SUCCESS_MESSAGE = {
    "POST": "CV uploaded Successfully",
    "PUT": "CV updated Successfully",
    "GET" : "Success",
    "DELETE" : "CV deleted Successfully"
}

APPLY_JOB_SUCCESS_MESSAGE = {
    "POST": "Job applied Sucessfully",
    "GET" : "Success"
}

SHORTLIST_JOB_SUCCESS_MESSAGE = {
    "POST": "Job saved Sucessfully",
    "PUT" : "saved job removed",
    "GET" : "Success"
}

MAIL_SEND_SUCCESS_MESSAGE = {
    "POST": "Mail Send Sucessfully"
}

CANDIDATE_RESUME_SUCCESS_MESSAGE = {
    # "POST": "Job Shortlist Sucessfully",
    "GET" : "Success"
}