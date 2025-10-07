# certifications app
"""
Utility functions for certificate generation and management.
"""

from django.conf import settings
from django.utils import timezone
import os

from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from arabic_reshaper import arabic_reshaper
from bidi.algorithm import get_display

def generate_certificate_filename(instance, filename):
    """
    Generate a unique filename for certificate uploads.
    Format: certificates/YEAR/MONTH/CERT-NUMBER_original-filename.ext
    """
    ext = filename.split('.')[-1]
    year = timezone.now().year
    month = timezone.now().month
    cert_number = instance.certificate_number or 'TEMP'
    
    filename = f"{cert_number}_{filename}"
    return os.path.join('certificates', str(year), f'{month:02d}', filename)


# def generate_certificate_pdf(certificate):
#     """
#     Generate a modern PDF certificate with Arabic support using ReportLab.
#     Requires: pip install arabic-reshaper python-bidi
    
#     You'll also need to download Arabic fonts (e.g., from Google Fonts):
#     - Amiri (https://fonts.google.com/specimen/Amiri)
#     - Cairo (https://fonts.google.com/specimen/Cairo)
#     - Tajawal (https://fonts.google.com/specimen/Tajawal)
#     """
#     buffer = BytesIO()
    
#     # Use landscape orientation for modern look
#     page_size = landscape(A4)
#     p = canvas.Canvas(buffer, pagesize=page_size)
#     width, height = page_size
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Current file directory
#     FONT_DIR = os.path.join(BASE_DIR, 'fonts')
#     # Register Arabic fonts (make sure to have the .ttf files in your project)
#     try:
#         pdfmetrics.registerFont(TTFont('Arabic-Bold', 
#             os.path.join(FONT_DIR, 'Cairo-Bold.ttf')))
#         pdfmetrics.registerFont(TTFont('Arabic-Regular', 
#             os.path.join(FONT_DIR, 'Cairo-Regular.ttf')))
#         has_arabic_font = True
#     except:
#         # Fallback if fonts aren't available
#         has_arabic_font = False
#         print("Warning: Arabic fonts not found. Arabic text may not display correctly.")
    
#     # Get certificate context
#     context = get_certificate_context(certificate)
    
#     # Modern color palette
#     primary_color = HexColor('#1e3a8a')      # Deep blue
#     secondary_color = HexColor('#3b82f6')    # Bright blue
#     accent_color = HexColor('#f59e0b')       # Amber
#     text_dark = HexColor('#1f2937')          # Dark gray
#     text_light = HexColor('#6b7280')         # Light gray
    
#     # Background - Modern gradient effect (simulated with rectangles)
#     p.setFillColor(HexColor('#f8fafc'))
#     p.rect(0, 0, width, height, fill=1, stroke=0)
    
#     # Decorative side panels
#     p.setFillColor(primary_color)
#     p.rect(0, 0, 0.4*inch, height, fill=1, stroke=0)
#     p.rect(width - 0.4*inch, 0, 0.4*inch, height, fill=1, stroke=0)
    
#     # Decorative top accent
#     p.setFillColor(accent_color)
#     p.rect(0.4*inch, height - 0.8*inch, width - 0.8*inch, 0.4*inch, fill=1, stroke=0)
    
#     # Modern border frame
#     p.setStrokeColor(primary_color)
#     p.setLineWidth(3)
#     p.rect(0.6*inch, 0.6*inch, width - 1.2*inch, height - 1.2*inch, fill=0, stroke=1)
    
#     # Inner decorative border
#     p.setStrokeColor(secondary_color)
#     p.setLineWidth(1)
#     p.rect(0.8*inch, 0.8*inch, width - 1.6*inch, height - 1.6*inch, fill=0, stroke=1)
    
#     # Decorative corner elements
#     corner_size = 0.6*inch
#     p.setFillColor(accent_color)
#     # Top left corner
#     p.circle(1*inch, height - 1*inch, corner_size/4, fill=1, stroke=0)
#     # Top right corner
#     p.circle(width - 1*inch, height - 1*inch, corner_size/4, fill=1, stroke=0)
#     # Bottom left corner
#     p.circle(1*inch, 1*inch, corner_size/4, fill=1, stroke=0)
#     # Bottom right corner
#     p.circle(width - 1*inch, 1*inch, corner_size/4, fill=1, stroke=0)
    
