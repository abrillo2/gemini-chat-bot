def get_user_credentials():
    """Temporary: Skip external APIs for now"""
    logger.info("Skipping external APIs for testing")
    return None

def fetch_gmail_messages(creds):
    """Mock Gmail data"""
    return "Recent emails: Project updates, Team meeting, Newsletter"

def fetch_drive_files(creds):
    """Mock Drive data"""
    return "Recent files: project-plan.docx, presentation.pdf, data.xlsx"
