"""
Mock Email Service - Prints emails to console instead of sending.
For testing purposes only.
"""

import time
from datetime import datetime


def send_email(to_email: str, subject: str, body: str, institution: str = "University") -> dict:
    """
    Mock email sending - prints to console instead of sending.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        institution: Name of the issuing institution
    
    Returns:
        dict with status and message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "=" * 60)
    print("MOCK EMAIL SERVICE")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("-" * 60)
    print(body)
    print("-" * 60)
    print("=" * 60)
    print("END OF MOCK EMAIL")
    print("=" * 60 + "\n")
    
    return {
        "status": "sent",
        "to": to_email,
        "timestamp": timestamp,
    }


def send_transcript_notification(
    student_email: str,
    student_name: str,
    hash_value: str,
    verification_url: str,
    institution: str,
) -> dict:
    """
    Send transcript notification email to student.
    
    Args:
        student_email: Student's email address
        student_name: Student's name
        hash_value: SHA-256 hash of the transcript
        verification_url: Full URL with token for accessing transcript
        institution: Name of issuing institution
    
    Returns:
        dict with status
    """
    subject = "Your Academic Transcript is Ready"
    
    body = f"""Dear {student_name or 'Student'},

Your academic transcript has been issued by {institution}.

You can view and download your transcript using the secure link below:

{verification_url}

IMPORTANT INFORMATION:
- This link will expire in 24 hours
- The link can only be used ONCE for download
- Keep this link secure and do not share it

If you did not request this transcript or have any questions, please contact your institution directly.

Best regards,
{institution}
"""
    
    return send_email(student_email, subject, body, institution)


def send_employer_notification(
    employer_email: str,
    student_name: str,
    transcript_hash: str,
    issuer_institution: str,
) -> dict:
    """
    Notify employer when a student shares their transcript verification link.
    
    Args:
        employer_email: Employer's email address
        student_name: Student's name
        transcript_hash: SHA-256 hash of the transcript
        issuer_institution: Name of issuing institution
    
    Returns:
        dict with status
    """
    subject = f"Transcript Verification Request from {student_name}"
    
    body = f"""Dear Employer,

{student_name} has shared their academic transcript verification with you.

Transcript Details:
- Institution: {issuer_institution}
- Hash: {transcript_hash}

You can verify this transcript by visiting:
{verification_url}

Best regards,
{institution}
"""
    
    return send_email(employer_email, subject, body, issuer_institution)