#     # Title section
#     p.setFillColor(primary_color)
#     p.setFont("Helvetica-Bold", 42)
#     p.drawCentredString(width/2, height - 1.8*inch, "CERTIFICATE")
    
#     p.setFillColor(text_light)
#     p.setFont("Helvetica", 16)
#     p.drawCentredString(width/2, height - 2.2*inch, "OF ACHIEVEMENT")
    
#     # Decorative line under title
#     p.setStrokeColor(accent_color)
#     p.setLineWidth(2)
#     p.line(width/2 - 2*inch, height - 2.4*inch, width/2 + 2*inch, height - 2.4*inch)
    
#     # Main text
#     p.setFillColor(text_dark)
#     p.setFont("Helvetica", 14)
#     p.drawCentredString(width/2, height - 3.2*inch, "This certificate is proudly presented to")
    
#     # Student name with Arabic support
#     student_name = context['student_name']
    
#     # Check if name contains Arabic characters
#     if has_arabic_font and any('\u0600' <= char <= '\u06FF' for char in student_name):
#         # Reshape and reorder Arabic text for proper display
#         reshaped_text = arabic_reshaper.reshape(student_name)
#         bidi_text = get_display(reshaped_text)
#         p.setFont("Arabic-Bold", 32)
#         p.setFillColor(secondary_color)
#         p.drawCentredString(width/2, height - 3.9*inch, bidi_text)
#     else:
#         # English name
#         p.setFont("Helvetica-Bold", 32)
#         p.setFillColor(secondary_color)
#         p.drawCentredString(width/2, height - 3.9*inch, student_name)
    
#     # Name underline
#     p.setStrokeColor(accent_color)
#     p.setLineWidth(1.5)
#     p.line(width/2 - 3.5*inch, height - 4.1*inch, width/2 + 3.5*inch, height - 4.1*inch)
    
#     # Course completion text
#     p.setFillColor(text_dark)
#     p.setFont("Helvetica", 14)
#     p.drawCentredString(width/2, height - 4.7*inch, "for successfully completing the course")
    
#     # Course title
#     p.setFont("Helvetica-Bold", 20)
#     p.setFillColor(primary_color)
#     p.drawCentredString(width/2, height - 5.2*inch, context['course_title'])
    
#     # Course details in a modern box layout
#     detail_y = height - 6.2*inch
#     box_width = 6*inch
#     box_x = width/2 - box_width/2
    
#     # Background box for details
#     p.setFillColor(HexColor('#e0e7ff'))
#     p.roundRect(box_x, detail_y - 0.6*inch, box_width, 0.9*inch, 0.1*inch, fill=1, stroke=0)
    
#     # Details in columns
#     p.setFillColor(text_dark)
#     p.setFont("Helvetica", 11)
    
#     col1_x = box_x + 0.5*inch
#     col2_x = box_x + 2.5*inch
#     col3_x = box_x + 4.5*inch
#     text_y = detail_y - 0.15*inch
    
#     # Column 1: Level
#     p.setFont("Helvetica-Bold", 11)
#     p.drawString(col1_x, text_y, "Level:")
#     p.setFont("Helvetica", 11)
#     p.drawString(col1_x, text_y - 0.25*inch, context['course_level'])
    
#     # Column 2: Duration
#     p.setFont("Helvetica-Bold", 11)
#     p.drawString(col2_x, text_y, "Duration:")
#     p.setFont("Helvetica", 11)
#     p.drawString(col2_x, text_y - 0.25*inch, f"{context['course_duration']} hours")
    
#     # Column 3: Completion Date
#     p.setFont("Helvetica-Bold", 11)
#     p.drawString(col3_x, text_y, "Completed:")
#     p.setFont("Helvetica", 11)
#     p.drawString(col3_x, text_y - 0.25*inch, 
#                  context['completion_date'].strftime('%d %b %Y'))
    
#     # Footer section
#     footer_y = 1.2*inch
    
#     # Certificate number
#     p.setFillColor(text_light)
#     p.setFont("Helvetica", 9)
#     p.drawString(1.2*inch, footer_y, f"Certificate No: {context['certificate_number']}")
    
#     # Issue date
#     p.drawRightString(width - 1.2*inch, footer_y, 
#                      f"Issued: {context['issue_date'].strftime('%d %B %Y')}")
    
