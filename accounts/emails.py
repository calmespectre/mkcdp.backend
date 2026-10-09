from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_verification_code(user, code, purpose):
    ttl = settings.CODE_TTL_MINUTES
    subject = "Your MKCDP verification code"
    text_body = (
        f"Hi {user.full_name or user.username},\n\n"
        f"Your MKCDP verification code is: {code}\n"
        f"This code expires in {ttl} minutes.\n\n"
        f"If you didn't request this, you can safely ignore this email.\n\n"
        f"— MKCDP"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#141414">
      <p style="font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#14532D;margin:0 0 12px">MKCDP</p>
      <h1 style="font-size:22px;margin:0 0 12px">Verify your email</h1>
      <p style="font-size:15px;color:#4A4A42;line-height:1.6">
        Hi {user.full_name or user.username},<br/>
        use the code below to continue. It expires in {ttl} minutes.
      </p>
      <div style="margin:24px 0;padding:18px 22px;border:1px solid #14532D22;border-radius:14px;text-align:center">
        <span style="font-size:32px;font-weight:700;letter-spacing:.35em;color:#14532D">{code}</span>
      </div>
      <p style="font-size:13px;color:#4A4A42">
        If you didn't request this, ignore this email.
      </p>
    </div>
    """
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)