#     # Verification code (centered)
#     p.setFont("Helvetica-Bold", 10)
#     p.setFillColor(primary_color)
#     p.drawCentredString(width/2, footer_y - 0.3*inch, 
#                        f"Verification Code: {context['verification_code']}")
    
#     # Optional: Add signature line
#     sig_y = 1.8*inch
#     sig_width = 2*inch
    
#     # Signature line
#     p.setStrokeColor(text_light)
#     p.setLineWidth(1)
#     p.line(width/2 - sig_width/2, sig_y, width/2 + sig_width/2, sig_y)
    
#     # Signature label
#     p.setFillColor(text_light)
#     p.setFont("Helvetica", 10)
#     p.drawCentredString(width/2, sig_y - 0.25*inch, "Authorized Signature")
    
#     # Optional: Add logo
#     # if context.get('institution_logo'):
#     #     try:
#     #         from reportlab.lib.utils import ImageReader
#     #         logo = ImageReader(context['institution_logo'])
#     #         logo_size = 1.2*inch
#     #         p.drawImage(logo, width/2 - logo_size/2, height - 1.3*inch,
#     #                    width=logo_size, height=logo_size, mask='auto')
#     #     except Exception as e:
#     #         print(f"Could not load logo: {e}")
    
#     p.showPage()
#     p.save()
    
#     buffer.seek(0)
#     return ContentFile(buffer.read(), name=f'{context["certificate_number"]}.pdf')

from io import BytesIO
from xhtml2pdf import pisa
from django.core.files.base import ContentFile
import arabic_reshaper
from bidi.algorithm import get_display

def get_certificate_html(context):
    """
    Generate modern landscape certificate HTML with CSS
    """
    
    # Handle Arabic text if needed
    student_name = context['student_name']
    name_direction = 'ltr'
    if any('\u0600' <= char <= '\u06FF' for char in student_name):
        student_name = get_display(arabic_reshaper.reshape(student_name))
        name_direction = 'rtl'
    
    course_title = context['course_title']
    if any('\u0600' <= char <= '\u06FF' for char in course_title):
        course_title = get_display(arabic_reshaper.reshape(course_title))
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Certificate of Achievement</title>
        <style>
            @page {{
                size: A4 landscape;
                margin: 0;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                width: 297mm;
                height: 210mm;
                overflow: hidden;
            }}
            
            /* Background Pattern */
            .bg-overlay {{
                position: absolute;
                width: 100%;
                height: 100%;
                background-image: 
                    repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.05) 35px, rgba(255,255,255,.05) 70px);
                opacity: 0.3;
            }}
            
            /* Main Certificate Container */
            .certificate-wrapper {{
                width: 277mm;
                height: 190mm;
                margin: 10mm;
                background: linear-gradient(to bottom, #ffffff 0%, #f8fafc 100%);
                border-radius: 20px;
                position: relative;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}
            
            /* Decorative Top Wave */
            .top-wave {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 80px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                clip-path: polygon(0 0, 100% 0, 100% 60%, 0 100%);
            }}
            
            /* Decorative Bottom Wave */
            .bottom-wave {{
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 60px;
                background: linear-gradient(90deg, #f093fb 0%, #764ba2 50%, #667eea 100%);
                clip-path: polygon(0 40%, 100% 0, 100% 100%, 0 100%);
            }}
            
            /* Border Frame */
            .border-outer {{
                position: absolute;
                top: 12mm;
                left: 12mm;
                right: 12mm;
                bottom: 12mm;
                border: 4px solid #667eea;
                border-radius: 15px;
                z-index: 1;
            }}
            
            .border-inner {{
                position: absolute;
                top: 15mm;
                left: 15mm;
                right: 15mm;
                bottom: 15mm;
                border: 2px solid #e0e7ff;
                border-radius: 12px;
                z-index: 1;
            }}
            
            /* Corner Decorations */
            .corner {{
                position: absolute;
                width: 40px;
                height: 40px;
                z-index: 2;
            }}
            
            .corner-tl {{
                top: 8mm;
                left: 8mm;
                background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                border-radius: 50%;
            }}
            
            .corner-tr {{
                top: 8mm;
                right: 8mm;
                background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
                border-radius: 50%;
            }}
            
            .corner-bl {{
                bottom: 8mm;
                left: 8mm;
                background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
                border-radius: 50%;
            }}
            
            .corner-br {{
                bottom: 8mm;
                right: 8mm;
                background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                border-radius: 50%;
            }}
            
            /* Side Accent Bars */
            .side-accent-left {{
                position: absolute;
                left: 0;
                top: 25%;
                width: 8px;
                height: 50%;
                background: linear-gradient(180deg, #f59e0b 0%, #ef4444 100%);
                z-index: 3;
            }}
            
            .side-accent-right {{
                position: absolute;
                right: 0;
                top: 25%;
                width: 8px;
                height: 50%;
                background: linear-gradient(180deg, #10b981 0%, #3b82f6 100%);
                z-index: 3;
            }}
            
            /* Main Content */
            .content {{
                position: relative;
                padding: 25mm 40mm;
                text-align: center;
                z-index: 5;
            }}
            
            /* Header Section */
            .header {{
                margin-top: 15px;
                margin-bottom: 20px;
            }}
            
            .badge-container {{
                margin-bottom: 15px;
            }}
            
            .certificate-badge {{
                display: inline-block;
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                position: relative;
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            }}
            
            .badge-star {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 36px;
                color: #fbbf24;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            .certificate-title {{
                font-size: 58px;
                font-weight: bold;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: 12px;
                margin: 10px 0;
                text-transform: uppercase;
            }}
            
            .certificate-subtitle {{
                font-size: 16px;
                color: #6b7280;
                letter-spacing: 6px;
                text-transform: uppercase;
                font-weight: 300;
                margin-top: 5px;
            }}
            
            .divider {{
                width: 120px;
                height: 4px;
                background: linear-gradient(90deg, transparent, #f59e0b, transparent);
                margin: 18px auto;
                border-radius: 2px;
            }}
            
            /* Body Section */
            .body {{
                margin: 25px 0;
            }}
            
            .presented-to {{
                font-size: 17px;
                color: #4b5563;
                margin-bottom: 20px;
                font-style: italic;
                font-weight: 300;
            }}
            
            .recipient-name {{
                font-size: 48px;
                font-weight: bold;
                color: #1e3a8a;
                margin: 25px 0;
                padding: 0 50px;
                position: relative;
                display: inline-block;
                direction: {name_direction};
            }}
            
            .name-underline {{
                width: 300px;
                height: 3px;
                background: linear-gradient(90deg, transparent, #667eea, transparent);
                margin: 15px auto;
                border-radius: 2px;
            }}
            
            .achievement-text {{
                font-size: 16px;
                color: #6b7280;
                margin: 25px 0 20px;
                font-weight: 300;
            }}
            
            .course-title {{
                font-size: 32px;
                font-weight: bold;
                color: #764ba2;
                margin: 20px 0 30px;
                padding: 0 40px;
                line-height: 1.3;
            }}
            
            /* Details Box */
            .details-container {{
                margin: 30px auto;
                max-width: 600px;
            }}
            
            .details-box {{
                background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 100%);
                padding: 25px 40px;
                border-radius: 20px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
                border: 2px solid #ddd6fe;
            }}
            
            .details-grid {{
                display: table;
                width: 100%;
                table-layout: fixed;
            }}
            
            .detail-item {{
                display: table-cell;
                text-align: center;
                padding: 8px 15px;
                vertical-align: middle;
            }}
            
            .detail-icon {{
                font-size: 24px;
                margin-bottom: 8px;
                display: block;
            }}
            
            .detail-label {{
                font-size: 11px;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 8px;
                font-weight: bold;
            }}
            
            .detail-value {{
                font-size: 18px;
                color: #1f2937;
                font-weight: bold;
            }}
            
            /* Footer Section */
            .footer {{
                position: absolute;
                bottom: 18mm;
                left: 0;
                right: 0;
                padding: 0 40mm;
                z-index: 5;
            }}
            
            .footer-content {{
                border-top: 2px solid #e5e7eb;
                padding-top: 15px;
            }}
            
            .signature-area {{
                text-align: center;
                margin-bottom: 15px;
            }}
            
            .signature-line {{
                width: 180px;
                height: 2px;
                background: linear-gradient(90deg, transparent, #9ca3af, transparent);
                margin: 0 auto 10px;
            }}
            
            .signature-label {{
                font-size: 12px;
                color: #6b7280;
                font-weight: 500;
            }}
            
            .metadata {{
                display: table;
                width: 100%;
                margin-top: 12px;
            }}
            
            .meta-left {{
                display: table-cell;
                text-align: left;
                font-size: 10px;
                color: #9ca3af;
                width: 33%;
            }}
            
            .meta-center {{
                display: table-cell;
                text-align: center;
                font-size: 11px;
                color: #667eea;
                font-weight: bold;
                width: 34%;
            }}
            
            .meta-right {{
                display: table-cell;
                text-align: right;
                font-size: 10px;
                color: #9ca3af;
                width: 33%;
            }}
            
            /* QR Code Placeholder */
            .qr-code {{
                position: absolute;
                bottom: 22mm;
                right: 18mm;
                width: 50px;
                height: 50px;
                background: #f3f4f6;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                z-index: 6;
            }}
            
            .qr-placeholder {{
                text-align: center;
                line-height: 50px;
                font-size: 9px;
                color: #9ca3af;
            }}
        </style>
    </head>
    <body>
        <div class="bg-overlay"></div>
        
        <div class="certificate-wrapper">
            <!-- Decorative Waves -->
            <div class="top-wave"></div>
            <div class="bottom-wave"></div>
            
            <!-- Borders -->
            <div class="border-outer"></div>
            <div class="border-inner"></div>
            
            <!-- Corner Decorations -->
            <div class="corner corner-tl"></div>
            <div class="corner corner-tr"></div>
            <div class="corner corner-bl"></div>
            <div class="corner corner-br"></div>
            
            <!-- Side Accents -->
            <div class="side-accent-left"></div>
            <div class="side-accent-right"></div>
            
            <!-- Main Content -->
            <div class="content">
                <!-- Header -->
                <div class="header">
                    <div class="badge-container">
                        <div class="certificate-badge">
                            <span class="badge-star">★</span>
                        </div>
                    </div>
                    <h1 class="certificate-title">CERTIFICATE</h1>
                    <p class="certificate-subtitle">Of Achievement</p>
                    <div class="divider"></div>
                </div>
                
                <!-- Body -->
                <div class="body">
                    <p class="presented-to">This certificate is proudly presented to</p>
                    
                    <h2 class="recipient-name">{student_name}</h2>
                    <div class="name-underline"></div>
                    
                    <p class="achievement-text">for successfully completing the course</p>
                    
                    <h3 class="course-title">{course_title}</h3>
                    
                    <!-- Details Box -->
                    <div class="details-container">
                        <div class="details-box">
                            <div class="details-grid">
                                <div class="detail-item">
                                    <span class="detail-icon">📚</span>
                                    <div class="detail-label">Level</div>
                                    <div class="detail-value">{context['course_level']}</div>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-icon">⏱️</span>
                                    <div class="detail-label">Duration</div>
                                    <div class="detail-value">{context['course_duration']} Hours</div>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-icon">✓</span>
                                    <div class="detail-label">Completed</div>
                                    <div class="detail-value">{context['completion_date'].strftime('%d %b %Y')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <div class="footer-content">
                    <div class="signature-area">
                        <div class="signature-line"></div>
                        <div class="signature-label">Authorized Signature</div>
                    </div>
                    
                    <div class="metadata">
                        <div class="meta-left">
                            Certificate No: {context['certificate_number']}
                        </div>
                        <div class="meta-center">
                            Verification: {context['verification_code']}
                        </div>
                        <div class="meta-right">
                            Issued: {context['issue_date'].strftime('%d %B %Y')}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- QR Code Placeholder -->
            <div class="qr-code">
                <div class="qr-placeholder">QR</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_certificate_pdf(certificate):
    """
    Main function to generate PDF certificate using xhtml2pdf
    
    Usage:
        certificate = Certificate.objects.get(id=1)
        pdf_file = generate_certificate_pdf(certificate)
        
        # Save to model
        certificate.pdf_file = pdf_file
        certificate.save()
        
        # Or return as HTTP response
        from django.http import HttpResponse
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{certificate.certificate_number}.pdf"'
        return response
    """
    
    # Get certificate context data
    context = get_certificate_context(certificate)
    
    # Generate HTML
    html_content = get_certificate_html(context)
    
    # Create PDF
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        html_content,
        dest=buffer,
        encoding='utf-8'
    )
    
    # Check for errors
    if pisa_status.err:
        raise Exception(f"Error generating PDF: {pisa_status.err}")
    
    # Return as ContentFile for Django
    buffer.seek(0)
    return ContentFile(
        buffer.read(),
        name=f'{context["certificate_number"]}.pdf'
    )


def validate_certificate_data(enrollment):
    """
    Validate that an enrollment is eligible for certificate issuance.
    
    Args:
        enrollment: Enrollment instance
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if enrollment is completed
    if enrollment.status != 'COMPLETED':
        return False, "Enrollment must be completed"
    
    # Check if enrollment has completion date
    if not enrollment.completion_date:
        return False, "Enrollment must have a completion date"
    
    # Check if certificate already exists
    if hasattr(enrollment, 'certificate'):
        return False, "Certificate already exists for this enrollment"
    
    # Check if course is active (optional business rule)
    if not enrollment.course.is_active:
        return False, "Cannot issue certificate for inactive course"
    
    # Check if student is active (optional business rule)
    if not enrollment.student.is_active:
        return False, "Cannot issue certificate for inactive student"
    
    return True, None


def get_certificate_context(certificate):
    """
    Get context data for certificate generation (for templates or PDF).
    
    Args:
        certificate: Certificate instance
    
    Returns:
        dict: Context data for certificate
    """
    context = {
        'certificate_number': certificate.certificate_number,
        'student_name': certificate.get_student_name(),
        'student_email': certificate.enrollment.student.email,
        'course_title': certificate.get_course_title(),
        'course_level': certificate.get_course_level(),
        'course_duration': certificate.enrollment.course.duration,
        'enrollment_date': certificate.enrollment.enrollment_date,
        'completion_date': certificate.get_completion_date(),
        'issue_date': certificate.issue_date,
        'duration_days': certificate.get_duration_days(),
        'verification_code': certificate.verification_code,
        'issued_by': certificate.issued_by.get_full_name() if certificate.issued_by else 'N/A',
        'institution_name': getattr(settings, 'INSTITUTION_NAME', 'Institute Name'),
        'institution_logo': getattr(settings, 'INSTITUTION_LOGO_URL', None),
    }
    return context


def bulk_issue_certificates(enrollment_ids, issued_by, issue_date=None, is_public=True):
    """
    Issue certificates for multiple enrollments.
    
    Args:
        enrollment_ids: List of enrollment IDs
        issued_by: User issuing the certificates
        issue_date: Date of issuance (defaults to today)
        is_public: Whether certificates should be publicly verifiable
    
    Returns:
        tuple: (success_count, error_list)
    """
    from enrollments.models import Enrollment
    from .models import Certificate
    
    if issue_date is None:
        issue_date = timezone.now().date()
    
    success_count = 0
    errors = []
    
    enrollments = Enrollment.objects.filter(id__in=enrollment_ids)
    
    for enrollment in enrollments:
        # Validate enrollment
        is_valid, error_msg = validate_certificate_data(enrollment)
        if not is_valid:
            errors.append({
                'enrollment_id': enrollment.id,
                'error': error_msg
            })
            continue
        
        try:
            Certificate.objects.create(
                enrollment=enrollment,
                issue_date=issue_date,
                is_public=is_public,
                issued_by=issued_by
            )
            success_count += 1
        except Exception as e:
            errors.append({
                'enrollment_id': enrollment.id,
                'error': str(e)
            })
    
    return success_count, errors


def format_certificate_number(year, sequence):
    """
    Format certificate number with consistent padding.
    
    Args:
        year: Year of issuance
        sequence: Sequence number
    
    Returns:
        str: Formatted certificate number
    """
    return f"CERT-{year}-{sequence:06d}"


def get_verification_url(certificate, request=None):
    """
    Get the full URL for certificate verification.
    
    Args:
        certificate: Certificate instance
        request: HttpRequest object (optional)
    
    Returns:
        str: Full verification URL
    """
    from django.urls import reverse
    
    if request:
        base_url = request.build_absolute_uri('/')
    else:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000/')
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    # Build verification URL
    verification_path = f"/api/certifications/public/certificates/verify/?code={certificate.verification_code}"
    
    return f"{base_url}{verification_path}"